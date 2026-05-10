from __future__ import annotations

import base64
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib import error, parse, request


UTC = timezone.utc
PRICING_STARTUP_TIMESTAMP_PATH = Path(__file__).resolve().parent / "cache" / "pricing_refresh_startup_at.txt"
PRICE_STATUS_UNAVAILABLE = "unavailable"
PRICE_STATUS_READY = "ready"
PRICE_STATUS_UNKNOWN = "UNK"
DEFAULT_CURRENCY = "USD"

_token_cache: dict[str, tuple[str, datetime]] = {}
_refresh_started = False


@dataclass
class PriceResult:
    status: str
    source: str = ""
    low_cents: int | None = None
    high_cents: int | None = None
    currency: str = DEFAULT_CURRENCY
    label: str = ""
    source_url: str = ""
    notes: str = ""


def serialize_pricing_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    low_cents = row["price_low_cents"]
    high_cents = row["price_high_cents"]
    has_range = low_cents is not None and high_cents is not None

    return {
        "status": row["price_status"] or PRICE_STATUS_UNAVAILABLE,
        "source": row["price_source"] or "",
        "label": row["price_label"] or "",
        "currency": row["price_currency"] or DEFAULT_CURRENCY,
        "low_cents": low_cents,
        "high_cents": high_cents,
        "display_range": format_price_range(low_cents, high_cents, row["price_currency"])
        if has_range
        else "Unavailable",
        "source_url": row["price_url"] or "",
        "notes": row["price_notes"] or "",
        "updated_at": row["price_updated_at"] or "",
    }


def format_price_range(low_cents: int | None, high_cents: int | None, currency: str) -> str:
    if low_cents is None or high_cents is None:
        return "Unavailable"
    low = f"${low_cents / 100:,.2f}"
    high = f"${high_cents / 100:,.2f}"
    if low_cents == high_cents:
        return low
    if currency and currency != "USD":
        return f"{low} - {high} {currency}"
    return f"{low} - {high}"


def pricing_is_configured() -> bool:
    return bool(
        os.getenv("EBAY_CLIENT_ID")
        and os.getenv("EBAY_CLIENT_SECRET")
    )


def pricing_debug_enabled() -> bool:
    return os.getenv("CATALOG_PRICE_DEBUG", "0") == "1"


def pricing_debug(message: str) -> None:
    if pricing_debug_enabled():
        print(f"[pricing] {message}")


def _get_item_field(item: Mapping[str, Any], key: str, default: Any = None) -> Any:
    if hasattr(item, "get"):
        return item.get(key, default)
    try:
        return item[key]
    except Exception:
        return default


def get_ebay_api_host() -> str:
    if os.getenv("EBAY_USE_SANDBOX", "0") == "1":
        return os.getenv("EBAY_API_HOST", "api.sandbox.ebay.com").strip()
    return os.getenv("EBAY_API_HOST", "api.ebay.com").strip()


def get_ebay_oauth_scope() -> str:
    if os.getenv("EBAY_MARKETPLACE_INSIGHTS_ENABLED", "0") == "1":
        return "https://api.ebay.com/oauth/api_scope/buy.marketplace.insights"
    return "https://api.ebay.com/oauth/api_scope"


def verify_ebay_pricing_configuration() -> dict[str, Any]:
    client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
    configured = bool(client_id and client_secret)
    insights_enabled = os.getenv("EBAY_MARKETPLACE_INSIGHTS_ENABLED", "0") == "1"
    host = get_ebay_api_host()
    scope = get_ebay_oauth_scope()

    status = "missing_credentials"
    token_available = False
    error = ""

    if configured:
        token = get_ebay_application_token(scope)
        if token:
            status = "ok"
            token_available = True
        else:
            status = "invalid_credentials"
            error = "Unable to obtain an OAuth token with the provided eBay credentials."

    return {
        "configured": configured,
        "status": status,
        "ebay_api_host": host,
        "oauth_scope": scope,
        "marketplace_insights_enabled": insights_enabled,
        "token_available": token_available,
        "error": error,
    }


def get_price_refresh_startup_hours() -> int:
    try:
        return max(1, int(os.getenv("CATALOG_PRICE_REFRESH_STARTUP_HOURS", "168")))
    except ValueError:
        return 168


def _read_last_startup_refresh_time() -> datetime | None:
    try:
        if not PRICING_STARTUP_TIMESTAMP_PATH.exists():
            return None
        text = PRICING_STARTUP_TIMESTAMP_PATH.read_text(encoding="utf-8").strip()
        if not text:
            return None
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _write_last_startup_refresh_time(timestamp: datetime) -> None:
    PRICING_STARTUP_TIMESTAMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRICING_STARTUP_TIMESTAMP_PATH.write_text(timestamp.isoformat(), encoding="utf-8")


def _should_refresh_on_startup() -> bool:
    last_refresh = _read_last_startup_refresh_time()
    if last_refresh is None:
        return True
    elapsed = datetime.now(UTC) - last_refresh
    return elapsed >= timedelta(hours=get_price_refresh_startup_hours())


def maybe_start_background_refresh(get_connection) -> None:
    global _refresh_started
    if _refresh_started:
        return
    if os.getenv("CATALOG_PRICE_REFRESH_ON_START", "1") != "1":
        return
    if not pricing_is_configured():
        return
    if not _should_refresh_on_startup():
        return

    _refresh_started = True

    def runner() -> None:
        try:
            with get_connection() as connection:
                refresh_catalog_prices(connection, limit=get_price_refresh_limit())
            _write_last_startup_refresh_time(datetime.now(UTC))
        except Exception:
            # Background pricing should never block app startup.
            pass

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()


def get_price_refresh_limit() -> int:
    try:
        return max(1, min(200, int(os.getenv("CATALOG_PRICE_REFRESH_LIMIT", "25"))))
    except ValueError:
        return 25


def get_price_refresh_ttl_hours() -> int:
    try:
        return max(1, int(os.getenv("CATALOG_PRICE_TTL_HOURS", "24")))
    except ValueError:
        return 24


def refresh_catalog_prices(
    connection,
    *,
    catalog_item_ids: Iterable[int] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    rows = list(select_catalog_rows_for_refresh(connection, catalog_item_ids, limit))
    refreshed = 0
    updated = 0

    for row in rows:
        refreshed += 1
        result = lookup_price(row)
        update_catalog_price(connection, row["id"], result)
        if result.status == PRICE_STATUS_READY:
            updated += 1

    return {
        "attempted": refreshed,
        "updated": updated,
        "configured": pricing_is_configured(),
    }


def select_catalog_rows_for_refresh(connection, catalog_item_ids, limit):
    params: list[Any] = []
    query = "SELECT * FROM catalog_items"

    if catalog_item_ids:
        ids = [int(item_id) for item_id in catalog_item_ids]
        placeholders = ", ".join("?" for _ in ids)
        query += f" WHERE id IN ({placeholders})"
        params.extend(ids)
    else:
        stale_cutoff = (
            datetime.now(UTC) - timedelta(hours=get_price_refresh_ttl_hours())
        ).strftime("%Y-%m-%d %H:%M:%S")
        query += " WHERE price_updated_at IS NULL OR price_updated_at = '' OR price_updated_at < ?"
        params.append(stale_cutoff)

    query += (
        " ORDER BY CASE WHEN price_updated_at IS NULL OR price_updated_at = '' THEN 0 ELSE 1 END,"
        " price_updated_at ASC, release_year ASC, item_name ASC"
    )
    if limit:
        query += " LIMIT ?"
        params.append(limit)

    return connection.execute(query, params).fetchall()


def update_catalog_price(connection, catalog_item_id: int, result: PriceResult) -> None:
    connection.execute(
        """
        UPDATE catalog_items
        SET price_source = ?,
            price_label = ?,
            price_low_cents = ?,
            price_high_cents = ?,
            price_currency = ?,
            price_url = ?,
            price_status = ?,
            price_notes = ?,
            price_updated_at = ?
        WHERE id = ?
        """,
        (
            result.source,
            result.label,
            result.low_cents,
            result.high_cents,
            result.currency,
            result.source_url,
            result.status,
            result.notes,
            datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
            catalog_item_id,
        ),
    )


def lookup_price(item: Mapping[str, Any]) -> PriceResult:
    for provider in (
        lookup_ebay_sold_comps,
        lookup_ebay_asking_prices,
    ):
        result = provider(item)
        if result and result.status == PRICE_STATUS_READY:
            return result

    existing_low = _get_item_field(item, "price_low_cents")
    existing_high = _get_item_field(item, "price_high_cents")
    existing_source = _get_item_field(item, "price_source", "")
    existing_label = _get_item_field(item, "price_label", "")
    existing_currency = _get_item_field(item, "price_currency", DEFAULT_CURRENCY)
    existing_url = _get_item_field(item, "price_url", "")
    existing_status = _get_item_field(item, "price_status", "")

    if existing_low is not None or existing_high is not None:
        pricing_debug(
            f"Preserving last known price for item_id={_get_item_field(item, 'id')} status={existing_status}"
        )
        return PriceResult(
            status=PRICE_STATUS_READY,
            source=existing_source,
            low_cents=existing_low,
            high_cents=existing_high,
            currency=existing_currency,
            label=existing_label,
            source_url=existing_url,
            notes="No new pricing found; preserving last known price.",
        )

    return PriceResult(
        status=PRICE_STATUS_UNKNOWN,
        source="",
        low_cents=None,
        high_cents=None,
        currency=DEFAULT_CURRENCY,
        label="",
        source_url="",
        notes="No pricing data found; status UNK.",
    )


def lookup_ebay_sold_comps(item: Mapping[str, Any]) -> PriceResult | None:
    if os.getenv("EBAY_MARKETPLACE_INSIGHTS_ENABLED", "0") != "1":
        return None

    token = get_ebay_application_token("https://api.ebay.com/oauth/api_scope/buy.marketplace.insights")
    if not token:
        return None

    host = get_ebay_api_host()
    endpoint = f"https://{host}/buy/marketplace_insights/v1_beta/item_sales/search"
    queries = build_catalog_search_queries(item)

    for query in queries:
        if not query:
            continue

        url = endpoint + "?" + parse.urlencode({"q": query, "limit": 10})
        pricing_debug(f"Sold comps query: {query}")
        try:
            data = fetch_json(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US"),
                },
            )
        except Exception as exc:
            pricing_debug(f"Sold comps request failed for query '{query}': {exc}")
            continue

        prices = extract_price_values(data, {"price", "itemSalePrice", "currentBidPrice"})
        pricing_debug(f"Sold comps result for '{query}' prices={prices}")
        if prices:
            return PriceResult(
                status=PRICE_STATUS_READY,
                source="eBay Sold Comps",
                low_cents=min(prices),
                high_cents=max(prices),
                currency=DEFAULT_CURRENCY,
                label="eBay sold comps (up to 90 days)",
                source_url=url,
                notes=f"eBay Marketplace Insights used query: {query}",
            )

    return None


def lookup_ebay_asking_prices(item: Mapping[str, Any]) -> PriceResult | None:
    token = get_ebay_application_token("https://api.ebay.com/oauth/api_scope")
    if not token:
        return None

    host = get_ebay_api_host()
    endpoint = f"https://{host}/buy/browse/v1/item_summary/search"
    filters = "buyingOptions:{FIXED_PRICE|AUCTION}"
    queries = build_catalog_search_queries(item)

    for query in queries:
        if not query:
            continue

        url = endpoint + "?" + parse.urlencode({"q": query, "limit": 10, "filter": filters})
        pricing_debug(f"Asking prices query: {query}")
        try:
            data = fetch_json(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US"),
                },
            )
        except Exception as exc:
            pricing_debug(f"Asking prices request failed for query '{query}': {exc}")
            continue

        item_summaries = data.get("itemSummaries", []) if isinstance(data, dict) else []
        prices = []
        for summary in item_summaries:
            price = summary.get("price", {})
            value = price.get("value")
            if value is None:
                continue
            try:
                prices.append(int(round(float(value) * 100)))
            except (TypeError, ValueError):
                continue

        if prices:
            return PriceResult(
                status=PRICE_STATUS_READY,
                source="eBay Asking",
                low_cents=min(prices),
                high_cents=max(prices),
                currency=DEFAULT_CURRENCY,
                label="eBay active listing range",
                source_url=url,
                notes=f"eBay active listings used query: {query}",
            )

    return None


def get_ebay_application_token(scope: str) -> str | None:
    client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None

    cached = _token_cache.get(scope)
    if cached and cached[1] > datetime.now(UTC):
        return cached[0]

    raw = f"{client_id}:{client_secret}".encode("utf-8")
    auth_header = base64.b64encode(raw).decode("ascii")
    data = parse.urlencode(
        {
            "grant_type": "client_credentials",
            "scope": scope,
        }
    ).encode("utf-8")
    host = get_ebay_api_host()
    req = request.Request(
        f"https://{host}/identity/v1/oauth2/token",
        data=data,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.URLError:
        return None

    token = payload.get("access_token")
    expires_in = int(payload.get("expires_in", 3600))
    if not token:
        return None

    _token_cache[scope] = (
        token,
        datetime.now(UTC) + timedelta(seconds=max(60, expires_in - 120)),
    )
    return token


def fetch_json(url: str, headers: Mapping[str, str] | None = None) -> dict[str, Any]:
    req = request.Request(url, headers=dict(headers or {}))
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        if pricing_debug_enabled():
            body = exc.read().decode("utf-8", errors="replace")
            pricing_debug(f"HTTPError {exc.code} {exc.reason} for {url}: {body}")
        raise


def build_catalog_search_query(item: Mapping[str, Any]) -> str:
    queries = build_catalog_search_queries(item)
    return queries[0] if queries else ""


def build_catalog_search_queries(item: Mapping[str, Any]) -> list[str]:
    def get_value(key: str) -> str:
        if hasattr(item, "get"):
            return str(item.get(key, "")).strip()
        try:
            return str(item[key]).strip()
        except Exception:
            return ""

    def clean_item_name(name: str) -> str:
        """Clean item names to remove scale info, parentheses, and other details that might not match eBay listings."""
        import re
        # Remove scale information like (1/55 Scale), (3.75"), etc.
        name = re.sub(r'\(\d+/?\d*\s*(?:scale|inch|"|cm|mm)\)', '', name, flags=re.IGNORECASE)
        # Remove other parenthetical info that might be too specific
        name = re.sub(r'\([^)]*(?:series|line|collection|wave)[^)]*\)', '', name, flags=re.IGNORECASE)
        # Clean up extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    item_name = clean_item_name(get_value("item_name"))
    property_name = get_value("property_name")
    manufacturer = get_value("manufacturer")
    release_year = get_value("release_year")
    wave = get_value("wave")

    # Skip empty, "0", or invalid values
    if release_year in ("0", "", "None", None):
        release_year = ""
    if wave in ("0", "", "None", None):
        wave = ""

    def combine(*values: str) -> str:
        return " ".join(value for value in values if value)

    queries: list[str] = []
    tried: set[str] = set()

    def add_query(*values: str) -> None:
        query = combine(*values)
        if query and len(query.split()) >= 2 and query not in tried:  # Require at least 2 words
            tried.add(query)
            queries.append(query)

    # Prioritize queries that are most likely to match eBay listings
    # Start with the most specific but realistic combinations
    if item_name and property_name and manufacturer:
        add_query(item_name, property_name, manufacturer)
    if item_name and property_name and release_year:
        add_query(item_name, property_name, release_year)
    if item_name and manufacturer and release_year:
        add_query(item_name, manufacturer, release_year)
    if item_name and property_name:
        add_query(item_name, property_name)
    if item_name and manufacturer:
        add_query(item_name, manufacturer)
    if item_name and release_year:
        add_query(item_name, release_year)
    if property_name and manufacturer:
        add_query(property_name, manufacturer)
    if item_name and wave:
        add_query(item_name, wave)
    # Only add single terms if they're substantial (more than 3 characters)
    if len(item_name) > 3:
        add_query(item_name)
    if len(property_name) > 3:
        add_query(property_name)

    return queries


def normalize_search_terms(value: str) -> list[str]:
    return [term for term in parse.unquote_plus(value).lower().replace("-", " ").split() if term]


def extract_price_values(data: Any, price_keys: set[str]) -> list[int]:
    values: list[int] = []

    def walk(node: Any, parent_key: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in price_keys and isinstance(value, dict):
                    amount = value.get("value")
                    if amount is not None:
                        try:
                            values.append(int(round(float(amount) * 100)))
                        except (TypeError, ValueError):
                            pass
                walk(value, key)
        elif isinstance(node, list):
            for child in node:
                walk(child, parent_key)

    walk(data)
    return values

from __future__ import annotations

import csv
import hashlib
import os
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import requests
import cloudscraper
from flask import Flask, Response, abort, jsonify, render_template, request
from pricing import (
    maybe_start_background_refresh,
    refresh_catalog_prices,
    serialize_pricing_summary,
    verify_ebay_pricing_configuration,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventory.db"
IMAGE_CACHE_DIR = BASE_DIR / "cache" / "catalog_images"
CATALOG_SEED_PATHS = [
    BASE_DIR / "data" / "catalog_seed.csv",
    BASE_DIR / "data" / "star_wars_catalog_generated.csv",
    BASE_DIR / "data" / "star_wars_actionfigure411_expanded.csv",
    BASE_DIR / "data" / "advanced_dungeons_dragons_catalog_seed.csv",
    BASE_DIR / "data" / "a_team_catalog_seed.csv",
    BASE_DIR / "data" / "barnyard_commandos_catalog_seed.csv",
    BASE_DIR / "data" / "beetlejuice_catalog_seed.csv",
    BASE_DIR / "data" / "biker_mice_from_mars_catalog_seed.csv",
    BASE_DIR / "data" / "bill_and_ted_catalog_seed.csv",
    BASE_DIR / "data" / "bionic_six_catalog_seed.csv",
    BASE_DIR / "data" / "blackstar_catalog_seed.csv",
    BASE_DIR / "data" / "bravestarr_catalog_seed.csv",
    BASE_DIR / "data" / "bucky_ohare_catalog_seed.csv",
    BASE_DIR / "data" / "ben_10_catalog_seed.csv",
    BASE_DIR / "data" / "captain_planet_catalog_seed.csv",
    BASE_DIR / "data" / "collectables_access_catalog_seed.csv",
    BASE_DIR / "data" / "captain_power_catalog_seed.csv",
    BASE_DIR / "data" / "care_bears_catalog_seed.csv",
    BASE_DIR / "data" / "centurions_catalog_seed.csv",
    BASE_DIR / "data" / "computer_warriors_catalog_seed.csv",
    BASE_DIR / "data" / "cops_n_crooks_catalog_seed.csv",
    BASE_DIR / "data" / "crystar_catalog_seed.csv",
    BASE_DIR / "data" / "darkwing_duck_catalog_seed.csv",
    BASE_DIR / "data" / "defenders_of_the_earth_catalog_seed.csv",
    BASE_DIR / "data" / "food_fighters_catalog_seed.csv",
    BASE_DIR / "data" / "golden_girl_catalog_seed.csv",
    BASE_DIR / "data" / "ghostbusters_real_catalog_seed.csv",
    BASE_DIR / "data" / "ghostbusters_filmation_catalog_seed.csv",
    BASE_DIR / "data" / "ghostbusters_extreme_catalog_seed.csv",
    BASE_DIR / "data" / "ghostbusters_modern_catalog_seed.csv",
    BASE_DIR / "data" / "ghostbusters_mattel_catalog_seed.csv",
    BASE_DIR / "data" / "gold_lightan_catalog_seed.csv",
    BASE_DIR / "data" / "greatest_american_hero_catalog_seed.csv",
    BASE_DIR / "data" / "gobots_catalog_seed.csv",
    BASE_DIR / "data" / "inhumanoids_catalog_seed.csv",
    BASE_DIR / "data" / "jem_catalog_seed.csv",
    BASE_DIR / "data" / "karate_kid_catalog_seed.csv",
    BASE_DIR / "data" / "mask_catalog_seed.csv",
    BASE_DIR / "data" / "muscle_catalog_seed.csv",
    BASE_DIR / "data" / "madballs_catalog_seed.csv",
    BASE_DIR / "data" / "mego_dolls_catalog_seed.csv",
    BASE_DIR / "data" / "machine_robo_catalog_seed.csv",
    BASE_DIR / "data" / "microman_catalog_seed.csv",
    BASE_DIR / "data" / "micronauts_catalog_seed.csv",
    BASE_DIR / "data" / "peewees_playhouse_catalog_seed.csv",
    BASE_DIR / "data" / "police_academy_catalog_seed.csv",
    BASE_DIR / "data" / "pulsar_catalog_seed.csv",
    BASE_DIR / "data" / "ring_raiders_catalog_seed.csv",
    BASE_DIR / "data" / "robotech_catalog_seed.csv",
    BASE_DIR / "data" / "robotech_macross_japanese_catalog_seed.csv",
    BASE_DIR / "data" / "sectaurs_catalog_seed.csv",
    BASE_DIR / "data" / "silverhawks_catalog_seed.csv",
    BASE_DIR / "data" / "starriors_catalog_seed.csv",
    BASE_DIR / "data" / "strawberry_shortcake_catalog_seed.csv",
    BASE_DIR / "data" / "super_naturals_catalog_seed.csv",
    BASE_DIR / "data" / "swamp_thing_catalog_seed.csv",
    BASE_DIR / "data" / "teddy_ruxpin_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_vintage_playmates_1988_1990_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_vintage_playmates_1991_1993_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_vintage_playmates_1994_1997_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_2003_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_fast_forward_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_2012_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_next_mutation_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_movie_2007_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_mutant_mayhem_actionfigure411_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_tales_catalog_seed.csv",
    BASE_DIR / "data" / "tmnt_small_modern_catalog_seed.csv",
    BASE_DIR / "data" / "thundercats_ljn_catalog_seed.csv",
    BASE_DIR / "data" / "thundercats_super7_catalog_seed.csv",
    BASE_DIR / "data" / "thundercats_matty_catalog_seed.csv",
    BASE_DIR / "data" / "thundercats_miniatures_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_g1_1984_1985_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_g1_1986_1987_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_g1_1988_1990_catalog_seed.csv",
    BASE_DIR / "data" / "tron_catalog_seed.csv",
    BASE_DIR / "data" / "visionaries_catalog_seed.csv",
    BASE_DIR / "data" / "voltron_catalog_seed.csv",
    BASE_DIR / "data" / "xmen_toybiz_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_battle_beasts_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_japanese_g1_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_transformerland_expanded_catalog_seed.csv",
    BASE_DIR / "data" / "transformers_transformerland_supplemental_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_mmpr_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_sentai_mmpr_era_catalog_seed.csv",
    BASE_DIR / "data" / "power_lords_catalog_seed.csv",
    BASE_DIR / "data" / "pirates_of_dark_water_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_zeo_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_zeo_ohranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_turbo_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_turbo_carranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_in_space_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_in_space_megaranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_lost_galaxy_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_lost_galaxy_gingaman_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_lightspeed_rescue_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_lightspeed_rescue_gogofive_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_time_force_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_time_force_timeranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_wild_force_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_wild_force_gaoranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_ninja_storm_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_ninja_storm_hurricaneger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_thunder_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_thunder_abaranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_spd_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_spd_dekaranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_mystic_force_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_mystic_force_magiranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_operation_overdrive_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_operation_overdrive_boukenger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_jungle_fury_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_jungle_fury_gekiranger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_rpm_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_rpm_goonger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_samurai_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_samurai_shinkenger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_megaforce_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_megaforce_goseiger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_super_megaforce_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_super_megaforce_gokaiger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_charge_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_super_charge_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_charge_kyoryuger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_ninja_steel_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_super_ninja_steel_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_ninja_steel_ninninger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_beast_morphers_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_beast_morphers_gobusters_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_fury_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_dino_fury_ryusoulger_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_cosmic_fury_catalog_seed.csv",
    BASE_DIR / "data" / "power_rangers_cosmic_fury_kyuranger_catalog_seed.csv",
    BASE_DIR / "data" / "motu_chronicles_catalog_seed.csv",
    BASE_DIR / "data" / "motu_origins_modern_catalog_seed.csv",
    BASE_DIR / "data" / "motu_masterverse_catalog_seed.csv",
    BASE_DIR / "data" / "gi_joe_arah_catalog_seed.csv",
    BASE_DIR / "data" / "gi_joe_classified_catalog_seed.csv",
    BASE_DIR / "data" / "gi_joe_modern_arah_catalog_seed.csv",
    BASE_DIR / "data" / "gi_joe_modern_2002_2005_catalog_seed.csv",
    BASE_DIR / "data" / "gi_joe_modern_2006_2009_catalog_seed.csv",
    BASE_DIR / "data" / "gi_joe_modern_vehicle_catalog_seed.csv",
]
DEFAULT_CONDITIONS = [
    "Sealed",
    "Boxed",
    "Carded",
    "Complete",
    "Loose",
    "Opened",
    "Damaged",
]
ALLOWED_IMAGE_HOSTS = {
    "www.figurerealm.com",
    "figurerealm.com",
    "collectorarchive.com",
    "www.collectorarchive.com",
    "actiontoys.com",
    "www.actiontoys.com",
    "mrjoe.com",
    "www.mrjoe.com",
    "www.toymania.com",
    "toymania.com",
    "www.figuronomy.com",
    "figuronomy.com",
    "galacticfigures.com",
    "www.toyarchive.com",
    "toyarchive.com",
    "www.dallasvintagetoys.com",
    "dallasvintagetoys.com",
    "2warpstoneptune.com",
    "www.2warpstoneptune.com",
    "wheeljackslab.com",
    "www.wheeljackslab.com",
    "6533-43952.el-alt.com",
    "toyzinger.com",
    "www.toyzinger.com",
    "image.toyzinger.com",
    "actionfigure411.com",
    "www.actionfigure411.com",
    "www.thetoycollectorsguide.com",
    "thetoycollectorsguide.com",
    "transformerland.com",
    "www.micromanforever.org",
    "micromanforever.org",
    "www.micro-outpost.com",
    "micro-outpost.com",
    "www.micropola.org",
    "micropola.org",
    "www.transformerland.com",
    "wharble.com",
    "www.wharble.com",
    "rockjem.com",
    "www.rockjem.com",
    "www.he-man.org",
    "he-man.org",
    "www.theoldrobots.com",
    "theoldrobots.com",
    "www.tmnttoys.com",
    "tmnttoys.com",
    "mymegolike.com",
    "www.mymegolike.com",
    "sourcehorsemen.com",
    "www.sourcehorsemen.com",
    "buckyohare.org",
    "www.buckyohare.org",
    "yojoe.com",
    "www.yojoe.com",
    "static.wikia.nocookie.net",
    "legendsverse.com",
    "www.legendsverse.com",
    "media.legendsverse.com",
  }


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def build_catalog_image_url(source_url: str) -> str:
    if not source_url:
        return ""

    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in ALLOWED_IMAGE_HOSTS:
        return source_url

    return f"/catalog-image?url={quote(source_url, safe='')}"


def catalog_image_cache_paths(source_url: str) -> tuple[Path, Path]:
    cache_key = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
    return (
        IMAGE_CACHE_DIR / f"{cache_key}.img",
        IMAGE_CACHE_DIR / f"{cache_key}.type",
    )


@lru_cache(maxsize=512)
def fetch_catalog_image(source_url: str) -> tuple[bytes, str]:
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    content_path, type_path = catalog_image_cache_paths(source_url)
    if content_path.exists() and type_path.exists():
        return content_path.read_bytes(), type_path.read_text(encoding="utf-8").strip()

    parsed = urlparse(source_url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    scraper_hosts = {
        "www.figurerealm.com",
        "figurerealm.com",
        "www.actionfigure411.com",
        "actionfigure411.com",
        "www.transformerland.com",
        "transformerland.com",
    }
    if parsed.netloc.lower() in scraper_hosts:
        headers["Referer"] = "https://www.figurerealm.com/"
        if parsed.netloc.lower() in {"www.actionfigure411.com", "actionfigure411.com"}:
            headers["Referer"] = "https://www.actionfigure411.com/"
        elif parsed.netloc.lower() in {"www.transformerland.com", "transformerland.com"}:
            headers["Referer"] = "https://www.transformerland.com/"
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        response = scraper.get(source_url, timeout=30, headers=headers)
    else:
        headers["Referer"] = parsed.scheme + "://" + parsed.netloc + "/"
        response = requests.get(source_url, timeout=30, headers=headers)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    content = response.content
    content_path.write_bytes(content)
    type_path.write_text(content_type, encoding="utf-8")
    return content, content_type


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                series TEXT DEFAULT '',
                category TEXT DEFAULT '',
                item_number TEXT DEFAULT '',
                owned INTEGER NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                condition TEXT DEFAULT 'Complete',
                storage_location TEXT DEFAULT '',
                source_name TEXT DEFAULT '',
                source_key TEXT DEFAULT '',
                catalog_item_id INTEGER,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_item_column(connection, "source_name", "TEXT DEFAULT ''")
        ensure_item_column(connection, "source_key", "TEXT DEFAULT ''")
        ensure_item_column(connection, "catalog_item_id", "INTEGER")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_source ON items (source_name, source_key)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_catalog_item_id ON items (catalog_item_id)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS catalog_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                franchise TEXT NOT NULL,
                property_name TEXT NOT NULL,
                product_line TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                release_year INTEGER NOT NULL,
                wave TEXT DEFAULT '',
                item_name TEXT NOT NULL,
                release_type TEXT NOT NULL DEFAULT 'vintage',
                source_name TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                packaged_image_url TEXT DEFAULT '',
                price_source TEXT DEFAULT '',
                price_label TEXT DEFAULT '',
                price_low_cents INTEGER,
                price_high_cents INTEGER,
                price_currency TEXT DEFAULT 'USD',
                price_url TEXT DEFAULT '',
                price_status TEXT DEFAULT 'unavailable',
                price_notes TEXT DEFAULT '',
                price_updated_at TEXT DEFAULT '',
                manual_catalog_override INTEGER NOT NULL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (franchise, property_name, product_line, manufacturer, release_year, wave, item_name, source_url)
            )
            """
        )
        ensure_catalog_column(connection, "image_url", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "packaged_image_url", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "price_source", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "price_label", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "price_low_cents", "INTEGER")
        ensure_catalog_column(connection, "price_high_cents", "INTEGER")
        ensure_catalog_column(connection, "price_currency", "TEXT DEFAULT 'USD'")
        ensure_catalog_column(connection, "price_url", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "price_status", "TEXT DEFAULT 'unavailable'")
        ensure_catalog_column(connection, "price_notes", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "price_updated_at", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "manual_catalog_override", "INTEGER NOT NULL DEFAULT 0")
        ensure_catalog_column(connection, "owned", "INTEGER NOT NULL DEFAULT 0")
        ensure_catalog_column(connection, "quantity_owned", "INTEGER NOT NULL DEFAULT 0")
        ensure_catalog_column(connection, "complete_count", "INTEGER NOT NULL DEFAULT 0")
        ensure_catalog_column(connection, "sealed_count", "INTEGER NOT NULL DEFAULT 0")
        ensure_catalog_column(connection, "packaged_count", "INTEGER NOT NULL DEFAULT 0")
        ensure_catalog_column(connection, "condition", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "storage_location", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "ownership_notes", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "inventory_source_name", "TEXT DEFAULT ''")
        ensure_catalog_column(connection, "inventory_updated_at", "TEXT DEFAULT ''")
        rebuild_catalog_table_if_needed(connection)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_catalog_release_year ON catalog_items (release_year)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_catalog_franchise ON catalog_items (franchise)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_catalog_release_type ON catalog_items (release_type)"
        )

    sync_catalog_seed_data()
    sync_catalog_inventory_from_linked_items()
    migrate_catalog_inventory_from_items_if_needed()


def ensure_item_column(
    connection: sqlite3.Connection, column_name: str, column_definition: str
) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(items)").fetchall()
    }
    if column_name not in columns:
        connection.execute(f"ALTER TABLE items ADD COLUMN {column_name} {column_definition}")


def ensure_catalog_column(
    connection: sqlite3.Connection, column_name: str, column_definition: str
) -> None:
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(catalog_items)").fetchall()
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE catalog_items ADD COLUMN {column_name} {column_definition}"
        )


def rebuild_catalog_table_if_needed(connection: sqlite3.Connection) -> None:
    table_sql_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'catalog_items'"
    ).fetchone()
    table_sql = table_sql_row["sql"] if table_sql_row else ""
    if (
        "source_url)" not in table_sql
        or "price_source" not in table_sql
        or "packaged_image_url" not in table_sql
        or "quantity_owned" not in table_sql
    ):
        connection.execute("DROP TABLE IF EXISTS catalog_items_new")
        connection.execute(
            """
            CREATE TABLE catalog_items_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                franchise TEXT NOT NULL,
                property_name TEXT NOT NULL,
                product_line TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                release_year INTEGER NOT NULL,
                wave TEXT DEFAULT '',
                item_name TEXT NOT NULL,
                release_type TEXT NOT NULL DEFAULT 'vintage',
                source_name TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                packaged_image_url TEXT DEFAULT '',
                price_source TEXT DEFAULT '',
                price_label TEXT DEFAULT '',
                price_low_cents INTEGER,
                price_high_cents INTEGER,
                price_currency TEXT DEFAULT 'USD',
                price_url TEXT DEFAULT '',
                price_status TEXT DEFAULT 'unavailable',
                price_notes TEXT DEFAULT '',
                price_updated_at TEXT DEFAULT '',
                manual_catalog_override INTEGER NOT NULL DEFAULT 0,
                owned INTEGER NOT NULL DEFAULT 0,
                quantity_owned INTEGER NOT NULL DEFAULT 0,
                complete_count INTEGER NOT NULL DEFAULT 0,
                sealed_count INTEGER NOT NULL DEFAULT 0,
                packaged_count INTEGER NOT NULL DEFAULT 0,
                condition TEXT DEFAULT '',
                storage_location TEXT DEFAULT '',
                ownership_notes TEXT DEFAULT '',
                inventory_source_name TEXT DEFAULT '',
                inventory_updated_at TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (franchise, property_name, product_line, manufacturer, release_year, wave, item_name, source_url)
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO catalog_items_new (
                id,
                franchise,
                property_name,
                product_line,
                manufacturer,
                release_year,
                wave,
                item_name,
                release_type,
                source_name,
                source_url,
                image_url,
                packaged_image_url,
                price_source,
                price_label,
                price_low_cents,
                price_high_cents,
                price_currency,
                price_url,
                price_status,
                price_notes,
                price_updated_at,
                manual_catalog_override,
                owned,
                quantity_owned,
                complete_count,
                sealed_count,
                packaged_count,
                condition,
                storage_location,
                ownership_notes,
                inventory_source_name,
                inventory_updated_at,
                notes,
                created_at
            )
            SELECT
                id,
                franchise,
                property_name,
                product_line,
                manufacturer,
                release_year,
                wave,
                item_name,
                release_type,
                source_name,
                source_url,
                image_url,
                packaged_image_url,
                price_source,
                price_label,
                price_low_cents,
                price_high_cents,
                price_currency,
                price_url,
                price_status,
                price_notes,
                price_updated_at,
                COALESCE(manual_catalog_override, 0),
                COALESCE(owned, 0),
                COALESCE(quantity_owned, 0),
                COALESCE(complete_count, 0),
                COALESCE(sealed_count, 0),
                COALESCE(packaged_count, 0),
                COALESCE(condition, ''),
                COALESCE(storage_location, ''),
                COALESCE(ownership_notes, ''),
                COALESCE(inventory_source_name, ''),
                COALESCE(inventory_updated_at, ''),
                notes,
                created_at
            FROM catalog_items
            """
        )
        connection.execute("DROP TABLE catalog_items")
        connection.execute("ALTER TABLE catalog_items_new RENAME TO catalog_items")


def infer_catalog_condition(
    quantity_owned: int,
    complete_count: int,
    sealed_count: int,
    packaged_count: int,
    explicit_condition: str = "",
) -> str:
    explicit = (explicit_condition or "").strip()
    if explicit:
        return explicit
    if quantity_owned <= 0:
        return ""
    if sealed_count >= quantity_owned:
        return "Sealed"
    if complete_count >= quantity_owned:
        return "Complete"
    if packaged_count >= quantity_owned:
        return "Packaged"
    return "Mixed"


def migrate_catalog_inventory_from_items_if_needed() -> None:
    with get_connection() as connection:
        has_direct_inventory = connection.execute(
            """
            SELECT COUNT(*)
            FROM catalog_items
            WHERE quantity_owned > 0
               OR TRIM(COALESCE(condition, '')) <> ''
               OR TRIM(COALESCE(storage_location, '')) <> ''
               OR TRIM(COALESCE(ownership_notes, '')) <> ''
            """
        ).fetchone()[0]
        legacy_linked_items = connection.execute(
            """
            SELECT COUNT(*)
            FROM items
            WHERE catalog_item_id IS NOT NULL
              AND owned = 1
            """
        ).fetchone()[0]
        if has_direct_inventory or legacy_linked_items == 0:
            return

        rows = connection.execute(
            """
            SELECT
                catalog_item_id,
                SUM(CASE WHEN owned = 1 THEN quantity ELSE 0 END) AS quantity_owned,
                SUM(
                    CASE
                        WHEN owned = 1
                          AND (
                              lower(condition) LIKE '%complete%'
                              OR lower(condition) LIKE '%sealed%'
                          )
                        THEN quantity
                        ELSE 0
                    END
                ) AS complete_count,
                SUM(CASE WHEN owned = 1 AND lower(condition) LIKE '%sealed%' THEN quantity ELSE 0 END) AS sealed_count,
                SUM(
                    CASE
                        WHEN owned = 1
                          AND (
                              lower(condition) LIKE '%sealed%'
                              OR lower(condition) LIKE '%boxed%'
                              OR lower(condition) LIKE '%carded%'
                              OR lower(condition) LIKE '%opened%'
                              OR lower(condition) LIKE '%packaged%'
                          )
                        THEN quantity
                        ELSE 0
                    END
                ) AS packaged_count,
                MAX(CASE WHEN TRIM(COALESCE(storage_location, '')) <> '' THEN storage_location ELSE '' END) AS storage_location,
                GROUP_CONCAT(CASE WHEN TRIM(COALESCE(notes, '')) <> '' THEN notes END, ' | ') AS ownership_notes,
                MAX(CASE WHEN TRIM(COALESCE(source_name, '')) <> '' THEN source_name ELSE 'Legacy items' END) AS inventory_source_name
            FROM items
            WHERE catalog_item_id IS NOT NULL
              AND owned = 1
            GROUP BY catalog_item_id
            """
        ).fetchall()

        for row in rows:
            quantity_owned = int(row["quantity_owned"] or 0)
            complete_count = int(row["complete_count"] or 0)
            sealed_count = int(row["sealed_count"] or 0)
            packaged_count = int(row["packaged_count"] or 0)
            connection.execute(
                """
                UPDATE catalog_items
                SET owned = ?,
                    quantity_owned = ?,
                    complete_count = ?,
                    sealed_count = ?,
                    packaged_count = ?,
                    condition = ?,
                    storage_location = ?,
                    ownership_notes = ?,
                    inventory_source_name = ?,
                    inventory_updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    1 if quantity_owned > 0 else 0,
                    quantity_owned,
                    complete_count,
                    sealed_count,
                    packaged_count,
                    infer_catalog_condition(
                        quantity_owned,
                        complete_count,
                        sealed_count,
                        packaged_count,
                    ),
                    row["storage_location"] or "",
                    row["ownership_notes"] or "",
                    row["inventory_source_name"] or "Legacy items",
                    row["catalog_item_id"],
                ),
            )
        connection.commit()


def sync_catalog_inventory_from_linked_items() -> None:
    with get_connection() as connection:
        linked_items = connection.execute(
            """
            SELECT COUNT(*)
            FROM items
            WHERE catalog_item_id IS NOT NULL
              AND owned = 1
            """
        ).fetchone()[0]
        if linked_items == 0:
            return

        connection.execute(
            """
            UPDATE catalog_items
            SET owned = 0,
                quantity_owned = 0,
                complete_count = 0,
                sealed_count = 0,
                packaged_count = 0,
                condition = '',
                storage_location = '',
                ownership_notes = '',
                inventory_source_name = '',
                inventory_updated_at = ''
            WHERE inventory_source_name <> 'Manual'
            """
        )

        rows = connection.execute(
            """
            SELECT
                catalog_item_id,
                SUM(CASE WHEN owned = 1 THEN quantity ELSE 0 END) AS quantity_owned,
                SUM(
                    CASE
                        WHEN owned = 1
                          AND (
                              lower(condition) LIKE '%complete%'
                              OR lower(condition) LIKE '%sealed%'
                          )
                        THEN quantity
                        ELSE 0
                    END
                ) AS complete_count,
                SUM(CASE WHEN owned = 1 AND lower(condition) LIKE '%sealed%' THEN quantity ELSE 0 END) AS sealed_count,
                SUM(
                    CASE
                        WHEN owned = 1
                          AND (
                              lower(condition) LIKE '%sealed%'
                              OR lower(condition) LIKE '%boxed%'
                              OR lower(condition) LIKE '%carded%'
                              OR lower(condition) LIKE '%opened%'
                              OR lower(condition) LIKE '%packaged%'
                          )
                        THEN quantity
                        ELSE 0
                    END
                ) AS packaged_count,
                MAX(CASE WHEN TRIM(COALESCE(storage_location, '')) <> '' THEN storage_location ELSE '' END) AS storage_location,
                GROUP_CONCAT(CASE WHEN TRIM(COALESCE(notes, '')) <> '' THEN notes END, ' | ') AS ownership_notes,
                MAX(
                    CASE
                        WHEN TRIM(COALESCE(source_name, '')) <> '' THEN source_name
                        ELSE 'Legacy items'
                    END
                ) AS inventory_source_name
            FROM items
            WHERE catalog_item_id IS NOT NULL
              AND owned = 1
            GROUP BY catalog_item_id
            """
        ).fetchall()

        for row in rows:
            quantity_owned = int(row["quantity_owned"] or 0)
            complete_count = int(row["complete_count"] or 0)
            sealed_count = int(row["sealed_count"] or 0)
            packaged_count = int(row["packaged_count"] or 0)
            connection.execute(
                """
                UPDATE catalog_items
                SET owned = ?,
                    quantity_owned = ?,
                    complete_count = ?,
                    sealed_count = ?,
                    packaged_count = ?,
                    condition = ?,
                    storage_location = ?,
                    ownership_notes = ?,
                    inventory_source_name = ?,
                    inventory_updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND inventory_source_name <> 'Manual'
                """,
                (
                    1 if quantity_owned > 0 else 0,
                    quantity_owned,
                    complete_count,
                    sealed_count,
                    packaged_count,
                    infer_catalog_condition(
                        quantity_owned,
                        complete_count,
                        sealed_count,
                        packaged_count,
                    ),
                    row["storage_location"] or "",
                    row["ownership_notes"] or "",
                    row["inventory_source_name"] or "Legacy items",
                    row["catalog_item_id"],
                ),
            )
        connection.commit()


def sync_catalog_seed_data() -> None:
    with get_connection() as connection:
        connection.execute("DROP TABLE IF EXISTS catalog_inventory_snapshot")
        connection.execute(
            """
            CREATE TEMP TABLE catalog_inventory_snapshot AS
            SELECT
                franchise,
                property_name,
                product_line,
                manufacturer,
                release_year,
                wave,
                item_name,
                source_url,
                owned,
                quantity_owned,
                complete_count,
                sealed_count,
                packaged_count,
                condition,
                storage_location,
                ownership_notes,
                inventory_source_name,
                inventory_updated_at
            FROM catalog_items
            """
        )
        connection.execute(
            """
            DELETE FROM catalog_items
            WHERE franchise = 'Care Bears'
              AND product_line = 'Vintage Care Bears - Poseable Figures with Accessories'
            """
        )
        connection.execute(
            """
            DELETE FROM catalog_items
            WHERE franchise = 'GoBots'
              AND property_name = 'Rock Lords'
              AND product_line = 'Rock Lords'
              AND wave = 'Heroic Rock Lords'
              AND item_name = 'Boulder'
              AND source_name = 'Collectables Access DB'
            """
        )
        connection.execute(
            """
            DELETE FROM catalog_items
            WHERE franchise = 'GoBots'
              AND product_line = 'Super Go-Bots'
              AND wave = 'Super Go-Bots'
              AND item_name = 'Staks Transport (Blue)'
              AND source_name = 'Collectables Access DB'
            """
        )

        for seed_path in CATALOG_SEED_PATHS:
            if not seed_path.exists():
                continue

            with seed_path.open(newline="", encoding="utf-8-sig") as csv_file:
                reader = csv.DictReader(csv_file)
                def is_access_licensed_product_row(raw_row: dict[str, str]) -> bool:
                    haystack = " ".join(
                        (
                            raw_row.get("wave", ""),
                            raw_row.get("product_line", ""),
                            raw_row.get("release_type", ""),
                            raw_row.get("item_name", ""),
                            raw_row.get("notes", ""),
                        )
                    ).lower()
                    return "licensed product" in haystack or "licenced product" in haystack

                rows = [
                    build_normalized_catalog_row(seed_path, row)
                    for row in reader
                    if not (
                        seed_path.name == "catalog_seed.csv"
                        and row["franchise"].strip() == "Star Wars"
                        and row["source_name"].strip() == "Galactic Figures"
                        and row["release_type"].strip().lower() == "vintage"
                    )
                    and not (
                        seed_path.name == "collectables_access_catalog_seed.csv"
                        and row["franchise"].strip() == "Pulsar"
                    )
                    and not (
                        seed_path.name == "collectables_access_catalog_seed.csv"
                        and row["franchise"].strip() == "Real Ghostbusters"
                        and not is_access_licensed_product_row(row)
                    )
                    and not (
                        seed_path.name == "collectables_access_catalog_seed.csv"
                        and row["franchise"].strip() == "Robotech"
                    )
                    and not (
                        seed_path.name == "collectables_access_catalog_seed.csv"
                        and row["franchise"].strip() == "Sectaurs"
                        and not is_access_licensed_product_row(row)
                    )
                      and not (
                          seed_path.name == "collectables_access_catalog_seed.csv"
                          and row["franchise"].strip() == "Silverhawks"
                          and not is_access_licensed_product_row(row)
                      )
                      and not (
                          seed_path.name == "collectables_access_catalog_seed.csv"
                          and row["franchise"].strip() == "Starriors"
                      )
                      and not (
                          seed_path.name == "collectables_access_catalog_seed.csv"
                          and row["franchise"].strip() == "Strawberry Shortcake"
                      )
                      and not (
                          seed_path.name == "collectables_access_catalog_seed.csv"
                          and row["franchise"].strip() == "Supernaturals"
                      )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Swamp Thing"
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Teenage Mutant Ninja Turtles"
                            and row["product_line"].strip() == "TMNT Vintage Playmates"
                            and row["release_year"].strip() in {"1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997"}
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Teenage Mutant Ninja Turtles"
                            and row["product_line"].strip() in {"TMNT 2003", "Fast Forward", "2012 Nick", "Next Mutation", "TMNT Movie Line", "Mutant Mayhem", "Heroes of Goo Jit Zu", "Teenage Mutant Ninja Turtles X Godzilla"}
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Thundercats"
                            and row["product_line"].strip() in {"Vintage Thundercats", "Thundercats Miniatures"}
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Visionaries"
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Tron"
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Transformers"
                            and row["product_line"].strip() in {"G1 Transformers", "Generation 1"}
                            and row["release_year"].strip() in {"1984", "1985", "1986", "1987", "1988", "1989", "1990"}
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["franchise"].strip() == "Transformers"
                            and row["product_line"].strip() == "Battlebeasts"
                            and row["release_year"].strip() in {"1987", "1988"}
                            and not is_access_licensed_product_row(row)
                        )
                        and not (
                            seed_path.name == "collectables_access_catalog_seed.csv"
                            and row["manufacturer"].strip() == "Mego"
                          and row["franchise"].strip()
                          in {"Star Trek", "World's Greatest Super Heroes"}
                      )
                  ]

            connection.executemany(
                """
                INSERT INTO catalog_items (
                    franchise,
                    property_name,
                    product_line,
                    manufacturer,
                    release_year,
                    wave,
                    item_name,
                    release_type,
                    source_name,
                    source_url,
                    image_url,
                    packaged_image_url,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(franchise, property_name, product_line, manufacturer, release_year, wave, item_name, source_url)
                DO UPDATE SET
                    release_type = excluded.release_type,
                    source_name = excluded.source_name,
                    source_url = excluded.source_url,
                    image_url = excluded.image_url,
                    packaged_image_url = excluded.packaged_image_url,
                    notes = excluded.notes
                WHERE COALESCE(catalog_items.manual_catalog_override, 0) = 0
                """,
                rows,
            )

        connection.execute(
            """
            UPDATE catalog_items
            SET owned = snapshot.owned,
                quantity_owned = snapshot.quantity_owned,
                complete_count = snapshot.complete_count,
                sealed_count = snapshot.sealed_count,
                packaged_count = snapshot.packaged_count,
                condition = snapshot.condition,
                storage_location = snapshot.storage_location,
                ownership_notes = snapshot.ownership_notes,
                inventory_source_name = snapshot.inventory_source_name,
                inventory_updated_at = snapshot.inventory_updated_at
            FROM catalog_inventory_snapshot AS snapshot
            WHERE snapshot.franchise = catalog_items.franchise
              AND snapshot.property_name = catalog_items.property_name
              AND snapshot.product_line = catalog_items.product_line
              AND snapshot.manufacturer = catalog_items.manufacturer
              AND snapshot.release_year = catalog_items.release_year
              AND snapshot.wave = catalog_items.wave
              AND snapshot.item_name = catalog_items.item_name
            """
        )
        connection.execute("DROP TABLE IF EXISTS catalog_inventory_snapshot")
        connection.commit()


def normalize_catalog_property_name(
    franchise: str, property_name: str, product_line: str
) -> str:
    if franchise == "Masters of the Universe":
        if product_line == "Princess of Power":
            return "Princess of Power"
        if product_line == "New Adventures of He-Man":
            return "New Adventures of He-Man"
        if product_line in {"He-Man 200X", "He-Man 200X Neca Staction"}:
            return "He-Man 200X"
        if product_line in {"Classics", "Club Grayskull"}:
            return "Classics"
        if product_line in {
            "Super 7 As Seen on TV",
            "Super 7 Three Terrors",
            "Super 7 Ultimate Edition",
        }:
            return "Super7"
    if franchise == "GoBots":
        if product_line in {"Go-Bots", "Super Go-Bots"}:
            return "Go-Bots"
        if product_line == "Rock Lords":
            return "Rock Lords"
        if product_line == "Machine Robo":
            return "Machine Robo"
    if franchise == "Teenage Mutant Ninja Turtles":
        if product_line == "TMNT Vintage Playmates":
            return "Teenage Mutant Ninja Turtles (Vintage Playmates)"
        if product_line in {"Next Mutation", "Ninja Turtles: The Next Mutation"}:
            return "Ninja Turtles: The Next Mutation"
        if product_line in {"TMNT 2003", "Fast Forward"}:
            return "Teenage Mutant Ninja Turtles (2003)"
        if product_line == "TMNT Movie Line":
            return "TMNT (2007 Film)"
        if product_line == "2012 Nick":
            return "Teenage Mutant Ninja Turtles (2012)"
        if product_line == "Mutant Mayhem":
            return "Teenage Mutant Ninja Turtles: Mutant Mayhem"
        if product_line == "Heroes of Goo Jit Zu":
            return "Heroes of Goo Jit Zu x TMNT"
        if product_line == "Teenage Mutant Ninja Turtles X Godzilla":
            return "TMNT x Godzilla"
        if product_line == "40th anniversary toyline":
            return "Teenage Mutant Ninja Turtles 40th Anniversary"
    return property_name


def normalize_mego_taxonomy(
    franchise: str,
    property_name: str,
    product_line: str,
    manufacturer: str,
    item_name: str,
) -> tuple[str, str, str]:
    manufacturer_name = manufacturer.strip().lower()
    normalized_franchise = franchise
    normalized_property = property_name
    normalized_product_line = product_line
    item_name_lower = item_name.strip().lower()

    if manufacturer_name != "mego":
        return normalized_franchise, normalized_property, normalized_product_line

    if franchise == "Star Trek":
        return "Mego", "Star Trek", "Star Trek"

    if franchise != "World's Greatest Super Heroes":
        return normalized_franchise, normalized_property, normalized_product_line

    normalized_franchise = "Mego Dolls"
    normalized_product_line = "World's Greatest Super Heroes"

    dc_keywords = (
        "aquaman",
        "aqualad",
        "bat",
        "bruce wayne",
        "catwoman",
        "clark kent",
        "dick grayson",
        "green arrow",
        "hall of justice",
        "isis",
        "joker",
        "kid flash",
        "lex luthor",
        "mr. mxyzptlk",
        "nubia",
        "penguin",
        "queen hippolyte",
        "riddler",
        "robin",
        "shazam",
        "speedy",
        "steve trevor",
        "supergirl",
        "superman",
        "supervator",
        "wayne foundation",
        "wondergirl",
        "wonderwoman",
        "wonder woman",
        "jor-el",
        "general zodd",
    )
    marvel_keywords = (
        "captain america",
        "falcon",
        "green goblin",
        "hulk",
        "human torch",
        "incredible hulk",
        "invisible girl",
        "iron man",
        "lizard",
        "mr. fantastic",
        "peter parker",
        "spider",
        "spiderman",
        "the thing",
        "thor",
    )

    if any(keyword in item_name_lower for keyword in dc_keywords):
        normalized_property = "DC Comics"
    elif any(keyword in item_name_lower for keyword in marvel_keywords):
        normalized_property = "Marvel Comics"
    elif "conan" in item_name_lower:
        normalized_property = "Conan the Barbarian"
    elif "tarzan" in item_name_lower:
        normalized_property = "Tarzan"
    else:
        normalized_property = "World's Greatest Super Heroes"

    return normalized_franchise, normalized_property, normalized_product_line


def normalize_mego_product_line(
    franchise: str,
    property_name: str,
    product_line: str,
    manufacturer: str,
    item_name: str,
    release_type: str,
    release_year: int,
) -> str:
    manufacturer_name = manufacturer.strip().lower()
    if franchise != "Mego Dolls" or manufacturer_name != "mego":
        return product_line
    if product_line not in {"Star Trek", "World's Greatest Super Heroes"}:
        return product_line

    item_name_lower = item_name.strip().lower()
    release_type_lower = release_type.strip().lower()

    if property_name == "Star Trek":
        if 1974 <= release_year <= 1977:
            return "Star Trek 1974-1977"
        if 1979 <= release_year <= 1980:
            return "Star Trek 1979-1980"
        return "Star Trek"

    if property_name == "DC Comics":
        if item_name_lower.startswith('12 inch:'):
            return 'WGSH - 12" Figures'
        if release_type_lower in {"vehicle", "playset", "accessory", "role-play"}:
            return "WGSH - Vehicles, Playsets, Accessories"
        return "WGSH - DC"

    if property_name == "Marvel Comics":
        if item_name_lower.startswith('12 inch:'):
            return 'WGSH - 12" Figures'
        if release_type_lower in {"vehicle", "playset", "accessory", "role-play"}:
            return "WGSH - Vehicles, Playsets, Accessories"
        return "WGSH - Marvel"

    if property_name == "World's Greatest Super Heroes":
        return "WGSH - Vehicles, Playsets, Accessories"

    if property_name in {"Conan the Barbarian", "Tarzan"}:
        if item_name_lower.startswith('12 inch:'):
            return 'WGSH - 12" Figures'
        return "WGSH - Other Properties"

    return product_line


def build_normalized_catalog_row(
    seed_path: Path, row: dict[str, str]
) -> tuple[str, str, str, str, int, str, str, str, str, str, str, str, str]:
    franchise = row["franchise"].strip()
    product_line = row["product_line"].strip()
    raw_property_name = row["property_name"].strip()
    manufacturer = row["manufacturer"].strip()
    item_name = row["item_name"].strip()
    release_type = row["release_type"].strip()
    release_year = int(row["release_year"])
    if franchise == "Silverhawks":
        franchise = "SilverHawks"
        raw_property_name = "SilverHawks"
        if product_line == "Silverhawks":
            product_line = "Licensed Products"
    if franchise == "Real Ghostbusters":
        franchise = "Ghostbusters"
        if raw_property_name == "Real Ghostbusters":
            raw_property_name = "The Real Ghostbusters"
    franchise, raw_property_name, product_line = normalize_mego_taxonomy(
        franchise, raw_property_name, product_line, manufacturer, item_name
    )
    property_name = normalize_catalog_property_name(
        franchise, raw_property_name, product_line
    )
    product_line = normalize_mego_product_line(
        franchise,
        property_name,
        product_line,
        manufacturer,
        item_name,
        release_type,
        release_year,
    )
    return (
        franchise,
        property_name,
        product_line,
        manufacturer,
        release_year,
        row["wave"].strip(),
        item_name,
        release_type,
        row["source_name"].strip(),
        row["source_url"].strip(),
        row.get("image_url", "").strip(),
        row.get("packaged_image_url", "").strip(),
        row["notes"].strip(),
    )


def serialize_item(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "series": row["series"],
        "category": row["category"],
        "item_number": row["item_number"],
        "owned": bool(row["owned"]),
        "quantity": row["quantity"],
        "condition": row["condition"],
        "storage_location": row["storage_location"],
        "source_name": row["source_name"],
        "source_key": row["source_key"],
        "catalog_item_id": row["catalog_item_id"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def build_photo_summary(row: sqlite3.Row) -> dict[str, Any]:
    has_loose_photo = bool((row["image_url"] or "").strip())
    has_packaged_photo = bool((row["packaged_image_url"] or "").strip())

    if has_loose_photo and has_packaged_photo:
        status = "both"
    elif has_loose_photo:
        status = "loose_only"
    elif has_packaged_photo:
        status = "packaged_only"
    else:
        status = "missing"

    return {
        "has_loose_photo": has_loose_photo,
        "has_packaged_photo": has_packaged_photo,
        "status": status,
    }


def build_release_bucket_sql() -> str:
    return """
        CASE
            WHEN lower(trim(coalesce(release_type, ''))) = 'reissue' THEN 'reissue'
            WHEN lower(trim(coalesce(release_type, ''))) = 'modern' THEN 'modern'
            WHEN lower(trim(coalesce(release_type, ''))) = 'vintage' THEN 'vintage'
            WHEN release_year >= 2000 THEN 'modern'
            ELSE 'vintage'
        END
    """


def get_release_bucket(row: sqlite3.Row) -> str:
    release_type = (row["release_type"] or "").strip().lower()
    if release_type in {"vintage", "modern", "reissue"}:
        return release_type
    if int(row["release_year"]) >= 2000:
        return "modern"
    return "vintage"


def build_inventory_summary(row: sqlite3.Row) -> dict[str, Any]:
    quantity_owned = int(row["quantity_owned"] or 0)
    complete_count = int(row["complete_count"] or 0)
    sealed_count = int(row["sealed_count"] or 0)
    packaged_count = int(row["packaged_count"] or 0)
    if quantity_owned <= 0:
        status = "missing"
    elif complete_count >= quantity_owned:
        status = "complete"
    else:
        status = "partial"
    return {
        "owned": quantity_owned > 0,
        "quantity_owned": quantity_owned,
        "complete_count": complete_count,
        "sealed_count": sealed_count,
        "original_packaging_count": packaged_count,
        "status": status,
        "condition": row["condition"] or "",
        "storage_location": row["storage_location"] or "",
        "ownership_notes": row["ownership_notes"] or "",
        "source_name": row["inventory_source_name"] or "",
        "updated_at": row["inventory_updated_at"] or "",
    }


def serialize_catalog_item(row: sqlite3.Row) -> dict[str, Any]:
    inventory_summary = build_inventory_summary(row)
    photo_summary = build_photo_summary(row)

    return {
        "id": row["id"],
        "franchise": row["franchise"],
        "property_name": row["property_name"],
        "product_line": row["product_line"],
        "manufacturer": row["manufacturer"],
        "release_year": row["release_year"],
        "wave": row["wave"],
        "item_name": row["item_name"],
        "release_type": row["release_type"],
        "release_bucket": get_release_bucket(row),
        "source_name": row["source_name"],
        "source_url": row["source_url"],
        "raw_image_url": row["image_url"],
        "raw_packaged_image_url": row["packaged_image_url"],
        "image_url": build_catalog_image_url(row["image_url"]),
        "packaged_image_url": build_catalog_image_url(row["packaged_image_url"]),
        "notes": row["notes"],
        "manual_catalog_override": bool(row["manual_catalog_override"]),
        "created_at": row["created_at"],
        "inventory_summary": inventory_summary,
        "inventory_record": {
            "owned": bool(row["owned"]),
            "quantity_owned": row["quantity_owned"],
            "complete_count": row["complete_count"],
            "sealed_count": row["sealed_count"],
            "packaged_count": row["packaged_count"],
            "condition": row["condition"],
            "storage_location": row["storage_location"],
            "ownership_notes": row["ownership_notes"],
            "source_name": row["inventory_source_name"],
            "updated_at": row["inventory_updated_at"],
        },
        "photo_summary": photo_summary,
        "pricing_summary": serialize_pricing_summary(row),
    }


def normalize_catalog_inventory_payload(payload: dict[str, Any]) -> dict[str, Any]:
    owned = bool(payload.get("owned", False))
    fields = {
        "quantity_owned": "Quantity owned",
        "complete_count": "Complete count",
        "sealed_count": "Sealed count",
        "packaged_count": "Original packaging count",
    }
    values: dict[str, int] = {}
    for key, label in fields.items():
        try:
            values[key] = int(payload.get(key, 0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be a whole number.") from exc
        if values[key] < 0:
            raise ValueError(f"{label} cannot be negative.")

    if owned and values["quantity_owned"] == 0:
        values["quantity_owned"] = 1
    if not owned:
        values = {key: 0 for key in values}

    if values["complete_count"] > values["quantity_owned"]:
        raise ValueError("Complete count cannot exceed quantity owned.")
    if values["sealed_count"] > values["quantity_owned"]:
        raise ValueError("Sealed count cannot exceed quantity owned.")
    if values["packaged_count"] > values["quantity_owned"]:
        raise ValueError("Original packaging count cannot exceed quantity owned.")

    condition = str(payload.get("condition", "")).strip()
    storage_location = str(payload.get("storage_location", "")).strip()
    ownership_notes = str(payload.get("ownership_notes", "")).strip()

    return {
        "owned": 1 if values["quantity_owned"] > 0 else 0,
        "quantity_owned": values["quantity_owned"],
        "complete_count": values["complete_count"],
        "sealed_count": values["sealed_count"],
        "packaged_count": values["packaged_count"],
        "condition": infer_catalog_condition(
            values["quantity_owned"],
            values["complete_count"],
            values["sealed_count"],
            values["packaged_count"],
            condition,
        ),
        "storage_location": storage_location,
        "ownership_notes": ownership_notes,
    }


def normalize_catalog_item_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required_fields = {
        "franchise": "Franchise",
        "property_name": "Property",
        "product_line": "Product line",
        "manufacturer": "Manufacturer",
        "item_name": "Item name",
    }
    item = {
        key: str(payload.get(key, "")).strip()
        for key in (
            "franchise",
            "property_name",
            "product_line",
            "manufacturer",
            "wave",
            "item_name",
            "release_type",
            "source_name",
            "source_url",
            "image_url",
            "packaged_image_url",
            "notes",
        )
    }

    for key, label in required_fields.items():
        if not item[key]:
            raise ValueError(f"{label} is required.")

    try:
        release_year = int(payload.get("release_year", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Release year must be a whole number.") from exc

    if release_year < 1900 or release_year > 2099:
        raise ValueError("Release year must be between 1900 and 2099.")

    item["release_year"] = release_year
    if not item["release_type"]:
        item["release_type"] = "vintage" if release_year < 2000 else "modern"
    if not item["source_name"]:
        item["source_name"] = "Manual"

    return item


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Name is required.")

    owned = bool(payload.get("owned", False))
    try:
        quantity = int(payload.get("quantity", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be a whole number.") from exc

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    if owned and quantity == 0:
        quantity = 1

    if not owned:
        quantity = 0

    condition = str(payload.get("condition", "Complete")).strip() or "Complete"

    return {
        "name": name,
        "series": str(payload.get("series", "")).strip(),
        "category": str(payload.get("category", "")).strip(),
        "item_number": str(payload.get("item_number", "")).strip(),
        "owned": 1 if owned else 0,
        "quantity": quantity,
        "condition": condition,
        "storage_location": str(payload.get("storage_location", "")).strip(),
        "notes": str(payload.get("notes", "")).strip(),
    }


def delete_ebay_user_data(username: str | None, user_id: str | None, eias_token: str | None) -> int:
    """
    Delete all data associated with an eBay user who has requested account deletion.

    Returns the number of records deleted.
    """
    deleted_count = 0

def delete_ebay_user_data(username: str | None, user_id: str | None, eias_token: str | None) -> int:
    """
    Delete all data associated with an eBay user who has requested account deletion.

    Returns the number of records deleted.
    """
    deleted_count = 0

    try:
        connection = get_connection()
        # Delete inventory data - set ownership to 0 and clear eBay-specific fields
        if username:
            connection.execute("UPDATE catalog_items SET quantity_owned = 0, condition = '', packaged_count = 0, sealed_count = 0, complete_count = 0, ownership_notes = '', source_name = '', storage_location = '' WHERE source_name = ?", (f"eBay:{username}",))
            deleted_count = connection.total_changes
        connection.close()
    except Exception as e:
        print(f"Error in delete_ebay_user_data: {e}")
        raise

    return deleted_count

    return deleted_count


@app.get("/")
def index() -> str:
    return render_template("index.html", default_conditions=DEFAULT_CONDITIONS)


@app.get("/api/meta")
def meta() -> Any:
    return jsonify({"conditions": DEFAULT_CONDITIONS})


@app.get("/api/items")
def list_items() -> Any:
    search = request.args.get("search", "").strip().lower()
    owned_filter = request.args.get("owned", "all").strip().lower()
    condition_filter = request.args.get("condition", "all").strip()

    query = "SELECT * FROM items WHERE 1 = 1"
    params: list[Any] = []

    if search:
        query += " AND (lower(name) LIKE ? OR lower(series) LIKE ? OR lower(category) LIKE ? OR lower(item_number) LIKE ? OR lower(notes) LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    if owned_filter == "owned":
        query += " AND owned = 1"
    elif owned_filter == "missing":
        query += " AND owned = 0"

    if condition_filter and condition_filter.lower() != "all":
        query += " AND condition = ?"
        params.append(condition_filter)

    query += " ORDER BY owned DESC, name COLLATE NOCASE ASC"

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return jsonify([serialize_item(row) for row in rows])


@app.get("/api/catalog-items")
def list_catalog_items() -> Any:
    search = request.args.get("search", "").strip().lower()
    franchise_filter = request.args.get("franchise", "all").strip()
    property_filter = request.args.get("property_name", "all").strip()
    product_line_filter = request.args.get("product_line", "all").strip()
    manufacturer_filter = request.args.get("manufacturer", "all").strip()
    release_type_filter = request.args.get("release_type", "all").strip().lower()
    owned_filter = request.args.get("owned", "all").strip().lower()
    condition_filter = request.args.get("condition", "all").strip()
    year_from_raw = request.args.get("year_from", "").strip()
    year_to_raw = request.args.get("year_to", "").strip()
    limit_raw = request.args.get("limit", "300").strip()

    try:
        limit = min(max(int(limit_raw), 1), 500)
    except ValueError:
        return jsonify({"error": "limit must be a whole number."}), 400

    query = "SELECT * FROM catalog_items WHERE 1 = 1"
    params: list[Any] = []

    if search:
        query += " AND (lower(franchise) LIKE ? OR lower(property_name) LIKE ? OR lower(product_line) LIKE ? OR lower(item_name) LIKE ? OR lower(notes) LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])

    if franchise_filter and franchise_filter.lower() != "all":
        query += " AND franchise = ?"
        params.append(franchise_filter)

    if property_filter and property_filter.lower() != "all":
        query += " AND property_name = ?"
        params.append(property_filter)

    if product_line_filter and product_line_filter.lower() != "all":
        query += " AND product_line = ?"
        params.append(product_line_filter)

    if manufacturer_filter and manufacturer_filter.lower() != "all":
        query += " AND manufacturer = ?"
        params.append(manufacturer_filter)

    if release_type_filter and release_type_filter != "all":
        if release_type_filter in {"vintage", "modern", "reissue"}:
            query += f" AND {build_release_bucket_sql()} = ?"
        else:
            query += " AND lower(release_type) = ?"
        params.append(release_type_filter)

    if owned_filter == "owned":
        query += " AND quantity_owned > 0"
    elif owned_filter == "missing":
        query += " AND quantity_owned = 0"

    if condition_filter and condition_filter.lower() != "all":
        query += " AND condition = ?"
        params.append(condition_filter)

    if year_from_raw:
        try:
            year_from = int(year_from_raw)
            query += " AND release_year >= ?"
            params.append(year_from)
        except ValueError:
            return jsonify({"error": "year_from must be a whole number."}), 400

    if year_to_raw:
        try:
            year_to = int(year_to_raw)
            query += " AND release_year <= ?"
            params.append(year_to)
        except ValueError:
            return jsonify({"error": "year_to must be a whole number."}), 400

    query += (
        " ORDER BY CASE WHEN quantity_owned > 0 THEN 0 ELSE 1 END ASC,"
        " franchise COLLATE NOCASE ASC,"
        " property_name COLLATE NOCASE ASC,"
        " product_line COLLATE NOCASE ASC,"
        " CASE"
        "   WHEN product_line = 'Classified Series' AND item_name LIKE '#% %' THEN 0"
        "   ELSE 1"
        " END ASC,"
        " CASE"
        "   WHEN product_line = 'Classified Series' AND item_name LIKE '#% %'"
        "   THEN CAST(SUBSTR(item_name, 2, INSTR(item_name || ' ', ' ') - 2) AS INTEGER)"
        "   ELSE NULL"
        " END ASC,"
        " wave COLLATE NOCASE ASC,"
        " item_name COLLATE NOCASE ASC,"
        " release_year ASC"
    )

    query += " LIMIT ?"
    params.append(limit + 1)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    truncated = len(rows) > limit
    response = jsonify([serialize_catalog_item(row) for row in rows[:limit]])
    response.headers["X-Catalog-Result-Limit"] = str(limit)
    response.headers["X-Catalog-Result-Truncated"] = "true" if truncated else "false"
    return response


@app.get("/api/catalog-filter-options")
def catalog_filter_options() -> Any:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT
                franchise,
                property_name,
                product_line,
                manufacturer
            FROM catalog_items
            ORDER BY
                franchise COLLATE NOCASE ASC,
                property_name COLLATE NOCASE ASC,
                product_line COLLATE NOCASE ASC,
                manufacturer COLLATE NOCASE ASC
            """
        ).fetchall()

    return jsonify(
        [
            {
                "franchise": row["franchise"],
                "property_name": row["property_name"],
                "product_line": row["product_line"],
                "manufacturer": row["manufacturer"],
            }
            for row in rows
        ]
    )


@app.get("/catalog-image")
def catalog_image() -> Response:
    source_url = unquote(request.args.get("url", "").strip())
    if not source_url:
        abort(400)

    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in ALLOWED_IMAGE_HOSTS:
        abort(400)

    try:
        content, content_type = fetch_catalog_image(source_url)
    except requests.RequestException:
        abort(502)

    return Response(
        content,
        content_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )


@app.get("/api/catalog-summary")
def catalog_summary() -> Any:
    release_bucket_sql = build_release_bucket_sql()
    with get_connection() as connection:
        total_items = connection.execute("SELECT COUNT(*) FROM catalog_items").fetchone()[0]
        owned_items = connection.execute(
            "SELECT COUNT(*) FROM catalog_items WHERE quantity_owned > 0"
        ).fetchone()[0]
        missing_items = total_items - owned_items
        total_quantity_owned = connection.execute(
            "SELECT COALESCE(SUM(quantity_owned), 0) FROM catalog_items"
        ).fetchone()[0]
        franchises = connection.execute(
            "SELECT COUNT(DISTINCT franchise) FROM catalog_items"
        ).fetchone()[0]
        vintage_items = connection.execute(
            f"SELECT COUNT(*) FROM catalog_items WHERE {release_bucket_sql} = 'vintage'"
        ).fetchone()[0]
        modern_items = connection.execute(
            f"SELECT COUNT(*) FROM catalog_items WHERE {release_bucket_sql} IN ('modern', 'reissue')"
        ).fetchone()[0]
        reissue_items = connection.execute(
            f"SELECT COUNT(*) FROM catalog_items WHERE {release_bucket_sql} = 'reissue'"
        ).fetchone()[0]
        items_with_loose_photos = connection.execute(
            "SELECT COUNT(*) FROM catalog_items WHERE TRIM(COALESCE(image_url, '')) <> ''"
        ).fetchone()[0]
        items_with_packaged_photos = connection.execute(
            "SELECT COUNT(*) FROM catalog_items WHERE TRIM(COALESCE(packaged_image_url, '')) <> ''"
        ).fetchone()[0]
        items_with_both_photo_types = connection.execute(
            """
            SELECT COUNT(*)
            FROM catalog_items
            WHERE TRIM(COALESCE(image_url, '')) <> ''
              AND TRIM(COALESCE(packaged_image_url, '')) <> ''
            """
        ).fetchone()[0]
        items_missing_all_photos = connection.execute(
            """
            SELECT COUNT(*)
            FROM catalog_items
            WHERE TRIM(COALESCE(image_url, '')) = ''
              AND TRIM(COALESCE(packaged_image_url, '')) = ''
            """
        ).fetchone()[0]
        
        # Calculate total net value
        total_net_value_cents = connection.execute(
            """
            SELECT COALESCE(SUM(
                quantity_owned * 
                CASE 
                    WHEN price_low_cents IS NOT NULL AND price_high_cents IS NOT NULL 
                    THEN (price_low_cents + price_high_cents) / 2.0
                    WHEN price_low_cents IS NOT NULL 
                    THEN price_low_cents
                    WHEN price_high_cents IS NOT NULL 
                    THEN price_high_cents
                    ELSE 0
                END
            ), 0) FROM catalog_items WHERE quantity_owned > 0
            """
        ).fetchone()[0]
        
        # Property breakdown with owned count and value
        property_rows = connection.execute(
            """
            SELECT 
                property_name, 
                COALESCE(SUM(quantity_owned), 0) AS owned_count,
                COALESCE(SUM(
                    quantity_owned * 
                    CASE 
                        WHEN price_low_cents IS NOT NULL AND price_high_cents IS NOT NULL 
                        THEN (price_low_cents + price_high_cents) / 2.0
                        WHEN price_low_cents IS NOT NULL 
                        THEN price_low_cents
                        WHEN price_high_cents IS NOT NULL 
                        THEN price_high_cents
                        ELSE 0
                    END
                ), 0) AS total_value_cents
            FROM catalog_items 
            WHERE quantity_owned > 0
            GROUP BY property_name 
            ORDER BY total_value_cents DESC, property_name ASC
            """
        ).fetchall()

    return jsonify(
        {
            "total_items": total_items,
            "owned_items": owned_items,
            "missing_items": missing_items,
            "total_quantity_owned": total_quantity_owned,
            "total_inventoried_items": total_quantity_owned,  # Same as total_quantity_owned
            "total_net_value_cents": int(total_net_value_cents),
            "total_net_value_display": f"${total_net_value_cents / 100:,.2f}",
            "franchises": franchises,
            "vintage_items": vintage_items,
            "modern_or_reissue_items": modern_items,
            "reissue_items": reissue_items,
            "items_with_loose_photos": items_with_loose_photos,
            "items_with_packaged_photos": items_with_packaged_photos,
            "items_with_both_photo_types": items_with_both_photo_types,
            "items_missing_all_photos": items_missing_all_photos,
            "property_breakdown": [
                {
                    "property": row["property_name"], 
                    "owned_count": row["owned_count"],
                    "total_value_cents": int(row["total_value_cents"]),
                    "total_value_display": f"${row['total_value_cents'] / 100:,.2f}"
                }
                for row in property_rows
            ],
        }
    )


@app.get("/api/catalog-photo-audit")
def catalog_photo_audit() -> Any:
    franchise_filter = request.args.get("franchise", "").strip()
    property_filter = request.args.get("property_name", "").strip()

    query = """
        SELECT
            franchise,
            property_name,
            COUNT(*) AS total_items,
            SUM(CASE WHEN TRIM(COALESCE(image_url, '')) <> '' THEN 1 ELSE 0 END) AS loose_photo_count,
            SUM(CASE WHEN TRIM(COALESCE(packaged_image_url, '')) <> '' THEN 1 ELSE 0 END) AS packaged_photo_count,
            SUM(
                CASE
                    WHEN TRIM(COALESCE(image_url, '')) <> ''
                     AND TRIM(COALESCE(packaged_image_url, '')) <> ''
                    THEN 1
                    ELSE 0
                END
            ) AS both_photo_count,
            SUM(
                CASE
                    WHEN TRIM(COALESCE(image_url, '')) = ''
                     AND TRIM(COALESCE(packaged_image_url, '')) = ''
                    THEN 1
                    ELSE 0
                END
            ) AS missing_all_photo_count
        FROM catalog_items
        WHERE 1 = 1
    """
    params: list[Any] = []

    if franchise_filter:
        query += " AND franchise = ?"
        params.append(franchise_filter)

    if property_filter:
        query += " AND property_name = ?"
        params.append(property_filter)

    query += """
        GROUP BY franchise, property_name
        ORDER BY missing_all_photo_count DESC, franchise COLLATE NOCASE ASC, property_name COLLATE NOCASE ASC
    """

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return jsonify(
        [
            {
                "franchise": row["franchise"],
                "property_name": row["property_name"],
                "total_items": row["total_items"],
                "loose_photo_count": row["loose_photo_count"],
                "packaged_photo_count": row["packaged_photo_count"],
                "both_photo_count": row["both_photo_count"],
                "missing_all_photo_count": row["missing_all_photo_count"],
            }
            for row in rows
        ]
    )


@app.post("/api/catalog-pricing-refresh")
def catalog_pricing_refresh() -> Any:
    payload = request.get_json(silent=True) or {}
    catalog_item_ids = payload.get("catalog_item_ids") or None
    limit = payload.get("limit")

    try:
        limit_value = int(limit) if limit is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "limit must be a whole number."}), 400

    try:
        with get_connection() as connection:
            result = refresh_catalog_prices(
                connection,
                catalog_item_ids=catalog_item_ids,
                limit=limit_value,
            )
            connection.commit()
    except Exception as exc:
        return jsonify({"error": f"Unable to refresh pricing: {exc}"}), 500

    return jsonify(result)


@app.get("/api/catalog-pricing-status")
def catalog_pricing_status() -> Any:
    return jsonify(verify_ebay_pricing_configuration())


@app.put("/api/catalog-items/<int:catalog_item_id>/inventory")
def update_catalog_item_inventory(catalog_item_id: int) -> Any:
    payload = request.get_json(silent=True) or {}
    try:
        inventory = normalize_catalog_inventory_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM catalog_items WHERE id = ?",
            (catalog_item_id,),
        ).fetchone()
        if existing is None:
            return jsonify({"error": "Catalog item not found."}), 404

        connection.execute(
            """
            UPDATE catalog_items
            SET owned = ?,
                quantity_owned = ?,
                complete_count = ?,
                sealed_count = ?,
                packaged_count = ?,
                condition = ?,
                storage_location = ?,
                ownership_notes = ?,
                inventory_source_name = 'Manual',
                inventory_updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                inventory["owned"],
                inventory["quantity_owned"],
                inventory["complete_count"],
                inventory["sealed_count"],
                inventory["packaged_count"],
                inventory["condition"],
                inventory["storage_location"],
                inventory["ownership_notes"],
                catalog_item_id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM catalog_items WHERE id = ?",
            (catalog_item_id,),
        ).fetchone()

    return jsonify(serialize_catalog_item(row))


@app.post("/api/catalog-items")
def create_catalog_item() -> Any:
    payload = request.get_json(silent=True) or {}
    try:
        item = normalize_catalog_item_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO catalog_items (
                    franchise,
                    property_name,
                    product_line,
                    manufacturer,
                    release_year,
                    wave,
                    item_name,
                    release_type,
                    source_name,
                    source_url,
                    image_url,
                    packaged_image_url,
                    manual_catalog_override,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    item["franchise"],
                    item["property_name"],
                    item["product_line"],
                    item["manufacturer"],
                    item["release_year"],
                    item["wave"],
                    item["item_name"],
                    item["release_type"],
                    item["source_name"],
                    item["source_url"],
                    item["image_url"],
                    item["packaged_image_url"],
                    item["notes"],
                ),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "A matching catalog item already exists."}), 409

        row = connection.execute(
            "SELECT * FROM catalog_items WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return jsonify(serialize_catalog_item(row)), 201


@app.put("/api/catalog-items/<int:catalog_item_id>")
def update_catalog_item(catalog_item_id: int) -> Any:
    payload = request.get_json(silent=True) or {}
    try:
        item = normalize_catalog_item_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM catalog_items WHERE id = ?",
            (catalog_item_id,),
        ).fetchone()
        if existing is None:
            return jsonify({"error": "Catalog item not found."}), 404

        try:
            connection.execute(
                """
                UPDATE catalog_items
                SET franchise = ?,
                    property_name = ?,
                    product_line = ?,
                    manufacturer = ?,
                    release_year = ?,
                    wave = ?,
                    item_name = ?,
                    release_type = ?,
                    source_name = ?,
                    source_url = ?,
                    image_url = ?,
                    packaged_image_url = ?,
                    manual_catalog_override = 1,
                    notes = ?
                WHERE id = ?
                """,
                (
                    item["franchise"],
                    item["property_name"],
                    item["product_line"],
                    item["manufacturer"],
                    item["release_year"],
                    item["wave"],
                    item["item_name"],
                    item["release_type"],
                    item["source_name"],
                    item["source_url"],
                    item["image_url"],
                    item["packaged_image_url"],
                    item["notes"],
                    catalog_item_id,
                ),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "A matching catalog item already exists."}), 409

        row = connection.execute(
            "SELECT * FROM catalog_items WHERE id = ?",
            (catalog_item_id,),
        ).fetchone()

    return jsonify(serialize_catalog_item(row))


@app.post("/api/items")
def create_item() -> Any:
    payload = request.get_json(silent=True) or {}
    try:
        item = normalize_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO items (
                name,
                series,
                category,
                item_number,
                owned,
                quantity,
                condition,
                storage_location,
                notes,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                item["name"],
                item["series"],
                item["category"],
                item["item_number"],
                item["owned"],
                item["quantity"],
                item["condition"],
                item["storage_location"],
                item["notes"],
            ),
        )
        new_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM items WHERE id = ?", (new_id,)).fetchone()

    return jsonify(serialize_item(row)), 201


@app.put("/api/items/<int:item_id>")
def update_item(item_id: int) -> Any:
    payload = request.get_json(silent=True) or {}
    try:
        item = normalize_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with get_connection() as connection:
        existing = connection.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if existing is None:
            return jsonify({"error": "Item not found."}), 404

        connection.execute(
            """
            UPDATE items
            SET name = ?,
                series = ?,
                category = ?,
                item_number = ?,
                owned = ?,
                quantity = ?,
                condition = ?,
                storage_location = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                item["name"],
                item["series"],
                item["category"],
                item["item_number"],
                item["owned"],
                item["quantity"],
                item["condition"],
                item["storage_location"],
                item["notes"],
                item_id,
            ),
        )
        row = connection.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    return jsonify(serialize_item(row))


@app.delete("/api/items/<int:item_id>")
def delete_item(item_id: int) -> Any:
    with get_connection() as connection:
        deleted = connection.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if deleted.rowcount == 0:
            return jsonify({"error": "Item not found."}), 404

    return ("", 204)


# eBay Marketplace Account Deletion Notification Endpoints
@app.get("/api/ebay/marketplace-account-deletion")
def ebay_marketplace_account_deletion_challenge() -> Any:
    """
    Handle eBay marketplace account deletion challenge code validation.
    eBay sends GET requests with challenge_code parameter to verify endpoint ownership.
    """
    challenge_code = request.args.get("challenge_code")
    if not challenge_code:
        return jsonify({"error": "Missing challenge_code parameter"}), 400

    # Get verification token from environment
    verification_token = os.getenv("EBAY_NOTIFICATION_VERIFICATION_TOKEN", "").strip()
    if not verification_token:
        app.logger.error("EBAY_NOTIFICATION_VERIFICATION_TOKEN not configured")
        return jsonify({"error": "Verification token not configured"}), 500

    # Get the full endpoint URL
    endpoint_url = request.url_root.rstrip("/") + request.path

    # Create SHA-256 hash: challengeCode + verificationToken + endpoint
    hash_input = challenge_code + verification_token + endpoint_url
    challenge_response = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    app.logger.info(f"eBay challenge code validation: challenge_code={challenge_code[:8]}..., response={challenge_response[:8]}...")

    return jsonify({"challengeResponse": challenge_response})


@app.post("/api/ebay/marketplace-account-deletion")
def ebay_marketplace_account_deletion_notification() -> Any:
    """
    Handle eBay marketplace account deletion notifications.
    Receives POST requests when eBay users request account deletion.
    """
    try:
        # Log the notification for debugging
        notification_data = request.get_json()
        if not notification_data:
            app.logger.warning("Received eBay notification with no JSON data")
            return ("", 400)

        app.logger.info(f"Received eBay marketplace account deletion notification: {notification_data}")

        # Validate notification structure
        metadata = notification_data.get("metadata", {})
        notification = notification_data.get("notification", {})
        data = notification.get("data", {})

        if metadata.get("topic") != "MARKETPLACE_ACCOUNT_DELETION":
            app.logger.warning(f"Received notification with unexpected topic: {metadata.get('topic')}")
            return ("", 400)

        # Extract user identifiers
        username = data.get("username")
        user_id = data.get("userId")
        eias_token = data.get("eiasToken")

        if not any([username, user_id, eias_token]):
            app.logger.warning("Received notification with no user identifiers")
            return ("", 400)

        # Delete all data associated with this eBay user
        deleted_count = delete_ebay_user_data(username, user_id, eias_token)

        # Log the deletion for compliance
        print(f"Successfully processed account deletion for user: username={username}, userId={user_id}, eiasToken={eias_token}, records_deleted={deleted_count}")

        # Acknowledge the notification
        return ("", 200)

    except Exception as e:
        app.logger.error(f"Error processing eBay marketplace account deletion notification: {e}")
        return ("", 500)

    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        app.logger.error(f"Error processing eBay marketplace account deletion notification: {e}")
        return ("", 500)


init_db()
maybe_start_background_refresh(get_connection)


if __name__ == "__main__":
    # Production configuration
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)

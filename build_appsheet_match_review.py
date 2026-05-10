from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import sync_appsheet_inventory as sync


DB_PATH = Path(r"C:\Collectables\Inventory\inventory.db")
DEFAULT_SOURCE = Path(r"C:\Users\ddepe\Downloads\AppSheet.ViewData.2026-04-10.csv")
DEFAULT_OUTPUT = Path(r"C:\Collectables\Inventory\appsheet_match_review.csv")


def main() -> int:
    csv_path = DEFAULT_SOURCE
    output_path = DEFAULT_OUTPUT

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        sync.ensure_catalog_inventory_columns(connection)
        (
            by_property_full,
            by_franchise_full,
            by_line_wave_item,
            by_line_wave_base_item,
            by_line_item,
            by_property_item,
            by_franchise_item,
            row_signatures,
        ) = sync.load_catalog_matchers(connection)

        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            source_rows = list(reader)

        review_rows: list[dict[str, str]] = []
        for raw_row in source_rows:
            row = sync.apply_source_row_corrections(raw_row)
            quantity = sync.to_int(row.get("OnHand", "0"))
            if quantity <= 0:
                continue

            catalog_item_id, match_strategy = sync.find_catalog_match(
                row,
                by_property_full,
                by_franchise_full,
                by_line_wave_item,
                by_line_wave_base_item,
                by_line_item,
                by_property_item,
                by_franchise_item,
                row_signatures,
            )

            catalog_row = None
            if catalog_item_id is not None:
                catalog_row = connection.execute(
                    """
                    SELECT id, franchise, property_name, product_line, manufacturer, release_year, wave, item_name
                    FROM catalog_items
                    WHERE id = ?
                    """,
                    (catalog_item_id,),
                ).fetchone()

            review_rows.append(
                {
                    "approved": "",
                    "OnHand": str(quantity),
                    "Complete": (row.get("Complete") or "").strip(),
                    "Sealed": (row.get("Sealed") or "").strip(),
                    "Boxed": (row.get("Boxed") or "").strip(),
                    "Item": (row.get("Item") or "").strip(),
                    "Type": (row.get("Type") or "").strip(),
                    "Property": (row.get("Property") or "").strip(),
                    "Line": (row.get("Line") or "").strip(),
                    "Wave": (row.get("Wave") or "").strip(),
                    "matched": "yes" if catalog_row is not None else "no",
                    "match_strategy": match_strategy,
                    "catalog_item_id": str(catalog_row["id"]) if catalog_row is not None else "",
                    "catalog_franchise": catalog_row["franchise"] if catalog_row is not None else "",
                    "catalog_property_name": catalog_row["property_name"] if catalog_row is not None else "",
                    "catalog_product_line": catalog_row["product_line"] if catalog_row is not None else "",
                    "catalog_manufacturer": catalog_row["manufacturer"] if catalog_row is not None else "",
                    "catalog_release_year": str(catalog_row["release_year"]) if catalog_row is not None else "",
                    "catalog_wave": catalog_row["wave"] if catalog_row is not None else "",
                    "catalog_item_name": catalog_row["item_name"] if catalog_row is not None else "",
                }
            )

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "approved",
                "OnHand",
                "Complete",
                "Sealed",
                "Boxed",
                "Item",
                "Type",
                "Property",
                "Line",
                "Wave",
                "matched",
                "match_strategy",
                "catalog_item_id",
                "catalog_franchise",
                "catalog_property_name",
                "catalog_product_line",
                "catalog_manufacturer",
                "catalog_release_year",
                "catalog_wave",
                "catalog_item_name",
            ],
        )
        writer.writeheader()
        writer.writerows(review_rows)

    matched_count = sum(1 for row in review_rows if row["matched"] == "yes")
    print(f"Review CSV written: {output_path}")
    print(f"Rows for review: {len(review_rows)}")
    print(f"Matched proposals: {matched_count}")
    print(f"Unmatched proposals: {len(review_rows) - matched_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

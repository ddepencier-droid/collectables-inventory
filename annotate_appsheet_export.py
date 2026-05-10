from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import sync_appsheet_inventory as sync


DB_PATH = Path(r"C:\Collectables\Inventory\inventory.db")
DEFAULT_SOURCE = Path(r"C:\Users\ddepe\Downloads\AppSheet.ViewData.2026-04-10.csv")
DEFAULT_OUTPUT = Path(r"C:\Users\ddepe\Downloads\AppSheet.ViewData.2026-04-10.annotated.csv")

ANNOTATION_FIELDS = [
    "match_status",
    "match_strategy",
    "matched_catalog_item_id",
    "matched_catalog_franchise",
    "matched_catalog_property_name",
    "matched_catalog_product_line",
    "matched_catalog_manufacturer",
    "matched_catalog_release_year",
    "matched_catalog_wave",
    "matched_catalog_item_name",
]


def main() -> int:
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT

    if not source_path.exists():
        print(f"Source CSV not found: {source_path}")
        return 1

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

        with source_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            source_rows = list(reader)
            base_fields = reader.fieldnames or []

        annotated_rows: list[dict[str, str]] = []
        for source_row in source_rows:
            row = sync.apply_source_row_corrections(source_row)
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

            annotated = dict(source_row)
            if catalog_item_id is None:
                annotated.update(
                    {
                        "match_status": "unknown",
                        "match_strategy": "unknown",
                        "matched_catalog_item_id": "unknown",
                        "matched_catalog_franchise": "unknown",
                        "matched_catalog_property_name": "unknown",
                        "matched_catalog_product_line": "unknown",
                        "matched_catalog_manufacturer": "unknown",
                        "matched_catalog_release_year": "unknown",
                        "matched_catalog_wave": "unknown",
                        "matched_catalog_item_name": "unknown",
                    }
                )
            else:
                catalog_row = connection.execute(
                    """
                    SELECT
                        id,
                        franchise,
                        property_name,
                        product_line,
                        manufacturer,
                        release_year,
                        wave,
                        item_name
                    FROM catalog_items
                    WHERE id = ?
                    """,
                    (catalog_item_id,),
                ).fetchone()
                if catalog_row is None:
                    annotated.update(
                        {
                            "match_status": "unknown",
                            "match_strategy": "unknown",
                            "matched_catalog_item_id": "unknown",
                            "matched_catalog_franchise": "unknown",
                            "matched_catalog_property_name": "unknown",
                            "matched_catalog_product_line": "unknown",
                            "matched_catalog_manufacturer": "unknown",
                            "matched_catalog_release_year": "unknown",
                            "matched_catalog_wave": "unknown",
                            "matched_catalog_item_name": "unknown",
                        }
                    )
                else:
                    annotated.update(
                        {
                            "match_status": "matched",
                            "match_strategy": match_strategy,
                            "matched_catalog_item_id": str(catalog_row["id"]),
                            "matched_catalog_franchise": catalog_row["franchise"],
                            "matched_catalog_property_name": catalog_row["property_name"],
                            "matched_catalog_product_line": catalog_row["product_line"],
                            "matched_catalog_manufacturer": catalog_row["manufacturer"],
                            "matched_catalog_release_year": str(catalog_row["release_year"]),
                            "matched_catalog_wave": catalog_row["wave"] or "",
                            "matched_catalog_item_name": catalog_row["item_name"],
                        }
                    )
            annotated_rows.append(annotated)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*base_fields, *ANNOTATION_FIELDS])
        writer.writeheader()
        writer.writerows(annotated_rows)

    matched_count = sum(1 for row in annotated_rows if row["match_status"] == "matched")
    print(f"Annotated CSV written: {output_path}")
    print(f"Rows annotated: {len(annotated_rows)}")
    print(f"Matched: {matched_count}")
    print(f"Unknown: {len(annotated_rows) - matched_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

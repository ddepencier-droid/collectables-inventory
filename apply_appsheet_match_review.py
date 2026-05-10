from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import sync_appsheet_inventory as sync


DB_PATH = Path(r"C:\Collectables\Inventory\inventory.db")
DEFAULT_REVIEW_PATH = Path(r"C:\Collectables\Inventory\appsheet_match_review.csv")
UNMATCHED_REPORT_PATH = Path(r"C:\Collectables\Inventory\appsheet_inventory_unmatched.csv")
SOURCE_NAME = "AppSheet"
TRUTHY = {"1", "true", "yes", "y", "approved", "x"}


def main() -> int:
    review_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REVIEW_PATH
    if not review_path.exists():
        print(f"Review CSV not found: {review_path}")
        return 1

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        sync.ensure_catalog_inventory_columns(connection)

        connection.execute("DELETE FROM items WHERE source_name = ?", (SOURCE_NAME,))
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
            WHERE inventory_source_name = ?
            """,
            (SOURCE_NAME,),
        )

        with review_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        inserted = 0
        approved = 0
        matched = 0
        unmatched_rows: list[dict[str, str]] = []
        matched_inventory: dict[int, dict[str, object]] = {}

        for row in rows:
            quantity = sync.to_int(row.get("OnHand", "0"))
            if quantity <= 0:
                continue

            is_approved = (row.get("approved") or "").strip().lower() in TRUTHY
            if not is_approved:
                continue
            approved += 1

            catalog_item_id = sync.to_int(row.get("catalog_item_id", "0"))
            is_matched = (row.get("matched") or "").strip().lower() == "yes" and catalog_item_id > 0
            if is_matched:
                matched += 1
                summary = matched_inventory.setdefault(
                    catalog_item_id,
                    {
                        "quantity_owned": 0,
                        "complete_count": 0,
                        "sealed_count": 0,
                        "packaged_count": 0,
                        "ownership_notes": [],
                    },
                )
                summary["quantity_owned"] = int(summary["quantity_owned"]) + quantity
                if sync.truthy(row.get("Complete", "")):
                    summary["complete_count"] = int(summary["complete_count"]) + quantity
                if sync.truthy(row.get("Sealed", "")):
                    summary["sealed_count"] = int(summary["sealed_count"]) + quantity
                if sync.truthy(row.get("Sealed", "")) or sync.truthy(row.get("Boxed", "")):
                    summary["packaged_count"] = int(summary["packaged_count"]) + quantity
                summary["ownership_notes"].append(
                    sync.build_notes(
                        {
                            "Property": row.get("Property", ""),
                            "Line": row.get("Line", ""),
                            "Wave": row.get("Wave", ""),
                            "OnHand": row.get("OnHand", ""),
                            "Complete": row.get("Complete", ""),
                            "Sealed": row.get("Sealed", ""),
                            "Boxed": row.get("Boxed", ""),
                        },
                        "approved-review",
                    )
                )
            else:
                unmatched_rows.append(
                    {
                        "Item": (row.get("Item") or "").strip(),
                        "Type": (row.get("Type") or "").strip(),
                        "Property": (row.get("Property") or "").strip(),
                        "Line": (row.get("Line") or "").strip(),
                        "Wave": (row.get("Wave") or "").strip(),
                        "OnHand": str(quantity),
                    }
                )

            connection.execute(
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
                    source_name,
                    source_key,
                    catalog_item_id,
                    notes,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    (row.get("Item") or "").strip(),
                    sync.build_series(
                        {
                            "Property": row.get("Property", ""),
                            "Line": row.get("Line", ""),
                        }
                    ),
                    (row.get("Type") or "").strip(),
                    (row.get("Wave") or "").strip(),
                    1,
                    quantity,
                    sync.derive_condition(
                        {
                            "Complete": row.get("Complete", ""),
                            "Sealed": row.get("Sealed", ""),
                            "Boxed": row.get("Boxed", ""),
                        }
                    ),
                    "",
                    SOURCE_NAME,
                    " | ".join(
                        [
                            (row.get("Property") or "").strip(),
                            (row.get("Line") or "").strip(),
                            (row.get("Wave") or "").strip(),
                            (row.get("Item") or "").strip(),
                        ]
                    ),
                    catalog_item_id if is_matched else None,
                    sync.build_notes(
                        {
                            "Property": row.get("Property", ""),
                            "Line": row.get("Line", ""),
                            "Wave": row.get("Wave", ""),
                            "OnHand": row.get("OnHand", ""),
                            "Complete": row.get("Complete", ""),
                            "Sealed": row.get("Sealed", ""),
                            "Boxed": row.get("Boxed", ""),
                        },
                        "approved-review" if is_matched else "approved-unmatched",
                    ),
                ),
            )
            inserted += 1

        for catalog_item_id, summary in matched_inventory.items():
            quantity_owned = int(summary["quantity_owned"])
            complete_count = int(summary["complete_count"])
            sealed_count = int(summary["sealed_count"])
            packaged_count = int(summary["packaged_count"])
            ownership_notes = " | ".join(
                note for note in summary["ownership_notes"] if isinstance(note, str) and note.strip()
            )
            connection.execute(
                """
                UPDATE catalog_items
                SET owned = ?,
                    quantity_owned = ?,
                    complete_count = ?,
                    sealed_count = ?,
                    packaged_count = ?,
                    condition = ?,
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
                    sync.infer_catalog_condition(
                        quantity_owned,
                        complete_count,
                        sealed_count,
                        packaged_count,
                    ),
                    ownership_notes,
                    SOURCE_NAME,
                    catalog_item_id,
                ),
            )

        with UNMATCHED_REPORT_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["Item", "Type", "Property", "Line", "Wave", "OnHand"],
            )
            writer.writeheader()
            writer.writerows(unmatched_rows)

        connection.commit()

    print(f"Approved review rows imported: {approved}")
    print(f"Rows inserted into items: {inserted}")
    print(f"Approved rows matched to catalog: {matched}")
    print(f"Approved rows still unmatched: {len(unmatched_rows)}")
    print(f"Unmatched report: {UNMATCHED_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

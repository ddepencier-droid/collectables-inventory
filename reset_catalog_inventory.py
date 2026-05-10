from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(r"C:\Collectables\Inventory\inventory.db")
BACKUP_DIR = Path(r"C:\Collectables\Inventory")


def export_catalog_inventory_snapshot(connection: sqlite3.Connection, destination: Path) -> int:
    rows = connection.execute(
        """
        SELECT
            id,
            franchise,
            property_name,
            product_line,
            manufacturer,
            release_year,
            wave,
            item_name,
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
        WHERE quantity_owned > 0
           OR TRIM(COALESCE(condition, '')) <> ''
           OR TRIM(COALESCE(storage_location, '')) <> ''
           OR TRIM(COALESCE(ownership_notes, '')) <> ''
        ORDER BY franchise, property_name, product_line, item_name
        """
    ).fetchall()

    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "franchise",
                "property_name",
                "product_line",
                "manufacturer",
                "release_year",
                "wave",
                "item_name",
                "owned",
                "quantity_owned",
                "complete_count",
                "sealed_count",
                "packaged_count",
                "condition",
                "storage_location",
                "ownership_notes",
                "inventory_source_name",
                "inventory_updated_at",
            ]
        )
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"catalog_inventory_backup_{timestamp}.csv"

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        exported = export_catalog_inventory_snapshot(connection, backup_path)

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
            """
        )
        deleted = connection.execute(
            "DELETE FROM items WHERE source_name = ?",
            ("AppSheet",),
        ).rowcount
        connection.commit()

    print(f"Backup written: {backup_path}")
    print(f"Exported catalog inventory rows: {exported}")
    print(f"Deleted AppSheet item rows: {deleted}")
    print("Catalog ownership fields reset to zero/blank.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

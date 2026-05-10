import sqlite3
conn = sqlite3.connect(r'C:\Collectables\Inventory\inventory.db')
rows = conn.execute("""
select franchise, property_name, product_line, manufacturer, release_year, wave, item_name, release_type, source_name, notes
from catalog_items
where lower(franchise) like '%voltron%'
   or lower(property_name) like '%voltron%'
   or lower(product_line) like '%voltron%'
   or lower(item_name) like '%voltron%'
order by franchise, property_name, product_line, release_year, item_name
""").fetchall()
print(len(rows))
for row in rows[:300]:
    print('|'.join(str(x) for x in row))

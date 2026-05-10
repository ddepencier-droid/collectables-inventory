# Collectables Inventory

A lightweight local web app for tracking collectible items, including ownership, quantity, condition, storage location, notes, and a growing reference catalog for vintage toy lines.

## Features

- Add, edit, and delete collectibles in your personal inventory
- Track whether you own an item and how many copies you have
- Store condition values like Sealed, Boxed, Carded, Complete, Loose, Opened, or Damaged
- Filter by ownership and condition
- Search across names, series, categories, item numbers, and notes
- Local SQLite database with no external service required
- Separate `catalog_items` table for a collectible master list seeded from researched source data
- Catalog API with filters for franchise, manufacturer, release type, and release year range
- Cached market pricing pipeline with provider priority:
  `eBay sold comps -> eBay active listings`

## Catalog Seed Data

The starter catalog lives in `data\catalog_seed.csv` and is imported automatically into the `catalog_items` table when the database is empty.

The current starter set focuses on a verified first pass across major vintage-friendly properties and later revival lines, including:

- Star Wars
- Masters of the Universe
- G.I. Joe
- Transformers
- Teenage Mutant Ninja Turtles

Each seed row includes:

- Franchise
- Property name
- Product line
- Manufacturer
- Release year
- Wave or assortment label
- Item name
- Release type (`vintage`, `reissue`, or `modern`)
- Source name
- Source URL
- Notes about interpretation or inference

## API Endpoints

- `GET /api/items`
- `POST /api/items`
- `PUT /api/items/<id>`
- `DELETE /api/items/<id>`
- `GET /api/catalog-items`
- `GET /api/catalog-summary`
- `GET /api/catalog-photo-audit`
- `GET /api/catalog-pricing-status`
- `POST /api/catalog-pricing-refresh`

Example catalog query:

`/api/catalog-items?franchise=Transformers&release_type=vintage&year_from=1984&year_to=1985`

Example photo audit query:

`/api/catalog-photo-audit?property_name=Biker%20Mice%20From%20Mars`

## Catalog Import Standard

Catalog work now includes a required photo workflow as part of the normal process.

For each new property or line, the target workflow is:

1. Build the checklist from a collector source with clear source attribution.
2. Use romaji for user-facing names when importing from Japanese-language sources. Keep native-script names only in notes when they help with source traceability.
3. Add a verified main image wherever one can be sourced.
4. Immediately run a dedicated second-source packaging pass for boxed/carded images.
5. Use the photo audit endpoint to measure remaining gaps before calling the property complete.
6. If packaged-photo coverage is still partial, report the property as `photo incomplete` instead of treating it as finished.

Photo coverage expectations:

- `both` means the item has loose and packaged photos
- `loose_only` means only the main/loose image is verified
- `packaged_only` means only the packaged image is verified
- `missing` means neither image has been sourced yet

Completion language:

- `Imported` means the checklist exists in the catalog
- `Photo pass started` means at least some verified images are attached
- `Packaging pass started` means the second-source packaged-photo search has begun
- `Photo complete` means every row has at least one verified image
- `Photo incomplete` means the line still needs one or more images
- `Fully illustrated` means every row has both loose and packaged photos

`GET /api/catalog-items` now returns a `photo_summary` block per catalog item, and `GET /api/catalog-summary` includes top-level photo coverage counts for the full catalog.

For very large franchises that need repeated multi-pass work, use a dedicated import
playbook when available.

Current franchise playbook:

- [TRANSFORMERS_IMPORT_WORKFLOW.md](C:/Collectables/Inventory/TRANSFORMERS_IMPORT_WORKFLOW.md)

## Pricing Setup

Catalog pricing is cached into the database and refreshed in this order:

1. `eBay sold comps` when Marketplace Insights access is available
2. `eBay active listing range` as the fallback/default

The app can attempt a background refresh on startup when credentials exist. You can also use the `Refresh prices` button in the catalog UI or call:

`GET /api/catalog-pricing-status`

to verify eBay auth and pricing configuration, then call:

`POST /api/catalog-pricing-refresh`

### Environment variables

- `EBAY_CLIENT_ID` — your eBay App ID / Application ID
- `EBAY_CLIENT_SECRET` — your eBay Cert ID / Client Secret
- `EBAY_MARKETPLACE_INSIGHTS_ENABLED=1` to enable historic sold-comps pricing
- `EBAY_MARKETPLACE_ID=EBAY_US`
- `EBAY_USE_SANDBOX=0` to use production eBay endpoints, or `1` for sandbox credentials
- `EBAY_API_HOST=api.ebay.com` to override the eBay API host if needed
- `CATALOG_PRICE_DEBUG=0` to enable pricing debug output when set to `1`
- `CATALOG_PRICE_REFRESH_ON_START=1`
- `CATALOG_PRICE_REFRESH_STARTUP_HOURS=168` to only run the startup refresh once every 7 days
- `CATALOG_PRICE_REFRESH_LIMIT=25`
- `CATALOG_PRICE_TTL_HOURS=24`

The app automatically loads `C:\collectables\inventory\.env` on startup. A starter template is included as:

- `C:\collectables\inventory\.env`
- `C:\collectables\inventory\.env.example`

Notes:

- eBay sold comps depend on Marketplace Insights access, which eBay documents as limited release.
- Active eBay listing prices are the default no-paywall fallback.

## Run locally

1. Open a terminal in `C:\collectables\inventory`
2. Create and activate a virtual environment if you want one
3. Install dependencies:
   `pip install -r requirements.txt`
4. Start the app:
   `python app.py`
5. Open `http://127.0.0.1:5000`

The SQLite database file will be created automatically as `inventory.db`.

## Catalog Import Standards

This project treats `catalog completeness` and `photo completeness` as separate checks.
It also treats `initial image coverage` and `packaged-photo coverage` as separate passes.

### Required steps for a new property

1. Build the item list from one or more collector/reference sources.
2. Record `source_name` and `source_url` for the checklist source.
3. For Japanese-source material, store user-facing names in `romaji` rather than Japanese script. Keep native-script names only in `notes` when they are useful for source traceability.
4. Add a verified main image for each item whenever one can be sourced.
5. Run a dedicated second-source pass for packaged photos immediately after the initial import.
6. Mark any remaining rows without a packaged image as `photo incomplete` instead of treating the property as finished.
7. Sync the curated seed into `inventory.db`.
8. Check `GET /api/catalog-photo-audit` before calling the property finished.

### Completion language

- `Imported` means the checklist exists in the catalog.
- `Photo pass started` means at least some verified images are attached.
- `Packaging pass started` means a second-source search for boxed/carded photos is underway.
- `Photo complete` means every row has at least one verified image.
- `Photo incomplete` means the checklist is present, but one or more rows still need a main photo, packaged photo, or both.
- `Fully illustrated` means every row has both loose and packaged photos.

### Working rule

Do not describe a property as `finished` unless:

- the checklist import is complete
- the packaging-photo pass has been attempted
- the response clearly states whether the property is `photo incomplete` or `fully illustrated`

For Japanese-exclusive lines, default to romaji in:

- `property_name`
- `product_line`
- `wave`
- `item_name`

Only preserve Japanese-script text in `notes` when it helps explain a source page, packaging label, or alternate title.

### API fields

Each catalog item exposes:

- `photo_summary.has_loose_photo`
- `photo_summary.has_packaged_photo`
- `photo_summary.status`

Valid `photo_summary.status` values:

- `both`
- `loose_only`
- `packaged_only`
- `missing`

### Audit endpoint

Use:

`GET /api/catalog-photo-audit`

Optional filters:

- `franchise`
- `property_name`

This endpoint returns per-property counts for:

- total items
- loose photo count
- packaged photo count
- both photo count
- missing all photo count

## Large franchise rule

For exceptionally large franchises with many eras or regional branches,
create and follow a dedicated workflow document instead of re-deciding structure
on each pass.

Current large-franchise playbook:

- `TRANSFORMERS_IMPORT_WORKFLOW.md`

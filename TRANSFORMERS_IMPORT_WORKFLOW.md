# Transformers Import Workflow

This workflow is the default playbook for expanding `Transformers` with minimal prompting.

It exists because `Transformers` is too large and too taxonomy-heavy to re-decide structure
every time we import a new era.

## Goal

Use one shared franchise:

- `franchise = Transformers`

Use `property_name` to separate major western and Japanese branches.
Use `product_line` for the specific toy line, subline, or assortment.

This keeps the catalog browsable while still supporting Japanese-exclusive material,
reissues, and modern collector lines.

## Default taxonomy

### Western properties

- `Transformers`
  Use for the main western retail family when the line is primarily sold under the core
  `Transformers` brand.
- `Beast Wars`
- `Beast Machines`
- `Transformers: Armada`
- `Transformers: Energon`
- `Transformers: Cybertron`
- `Transformers Animated`
- `Transformers Prime`
- `Robots in Disguise`
- `Transformers (Movie)`
- `War for Cybertron Trilogy`
- `Legacy`
- `Studio Series`
- `Masterpiece`

### Japanese properties

Use the specific Japanese source line in romaji:

- `Fight! Super Robot Lifeform Transformers`
- `Transformers: The Headmasters`
- `Transformers: Chojin Masterforce`
- `Transformers: Victory`
- `Transformers: Zone`
- `Beast Wars II`
- `Beast Wars Neo`
- `Transformers: Car Robots`
- `Transformers: Micron Legend`
- `Transformers: Superlink`
- `Transformers: Galaxy Force`
- `Transformers Go!`
- `Diaclone`
- `Micro Change`

If a Japanese line is the source material for a western line, keep it under the
`Transformers` franchise but preserve the Japanese property name.

## Product line rules

Use `product_line` for the exact sell-through line or assortment:

- `Generation 1`
- `Battle Beasts`
- `Commemorative Series`
- `Encore`
- `Binaltech`
- `Alternators`
- `Henkei! Henkei!`
- `Siege`
- `Earthrise`
- `Kingdom`
- `Studio Series 86`
- `Missing Link`

When a line has both a broad family and a narrow collector subline, prefer:

- `property_name = broad family`
- `product_line = exact line`

Example:

- `property_name = Transformers`
- `product_line = Studio Series`

or

- `property_name = Transformers`
- `product_line = Studio Series 86`

## Name rules

- Use the package/checklist name as the default item name.
- For Japanese-source material, use `romaji` in user-facing fields.
- Keep native-script text only in `notes`.
- Keep well-known westernized names only when the item was actually sold that way.
- Prefer explicit variant labels over duplicate bare names.

Examples:

- `Convoy` stays `Convoy` in a Japanese-exclusive line.
- `Optimus Prime` stays `Optimus Prime` in a western line.
- Use variant labels like `Starscream (Coronation)` or `Bumblebee (Gold Bug Recolor)`
  when the checklist/source clearly distinguishes them.

## Release bucket rules

- `release_year < 2000` defaults to vintage unless clearly a later reissue line.
- Explicit reissues should use the reissue-appropriate product line and notes.
- Modern collector lines should stay modern even when they reproduce vintage tooling.

## Photo rules

Transformers should follow the normal project photo workflow:

1. Import checklist.
2. Add verified main image.
3. Run dedicated packaged-photo pass.
4. Report whether the property is `photo incomplete` or `fully illustrated`.

### Source priority by era

#### Western vintage and broad retail

- `Transformerland`
- `TFU.info`
- `ActionFigure411` when available
- `Figure Realm` as support

#### Japanese-exclusive and Takara-heavy lines

- `TFU.info`
- `TFormers`
- Japanese fan wikis / collection sites when stable
- `Transformerland` where coverage exists

#### Modern collector lines

- `ActionFigure411`
- official retailer/manufacturer pages when needed

### Image honesty rule

Do not infer a loose photo from a package-front image.
Do not reuse one hero image across many rows unless the row is explicitly documented
as a group-pack or category image fallback in `notes`.

## Default import order

Unless the user explicitly redirects, process Transformers in this order:

1. `Generation 1` western core
   `1984-1990`
2. `Battle Beasts`
3. western late-90s / early-2000s bridge lines
4. `Armada` / `Energon` / `Cybertron`
5. movie-era western lines
6. `Animated` / `Prime` / later `Robots in Disguise`
7. `War for Cybertron Trilogy`
8. `Legacy` / `Studio Series` / `Masterpiece`
9. Japanese-exclusive G1 continuation
   `Headmasters`, `Masterforce`, `Victory`, `Zone`
10. Japanese Beast-era and later Takara branches
11. pre-Transformers Japanese source families
   `Diaclone`, `Micro Change`

## Batch size rules

To minimize prompting, use these default chunk sizes:

- western vintage:
  year blocks of `2-3` years
- large modern lines:
  by major product line
- Japanese exclusives:
  one property at a time

Only stop for user confirmation when:

- a naming decision would merge or split a major family in a surprising way
- a source conflict would risk bad taxonomy
- two different structures are both plausible and would be costly to unwind

Otherwise, proceed automatically and report assumptions after the import.

## Seed naming convention

Use predictable filenames:

- `transformers_g1_1984_1985_catalog_seed.csv`
- `transformers_g1_1986_1987_catalog_seed.csv`
- `transformers_battle_beasts_catalog_seed.csv`
- `transformers_headmasters_catalog_seed.csv`
- `transformers_studio_series_catalog_seed.csv`

Avoid one giant monolithic Transformers seed if the line can be cleanly split.

## Live cleanup rules

After each Transformers batch:

1. sync curated seed
2. remove stale Access duplicates for the replaced slice
3. preserve licensed-product or owned-inventory extras unless the curated seed
   explicitly supersedes them
4. verify live counts by:
   - source
   - property
   - product line
   - photo coverage

## First recommended execution sequence

The default starting sequence from the current database state is:

1. `Generation 1`
   `1984-1985`
2. `Generation 1`
   `1986-1987`
3. `Generation 1`
   `1988-1990`
4. `Battle Beasts`
5. Japanese G1 continuation
   `Headmasters`, `Masterforce`, `Victory`

That sequence gives the biggest value quickly while establishing the taxonomy for
everything else.

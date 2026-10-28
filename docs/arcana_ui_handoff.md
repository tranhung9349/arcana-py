# Arcana gothic interface

Implemented 27 October 2026 with the UI UX Pro Max workflow. The theme covers Gieo bộ số, Tra ngày theo việc, Mai Hoa, Gieo 3 đồng / Lục Hào, and Luận Giải Bát Tự.

## Delivered

- Replaced the previous green/light stylesheet with a shared token-based ink, amethyst and antique-gold design.
- Added a compass identity/favicon, a celestial seal, pointed manuscript arches, consistent outline navigation icons and contextual workspace introductions.
- Redesigned forms, selected navigation, number medallions, history, date tiles, date dialog, hexagrams, four-pillar charts, AI articles and evidence disclosures.
- Preserved the existing brand tagline and all feature/controller IDs. `arcana_ui.js` only updates introductory text in response to existing navigation buttons; it performs no network requests.
- Self-hosted ten Latin/Vietnamese WOFF2 subsets, approximately 147 KB including font CSS and licenses. No runtime font CDN or animation dependency.
- Added keyboard skip navigation, visible focus, minimum 44px disclosure targets, 48px form actions, reduced-motion rules and forced-color handling.

## Verified

- Existing frontend suite: **31 passed**. All frontend JavaScript passes `node --check`.
- HTML IDs are unique, local HTML asset references exist, and SVGs parse successfully.
- Browser checks at 375, 768, 1024 and 1440 CSS pixels: no document horizontal overflow for the saved number result. Saved Bazi checked at 375/768/1024; saved Mai Hoa and Liu Hao checked at 375. Landscape date page checked at 812×375.
- Loaded the saved number draw, opened its deep Mai Hoa explanation, and verified cached real AI articles for Bazi, Mai Hoa and Liu Hao. These showed prose without serialized structures.
- Performed a single-day date search for 13 October 2026 using the existing synthetic 1994 sample. Verified the mobile date dialog, explanation, scroll area, Escape dismissal and focus restoration to the originating tile.
- No paid AI generation was initiated for visual verification.
- Font loading reached `loaded` in the browser. Reduced-motion support is implemented in CSS; the operating-system preference was not changed during this task.

Measured semantic color contrast against relevant opaque surfaces:

| Pair | Ratio |
| --- | --- |
| Main text / raised surface | 13.84:1 |
| Secondary text / raised surface | 7.67:1 |
| Muted text / raised surface | 6.56:1 |
| Gold text / panel | 10.06:1 |
| Amethyst text / purple panel | 7.35:1 |
| Favorable text / favorable surface | 9.34:1 |
| Error text / error surface | 8.23:1 |
| Button text / darker gold | 8.54:1 |
| Input outline / surrounding panel | 3.23:1 |

## Screenshots

- `docs/research/arcana-ui/desktop.png` — desktop home.
- `docs/research/arcana-ui/mobile.png` — mobile Liu Hao workspace.
- `docs/research/arcana-ui/date-mobile.png` — date explanation dialog.

Design decisions and tokens: `design-system/arcana/MASTER.md`.

## Tailwind migration and select alignment — 28 October 2026

- Added project-local Tailwind CSS/CLI **4.3.3**, pinned dependencies and npm lockfile. `npm run build:css` compiles `web/styles/app.css` and `web/styles/arcana.css` to the served `web/style.css`; `npm run watch:css` supports development. Python serves the generated asset without a runtime CDN or Node process.
- Migrated main gutters, responsive workspace grids and navigation columns to Tailwind utilities. Shared label, input, select, textarea, paired-field and manual-coin layouts use Tailwind component utilities. Kept existing gothic artwork, palette, typography and reading styles in the component layer. Tailwind Preflight is intentionally omitted to preserve existing prose/list defaults.
- Selects now have a consistent 48px height, 24px line height, zero vertical padding and a local gold chevron, with 44px reserved on the right. Native selection/keyboard semantics remain. Forced-colors restores the native arrow.
- Paired date/time controls align at their bottom edge when labels wrap. Low-specificity shared input rules allow the paired-field auto margin to work. Manual coin faces stack inside each throw instead of squeezing three select values into a narrow column. Shortened the two casting-method labels while keeping their values and behavior.

Verified after migration:

- All five workspaces at **375, 768, 1024 and 1440px**: no horizontal document overflow; every visible select is 48px tall with the shared chevron.
- All **18 manual coin selects** at those four widths: no overflow, height 48px, minimum observed width 176px. Selecting three faces updates the existing line-state description correctly.
- Paired dates/hours share the same top and bottom at 768/1024/1440px, including the wrapped hour label; at 375px they stack at full width. The second date subject and custom casting-time fields still appear when selected.
- Saved Bazi rereading select and all three saved Liu Hao controls checked at 375/1024px. Cached prose remains readable. Keyboard Tab shows the 2px amethyst outline. No paid AI generation initiated.
- Date workspace at **812×375**: no horizontal overflow. Browser viewport override reset afterward.
- **31 frontend tests passed**. All **147 original HTML IDs retained**, no duplicate IDs, all local HTML asset references resolve, and generated CSS contains compiled Tailwind utilities without build directives.

Screenshots: `docs/research/arcana-tailwind/desktop.png` and `docs/research/arcana-tailwind/mobile.png`.

Build guidance follows the official [Tailwind CLI installation](https://tailwindcss.com/docs/installation/tailwind-cli), [directives](https://tailwindcss.com/docs/functions-and-directives) and [incremental integration without Preflight](https://tailwindcss.com/docs/preflight#disabling-preflight).

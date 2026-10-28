# Arcana — Celestial Gothic

Arcana is a Vietnamese divination and reflection tool with five workspaces: number rituals, date selection, Mai Hoa, Liu Hao, and Ba Zi. Its visual identity is a quiet gothic reading room: ink, amethyst, antique gold, fine celestial linework, and illuminated manuscript arches.

## Foundations

- Use `web/styles/app.css` for Tailwind theme aliases, explicit HTML/JS sources and breakpoints, and `web/styles/arcana.css` for shared components and semantic theme tokens. `web/style.css` is the generated asset; rebuild it with `npm run build:css`.
- Ink `#0e0b14`; surface `#17121f`; raised surface `#20192b`.
- Main text `#eee7dc`; secondary text `#b6aabd`; muted text `#aa9cb1`.
- Antique gold `#ddbf83` for primary actions and emphasis; amethyst `#c3a4e6` for secondary highlights.
- Jade `#a4d4bc` and rose `#eeaaa9` identify favorable and caution states alongside written labels.
- Controls use `#75627f` outlines. Decorative borders may be quieter; essential controls may not.
- Cormorant Garamond for display typography; Be Vietnam Pro for Vietnamese interface text and reading prose. Local WOFF2 subsets cover Latin and Vietnamese. Both fonts retain their SIL licenses in `web/fonts/`.
- Use line SVGs at consistent stroke weights. Compass, celestial seal, and pointed arch are decorative; they carry no calculation or prediction semantics.

## Layout and interaction

- At desktop widths, use a 346px form column and a flexible reading panel inside a 1280px container.
- At 850px and below, navigation becomes two columns and the workspace becomes one column.
- At 600px and below, use 16px form inputs, single-column date fields, and 16px page gutters.
- Avoid fixed navigation or overlays that obscure the reading or keyboard focus.
- Keep primary buttons at least 48px tall and history/disclosure targets at least 44px tall.
- Use native inputs, selects, details and dialog semantics. Keep selected navigation labels explicit through `aria-pressed`.
- All text inputs and selects use the same 48px height. Selects retain native interaction with `appearance-none`, a local SVG chevron and 44px reserved at the right. Restore native appearance in forced-colors mode.
- Labels and paired fields use shrinkable grid/flex tracks. Paired controls align at the bottom when one label wraps. Manual coin faces stack within each throw so their selected text and chevrons remain readable in the narrow form column.
- Use a visible amethyst focus outline; support the skip link, native Escape behavior, and focus restoration after dialogs.
- Hover/press feedback uses 160ms color, border and shadow transitions. No ambient looping animation. Honor reduced motion and forced colors.
- Long articles use 15–17px body text with 1.9–2 line height. Fold detailed evidence behind native disclosures.
- Keep domain calculations, saved reading content, API behavior and prose-only display protections independent of the theme.

## Skill guidance applied

UI UX Pro Max searches included product-wide dark/mystical direction, `dark luxury ornate` in the style domain (Dark Mode OLED), and `elegant serif editorial` in typography (Classic Elegant). Broad design-system output was too generic for the requested gothic direction; the final palette, local Vietnamese font pairing and celestial artwork are deliberate project-specific design decisions.

## Verification

See `docs/arcana_ui_handoff.md` for tested screens, contrast measurements and screenshots.

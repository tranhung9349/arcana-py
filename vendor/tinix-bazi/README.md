# Tinix BaZi engine in Arcana

Vendored from https://github.com/vhphuoc1102/tinix-bazi.git at commit
`80ff4463d0397c1b11db76f38d880255f55558bc`.
`src/bazi/` and `src/utils/random.js` retain the upstream source and comments.
The upstream backend package declares the MIT license; its repository has no
standalone LICENSE file. Original package metadata is in `UPSTREAM_PACKAGE.json`.

`runner.cjs` is Arcana's stdin/stdout adapter. The Express server, authentication,
database service and OpenRouter service are not imported. Python invokes Node
with an isolated environment; Node never receives LLM credentials.

Runtime: Node.js >=18 and `lunar-javascript==1.7.7` (the upstream lockfile version).
Install from the project root with `npm ci`.

Documented local changes:

- `calculator.js`: preserve hour zero, accept seconds, use sect 1. Python converts
  the Vietnam instant to Beijing before passing its components; both calendars'
  four pillars must agree or the request fails.
- `output.js`: accept an explicit reference time so age-related text follows the
  selected year rather than the host clock.
- `luan_dong.js`, `dong_tinh_luan.js`: use the selected reference year.
- `quan_he.js`: require distinct tokens for two-member combinations; sort branch
  pairs by the branch table instead of Unicode; compare hidden stems and visible
  stems using the same Vietnamese representation when finding roots.
- `luan_giai/core.js`: show year-pillar Na Yin separately from the day master;
  label day-based element prose as Nhật chủ instead of the ambiguous “Kim mệnh”.
- `runner.cjs`: seed the source's random wording for reproducibility inside the
  isolated process and restore `Math.random` afterward.

`manifest.json` records the original and installed SHA-256 for each source file,
and marks modified files. `TinixBaziEngine` verifies installed hashes at startup.
Update that manifest deliberately whenever the source or adapter changes.

The source has several strength-scoring methods. Arcana's public assessment uses
`phan_tich.can_bang_ngu_hanh`; other source analyses remain available for reference.
Source classical-text commentary is presented as engine commentary, not as an
authenticated quotation. Annual and luck scores keep the upstream conventions.

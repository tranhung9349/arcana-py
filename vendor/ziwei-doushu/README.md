# ziwei-doushu in Arcana

The files in `lib/ziwei/` are the chart and pattern engine from
[Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu/tree/78eafbf54d4b571833c78b921b1898be256e7dac).
`manifest.json` records the pinned commit and installed file checksums. The
only source patch removes Next.js's `server-only` marker in `patterns.ts`
because Arcana invokes it in a dedicated Node process.

`runner.cjs` reads a Gregorian date, branch index and gender on stdin. It emits
one chart and the matching pattern conditions on stdout. It uses the upstream
default split leap-month and star brightness settings. Arcana supplies the
effective date using the Vietnam civil clock and advances the date at 23:00.
The runner uses the pinned `iztro`, `lunar-javascript` and `tsx` dependencies
from the project root. It does not import the upstream web app or data releases.

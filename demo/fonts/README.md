# Preview fonts

Self-hosted so the preview loads nothing from another origin.

| File | Family | Source | Licence |
| --- | --- | --- | --- |
| `atkinson-hyperlegible-next.woff2` | Atkinson Hyperlegible Next, variable `wght` 200–800 | `google/fonts` `ofl/atkinsonhyperlegiblenext/AtkinsonHyperlegibleNext[wght].ttf` | [OFL 1.1](OFL-AtkinsonHyperlegibleNext.txt) |
| `atkinson-hyperlegible-mono.woff2` | Atkinson Hyperlegible Mono, variable `wght` 200–800 | `google/fonts` `ofl/atkinsonhyperlegiblemono/AtkinsonHyperlegibleMono[wght].ttf` | [OFL 1.1](OFL-AtkinsonHyperlegibleMono.txt) |

Both files are subsets (Basic Latin, Latin-1, common punctuation, `≤ ≥ ≈ ≠ −`, Greek `μ π`)
converted to WOFF2 with fontTools. The upstream fonts lack the micro sign
U+00B5 used in `µT`, so the subset maps U+00B5 to the existing Greek mu glyph
(U+03BC). No outlines were changed.

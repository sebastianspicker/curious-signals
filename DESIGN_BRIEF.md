# Design brief: Curious Signals static preview

Scope: the one rendered surface this repository ships, `demo/` (deployed to
GitHub Pages as the "Live preview" linked from the README). Firmware, experiment
XML, and tooling are out of scope except where the preview quotes their facts.

## 1. Product summary

Curious Signals is a classroom kit. An original Arduino Nano 33 BLE Sense runs
one sketch, advertises as `phyphox-sense`, and streams 20-byte frames (five
little-endian `float32`: device time plus four channels) to the phyphox app on a
phone. Seven generated `.phyphox` files select sensor modes 1–6 and 9. A
separate astronomy collection uses other sensors and never touches the board.

The preview is a deterministic, offline page. It shows what each mode produces
(channels, units, plausible trace shapes) without hardware, Bluetooth, or a
phone. It must make no network, sensor, storage, or Bluetooth calls; the browser
test enforces this down to the exact set of requested URLs.

**Moment of value:** a teacher picks a mode and sees what will appear on the
students' phones, with the right channels, units, and plausible magnitudes. They
also learn which file to import and what the board needs. The second moment is
for the technically curious: seeing what is actually sent over the air.

## 2. Audience

**Primary: a secondary-school or first-year-university physics teacher**,
probably in a German-speaking (or French-speaking) system, already familiar
with phyphox. They prepare at a desk, decide whether the kit is worth a lesson,
and often project the page to a class.

- Expertise: strong physics, moderate electronics, little patience for software
  setup. Knows units, axes, and noise; notices a wrong unit immediately.
- Goals: know what each mode shows, which file to import, what hardware to buy
  (original board, not Rev2), and where the limits are.
- Anxieties: a lesson failing in front of 28 students; buying the wrong board;
  several boards in one room interfering; data that looks real but isn't.
- Distrusts: EdTech gloss, stock photos of smiling children, claims that hide
  the limits, dashboards that look impressive and say nothing.
- Daily tools: phyphox, a projector, Arduino IDE, worksheets, graph paper,
  GeoGebra/Excel.
- Quality signals for them: correct SI units and symbols, honest scope
  statements, legibility from the back row, numbers that are easy to tell apart
  (`0`/`O`, `1`/`l`, `A0`/`AO`), and plots that follow graphing conventions.

**Secondary:** students holding a phone at 390 px next to the real phyphox
layout; and makers/contributors who want the wire format.

## 3. Key journeys

1. **Preview a mode** (primary): land → pick a mode → read the trace, readouts,
   units → optionally play the simulated stream.
2. **Get set up:** learn the board, the firmware command, and which file to
   import for the mode currently selected → follow the link to the file.
3. **Understand the wire format:** see the 20-byte frame for the current sample,
   including `NaN` for unused channels and the unit phyphox converts from.
4. **Check the limits:** what is real, what is simulated, what the kit can't do
   (one board in range, no Rev2, no calibration proof).
5. **Leave for the repository:** experiment files, companion, license.

## 4. Brand traits

| Trait | Not tipping into |
| --- | --- |
| Precise: units, symbols, figures are exact | Pedantic: no wall of caveats |
| Candid: says what is simulated, once, clearly | Apologetic: no "Not run here" on every card |
| Classroom-sturdy: legible on a projector at the back of the room | Childish: no primary-colour toy look |
| Instrument-like: feels like a lab tool that writes data | Cold: still warm and inviting to a non-programmer |
| Curious: invites "what happens if…" | Cute: no mascots, sparkles, or exclamation marks |

## 5. Market observations

Reasoned from knowledge of the category, not live browsing:

- **phyphox.org**: white, academic, orange accent, function first. The app
  itself is dark with orange chrome. Users of this kit know it intimately.
- **Arduino education / Science Journal**: Arduino teal, rounded friendly
  illustration, product photography. The current preview's teal (`#009297`,
  near Arduino's `#00979D`) reads as an Arduino sub-brand, which the project
  isn't.
- **PASCO, Vernier**: corporate edu blue, product shots, catalogue grids.
- **Generic sensor dashboards**: dark mode, neon traces, glowing cards.

Conventions to keep (users rely on them): time on the x axis, units next to
every number, a legend, phyphox's channel colour mapping (x green, y blue,
z yellow, magnitude white; temperature orange, humidity blue; R/G/B for light).

Conventions to break: dark neon dashboards, product-photo heroes, three
identical feature cards, a borrowed hardware-brand colour.

## 6. What to keep

- The single-page structure: mode selector, chart, readouts, playback, a
  how-it-works strip, a scope statement. It works; the problem is execution.
- All behaviour and every string the browser tests pin (title, button labels,
  status messages, `N.N s fixture`, readout text).
- The deterministic fixture maths (byte-for-byte; a test compares all values).
- The honesty. The repository's tone is unusually candid about limits, and that
  is brand equity worth amplifying.
- The favicon idea (a pulse trace). There is no logo beyond the wordmark.

## 7. Current weaknesses

- Borrowed identity: Arduino-like teal on a near-black dashboard. Nothing
  says "classroom" or "phyphox".
- System/Inter typography; no typographic voice; readout numerals are small.
- The chart is a fixed 920×360 viewBox scaled to the container, so at 390 px
  its axis labels render at about 5 px, unreadable on the phone it's meant for.
- Trace colours (blue/green/yellow/white) don't match phyphox's mapping, so a
  student comparing side by side sees different colours for the same axis.
- "Simulated fixture value" is repeated under every readout, and "Not run here"
  under every step: four and three repetitions of the same caveat.
- The three how-it-works cards are generic and identical, and step 2 doesn't
  say which file matches the selected mode.
- Modes 7 and 8 silently disappear, so the jump 6 → 9 looks like a bug.
- The most useful classroom caveats (one board in range, original board only)
  are only in the README.
- Mobile: a horizontally scrolling strip of 150 px mode buttons hides most modes.

## 8. Constraints (load-bearing)

- Requests limited to same-origin static files; no `fetch`, storage, cookies,
  sensors, Bluetooth (the test guards these APIs). No CDN fonts or scripts.
  Self-hosted fonts mean the test's request allow-list must grow by those files.
- Globals `modes`, `state`, `fixtures`, `pointCount`, `precisionFor`,
  `modeUnit`, `fixtureValue` are read by tests; scripts stay classic and global.
- IDs: `#mode-list`, `[data-mode]` with `aria-pressed`, `#readouts output`
  (`aria-live="off"`, `aria-labelledby`, text "value unit"), `#chart-lines
  polyline` (one per series), `#chart-labels text` (17 for mode 5),
  `#toggle-stream`, `#reset-fixture` (next in tab order), `#stream-status`,
  `#chart-progress`, `.wordmark`, `.chart-shell` (screenshot target).
- Contrast measured by the test against each control's *own* computed
  background, so controls need opaque backgrounds in every state.
- Playback cadence: 90 ms per point (450 ms → "1.0 s fixture").
- Reduced motion: no playback animation, `scroll-behavior: auto`.
- No horizontal scroll at 390 px. GitHub Pages serves `demo/` as is (no build).
- README screenshots in `docs/images/` are regenerated from the browser test.
- Fonts must be openly licensed; the licence must ship with the files.

## 9. Assumptions log

| # | Assumption | Evidence | Confidence |
| --- | --- | --- | --- |
| A1 | Primary audience is physics teachers who already use phyphox | README "classroom kit", phyphox integration, de/fr translations, astronomy companion's teaching caveats, author's German context | High |
| A2 | The page is often projected in a lit classroom | Classroom framing; README says students compare it with phyphox; projectors are standard in German classrooms | Medium |
| A3 | A light, paper-like default reads better than dark for that context | Projectors wash out dark UIs in daylight; teachers print and annotate on paper | Medium |
| A4 | Matching phyphox's per-channel colours helps more than an independent palette | Experiment XML sets colours; README invites side-by-side comparison | High |
| A5 | Showing the encoded 20-byte frame is valuable, not noise | Contract, firmware README and AGENTS all centre on the frame; makers are a stated audience | Medium |
| A6 | The fixture's 121 points span 24 s, i.e. one point per 200 ms | `pointCount = 121`, x axis labelled 0–24 s, progress `(n-1)/5` | High |
| A7 | Wire units: accel in g (×9.81), gyro in °/s (×π/180), pressure in kPa (×10), analog in raw counts (×3.226 → mV) | `src/phyphox/*.xml` analysis formulas and firmware comments | High |
| A8 | Users don't need the preview in German or French | Page is English; repo docs are English; astronomy translations are app-side | Low–medium |
| A9 | Self-hosted fonts are acceptable within the "no network" rule | The rule's intent is privacy/offline: same-origin static files already load (CSS, JS) | Medium |

---

## Design Direction

### Mining the domain

- **Materials:** Millimeterpapier (orange-ruled graph paper that German physics
  classes still use), lab notebooks, pen strip-chart recorders, worksheet
  photocopies, the Arduino's tiny silk-screened pin labels.
- **Tools and rituals:** "Versuch" protocols (setup → measurement →
  evaluation), reading a value off a graph, the teacher at the projector.
- **Vocabulary:** mode, channel, CH1–CH5, frame, notify, `float32`, `NaN`,
  fixture, sample.
- **Emotional state:** a teacher preparing alone in the evening, wanting
  certainty before tomorrow's lesson; a student holding a phone, a bit unsure
  what the numbers mean.

### Direction A: "Recorder paper"

- **Concept:** the page is a sheet from a pen recorder on millimetre paper. The
  instrument writes, the teacher reads. Traces are ink on paper. The frame the
  board sends is printed under the plot like a recorder's data margin.
  This fits a projected, lit classroom and the teacher's own graph-paper
  habits. It's candid because paper shows only what was written.
- **Typography:** Atkinson Hyperlegible Next (text, headings) with Atkinson
  Hyperlegible Mono (numerals, units, channel codes, bytes). The family was
  drawn for low-vision legibility, with strongly differentiated `0/O`, `1/l/I`,
  `A0/AO`. That is exactly the failure mode of reading readouts from the back
  row. One superfamily; hierarchy comes from weight and the
  proportional/mono switch. Scale 12 / 14 / 16 / 18 / 22 / 28 / 40 /
  clamp(40–64) readouts.
- **Colour:** paper, ink, three ink greys, one ruling colour (millimetre-paper
  sepia-orange, used only for grid lines and the active marker), and six pen
  inks translated from phyphox's own channel colours to ink-on-paper (green,
  blue, ochre for yellow, ink for white, red, orange). Dark mode is a "night
  sheet" with the same roles.
- **Layout:** 8 px base unit with 40 px majors (the 1 mm/5 mm rhythm of graph
  paper); a left mode index and a wide sheet on desktop; on phones a numeric
  keypad of the seven modes, then a full-width plot drawn at true pixel size.
- **Motion:** only the pen writes. During playback a pen head leads each trace.
  Colour transitions on controls take 120 ms. Nothing fades in on scroll.
- **Signature details:** (1) the live 20-byte frame strip with hex bytes
  grouped CH1–CH5, wire values in wire units, `NaN` shown as `00 00 c0 7f`;
  (2) the mode index shows the gap honestly: "7, 8 reserved".
- **Against the category:** neither dark dashboard nor product catalogue. It
  looks like the paper a physics teacher already trusts.
- **Refuses:** gradients, glows, cards with shadows, hero images, icons in
  circles, coloured headline text.

### Direction B: "Instrument faceplate"

- **Concept:** a bench instrument front panel: anodised dark plate, engraved
  labels, a rotary mode selector, seven-segment-style readouts, the plot as an
  oscilloscope screen.
- **Typography:** a DIN-like engineering grotesk (e.g. "Barlow Semi Condensed")
  for engraved labels, a segment-inspired mono for readouts.
- **Colour:** graphite plate, engraved off-white, one phosphor colour for
  traces, amber for warnings.
- **Layout:** a fixed panel grid with hard modules; dense; the page is "the
  device".
- **Motion:** knob rotation on mode change, a phosphor persistence trail.
- **Signature:** a rotary selector with detents at 1–6 and 9, blanked at 7/8.
- **Against the category:** more physical than a dashboard.
- **Refuses:** paper, softness, editorial text.
- **Risk:** it is still a dark dashboard, washes out on projectors, is
  skeuomorphic, and its phosphor monochrome loses phyphox's per-channel colours.

### Direction C: "Versuchsprotokoll" (lab handout)

- **Concept:** an A4 lab handout: numbered sections (Aufbau, Durchführung,
  Auswertung), figure captions "Fig. 5", margin notes for caveats, printable.
- **Typography:** a text serif (e.g. "Source Serif 4") for prose, a grotesk for
  figure labels, mono for code.
- **Colour:** white page, black text, one red pen for teacher annotations.
- **Layout:** a single editorial column with a wide margin rail for notes;
  sections in reading order.
- **Motion:** none beyond playback.
- **Signature:** red margin annotations carrying every caveat beside the claim
  it qualifies; a print stylesheet that produces a usable worksheet.
- **Against the category:** reads like teaching material, not a product.
- **Refuses:** app chrome, panels, any dashboard feel.
- **Risk:** puts the interactive moment of value below the fold, and the
  long-form reading model fights the "pick a mode, see the trace" journey and
  the phone user.

### Choice: Direction A, "Recorder paper"

A wins on the primary journey and the primary person. It keeps the plot as the
hero, as an instrument would, while looking like the paper teachers already
trust. It is the most legible option on a projector (A2, A3), and its ink
palette can carry phyphox's channel colours faithfully (A4). The typeface choice
has a reason specific to this audience: telling numbers apart at a distance.

From C it borrows figure captions, a short print stylesheet, and the habit of
putting each caveat next to the claim it qualifies. From B it borrows nothing
visual, but keeps the idea that the mode selector should show the reserved gap.

**Trading away:** B's instant "device" read and C's long-form teaching voice.
A light default may feel less "techy" to makers; dark mode (night sheet) covers
them. If A2/A3 are wrong and the page is mostly read on personal screens, the
paper look still holds, because it is a calm, high-contrast reading surface, and
`prefers-color-scheme: dark` is honoured.

### Anti-pattern check

- No gradients, glows, glass, blobs, grain, centred hero, card rows, bento,
  Inter, emoji, or sparkle icons.
- The graph-paper grid appears only inside the plot, where it has a real job
  (reading values), not as page decoration.
- The only icons are the existing play/pause/reset glyphs and two monoline
  marks, drawn to the ink stroke weight.

---

## Critique log (rendered review)

Reviewed as Playwright screenshots at 390, 768, 1024 and 1440 px, light and
dark, at rest, mid-playback, and with keyboard focus. Text overflow was also
checked programmatically for every mode at 320–1920 px, in the full and
two-point playback states.

| Pass | Finding | Fix |
| --- | --- | --- |
| 1 | Mode keys cross-faded through grey-on-grey (2.4:1 mid-transition) | Selector switches instantly, like a detent |
| 1 | Four-channel readouts truncated the unit ("-0.36 m…") at 1440 px | Denser readout size for four channels; no ellipsis |
| 1 | Sketch path broke mid-word | `<wbr>` after path separators; `break-word` |
| 1 | Phone: the plot started below the first screen | Spec plate hidden on phones (it repeats step 02 and the frame panel) |
| 1 | Phone: playback buttons wrapped their labels | Full-width stacked buttons |
| 1 | Tablet keypad: 100 px keys showed only a digit | Mode names shown under the digit between 601 and 860 px |
| 2 | 320 px: a lone pressure readout overflowed half a row | A single readout spans the row |
| 2 | — | No overflow at any width; all browser, contrast, and runtime-boundary tests pass |

Assumption check: if A2/A3 are wrong (the page is mostly read on personal
screens, not projected), the paper sheet is still a calm, high-contrast reading
surface, and dark mode follows the system setting. If A5 is wrong (the frame is
noise for teachers), it sits below the controls and costs nothing in the primary
journey. If A8 is wrong, all copy is in the HTML and in `fixtures.js`
descriptions, ready for translation.

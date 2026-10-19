# THE COUNTER: Design Brief

The single source of truth for what THE COUNTER is, how it must look, feel and sound, and what a design agent may and may not change. If another document disagrees with this one, this one wins. Working draft 02, October 2026. Supersedes `docs/BRAND.md`, which is now Part II here.

## How to use this brief

- Read it end to end before touching UI. Parts I to III are law. Part IV is a snapshot and may drift: verify against the code. Part V is the task.
- Propose before implementing: for each change say what, which law it serves, and the visible result. Tomas wants a confident recommendation, not a menu.
- Where the brief is silent, choose the option that best satisfies the one-sun, light-does-the-talking, function-draws-form principles, and say so. Flag anything that needs a human call in Part V.4 rather than guessing.

## Part I. Product

### Who and why

One user, Tomas: a hobbyist brewer with a refractometer and a Fellow Ode Gen 2, brewing V60, Hario Switch, Aeropress (hot and flash-iced) and the occasional Chemex. The laptop is open on the counter mid-brew, so hands may be wet and attention is split. It is a hobby project and must stay fun. There is no multi-user, hosting or sync requirement.

### The two jobs

1. Log a brew fast. The old four-step wizard killed the habit; speed is the product.
2. See improvement over time: where each cup landed on the extraction chart and whether the process is converging on the ideal zone.

### The three moments

Plan, then Brew, then Taste. Plan prefills a recipe from history. Brew is a wall-clock timer where keyboard events (space bar) capture the pour structure into `brew_events`. Taste records TDS and impressions; a brew stays a draft until scored. The home screen is Today. The rest of the surface: Log (history), Chart (control chart), Shelf (beans), Milestones, and a `/design` specimen route.

### Locked product decisions

- Stack: SvelteKit (Svelte 5, TypeScript, adapter-node), SQLite via better-sqlite3 and Drizzle, charts in custom Svelte SVG with d3-scale only.
- Methods offered in pickers: V60, V60 ceramic, Hario Switch, Aeropress, Aeropress flash iced, Chemex. French Press and Espresso exist only in history.
- Flash-iced Aeropress tracks ice and hot water; ratio and extraction use total water.
- Brewing math is frozen for comparability with the historical brews (see Part III).
- Future: smart-scale time-series logging. Keep `brew_events` forward compatible. Do not build it now.
- `docs/FEATURE_ROADMAP.md` is retired. Do not resurrect it or follow any instruction that cites it.

## Part II. Brand: HARD LIGHT

Approved direction: engraved miniatures, IBM Plex system, engine on hero moments. Clause numerals below are the brand book's own.

Brand guidelines for THE COUNTER. Working draft 01, July 2026.
Approved direction: engraved miniatures, IBM Plex system, engine on hero moments.

### 1.0 The idea

Light is the interface. The instrument reads coffee the way a prism reads the sun, and the app behaves like that instrument.

The Counter is not decorated software. It is an optical instrument with a screen: every reading behaves like light passing through a sample. Refracted, decomposed, resolved. Chrome is its chassis, liquid is its subject, one harsh sun is its condition. Nothing is illustrated to look scientific; the interface obeys physics, so it feels scientific.

Because instruments this good get carried, it carries heritage: engraved miniatures in its borders, the way navigators once illuminated their charts. The tension is the brand: machine precision, human margins. Regal red, worn daily.

Personality: precise, not cold. Regal, not ornate. Alive, not animated. Heritage as cargo.

### 2.0 The world

Galley of a Mars habitat, 07:00 local, year 2075. One skylight, no atmosphere to soften it: the sun lands hard, shadows are long and edged. The floor is command red, a gradient by nature: blazing where lit, oxblood where the chair's shadow falls. Chrome legs carry the room in miniature on their surface.

On the counter: 18 grams of a washed Ethiopian, nine months from a homeworld harvest. The astronaut doesn't brew to survive. They brew to remember. The instrument that helps them is exact about the coffee and reverent about where it came from.

Reference wall: hard-light still photography (the chrome chair on the red floor; the martini and its caustic), caustic and dispersion photography, Ottoman and Persian manuscript borders (My Name Is Red), NASA 1976 worm standards, Imperial command-deck restraint (a hint, never a costume), Braun instrument faces, Kubrick corridors, living spectral edges (the Siri fringe, taken as insight: light that responds, not decorates).

### 3.0 Principles

1. One sun. A single fixed light source governs every surface. All highlights, shadows, and reflections agree with it. Nothing glows without a reason.
2. Light does the talking. State changes are light events: a verified reading casts a caustic; a live value wears a spectral fringe; chrome glints when data moves. Color is never applied; it is cast.
3. Gradient is the truth of color. No large flat fills. Red exists as a lit field: solar at the top of its arc, oxblood in shadow. Flat color is reserved for text and hairlines.
4. Function draws the form. Panels, rails, and dials exist because a workflow needs them. If a shape isn't load-bearing, it isn't there. Boxes earn their corners.
5. Heritage rides along. Engraved miniatures occupy dedicated margins: borders, medallions, frontispieces. Never scattered through controls. The instrument is modern; its margins remember.
6. Mercurial, disciplined. The interface reacts to data first and the hand second, and every reaction settles fast and means something. Alive is a property of physics here, not of easing curves.

### 4.0 Color: fields, not fills

| Name | Values | Role |
|---|---|---|
| Bone | #FFFFFF to #F5EFEA to #EFE3DE | the sunlit wall; default ground |
| Graphite | #141519 | text, hairlines, engraving ink |
| Solar Red | #FF4D2E to #DE2B1B to #8E1A0D (160deg) | command fields, live brew, the one loud voice |
| Ember | #8E1A0D to #5C0E06 | red in shadow; over-extraction; gravity |
| Chrome | material, not color; static fallback ramp #CDD0D4 / #F6F7F8 / #96999E / #E9EBED / #AEB1B6 | rails, frames, the chronometer |
| Dispersion | rgba stops of solar/amber/olive/cyan/violet at low alpha | exists only where light passes through liquid: fringes, caustic edges, live readings |
| Olive (specimen) | #6B7C3F | zone: ideal. Appears inside readings and fringes only |
| Amber (specimen) | #E8A33D | zone: under. Same restriction |
| Gold leaf | #C9A227 | illumination accents in miniatures and medallion rims only. Never UI chrome, never buttons |

Rules. Red is the only loud color; one red action per screen. Solar/vermillion means brand, live, latest; it is never a zone color (over-extraction is ember). Large fields are always gradients; flat color only on text and hairlines. Body-size red text uses ember for contrast; solar red on bone is display sizes only.

### 5.0 Light and material: laws of the engine

The renders and the product share one lighting rig. The engineering (a WebGL layer: environment-mapped chrome, transmissive liquid, screen-space caustics, pointer-aware speculars, tiered CSS fallback) serves these laws, never the reverse.

- L1. One sun, fixed at 10 o'clock high. Shadows fall long and crisp; on red they read ember, on bone they read warm graphite.
- L2. Chrome reflects the actual scene: a chrome rail near a red panel bends red across its surface. The cursor is a hand near the instrument; speculars shift subtly as it passes.
- L3. Liquid refracts. A measured sample projects a caustic: dark rim, burning core, dispersive fringe. Its color mixes from what the liquid knows (zone tints in the fringe).
- L4. Light events are earned. TDS entered: the reading decomposes through the prism. Zone verified: the caustic blooms once, then breathes. Personal best: a single gold glint. No idle shimmer.
- L5. Budget. Engine on the moments that matter (live brew, verdicts, chart); stills elsewhere. 60fps or it ships as a still. Reduced motion collapses every behavior to its resolved state.
- L6. The fringe. A narrow spectral edge may live on exactly one element per screen: the currently live value. It is the pulse of the instrument, not a style.

### 6.0 Typography

One engineered family, two cuts. IBM Plex Sans carries structure and prose at tight tracking; IBM Plex Mono carries every number, timestamp, and label. The IBM lineage is mission-control by birth. No serif, no script (standing rule), no third voice: the miniatures are the only ornament this system needs.

The typographic law:

- No letterspaced all-caps, anywhere. Tracked small caps are fashion, not engineering.
- Labels are lowercase mono, untracked, small ("ideal-zone hit rate, last 10").
- Hierarchy comes from size, weight, and clause numerals ("4.0 Color"), never from case or tracking.
- No em dashes in UI copy, headings, or documentation. Joins use colons and periods.
- The middot survives only between readings: 18.0g · 1:16.7 · 94.5°C.
- Numerals are tabular in any column.

### 7.0 Engraved miniatures: heritage as cargo

The brush-ink set is retired: 5.5px wobble strokes are warm and naive, and the reference world is hairline and exact. The hand survives in what is drawn and how it is composed, exactly as it did in the manuscripts. Never in stroke wobble.

Specification. Two-weight engraving on a 96 grid: 1.3px structure strokes, 0.55px detail strokes, machine-steady. High stroke density (a plate should reward zooming). One red act per plate (a drip, a lens center, an exit ray). Gold leaf only at compass points and medallion rims. Each plate framed by an engraved double ring and captioned in lowercase mono ("plate i · the pour").

Where they live: dedicated margins only. Masthead frontispiece, chart frame corners, milestone medallions, empty states, brew-method plates. Inside controls: no icons at all; type and light do that work.

Inventory: the Pour (V60), the Switch, the Press (Aeropress), the Hourglass (Chemex), the Eye (refractometer), Decomposition (prism), the Drop, the Kettle, the Bean Branch, the Vessel (the ride home), the Habitat.

### 8.0 Motion and reactivity

Reactions are physical and fast: speculars track the pointer continuously; state light blooms in 240ms or less and settles; the only persistent motion is the caustic's slow breath and the live timer. Hierarchy of aliveness: data events, then pointer, then time. Anything decorative that survives a "would an instrument do this?" test was probably load-bearing after all. `prefers-reduced-motion` resolves every behavior to its final state.

### 9.0 Voice

Flight-manual terse. Verbs first, no exclamation, no charm padding. Warmth is carried by light and miniatures, never by copy.

| Retired | Standard |
|---|---|
| Kettle's ready — start the bloom | Start brew |
| Brew's down — taste it → | Taste |
| Stamp it — done | Complete |
| Nothing poured yet — the kettle's cold. | No brews today |
| The measurements — whenever the sample's cool | Measurements |
| Correct this record | Edit record |

Errors state the fact and the remedy: "Combined weight is below mug weight. Check the scale."

### 10.0 Applied to The Counter's actual work

- Plan: the flight plan. Bone ground, chrome rails, prefilled recipe as a checklist; the reachability advisory is a caution light, not a paragraph.
- Brew: the burn. The one full Solar Red screen. Chrome chronometer ring, white mono digits, spacebar events strike glints along a chrome rail; long ember shadows.
- Taste: the optical bench. TDS enters the prism; extraction, zone, and score fan out as decomposed light; the verified verdict earns its caustic.
- The Log: the manifest. Dense mono rows, hairline rules, zone read as a small cast light, not a dot sticker.
- The Chart: the star map. Bone field, graphite cups, iso-ratio rays as chrome hairlines, the ideal box a standing caustic pool, the latest cup a red sphere on a chrome pick. Engraved ornaments in the frame corners.
- The Shelf: the specimen rack. Bags as labeled specimens with remaining-mass gauges.
- Milestones: service medals. Gold-rimmed engraved medallions.

### 11.0 Out of scope

Cockpit kitsch. Literal Star Wars marks. Script fonts (standing rule). Idle particle effects. Paper, kraft, stamps, and wobble. Letterspaced caps and em dashes.

## Part III. Hard constraints for any agent

Design law (breaking any of these is a defect, not a trade-off):

- No script or handwriting fonts, ever. Ornament comes only from engraved-miniature SVGs, in dedicated margins, never inside controls.
- No letterspaced all-caps, no em dashes in copy or docs, middot only between readings, tabular numerals in columns.
- One sun at 10 o'clock; one red action per screen; at most one fringe element per screen; no large flat fills; solar red is never a zone color; gold only in miniatures and medallion rims.
- Zone semantics: olive ideal, amber under, ember over. Strength Weak below 1.15, Ideal to 1.35, Strong above. Extraction Under below 18, Ideal to 22, Over above.
- No idle shimmer or particles. The engine runs only on hero moments (live brew, verdict, chart) and must hold 60fps or ship as a still. `prefers-reduced-motion` resolves everything to its final state.
- Voice is flight-manual terse: verbs first, no exclamation marks, errors state the fact and the remedy.

Engineering law:

- Never change brewing math in `app/src/lib/brewing/` or the thresholds above. `tests/unit/golden-migration.test.ts` enforces parity with the real dataset; any diff needs a written justification.
- Derived values are computed on read, never stored.
- Never touch `data/` from tests or scripts. E2E runs against a disposable sandbox DB in `app/.e2e-data/`.
- TDD: failing test first, then implementation. Unit tests in `app/tests/unit/` or beside the module, e2e in `app/tests/e2e/`. Gates: `npm test`, `npm run check`, `npm run test:e2e`, all green.
- Workflow: branch, commit, push, PR, wait for green CI, and ask Tomas before merging. Update README release notes (minor for features, patch for fixes) in the same PR.

## Part IV. Current state (verify against code)

- Implemented: tokens (`app/src/lib/styles/tokens.css`), Plex type, the eleven engraved plates plus medallions (`app/src/lib/components/engravings/`), the WebGL engine (`app/src/lib/light/`: chrome, caustic), flight-manual copy on every surface, ratio rays and reachability advisory, the control chart with hover card and variable panel.
- Routes: Today, `/brew` (plan), `/brew/[id]/live`, `/brew/[id]/taste`, `/log`, `/log/[id]`, `/chart`, `/shelf`, `/design`.
- Release history is in the README; v1.2.1 is the latest at time of writing.
- Known drift to fix when touched: the older CLAUDE.md text pointed at `components/ink/`; the real directory is `components/engravings/`.

## Part V. Improvement brief

### V.1 Objective

Make the app measurably more faithful to Part II and more pleasant to use mid-brew, without changing what it computes. Success is that a reviewer holding this brief and a screenshot of any screen cannot find a law being broken, and that logging a brew is no slower than today.

### V.2 Method

1. Run the app (`cd app && npm run dev:up`) and capture every route at laptop width and at a narrow width, with the engine on and with reduced motion on.
2. Audit each screen against the clauses in Part II and the constraints in Part III. Produce a findings table: screen, clause violated or opportunity, evidence (screenshot or selector), proposed fix, effort.
3. Rank by user impact on the two jobs first, brand fidelity second, polish third. Present the ranked list and a recommended first batch. Stop for approval.
4. Implement the approved batch test-first, one PR per coherent batch, each with before and after screenshots.

### V.3 Lenses to audit with

- Part II section 10: does each screen play its role (flight plan, the burn, optical bench, manifest, star map, specimen rack, service medals)?
- Mid-brew ergonomics: tap and key targets, glanceable timer, no precision needed with wet hands, nothing that blocks the space-bar event capture.
- Law compliance: fringe count per screen, red actions per screen, flat fills, tracked caps, em dashes, miniatures outside margins, copy that is not flight-manual terse.
- Performance and accessibility: engine frame rate and still fallback, contrast of body-size red (must use ember), focus states, reduced motion.
- Empty, loading, error and extreme-value states (no brews, one brew, missing TDS, very high or low extraction).

### V.4 Open questions for Tomas (do not decide alone)

- Any change to the information architecture or to the three-moment flow.
- Adding a new engraved plate or changing the miniature inventory.
- Any new dependency, and any change to the engine's performance tiers.
- Anything that alters stored data or CSV export layout.

### V.5 Out of scope

Everything in Part II section 11, plus the smart-scale feed, hosting, multi-user features, changes to scoring or thresholds, and revival of the retired roadmap.

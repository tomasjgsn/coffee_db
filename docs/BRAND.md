# HARD LIGHT

Brand guidelines for THE COUNTER. Working draft 01, July 2026.
Approved direction: engraved miniatures, IBM Plex system, engine on hero moments.

## 1.0 The idea

Light is the interface. The instrument reads coffee the way a prism reads the sun, and the app behaves like that instrument.

The Counter is not decorated software. It is an optical instrument with a screen: every reading behaves like light passing through a sample. Refracted, decomposed, resolved. Chrome is its chassis, liquid is its subject, one harsh sun is its condition. Nothing is illustrated to look scientific; the interface obeys physics, so it feels scientific.

Because instruments this good get carried, it carries heritage: engraved miniatures in its borders, the way navigators once illuminated their charts. The tension is the brand: machine precision, human margins. Regal red, worn daily.

Personality: precise, not cold. Regal, not ornate. Alive, not animated. Heritage as cargo.

## 2.0 The world

Galley of a Mars habitat, 07:00 local, year 2075. One skylight, no atmosphere to soften it: the sun lands hard, shadows are long and edged. The floor is command red, a gradient by nature: blazing where lit, oxblood where the chair's shadow falls. Chrome legs carry the room in miniature on their surface.

On the counter: 18 grams of a washed Ethiopian, nine months from a homeworld harvest. The astronaut doesn't brew to survive. They brew to remember. The instrument that helps them is exact about the coffee and reverent about where it came from.

Reference wall: hard-light still photography (the chrome chair on the red floor; the martini and its caustic), caustic and dispersion photography, Ottoman and Persian manuscript borders (My Name Is Red), NASA 1976 worm standards, Imperial command-deck restraint (a hint, never a costume), Braun instrument faces, Kubrick corridors, living spectral edges (the Siri fringe, taken as insight: light that responds, not decorates).

## 3.0 Principles

1. One sun. A single fixed light source governs every surface. All highlights, shadows, and reflections agree with it. Nothing glows without a reason.
2. Light does the talking. State changes are light events: a verified reading casts a caustic; a live value wears a spectral fringe; chrome glints when data moves. Color is never applied; it is cast.
3. Gradient is the truth of color. No large flat fills. Red exists as a lit field: solar at the top of its arc, oxblood in shadow. Flat color is reserved for text and hairlines.
4. Function draws the form. Panels, rails, and dials exist because a workflow needs them. If a shape isn't load-bearing, it isn't there. Boxes earn their corners.
5. Heritage rides along. Engraved miniatures occupy dedicated margins: borders, medallions, frontispieces. Never scattered through controls. The instrument is modern; its margins remember.
6. Mercurial, disciplined. The interface reacts to data first and the hand second, and every reaction settles fast and means something. Alive is a property of physics here, not of easing curves.

## 4.0 Color: fields, not fills

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

## 5.0 Light and material: laws of the engine

The renders and the product share one lighting rig. The engineering (a WebGL layer: environment-mapped chrome, transmissive liquid, screen-space caustics, pointer-aware speculars, tiered CSS fallback) serves these laws, never the reverse.

- L1. One sun, fixed at 10 o'clock high. Shadows fall long and crisp; on red they read ember, on bone they read warm graphite.
- L2. Chrome reflects the actual scene: a chrome rail near a red panel bends red across its surface. The cursor is a hand near the instrument; speculars shift subtly as it passes.
- L3. Liquid refracts. A measured sample projects a caustic: dark rim, burning core, dispersive fringe. Its color mixes from what the liquid knows (zone tints in the fringe).
- L4. Light events are earned. TDS entered: the reading decomposes through the prism. Zone verified: the caustic blooms once, then breathes. Personal best: a single gold glint. No idle shimmer.
- L5. Budget. Engine on the moments that matter (live brew, verdicts, chart); stills elsewhere. 60fps or it ships as a still. Reduced motion collapses every behavior to its resolved state.
- L6. The fringe. A narrow spectral edge may live on exactly one element per screen: the currently live value. It is the pulse of the instrument, not a style.

## 6.0 Typography

One engineered family, two cuts. IBM Plex Sans carries structure and prose at tight tracking; IBM Plex Mono carries every number, timestamp, and label. The IBM lineage is mission-control by birth. No serif, no script (standing rule), no third voice: the miniatures are the only ornament this system needs.

The typographic law:

- No letterspaced all-caps, anywhere. Tracked small caps are fashion, not engineering.
- Labels are lowercase mono, untracked, small ("ideal-zone hit rate, last 10").
- Hierarchy comes from size, weight, and clause numerals ("4.0 Color"), never from case or tracking.
- No em dashes in UI copy, headings, or documentation. Joins use colons and periods.
- The middot survives only between readings: 18.0g · 1:16.7 · 94.5°C.
- Numerals are tabular in any column.

## 7.0 Engraved miniatures: heritage as cargo

The brush-ink set is retired: 5.5px wobble strokes are warm and naive, and the reference world is hairline and exact. The hand survives in what is drawn and how it is composed, exactly as it did in the manuscripts. Never in stroke wobble.

Specification. Two-weight engraving on a 96 grid: 1.3px structure strokes, 0.55px detail strokes, machine-steady. High stroke density (a plate should reward zooming). One red act per plate (a drip, a lens center, an exit ray). Gold leaf only at compass points and medallion rims. Each plate framed by an engraved double ring and captioned in lowercase mono ("plate i · the pour").

Where they live: dedicated margins only. Masthead frontispiece, chart frame corners, milestone medallions, empty states, brew-method plates. Inside controls: no icons at all; type and light do that work.

Inventory: the Pour (V60), the Switch, the Press (Aeropress), the Hourglass (Chemex), the Eye (refractometer), Decomposition (prism), the Drop, the Kettle, the Bean Branch, the Vessel (the ride home), the Habitat.

## 8.0 Motion and reactivity

Reactions are physical and fast: speculars track the pointer continuously; state light blooms in 240ms or less and settles; the only persistent motion is the caustic's slow breath and the live timer. Hierarchy of aliveness: data events, then pointer, then time. Anything decorative that survives a "would an instrument do this?" test was probably load-bearing after all. `prefers-reduced-motion` resolves every behavior to its final state.

## 9.0 Voice

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

## 10.0 Applied to The Counter's actual work

- Plan: the flight plan. Bone ground, chrome rails, prefilled recipe as a checklist; the reachability advisory is a caution light, not a paragraph.
- Brew: the burn. The one full Solar Red screen. Chrome chronometer ring, white mono digits, spacebar events strike glints along a chrome rail; long ember shadows.
- Taste: the optical bench. TDS enters the prism; extraction, zone, and score fan out as decomposed light; the verified verdict earns its caustic.
- The Log: the manifest. Dense mono rows, hairline rules, zone read as a small cast light, not a dot sticker.
- The Chart: the star map. Bone field, graphite cups, iso-ratio rays as chrome hairlines, the ideal box a standing caustic pool, the latest cup a red sphere on a chrome pick. Engraved ornaments in the frame corners.
- The Shelf: the specimen rack. Bags as labeled specimens with remaining-mass gauges.
- Milestones: service medals. Gold-rimmed engraved medallions.

## 11.0 Out of scope

Cockpit kitsch. Literal Star Wars marks. Script fonts (standing rule). Idle particle effects. Paper, kraft, stamps, and wobble. Letterspaced caps and em dashes.

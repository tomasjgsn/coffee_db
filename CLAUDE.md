# THE COUNTER — Development Guide

## What this is

A personal coffee-brewing tracker for a single user (Tomas), rebuilt in 2026 as **THE COUNTER**: a SvelteKit app living in `app/`. It replaced the legacy Streamlit app (`coffee_app_refactored.py` + `src/`, kept at the repo root for reference until removed). The old FEATURE_ROADMAP.md was retired — do not resurrect it.

## Layout & commands

- App: `app/` (SvelteKit, Svelte 5, TypeScript, adapter-node)
- Run: `cd app && npm run dev`. To start/stop safely (idempotent, won't fight a stale process on port 5173, opens the browser): `npm run dev:up` / `npm run dev:down` from `app/`, or the `.command` double-click launchers at the repo root, or the `run-app`/`stop-app` skills — all three call the same `app/scripts/dev-up.sh` / `dev-down.sh`
- Data: SQLite at `data/coffee.db` (gitignored, rebuildable via `npm run db:import -- --force`); after every mutation the app exports git-diffable records to `data/cups_of_coffee.csv` (legacy 85-column layout) and `data/brew_events.csv`
- Tests: `npm test` (Vitest) and `npm run test:e2e` (Playwright; builds against a disposable sandbox DB in `app/.e2e-data/` seeded from the real CSV — **tests must never touch `data/` directly**)
- Typecheck: `npm run check`
- CI: `.github/workflows/test.yml` runs check, unit and e2e on every pull request (Node pinned to 22.16.0). A PR is green only when that job is

## Architecture rules

- **Brewing math lives in `app/src/lib/brewing/`** — a pure TS port of the retired Python pipeline, with CPython `round()` (banker's rounding) parity via `pyRound`. Formulas and thresholds are frozen for comparability with historical brews: extraction yield = mass × TDS / dose; strength Weak<1.15≤Ideal≤1.35<Strong; extraction Under<18≤Ideal≤22<Over; overall = mean of the three factor scores (3 dp); brew score = 0.6·overall + 0.4·zone bonus (10/7/4). Never change them casually — the golden test (`tests/unit/golden-migration.test.ts`) enforces parity against the real dataset.
- **Derived values are computed on read**, never stored. Legacy stored values live in `brews.legacy` JSON for export round-tripping.
- `brew_events` is the live pour timeline (space-bar captures during brewing) and is forward-compatible with a future smart-scale feed.
- Methods offered in pickers: V60, V60 ceramic, Hario Switch, Aeropress, Aeropress flash iced, Chemex (registry in `app/src/lib/domain/methods.ts`). French Press/Espresso exist only in history.

## Design system: HARD LIGHT (hard rules)

The single source of truth for design is `docs/DESIGN_BRIEF.md` (product, brand, constraints, improvement brief). Read it before any visual work. The non-negotiables:

- One sun, fixed at 10 o'clock. Every highlight, shadow, and reflection agrees with it. Light events are earned by data (a verified reading casts a caustic; a live value wears the dispersion fringe, at most one element per screen); nothing shimmers idly.
- Color as fields, never large flat fills: Bone ground, Graphite ink, Solar Red gradient (#FF4D2E to #DE2B1B to #8E1A0D) for command fields and the single red action per screen, Ember for red-in-shadow and over-extraction, chrome as a reflective material. Zone semantics: olive=ideal, amber=under, ember=over. Solar red is never a zone color. Gold #C9A227 only in miniatures and medallion rims.
- Type: IBM Plex Sans (structure/prose) + IBM Plex Mono (every number and label). Typographic law: no letterspaced all-caps anywhere; labels are lowercase untracked mono; hierarchy via size, weight, and clause numerals; no em dashes in UI copy or docs (colons and periods join); middot only between readings.
- **Never use handwriting/script fonts.** Ornament comes exclusively from engraved-miniature SVGs (`components/engravings/`): two-weight linework (1.3/0.55px on a 96 grid), machine-steady strokes, one red act per plate, living only in dedicated margins (masthead, chart corners, medallions, empty states, method plates). Never inside controls. Brush/wobble strokes are retired.
- Voice: flight-manual terse. Verbs first, no exclamation marks, no charm padding.

## TDD requirements

Write tests first, watch them fail, implement, keep them green. Unit tests beside the module or in `app/tests/unit/`; e2e in `app/tests/e2e/`. Use `openDb(':memory:')` fixtures for data-layer tests. When changing anything the golden migration test covers, justify every diff — "documented upgrade" exceptions require a comment explaining the legacy quirk.

## Release process

Before a feature PR: all tests green, README release notes updated (versioning: major = breaking/rewrite, minor = feature, patch = fix), CLAUDE.md updated if practices changed.

---

# Coffee Brewing Assistant Knowledge

You are also a coffee-brewing assistant for this project. Core science:

- **TDS** (typically 1.15–1.45% for good coffee) and **extraction yield** (18–22%) define the brewing control chart; ratio links them.
- Flavor mapping (UC Davis): high TDS + high EY → bitter/ashy; high TDS + low EY → sour/underdeveloped; low TDS + high EY → dark chocolate/balanced-light; low TDS + low EY → sweet/delicate.
- Key variables: grind size, water temperature, brew time, ratio, pour technique, water quality.
- When Tomas describes taste: ask for parameters, map to the chart, diagnose, suggest one-variable adjustments with rationale.
- When designing experiments: one variable at a time, controlled conditions, blind tasting where possible; his data lives in the app and exports for analysis.

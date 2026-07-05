# THE COUNTER ☕
Field notes on extraction — a personal coffee-brewing companion. Plan a brew from your last one, brew it against a live timer that captures every pour, taste and score it when the sample cools, and watch the dots walk into the ideal zone.

**Quick start:** `cd app && npm install && npm run db:import && npm run dev`

## 📋 Release Notes

### v1.2.1 - Local dev tooling (July 2026)

#### Technical Improvements
- **Start/stop scripts** - `app/scripts/dev-up.sh` / `dev-down.sh` idempotently start or stop the dev server, safely refusing to touch anything on port 5173 that isn't THE COUNTER's own Vite process, and open the browser on start
- Three equivalent entry points to the same scripts, so nothing's duplicated between them: `npm run dev:up` / `dev:down` from `app/`, double-clickable `start-counter.command` / `stop-counter.command` at the repo root, and `run-app` / `stop-app` Claude skills

---

### v1.2.0 - Ratio Rays & Reachability (July 2026)

#### New Features
- **Iso-ratio guide rays** - the chart now draws Lockhart's missing diagonals: a labeled 1:14…1:20 ray fan computed from the current slice's *measured* water retention, plus the hovered cup's own ray in clay. Grind/temp/time slide a cup along its ray; only the recipe changes rays
- **Reachability advisory** - when a filtered slice (or a recipe being planned) sits on a ray that cannot pass through the Ideal-Ideal box, the app says so and gives the reachable ratio window — on The Chart and on the Plan page before pouring
- **Immersion reading** - Hario Switch and Aeropress cups show the immersion-convention extraction (TDS × water ÷ dose, per Rao/Gagné) as a secondary figure on hover cards and detail pages; the frozen percolation formula still drives all zones and scores

#### Technical Improvements
- New pure `lib/brewing/rays.ts` (ray slopes, box window, measured LRR, immersion EY), written test-first; frozen formulas and golden test untouched
- 63 unit + 23 e2e tests passing

---

### v1.1.0 - The Chart, Instrumented (July 2026)

#### New Features
- **Hover & pin cards** - every dot on the control chart opens a mini bag-label on hover (bean, method, grind · temp · ratio · rest days, TDS→EY, zone, scores, tasting note); click pins it with a link to the cup, Escape closes
- **Compound filters** - bean, method, flavor profile, and range (all / last 25 / last 10); the chart, stats, panels, and trend all react to the same slice
- **Tint encoding** - dots tint pale-kraft→ink by grind, temp, ratio, or rest days, with a min→max ramp legend (palette stays the seven pigments)
- **"What moves the needle"** - four mini scatters of score vs grind / temp / ratio / rest days for the current slice, each with a gated dashed least-squares trend and ↗/↘/— direction (≥6 cups, |r| ≥ 0.25)
- **By flavor profile** - average score per profile as a dot plot with counts
- **Reactive stats** - hit rate (last 10 vs previous 10 within slice), average score, best cup link
- Bean rest-days for analysis uses roast date first (purchase-date fallback); the exported legacy field is unchanged

#### Technical Improvements
- New pure `analysis.ts` (least squares + gated trend direction), unit-tested first
- Chart payload enriched server-side; all slicing/statistics client-side over one load
- 56 unit + 19 e2e tests passing

---

### v1.0.0 - THE COUNTER: Full Redesign & Replatform (July 2026)

#### The headline
The Streamlit app has been replaced by **THE COUNTER**, a SvelteKit (Svelte 5) + SQLite app in `app/`, with a ground-up visual identity: coffee-bag label typography (Archivo caps + IBM Plex Mono + Fraunces), a seven-pigment paper/ink palette, brush-ink illustrations, and wine-bar-menu interactions. The legacy Streamlit app remains at the repo root for reference.

#### New Features
- **Brew companion** - brewing is three moments instead of one form:
  - *Plan*: recipe card prefilled from your last brew of that bean + method (falls back to the bean, then a house template), delta highlighting, editable pour plan
  - *Brew*: wall-clock live timer (survives reloads and sleep), keyboard event capture — space marks pours, s/t/v/p/d mark swirls, stirs, valve, press, drawdown — with per-pour scale readings; pour structure is finally data (`brew_events`)
  - *Taste*: hours later if needed (drafts wait on Today), TDS → live extraction yield and zone, half-step three-factor dots, notes
- **Aeropress flash iced** - Workshop-style hot press onto ice, with hot water + ice tracked separately and ratio/extraction on total water
- **The Log** - menu-style history with dotted leaders, zone dots, filters; bag-label detail pages with inline correction and delete
- **The Shelf** - bean bags as kraft labels with per-bag stats, remaining-grams dots, new-bag form, retire/restore
- **The Chart** - reskinned brewing control chart, ideal-zone hit rate (last 10 vs previous 10), score trend, per-bean dial-in journey
- **Today** - open drafts, one-tap pour-it-again, today's menu, milestone stamp collection (cup counts, first Ideal-Ideal per bag, personal bests, ideal streaks)

#### Technical Improvements
- SQLite (better-sqlite3 + Drizzle) at `data/coffee.db`; every mutation re-exports git-diffable `data/cups_of_coffee.csv` (legacy 85-column layout preserved) plus new `data/brew_events.csv`
- Pure TS brewing calc library with CPython banker's-rounding parity; derived fields computed on read
- Golden migration test: all 61 legacy brews import losslessly (10 bags deduped), every derived value recomputes to the stored Python-pipeline value, full 85-column round-trip
- Playwright e2e runs against a disposable sandbox database — tests never touch real data
- 48 unit tests + 14 e2e tests passing
- Devices pruned to what's actually brewed: V60 (+ceramic), Hario Switch, Aeropress (hot + flash iced), Chemex; French Press/Espresso remain viewable in history
- FEATURE_ROADMAP.md retired; CLAUDE.md rewritten for the new stack

---

### v0.6.0 - V60 Workflow Improvements (January 2025)

#### New Features
- **V60 Pour Timing Fields** - Added new V60-specific timing parameters:
  - `v60_time_between_pours_s`: Average time waited between pour phases
  - `v60_time_to_pour_s`: Average duration of each pour phase

#### Workflow Changes
- **Removed drawdown_time from V60** - V60 and V60 ceramic no longer track drawdown time separately (total brew time is sufficient)
- This change applies to both V60 and V60 ceramic devices (V60 ceramic inherits from V60)

#### Technical Improvements
- Added 4 new V60 tests for time fields
- Updated CSV schema with 2 new columns
- 228 tests passing

---

### v0.4.0 - Hario Switch Workflow & Time Input UX (January 2025)

#### UX Improvements
- **MM'SS" Time Format** - All time inputs now match standard timer format (e.g., 2'30")
  - Separate minute and second inputs for natural data entry
  - Display shows both formats: `2'30" (150s)`
  - Backend stores values in seconds (no database changes needed)

- **Improved Form Layout** - Fields reorganized to match brewing workflow:
  - Mug weight moved to Step 2 (measured before brewing)
  - Post-brew measurements (total time, final weight) at bottom of Step 3
  - Logical grouping: setup → parameters → results

- **Hario Switch Enhancements**:
  - Auto-calculated drawdown time: `total brew time - valve release time`
  - All times clearly marked as absolute (since start of brew)
  - Removed redundant inputs (mug weight now in Step 2)

#### Time Inputs Updated
All device time fields now use MM'SS" format:
- Total brew time, bloom time, drawdown time
- Valve release time, infusion duration (Hario Switch)
- Steep time, wait time, press duration (AeroPress)
- Initial steep, settling time (French Press)
- Shot time, pre-infusion (Espresso)

#### Technical Improvements
- Added time input validation tests (9 new tests)
- Removed obsolete integration tests
- 215 tests passing

---

### v0.3.0 - Modern Wizard UX & Dynamic Brew Inputs (January 2025)

#### New Features
- **Multi-Step Wizard for Add Cup** - Redesigned data entry with 4 focused steps:
  1. Bean Selection - Choose coffee and set brew date
  2. Equipment Setup - Grinder, brew device, and mug weight
  3. Brew Parameters - Water, dose, and device-specific settings
  4. Results & Score - TDS, flavor profile, and 3-factor scoring

- **Smart Defaults** - Quick start buttons to repeat last brew or use best-rated settings
- **Visual Progress Stepper** - Shows completed/active/pending steps with progress bar
- **Real-time Brew Ratio** - Calculates and displays ratio as you enter parameters

- **Device-Specific Brew Parameters** - Dynamic form fields based on brewing device:
  | Device | Parameters |
  |--------|------------|
  | Hario Switch | water_before_grinds, infusion_duration, stir, valve_release_time, drawdown_time (auto-calc) |
  | V60 | swirl_after_bloom, final_swirl, num_pours, time_between_pours, time_to_pour |
  | AeroPress | orientation, steep_time, press_duration |
  | French Press | initial_steep, break_crust, plunge_depth (Hoffmann method) |
  | Espresso | yield, shot_time, preinfusion, pressure |

#### Technical Improvements
- New `wizard_components.py` with reusable wizard UI patterns
- `render_time_input()` helper for MM'SS" format time entry
- Device configuration system in `brew_device_config.py` with inheritance support
- Config inheritance reduces code duplication (V60 ceramic, Hoffman top up inherit from V60)
- Hario Switch drawdown marked as calculated field in config
- 25 new CSV columns for device-specific data
- Fixed NaT date handling in bean selection
- 114 tests passing

---

## 🎯 Overview
This project aims to create a scientific approach to coffee brewing by correlating coffee bean characteristics, roast profiles, brewing parameters, and tasting results. The system includes interactive brewing control charts, ML-powered recommendations, and cross-platform data entry.
## ✨ Features
### Current Goals

📊 Scientific Data Tracking: TDS%, extraction percentages, brew ratios, and flavor profiles
📱 Modern UI: Clean, intuitive interface starting on desktop, expanding to mobile
🔬 Brewing Science: Interactive control charts based on latest coffee research
📈 Analytics: Track brewing improvements and identify optimal parameters
🖼️ Multi-media Support: Photos, notes, and structured data storage

### Future Roadmap

🤖 Machine Learning: Predictive models for optimal brewing parameters
📊 Advanced Analytics: Trend analysis and brewing pattern recognition
🌐 IoT Integration: Connect smart scales, grinders, and brewing equipment
👥 Community Features: Share recipes and compare brewing techniques
📚 Knowledge Base: Coffee science education and brewing guides

## 🏗️ Architecture
### Tech Stack

Frontend: React + TypeScript (Web), React Native + Expo (Mobile)
Backend: FastAPI + Python 3.11+
Database: PostgreSQL + TimescaleDB
Authentication: Supabase Auth
Storage: Supabase Storage
ML/Analytics: scikit-learn, pandas, numpy
Deployment: Docker + Railway/Render

### System Design
┌─────────────────┐    ┌─────────────────┐
│   Web App       │    │   Mobile App    │
│  (React + TS)   │    │ (React Native)  │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │ HTTPS/REST
          ┌──────────▼───────────┐
          │    FastAPI Backend   │
          │   (Python + ML)      │
          └──────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌───────▼────────┐   ┌───▼────┐
│ Auth  │    │  PostgreSQL +  │   │Storage │
│Service│    │  TimescaleDB   │   │Service │
└───────┘    └────────────────┘   └────────┘
## 📊 Data Model
### Core Entities

Coffee Beans: Origin, variety, processing method, purchase info
Roast Profiles: Roast level, temperature curves, color measurements
Brewing Sessions: Method, grind size, water temp, ratios, timing
Tasting Results: Ratings, flavor notes, sensory scores
Equipment: Grinders, brewers, scales with calibration data

### Scientific Calculations

Brew ratio calculations (coffee:water)
TDS to extraction percentage conversion
Control chart positioning and flavor mapping
Statistical analysis of brewing consistency

## 🚀 Getting Started

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd coffee_db

# Run setup script (creates virtual environment and installs dependencies)
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Run data processing
python scripts/data_processing/calculate_metrics.py
```

### Manual Setup
If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Prerequisites

- Python 3.11+
- Node.js 18+ (for future frontend development)
- Docker & Docker Compose (for future full-stack deployment)
- PostgreSQL 15+ (or use provided Docker setup when available)

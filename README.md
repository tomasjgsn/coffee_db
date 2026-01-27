# ☕ Coffee Database
A comprehensive coffee brewing database with scientific analysis capabilities, machine learning models, and modern UI for tracking and optimizing your coffee brewing journey.

## 📋 Release Notes

### v0.7.0 - Unified Brewing Score & Parameter Sensitivity Analysis (January 2025)

#### New Features
- **Unified Brewing Score** - A brew-ratio-aware objective scoring system (0-100):
  - Measures distance from the optimal point for your specific brew ratio
  - Uses normalized Euclidean distance with exponential decay
  - Shows 0.636 correlation with user ratings on existing data
  - Score = 100 at the optimal point for any brew ratio

- **Isometric Brew Ratio Lines** - Visual representation of constant brew ratios on the brewing control chart:
  - Common ratios displayed: 50, 55, 60, 65, 70, 75, 80 g/L
  - Optimal point markers for each ratio (diamond shapes)
  - Formula: TDS = (Brew_Ratio / 1000) × Extraction

- **Parameter Sensitivity Analysis** - New visualizations for brewing optimization:
  - Parameter sensitivity charts (grind size, temperature, brew ratio vs score)
  - Correlation heatmap between all brewing parameters
  - Cross-parameter heatmaps (e.g., Grind × Temperature → Score)
  - Score distribution histogram with mean indicator
  - Score trend over time with rolling average
  - Score distribution by bean type (box plots)

- **Score Contour Visualization** - 2D heatmap showing unified score across extraction-TDS space

#### Technical Improvements
- New `UnifiedBrewingScore` class with methods:
  - `get_optimal_point(brew_ratio)` - Calculate optimal (extraction, TDS) for any ratio
  - `calculate(extraction, tds, brew_ratio)` - Compute unified score
  - `get_distance()` - Normalized distance from optimal
  - `get_gradient()` - Gradient for sensitivity analysis
- Integrated into data processing pipeline (`process_entry_data.py`)
- 12 new visualization methods in `VisualizationService`
- 28 new tests for unified score calculations
- 256 tests passing

#### Brewing Science Notes
The unified score respects the physical constraint that TDS and extraction are linked by brew ratio. The optimal point varies along each isometric line:
- 55 g/L: Optimal at E=21.27%, T=1.17%
- 65 g/L: Optimal at E=19.33%, T=1.26% (near global ideal)
- 75 g/L: Optimal at E=17.54%, T=1.32%

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

# ☕ Coffee Database
A comprehensive coffee brewing database with scientific analysis capabilities, machine learning models, and modern UI for tracking and optimizing your coffee brewing journey.

## 📋 Release Notes

### v0.3.0 - Modern Wizard UX & Dynamic Brew Inputs (January 2025)

#### New Features
- **Multi-Step Wizard for Add Cup** - Redesigned data entry with 4 focused steps:
  1. Bean Selection - Choose coffee and set brew date
  2. Equipment Setup - Grinder and brew device selection
  3. Brew Parameters - Water, dose, and device-specific settings
  4. Results & Score - TDS, flavor profile, and 3-factor scoring

- **Smart Defaults** - Quick start buttons to repeat last brew or use best-rated settings
- **Visual Progress Stepper** - Shows completed/active/pending steps with progress bar
- **Real-time Brew Ratio** - Calculates and displays ratio as you enter parameters

- **Device-Specific Brew Parameters** - Dynamic form fields based on brewing device:
  | Device | Parameters |
  |--------|------------|
  | Hario Switch | water_before_grinds, infusion_duration, stir, drawdown_time |
  | V60 | swirl_after_bloom, final_swirl, num_pours, drawdown_time |
  | AeroPress | orientation, steep_time, press_duration |
  | French Press | initial_steep, break_crust, plunge_depth (Hoffmann method) |
  | Espresso | yield, shot_time, preinfusion, pressure |

#### Technical Improvements
- New `wizard_components.py` with reusable wizard UI patterns
- Device configuration system in `brew_device_config.py` with inheritance support
- Config inheritance reduces code duplication (V60 ceramic, Hoffman top up inherit from V60)
- 25 new CSV columns for device-specific data
- Fixed NaT date handling in bean selection
- 111 tests passing (40 device + 51 service + 20 wizard)

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

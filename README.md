# ☕ Coffee Database
A comprehensive coffee brewing database with scientific analysis capabilities, machine learning models, and modern UI for tracking and optimizing your coffee brewing journey.
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

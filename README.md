# JAL-VAANI

![JAL VAANI Banner](SCRIPTS/banner.png)

## 🌍 Groundwater Intelligence System — India (Ground-Water Level Predictions + Recharge Trends using AI)

End-to-End Automated Groundwater Forecasting & Recharge Prediction Platform
Real government sensor data + NASA climate data + Time-Series Modeling + Machine Learning
Fully automated with incremental updates and cloud deployment ready.



## 🚀 What Is This Project?

This project is a production-style groundwater analytics system that:

- Collects live groundwater level data from Government of India (WRIS)
- Collects daily rainfall + temperature from NASA POWER API
- Automatically updates datasets every few hours
- Cleans corrupted sensor resets and noise
- Forecasts future groundwater levels (6 months ahead)
- Predicts monthly groundwater recharge / depletion using ML
- Works across multiple Indian states and districts
- Runs fully automated on a Linux server using cron / GitHub Actions



## 🧠 System Architecture

WRIS API (Govt)  -->  Incremental Downloader  -->  WATER_DATA (District CSVs)  -->  Cleaning & Normalization  -->  Time-Series Forecast Engine (Seasonal Model)

RAIN_DATA (NASA Climate)  -->  Recharge Feature Builder  -->  Random Forest Model  -->  Monthly Recharge Prediction & Trend visualization



## 🔥 Core Capabilities :: 

✅ Live Data Pipeline
- Auto fetches new data every 6 hours
- Appends only new records
- Handles network failures & retries safely
- Production-grade incremental updates


✅ Groundwater Forecasting Engine
- Uses weekly seasonal pattern modeling
- Preserves:
  - Realistic seasonal trends
  - Long-term drift
  - Natural variability
- Prevents:
  - Unrealistic Data jumps
  - Sensor noise propagation
  - Physically unrealistic values
- Forecast horizon: 6 months


✅ Recharge Prediction AI (Random Forest)
Predicts monthly groundwater recharge/depletion using:
- Features Used:
  - Rainfall total & averages
  - Temperature averages
  - Soil type encoding
  - Urbanization indicator
  - Well depth
  - Aquifer type
  - Historical lag values
  - Trained on multi-state historical data.
- Outputs:
  - Recharge change (meters/month)
  - Feature importance ranking
  - Confidence interval estimation
  - Error statistics report


✅ Physics-Aware Constraints
- Unlike blind ML:
  - Maximum groundwater movement limits enforced
  - Hard upper/lower groundwater bounds
  - Seasonal continuity preserved
  - Realistic slope control

### This avoids “AI hallucinating impossible hydrology”.



## 📁 Project Folder Structure

ROOT
- WATER_DATA/
  - state/
    - district.csv

- RAIN_DATA/
  - state/
    - district_rain.csv

- OUTPUTS/
  - recharge_training.csv
  - recharge_stats.txt
  - soil_mapping.csv
  - urban_mapping.csv

- MODELS/
  - recharge_rf_model.pkl

- SCRIPTS/
  - gwl_data_scrapes.py
  - nasa_incremental_fetch.py
  - groundwater_forecast.py
  - recharge_dataset_builder.py
  - train_recharge_model.py

- requirements.txt
- README.md



## ⚙️ Installation

- 1️⃣ Clone Repository
  - git clone <your_repo_url>
  - cd JAL-VAANI

- 2️⃣ Install Dependencies
  - pip install -r requirements.txt



## ▶️ Running Pipeline

- 3️⃣ Update Government Groundwater Data
  - python SCRIPTS/gwl_data_scraper.py

- 4️⃣ Update NASA Climate Data
  - python SCRIPTS/rain_data_scraper.py

- 5️⃣ Run Following files to Clean & Prepare Data
  - sort_ascending_dt.py
  - add_seasonal_features.py
  - data_extractor.py

- 6️⃣ Run Following Files to Build Recharge Predictions Dataset
  - build_recharge_dataset.py
  - clean_recharge_dataset.py
  - add_lag_features.py
  - detect_recharge_outliers.py
  - fix_recharge_outliers.py

- 7️⃣ Train Recharge Prediction Model
  - python SCRIPTS/train_recharge_model.py
  - Model saved to:
  - MODELS/recharge_rf_model.pkl

- 8️⃣ Run Groundwater Forecast
  - python SCRIPTS/train_sarima_final.py
  - Generates district-wise future prediction plots.



## ⏱ Automation (Production Mode)

Designed to run using:
- Linux Cron Jobs / GitHub Actions Scheduler
- Every 6 hours:
  - Fetch new data
  - Update CSVs
  - Rebuild recharge dataset
  - Retrain model
  - Refresh predictions
### Zero manual work after deployment.



## 📊 Model Transparency

- Recharge model outputs:
  - RMSE
  - MAE
  - R² Score
  - Error %
  - 95% Confidence Interval
  - Feature importance ranking
- Saved automatically to:
  - OUTPUTS/recharge_stats.txt
### This makes the system auditable and explainable.



## 🛡 Data Safety Features
- Auto retry on network failure
- Partial download recovery
- Corrupt file detection
- Invalid datasets and Inactive sensors auto skip
- No overwrite accidents
- Append-only data strategy



## 🌐 Data Sources
- WRIS India — Groundwater Observation Wells (DWLRs)
- NASA POWER API — Rainfall & Temperature
- Public open datasets
- Used strictly for educational and research purposes.



## ⚠ Disclaimer
This system provides data-driven estimates, not official hydrological policy values.
Always validate with:
- Field surveys
- Government bulletins
- Hydrogeology experts
  


## 💎 Author
Built by: Bhavesh Gudlani
Focus: AI + Time Series + Infrastructure Automation + Environmental Intelligence

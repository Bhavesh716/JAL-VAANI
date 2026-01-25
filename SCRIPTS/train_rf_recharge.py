import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib


# ---------------- PATH CONFIG ----------------

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(ROOT_DIR, "OUTPUTS", "recharge_rf_ready_clean.csv")
STATS_FILE = os.path.join(ROOT_DIR, "OUTPUTS", "recharge_stats.txt")
MODEL_FILE = os.path.join(ROOT_DIR, "MODELS", "recharge_rf_model.pkl")


# ---------------- PHYSICAL LIMITS ----------------

MAX_PHYSICAL_DELTA = 6     # meters per month clamp
MIN_PHYSICAL_DELTA = -6


print("Loading dataset...")

df = pd.read_csv(DATA_FILE)


# ---------------- FEATURES ----------------

FEATURES = [
    "rain_total",
    "rain_avg",
    "temp_avg",
    "soil",
    "urban",
    "well_depth",
    "aquifer_type",
    "gw_delta_lag1",
    "gw_delta_lag2",
    "rain_total_lag1",
    "rain_total_lag2",
    "temp_avg_lag1"
]

TARGET = "gw_delta"


X = df[FEATURES]
y = df[TARGET]

print("Total samples:", len(df))


# ---------------- TRAIN TEST SPLIT ----------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    shuffle=True
)

print("Train samples:", len(X_train))
print("Test samples :", len(X_test))


# ---------------- RANDOM FOREST ----------------

print("Training Random Forest...")

rf = RandomForestRegressor(
    n_estimators=300,
    max_depth=15,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)


# ---------------- PREDICTION ----------------

pred_raw = rf.predict(X_test)


# ---------------- PHYSICAL LIMIT CLAMP ----------------

pred = np.clip(pred_raw, MIN_PHYSICAL_DELTA, MAX_PHYSICAL_DELTA)


# ---------------- METRICS ----------------

rmse = np.sqrt(mean_squared_error(y_test, pred))
mae = mean_absolute_error(y_test, pred)
r2 = r2_score(y_test, pred)

mean_abs_target = np.mean(np.abs(y_test))

error_percent = (mae / mean_abs_target) * 100
accuracy_percent = 100 - error_percent


# ---------------- CONFIDENCE INTERVAL ----------------

residuals = y_test.values - pred
std_resid = np.std(residuals)

ci_95 = 1.96 * std_resid


# ---------------- FEATURE IMPORTANCE ----------------

importances = rf.feature_importances_

feature_table = list(zip(FEATURES, importances))
feature_table = sorted(feature_table, key=lambda x: x[1], reverse=True)


# ---------------- SAVE MODEL ----------------

os.makedirs(os.path.join(ROOT_DIR, "MODELS"), exist_ok=True)

joblib.dump(rf, MODEL_FILE)

print("\nModel saved at:", MODEL_FILE)


# ---------------- SAVE STATS FILE ----------------

os.makedirs(os.path.join(ROOT_DIR, "OUTPUTS"), exist_ok=True)

with open(STATS_FILE, "w") as f:

    f.write("====== RECHARGE PREDICTION MODEL REPORT ======\n\n")

    f.write(f"Total Samples: {len(df)}\n")
    f.write(f"Training Samples: {len(X_train)}\n")
    f.write(f"Testing Samples: {len(X_test)}\n\n")

    f.write("---- Performance Metrics ----\n")
    f.write(f"RMSE (meters): {rmse:.3f}\n")
    f.write(f"MAE  (meters): {mae:.3f}\n")
    f.write(f"R2 Score     : {r2:.4f}\n")
    f.write(f"Mean Target Magnitude: {mean_abs_target:.3f}\n\n")

    f.write("---- Accuracy Estimation ----\n")
    f.write(f"Error %   : {error_percent:.2f} %\n")
    f.write(f"Accuracy %: {accuracy_percent:.2f} %\n\n")

    f.write("---- Confidence Interval ----\n")
    f.write(f"95% CI Range: ±{ci_95:.3f} meters\n\n")

    f.write("---- Physical Constraints ----\n")
    f.write(f"Prediction Clamp Range: {MIN_PHYSICAL_DELTA} to {MAX_PHYSICAL_DELTA} meters/month\n\n")

    f.write("---- Feature Importance ----\n")

    for name, val in feature_table:
        f.write(f"{name:20s} : {val:.4f}\n")


print("\n====== MODEL PERFORMANCE ======")
print("RMSE:", round(rmse, 3))
print("MAE :", round(mae, 3))
print("Accuracy %:", round(accuracy_percent, 2))
print("95% CI ±", round(ci_95, 3))

print("\nStats saved to:", STATS_FILE)

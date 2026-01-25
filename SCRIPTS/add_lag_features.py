import pandas as pd
import os

ROOT = ".."

OUTPUT_DIR = os.path.join(ROOT, "OUTPUTS")

INPUT_FILE  = os.path.join(OUTPUT_DIR, "recharge_training_clean.csv")
OUTPUT_FILE  = os.path.join(OUTPUT_DIR, "recharge_rf_ready.csv")

print("Loading dataset...")

df = pd.read_csv(INPUT_FILE)

# ---------------- SORT PROPERLY ----------------

df = df.sort_values(
    by=["district", "year", "month"]
).reset_index(drop=True)

print("Adding lag features...")

# ---------------- LAG FEATURES ----------------

df["gw_delta_lag1"] = df.groupby("district")["gw_delta"].shift(1)
df["gw_delta_lag2"] = df.groupby("district")["gw_delta"].shift(2)

df["rain_total_lag1"] = df.groupby("district")["rain_total"].shift(1)
df["rain_total_lag2"] = df.groupby("district")["rain_total"].shift(2)

df["temp_avg_lag1"] = df.groupby("district")["temp_avg"].shift(1)

# ---------------- DROP BROKEN ROWS ----------------

before = len(df)

df = df.dropna()

after = len(df)

print("Rows before:", before)
print("Rows after :", after)
print("Dropped    :", before - after)

# ---------------- SAVE ----------------

df.to_csv(OUTPUT_FILE, index=False)

print("DONE ✅")
print("Saved as:", OUTPUT_FILE)

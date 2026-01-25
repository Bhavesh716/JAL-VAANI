import pandas as pd
import os

# ---------------- PATH CONFIG ----------------

ROOT = ".."

OUTPUT_DIR = os.path.join(ROOT, "OUTPUTS")

INPUT_FILE = os.path.join(OUTPUT_DIR, "recharge_training.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "recharge_training_clean.csv")

df = pd.read_csv(INPUT_FILE)

print("Initial rows:", len(df))

# Drop rows with missing target
df = df.dropna(subset=["gw_delta"])

# Fill remaining missing numeric values
df["rain_total"] = df["rain_total"].fillna(0)
df["rain_avg"] = df["rain_avg"].fillna(0)
df["temp_avg"] = df["temp_avg"].fillna(df["temp_avg"].median())

df["well_depth"] = df["well_depth"].fillna(df["well_depth"].median())
df["aquifer_type"] = df["aquifer_type"].fillna(1)

print("Final rows:", len(df))

df.to_csv(OUTPUT_FILE, index=False)

print("CLEAN FILE SAVED: recharge_training_clean.csv")

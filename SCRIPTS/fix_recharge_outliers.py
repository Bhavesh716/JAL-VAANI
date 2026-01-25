import pandas as pd
import numpy as np
import os

# ---------------- PATH CONFIG ----------------

ROOT = ".."
OUTPUT_DIR = os.path.join(ROOT, "OUTPUTS")

FILE = os.path.join(OUTPUT_DIR, "recharge_rf_ready.csv")
OUT_FILE = os.path.join(OUTPUT_DIR, "recharge_rf_ready_clean.csv")

MAX_DELTA = 8
MIN_DELTA = -8

print("Loading recharge dataset...")

df = pd.read_csv(FILE)

print("\nBefore cleaning:")
print(df["gw_delta"].describe())

# ---------------- FLAG IMPOSSIBLE VALUES ----------------

mask = (df["gw_delta"] > MAX_DELTA) | (df["gw_delta"] < MIN_DELTA)

print("\nOutliers detected:", mask.sum())

df.loc[mask, "gw_delta"] = np.nan

# ---------------- DISTRICT-WISE INTERPOLATION ----------------

df["gw_delta"] = (
    df.groupby("district")["gw_delta"]
      .transform(lambda x: x.interpolate(limit_direction="both"))
)

# ---------------- FINAL SAFETY FILL ----------------

df["gw_delta"] = df["gw_delta"].fillna(0)

print("\nAfter cleaning:")
print(df["gw_delta"].describe())

# ---------------- SAVE ----------------

df.to_csv(OUT_FILE, index=False)

print("\nSaved cleaned dataset:", OUT_FILE)

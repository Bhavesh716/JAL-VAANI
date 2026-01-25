import pandas as pd
import os
# ---------------- PATH CONFIG ----------------

ROOT = ".."
OUTPUT_DIR = os.path.join(ROOT, "OUTPUTS")
INPUT_FILE = os.path.join(OUTPUT_DIR, "recharge_rf_ready.csv")

df = pd.read_csv(INPUT_FILE)

print(df["gw_delta"].describe())

print("\nTop 10 extreme values:")
print(df["gw_delta"].sort_values(ascending=False).head(10))

print("\nBottom 10 extreme values:")
print(df["gw_delta"].sort_values().head(10))

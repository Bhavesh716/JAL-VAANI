import os
import pandas as pd
import numpy as np

# ---------------- PATH CONFIG ----------------

ROOT = ".."
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")

print("\nADDING SEASON FEATURES (ROBUST MODE)\n")

for state in os.listdir(WATER_ROOT):

    if not os.path.isdir(state):
        continue

    print("Processing state:", state)

    for file in os.listdir(state):

        if not file.endswith(".csv"):
            continue

        if "_rain" in file:
            continue

        path = os.path.join(state, file)

        try:
            df = pd.read_csv(path)

            # Robust mixed-format parsing
            df["datetime"] = pd.to_datetime(
                df["datetime"],
                format="mixed",
                errors="coerce"
            )

            before = len(df)

            df = df.dropna(subset=["datetime"])

            after = len(df)

            if after == 0:
                print("SKIPPED (no valid datetime):", file)
                continue

            df["month"] = df["datetime"].dt.month

            df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
            df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)

            df.to_csv(path, index=False)

            print(f"UPDATED: {file}  | rows kept: {after}/{before}")

        except Exception as e:
            print("FAILED:", file, e)

print("\nDONE — ALL FILES NORMALIZED\n")

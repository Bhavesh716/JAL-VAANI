import os
import pandas as pd
from datetime import datetime, timedelta

# ---------------- PATH CONFIG ----------------

ROOT = ".."

WATER_ROOT = os.path.join(ROOT, "WATER_DATA")
RAIN_ROOT  = os.path.join(ROOT, "RAIN_DATA")
OUTPUT_DIR = os.path.join(ROOT, "OUTPUTS")

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "recharge_training.csv")

SOIL_FILE  = os.path.join(OUTPUT_DIR, "soil_mapping.csv")
URBAN_FILE = os.path.join(OUTPUT_DIR, "urban_mapping.csv")

# ---------------- LOAD STATIC MAPS ----------------

soil_df = pd.read_csv(SOIL_FILE)
urban_df = pd.read_csv(URBAN_FILE)

soil_map = dict(zip(soil_df["district"], soil_df["soil_type"]))
urban_map = dict(zip(urban_df["district"], urban_df["urban"]))

soil_encode = {
    "alluvial": 1,
    "black": 2,
    "red": 3,
    "sandy": 4,
    "laterite": 5
}

aquifer_encode = {
    "Unconfined": 1,
    "Semi-Confined": 2,
    "Confined": 3
}

# ---------------- RAIN CSV LOADER ----------------

def load_rain_csv(path):

    rows = []
    data_start = False

    with open(path, "r") as f:
        for line in f:

            if line.startswith("YEAR"):
                data_start = True
                continue

            if not data_start:
                continue

            parts = line.strip().split(",")

            if len(parts) < 4:
                continue

            try:
                year = int(parts[0])
                doy  = int(parts[1])
                rain = float(parts[2])
                temp = float(parts[3])
            except:
                continue

            date = datetime(year, 1, 1) + timedelta(days=doy - 1)

            rows.append([date, rain, temp])

    df = pd.DataFrame(rows, columns=["date", "rain", "temp"])
    return df


# ---------------- MAIN PIPELINE ----------------

all_rows = []

print("\nBUILDING RECHARGE TRAINING DATASET\n")


for state in os.listdir(WATER_ROOT):

    state_path = os.path.join(WATER_ROOT, state)

    if not os.path.isdir(state_path):
        continue

    print("State:", state)

    for file in os.listdir(state_path):

        if not file.endswith(".csv"):
            continue

        if "_rain" in file.lower():
            continue

        district = file.replace(".csv", "").replace("_", " ")

        gw_path = os.path.join(state_path, file)
        rain_path = os.path.join(RAIN_ROOT, state, file.replace(".csv", "_rain.csv"))

        if not os.path.exists(rain_path):
            print("Missing rain file:", district)
            continue


        # ---------- LOAD GW DATA ----------

        gw_df = pd.read_csv(gw_path)

        gw_df["datetime"] = pd.to_datetime(gw_df["datetime"], errors="coerce")
        gw_df = gw_df.dropna(subset=["datetime"])

        if len(gw_df) < 10:
            print("Skipping small GW file:", district)
            continue

        gw_df["year"] = gw_df["datetime"].dt.year
        gw_df["month"] = gw_df["datetime"].dt.month

        gw_month = (
            gw_df
            .groupby(["year", "month"])["water_level"]
            .mean()
            .reset_index()
        )


        # ---------- LOAD RAIN DATA ----------

        rain_df = load_rain_csv(rain_path)

        if len(rain_df) == 0:
            print("Empty rain file:", district)
            continue

        rain_df["year"] = rain_df["date"].dt.year
        rain_df["month"] = rain_df["date"].dt.month

        rain_month = rain_df.groupby(["year", "month"]).agg(
            rain_total=("rain", "sum"),
            rain_avg=("rain", "mean"),
            temp_avg=("temp", "mean")
        ).reset_index()


        # ---------- MERGE ----------

        merged = pd.merge(
            gw_month,
            rain_month,
            on=["year", "month"],
            how="inner"
        )

        merged = merged.sort_values(["year", "month"])


        # ---------- RECHARGE PROXY ----------

        merged["gw_prev"] = merged["water_level"].shift(1)
        merged["gw_delta"] = merged["water_level"] - merged["gw_prev"]

        merged = merged.dropna(subset=["gw_delta"])


        # ---------- STATIC FEATURES ----------

        soil = soil_map.get(district, "black")
        soil_code = soil_encode.get(soil, 2)

        urban = urban_map.get(district, 0)

        aquifer_raw = gw_df["aquiferType"].mode()
        aquifer_code = aquifer_encode.get(
            aquifer_raw.iloc[0], 1
        ) if len(aquifer_raw) else 1

        depth_val = gw_df["wellDepth"].median()


        # ---------- APPEND FINAL ROWS ----------

        for _, r in merged.iterrows():

            all_rows.append([
                district,
                state,
                int(r["year"]),
                int(r["month"]),
                r["rain_total"],
                r["rain_avg"],
                r["temp_avg"],
                soil_code,
                urban,
                depth_val,
                aquifer_code,
                r["gw_delta"]
            ])


# ---------------- SAVE FINAL CSV ----------------

final_df = pd.DataFrame(all_rows, columns=[
    "district", "state", "year", "month",
    "rain_total", "rain_avg", "temp_avg",
    "soil", "urban", "well_depth", "aquifer_type",
    "gw_delta"
])

os.makedirs(OUTPUT_DIR, exist_ok=True)

final_df.to_csv(OUTPUT_FILE, index=False)

print("\nRECHARGE TRAINING DATASET SAVED:", OUTPUT_FILE)

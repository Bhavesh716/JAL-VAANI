import os
import pandas as pd
import numpy as np
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATE_COL = "datetime"
VALUE_COL = "water_level"

FUTURE_WEEKS = 26
MIN_ROWS_REQUIRED = 60

NOISE_SCALE = 0.5
MAX_WEEKLY_CHANGE = 1.5
MAX_LEVEL = 0
MIN_LEVEL = -150

OUTPUTS = os.path.join(ROOT, "OUTPUTS")
RAIN_ROOT = os.path.join(ROOT, "RAIN_DATA")
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")


# ---------------- UTIL ----------------

def normalize(x):
    return x.lower().replace(" ", "").replace("-", "").replace("_", "").strip()


# ---------------- RAIN + TEMP ----------------

def get_latest_rain_temp(state, district):

    rain_file = os.path.join(
        RAIN_ROOT, state, district.replace(" ", "_") + "_rain.csv"
    )

    if not os.path.exists(rain_file):
        return None, None

    with open(rain_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data_start = 0
    for i, l in enumerate(lines):
        if l.startswith("YEAR"):
            data_start = i + 1
            break

    rows = [x.strip().split(",") for x in lines[data_start:] if len(x.split(",")) >= 4]

    for row in reversed(rows):
        try:
            rain = float(row[2])
            temp = float(row[3])
            return rain, temp
        except:
            continue

    return None, None


# ---------------- SOIL ----------------

def get_soil(district):

    path = os.path.join(OUTPUTS, "soil_mapping.csv")

    if not os.path.exists(path):
        return "black"

    df = pd.read_csv(path)

    for _, r in df.iterrows():
        if normalize(r["district"]) == normalize(district):
            return r["soil_type"].lower()

    return "black"


# ---------------- URBAN ----------------

def get_urban(district):

    path = os.path.join(OUTPUTS, "urban_mapping.csv")

    if not os.path.exists(path):
        return 0

    df = pd.read_csv(path)

    for _, r in df.iterrows():
        if normalize(r["district"]) == normalize(district):
            return int(r["urban"])

    return 0


# ---------------- MAIN PREDICTION ----------------

def get_prediction(state, district, target_date):

    file_path = os.path.join(
        WATER_ROOT, state, district.replace(" ", "_") + ".csv"
    )

    if not os.path.exists(file_path):
        return {"status": "error", "reason": "water file missing"}

    df = pd.read_csv(file_path)

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, VALUE_COL])
    df = df.sort_values(DATE_COL)

    if len(df) < MIN_ROWS_REQUIRED:
        return {"status": "error", "reason": "insufficient rows"}

    base = df.set_index(DATE_COL)[VALUE_COL]

    weekly = base.resample("W").mean().dropna()

    if len(weekly) < 52:
        return {"status": "error", "reason": "weekly data insufficient"}

    weekly_values = weekly.values
    weekly_time = weekly.index

    # -------- FORECAST ENGINE --------

    last_year = weekly_values[-52:]

    seasonal_delta = np.diff(last_year)
    seasonal_delta = np.clip(
        seasonal_delta,
        -MAX_WEEKLY_CHANGE,
        MAX_WEEKLY_CHANGE
    )

    noise_std = np.std(np.diff(weekly_values))
    noise = np.random.normal(0, noise_std * NOISE_SCALE, FUTURE_WEEKS)

    forecast = []
    current = weekly_values[-1]

    for i in range(FUTURE_WEEKS):

        step = seasonal_delta[i % len(seasonal_delta)]
        val = current + step + noise[i]

        delta = val - current

        if delta > MAX_WEEKLY_CHANGE:
            val = current + MAX_WEEKLY_CHANGE

        if delta < -MAX_WEEKLY_CHANGE:
            val = current - MAX_WEEKLY_CHANGE

        if val > MAX_LEVEL:
            val = MAX_LEVEL

        if val < MIN_LEVEL:
            val = MIN_LEVEL

        forecast.append(val)
        current = val

    forecast = np.array(forecast)

    forecast = forecast + (weekly_values[-1] - forecast[0])

    future_dates = pd.date_range(
        start=weekly_time[-1],
        periods=FUTURE_WEEKS,
        freq="W"
    )

    # -------- TARGET PICK --------

    target_date = datetime.strptime(target_date, "%d/%m/%Y")

    pred_value = None

    for d, v in zip(future_dates, forecast):
        if d.date() >= target_date.date():
            pred_value = round(float(v), 3)
            break

    if pred_value is None:
        return {"status": "error", "reason": "target out of range"}

    # -------- AUX FEATURES --------

    rain, temp = get_latest_rain_temp(state, district)

    if rain is None or temp is None:
        rain = 0
        temp = 25

    evapo = round(temp * 0.5, 2)

    soil = get_soil(district)
    urban = get_urban(district)

    month = target_date.month

    sin_month = np.sin(2 * np.pi * month / 12)
    cos_month = np.cos(2 * np.pi * month / 12)

    soil_map = {
        "black": 0,
        "red": 1,
        "laterite": 2,
        "alluvial": 3,
        "sandy": 4
    }

    soil_val = soil_map.get(soil, 0)

    # -------- HISTORY + PRED CHART DATA --------

    history = []
    prediction = []

    for t, v in zip(weekly_time, weekly_values):
        history.append({
            "x": t.strftime("%Y-%m-%d"),
            "y": round(float(v), 3)
        })

    for t, v in zip(future_dates, forecast):
        prediction.append({
            "x": t.strftime("%Y-%m-%d"),
            "y": round(float(v), 3)
        })

    # -------- FINAL OUTPUT --------

    return {

        "status": "ok",

        "predicted_wl": pred_value,

        "features": [
            pred_value,
            rain,
            evapo,
            soil_val,
            urban,
            month,
            sin_month,
            cos_month,
            0, 0, 0, 0   # padding for 12-feature RF model
        ],

        "history": history,
        "prediction": prediction
    }

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATE_COL = "datetime"
VALUE_COL = "water_level"

FUTURE_WEEKS = 26
MIN_ROWS_REQUIRED = 60

NOISE_SCALE = 0.5
MAX_WEEKLY_CHANGE = 1.5
MAX_LEVEL = 0
MIN_LEVEL = -150


def get_prediction(state, district, target_date):

    file_path = os.path.join(
        ROOT, "WATER_DATA", state, district.replace(" ", "_") + ".csv"
    )

    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, VALUE_COL])
    df = df.sort_values(DATE_COL)

    if len(df) < MIN_ROWS_REQUIRED:
        return None

    base = df.set_index(DATE_COL)[VALUE_COL]

    weekly = base.resample("W").mean().dropna()

    if len(weekly) < 52:
        return None

    weekly_values = weekly.values
    weekly_time = weekly.index

    # -------- SARIMA STYLE FORECAST --------

    last_year = weekly_values[-52:]

    seasonal_delta = np.diff(last_year)
    seasonal_delta = np.clip(seasonal_delta,
                             -MAX_WEEKLY_CHANGE,
                              MAX_WEEKLY_CHANGE)

    noise_std = np.std(np.diff(weekly_values))

    noise = np.random.normal(
        0,
        noise_std * NOISE_SCALE,
        FUTURE_WEEKS
    )

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

    shift = weekly_values[-1] - forecast[0]
    forecast = forecast + shift

    future_dates = pd.date_range(
        start=weekly_time[-1],
        periods=FUTURE_WEEKS,
        freq="W"
    )

    # ---------- TARGET DATE PICK ----------

    target_date = datetime.strptime(target_date, "%d/%m/%Y")

    pred_value = None

    for d, v in zip(future_dates, forecast):
        if d.date() >= target_date.date():
            pred_value = round(float(v), 2)
            break

    # ---------- CHART PACKETS ----------

    history = []
    prediction = []

    for t, v in zip(weekly_time, weekly_values):
        history.append({
            "x": t.strftime("%Y-%m-%d"),
            "y": round(float(v), 2)
        })

    for t, v in zip(future_dates, forecast):
        prediction.append({
            "x": t.strftime("%Y-%m-%d"),
            "y": round(float(v), 2)
        })

    return {
        "predicted_wl": pred_value,
        "history": history,
        "prediction": prediction
    }

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

WATER_ROOT = os.path.join(ROOT, "WATER_DATA")


def get_prediction(state, district, target_date):

    FILE_PATH = os.path.join(
        WATER_ROOT,
        state,
        district.replace(" ", "_") + ".csv"
    )

    if not os.path.exists(FILE_PATH):
        return {"status": "error", "reason": "file missing"}

    df = pd.read_csv(FILE_PATH)

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, VALUE_COL])
    df = df.sort_values(DATE_COL)

    if len(df) < MIN_ROWS_REQUIRED:
        return {"status": "error", "reason": "insufficient rows"}


    temp = pd.DataFrame({
        "date": df[DATE_COL],
        "val": df[VALUE_COL]
    })

    temp = temp.set_index("date")

    weekly = temp.resample("W").mean().dropna()

    if len(weekly) < 52:
        return {"status": "error", "reason": "weekly insufficient"}

    weekly_values = weekly["val"].values
    weekly_time = weekly.index


    # ---------------- SARIMA CORE ----------------

    last_year = weekly_values[-52:]

    seasonal_delta = np.diff(last_year)

    seasonal_delta = np.clip(
        seasonal_delta,
        -MAX_WEEKLY_CHANGE,
        MAX_WEEKLY_CHANGE
    )

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


    # ---------------- predicted_wl ----------------

    predicted_wl = round(float(forecast[-1]), 3)


    # ---------------- SIX MONTH RAW ----------------

    six_hist = []
    six_pred = []

    for t, v in zip(weekly_time, weekly_values):
        six_hist.append({
            "x": t.strftime("%Y-%m-%d"),
            "y": round(float(v), 3)
        })

    for t, v in zip(future_dates, forecast):
        six_pred.append({
            "x": t.strftime("%Y-%m-%d"),
            "y": round(float(v), 3)
        })


    # ---------------- WEEKLY (SAME AS SARIMA BASE) ----------------

    weekly_hist = six_hist.copy()
    weekly_pred = six_pred.copy()


    # ---------------- MONTHLY AGG ----------------

    hist_df = pd.DataFrame({
        "date": weekly_time,
        "val": weekly_values
    }).set_index("date")

    pred_df = pd.DataFrame({
        "date": future_dates,
        "val": forecast
    }).set_index("date")


    monthly_hist_df = hist_df.resample("ME").mean().dropna()
    monthly_pred_df = pred_df.resample("ME").mean().dropna()


    monthly_hist = []
    monthly_pred = []

    for t, v in zip(monthly_hist_df.index, monthly_hist_df["val"].values):
        monthly_hist.append({
            "x": t.strftime("%Y-%m"),
            "y": round(float(v), 3)
        })

    for t, v in zip(monthly_pred_df.index, monthly_pred_df["val"].values):
        monthly_pred.append({
            "x": t.strftime("%Y-%m"),
            "y": round(float(v), 3)
        })


    # ---------------- FEATURES (ONLY ADDITION) ----------------

    target_date = datetime.strptime(target_date, "%d/%m/%Y")

    month = target_date.month

    sin_month = np.sin(2 * np.pi * month / 12)
    cos_month = np.cos(2 * np.pi * month / 12)


    features = [
        predicted_wl,
        0,      # rain placeholder
        0,      # evapo placeholder
        0,      # soil placeholder
        0,      # urban placeholder
        month,
        sin_month,
        cos_month,
        0, 0, 0, 0   # padding (12 total)
    ]


    # ---------------- FINAL OUTPUT ----------------

    return {

        "status": "ok",

        "predicted_wl": predicted_wl,

        "features": features,

        "weekly": {
            "history": weekly_hist,
            "prediction": weekly_pred
        },

        "monthly": {
            "history": monthly_hist,
            "prediction": monthly_pred
        },

        "six_month": {
            "history": six_hist,
            "prediction": six_pred
        }
    }

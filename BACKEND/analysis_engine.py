import pandas as pd
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")

DATE_COL = "datetime"
VALUE_COL = "water_level"

MAX_WEEKLY_CHANGE = 1.5
MAX_LEVEL = 0
MIN_LEVEL = -150


def smooth_series(series):

    values = series.values

    smoothed = [values[0]]

    for i in range(1, len(values)):

        prev = smoothed[-1]
        cur = values[i]

        delta = cur - prev

        if delta > MAX_WEEKLY_CHANGE:
            cur = prev + MAX_WEEKLY_CHANGE

        if delta < -MAX_WEEKLY_CHANGE:
            cur = prev - MAX_WEEKLY_CHANGE

        cur = min(cur, MAX_LEVEL)
        cur = max(cur, MIN_LEVEL)

        smoothed.append(cur)

    return np.array(smoothed)


def get_analysis(state, district):

    path = os.path.join(
        WATER_ROOT,
        state,
        district.replace(" ", "_") + ".csv"
    )

    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, VALUE_COL])
    df = df.sort_values(DATE_COL)

    if len(df) < 30:
        return None

    base = df.set_index(DATE_COL)[VALUE_COL]

    # -------- WEEKLY --------
    weekly = base.resample("W").mean().dropna()

    weekly_vals = smooth_series(weekly)

    weekly_data = [
        {
            "x": str(k.strftime("%Y-W%U")),
            "y": round(float(v), 2)
        }
        for k, v in zip(weekly.index, weekly_vals)
    ]

    # -------- MONTHLY --------
    monthly = base.resample("ME").mean().dropna()

    monthly_vals = smooth_series(monthly)

    monthly_data = [
        {
            "x": k.strftime("%Y-%m"),
            "y": round(float(v), 2)
        }
        for k, v in zip(monthly.index, monthly_vals)
    ]

    # -------- SEASONAL (Quarter) --------
    seasonal = base.resample("QE").mean().dropna()

    seasonal_vals = smooth_series(seasonal)

    seasonal_data = [
        {
            "x": f"{k.year}-Q{((k.month-1)//3)+1}",
            "y": round(float(v), 2)
        }
        for k, v in zip(seasonal.index, seasonal_vals)
    ]

    return {
        "weekly": weekly_data,
        "monthly": monthly_data,
        "seasonal": seasonal_data
    }

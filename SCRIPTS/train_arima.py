import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

ROOT_FOLDER = ".."

DATE_COL = "datetime"
VALUE_COL = "water_level"

FUTURE_DAYS = 180
MIN_ROWS_REQUIRED = 40

state_folders = ["maharashtra","gujarat"]


for STATE in state_folders:

    FOLDER = os.path.join(ROOT_FOLDER, "WATER_DATA", STATE)

    if not os.path.exists(FOLDER):
        continue

    for file in os.listdir(FOLDER):

        if not file.endswith(".csv"):
            continue

        FILE_PATH = os.path.join(FOLDER, file)

        try:

            df = pd.read_csv(FILE_PATH)

            df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
            df = df.dropna(subset=[DATE_COL, VALUE_COL])
            df = df.sort_values(DATE_COL)

            if len(df) < MIN_ROWS_REQUIRED:
                continue

            time = df[DATE_COL]
            series = df[VALUE_COL].astype(float).values

            model = ARIMA(series, order=(1,1,1), trend="t")
            model_fit = model.fit()

            base_forecast = model_fit.forecast(steps=FUTURE_DAYS)

            residuals = model_fit.resid
            noise = np.random.choice(residuals, size=FUTURE_DAYS, replace=True)
            noise = noise * 0.6

            final_forecast = base_forecast + noise

            future_dates = pd.date_range(
                start=time.iloc[-1] + pd.Timedelta(days=1),
                periods=FUTURE_DAYS
            )

            plt.figure(figsize=(14,6))

            plt.plot(time, series, label="Historical")
            plt.plot(future_dates, final_forecast, color="orange", label="Forecast")

            plt.title(f"{STATE.upper()} — {file.replace('.csv','')}")
            plt.legend()
            plt.grid(True)
            plt.show()

        except:
            continue

print("\nDONE")

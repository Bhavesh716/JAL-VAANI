import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX

ROOT_FOLDER = ".."
STATE_FOLDERS = ["maharashtra", "gujarat"]

DATE_COL = "datetime"
VALUE_COL = "water_level"

MIN_ROWS_REQUIRED = 60
FUTURE_WEEKS = 26


for STATE in STATE_FOLDERS:

    print("\n########################################")
    print("PROCESSING STATE:", STATE.upper())
    print("########################################")

    FOLDER = os.path.join(ROOT_FOLDER, "WATER_DATA", STATE)

    if not os.path.exists(FOLDER):
        continue

    files = sorted(os.listdir(FOLDER))


    for file in files:

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

            df = df.set_index(DATE_COL)

            weekly = df[VALUE_COL].resample("W").mean()
            weekly = weekly.interpolate()

            if len(weekly) < 40:
                continue

            time = weekly.index
            series = weekly.values


            model = SARIMAX(
                series,
                order=(1,1,1),
                seasonal_order=(1,1,1,52),
                trend="t",
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            model_fit = model.fit(disp=False)

            base_forecast = model_fit.forecast(steps=FUTURE_WEEKS)

            residuals = model_fit.resid
            noise = np.random.choice(residuals, size=FUTURE_WEEKS, replace=True)
            noise = noise * 0.5

            final_forecast = base_forecast + noise

            future_dates = pd.date_range(
                start=time[-1] + pd.Timedelta(weeks=1),
                periods=FUTURE_WEEKS,
                freq="W"
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

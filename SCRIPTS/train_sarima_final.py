import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT_FOLDER = ".."

STATE_FOLDERS = ["rajasthan","maharashtra","madhya pradesh","gujarat","uttar pradesh"]

DATE_COL = "datetime"
VALUE_COL = "water_level"

FUTURE_WEEKS = 26
MIN_ROWS_REQUIRED = 60

NOISE_SCALE = 0.5

MAX_WEEKLY_CHANGE = 1.5
MAX_LEVEL = 0
MIN_LEVEL = -150


for STATE in STATE_FOLDERS:

    print("\nPROCESSING:", STATE.upper())

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

            temp = pd.DataFrame({
                "date": df[DATE_COL],
                "val": df[VALUE_COL]
            })

            temp = temp.set_index("date")
            weekly = temp.resample("W").mean().dropna()

            if len(weekly) < 52:
                continue

            weekly_values = weekly["val"].values
            weekly_time = weekly.index


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


            plt.figure(figsize=(14,6))

            plt.plot(weekly_time, weekly_values, label="Historical")
            plt.plot(future_dates, forecast, color="orange", label="Forecast")

            plt.title(f"{STATE.upper()} — {file.replace('.csv','')}")
            plt.legend()
            plt.grid(True)
            plt.show()


        except:
            continue


print("\nALL STATES FORECASTING COMPLETE")

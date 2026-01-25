import csv
import os
from datetime import datetime

ROOT = ".."
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")

DATETIME_COL = "datetime"


for state in os.listdir(WATER_ROOT):

    state_path = os.path.join(WATER_ROOT, state)

    if not os.path.isdir(state_path):
        continue

    for file in os.listdir(state_path):

        if not file.endswith(".csv"):
            continue

        path = os.path.join(state_path, file)

        with open(path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        header = rows[0]
        data = rows[1:]

        if DATETIME_COL not in header:
            continue

        idx = header.index(DATETIME_COL)

        data.sort(key=lambda x: datetime.strptime(x[idx], "%Y-%m-%d %H:%M:%S"))

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)

print("\n===== ALL WATER FILES SORTED =====\n")

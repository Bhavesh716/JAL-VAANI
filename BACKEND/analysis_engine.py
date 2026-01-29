import csv
import os
from datetime import datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATER_DATA = os.path.join(ROOT, "WATER_DATA")


def parse_date(dt):
    return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")


def get_analysis_data(state, district):

    path = os.path.join(WATER_DATA, state, district.replace(" ", "_") + ".csv")

    if not os.path.exists(path):
        return {"error": "file_not_found"}

    weekly = defaultdict(list)
    monthly = defaultdict(list)
    seasonal = defaultdict(list)

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:

            try:
                wl = float(row[6])
                dt = parse_date(row[9])

                year = dt.year
                week = dt.isocalendar()[1]
                month = dt.month

                quarter = (month - 1) // 3 + 1

                weekly[f"{year}-W{week}"].append(wl)
                monthly[f"{year}-{month:02d}"].append(wl)
                seasonal[f"{year}-Q{quarter}"].append(wl)

            except:
                continue

    def mean_dict(data):
        out = []
        for k in sorted(data):
            avg = sum(data[k]) / len(data[k])
            out.append({"x": k, "y": round(avg, 2)})
        return out

    return {
        "weekly": mean_dict(weekly),
        "monthly": mean_dict(monthly),
        "seasonal": mean_dict(seasonal)
    }

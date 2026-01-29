import os
import csv

ROOT = ".."
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")


def clamp(x):
    if x < 0:
        return 0
    if x > 1:
        return 1
    return x


def read_last_valid_row(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        if len(rows) <= 1:
            return None

        for row in reversed(rows):

            if not row:
                continue

            if len(row) < 10:
                continue

            try:
                water_level = float(row[6])
                well_depth = float(row[7])

                return {
                    "stationCode": row[0],
                    "latitude": float(row[2]),
                    "longitude": float(row[3]),
                    "state": row[4],
                    "district": row[5],
                    "water_level": water_level,
                    "well_depth": well_depth,
                    "datetime": row[9]
                }

            except:
                continue

        return None

    except:
        return None


def get_latest_water_snapshot():

    output = []

    for root, _, files in os.walk(WATER_ROOT):

        for file in files:

            if not file.endswith(".csv"):
                continue

            path = os.path.join(root, file)

            data = read_last_valid_row(path)

            if not data:
                continue

            wl = data["water_level"]
            depth = data["well_depth"]

            normalized = (depth - abs(wl)) / depth
            normalized = clamp(normalized)

            output.append({
                "state": data["state"],
                "district": data["district"],
                "lat": data["latitude"],
                "lon": data["longitude"],
                "datetime": data["datetime"],
                "water_level": wl,
                "well_depth": depth,
                "normalized": round(normalized, 3)
            })

    return output

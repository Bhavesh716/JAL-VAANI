import os
import csv
import time
import requests
from datetime import datetime, timedelta

ROOT = ".."

WATER_ROOT = os.path.join(ROOT, "WATER_DATA")
RAIN_ROOT  = os.path.join(ROOT, "RAIN_DATA")

REQUEST_SLEEP = 1
MAX_RETRIES = 3
RETRY_SLEEP = 5

STATES = ["rajasthan","uttar pradesh","maharashtra","madhya pradesh","gujarat"]

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def extract_lat_lon(csv_path):

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

        return row[header.index("latitude")], row[header.index("longitude")]


def get_last_rain_date(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        if len(rows) <= 1:
            return None

        last = rows[-1][0]
        return datetime.strptime(last, "%Y%m%d")

    except:
        return None


def fetch_rainfall(lat, lon, start, end):

    params = {
        "parameters": "PRECTOTCORR,T2M",
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": start,
        "end": end,
        "format": "CSV"
    }

    for _ in range(MAX_RETRIES):

        try:
            r = session.get(BASE_URL, params=params, timeout=60)
            if r.status_code == 200:
                return r.text
        except:
            pass

        time.sleep(RETRY_SLEEP)

    return None


def deduplicate_rain_csv():

    print("\n===== RAIN DUPLICATION CLEANUP STARTED =====")

    for root, _, files in os.walk(RAIN_ROOT):

        for file in files:

            if not file.endswith(".csv"):
                continue

            path = os.path.join(root, file)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    rows = list(csv.reader(f))

                if len(rows) <= 1:
                    continue

                header = rows[0]
                data = rows[1:]

                seen = set()
                unique_rows = []

                for row in data:
                    key = row[0]
                    if key not in seen:
                        seen.add(key)
                        unique_rows.append(row)

                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(unique_rows)

                print(file, "cleaned:", len(data), "→", len(unique_rows))

            except:
                print(file, "cleanup failed")

    print("\n===== RAIN DUPLICATION CLEANUP DONE =====")


print("\n===== NASA RAIN INCREMENTAL UPDATE STARTED =====")

for state in STATES:

    water_state = os.path.join(WATER_ROOT, state)
    rain_state  = os.path.join(RAIN_ROOT, state)

    if not os.path.isdir(water_state):
        continue

    os.makedirs(rain_state, exist_ok=True)

    for file in os.listdir(water_state):

        if not file.endswith(".csv"):
            continue

        rain_file = file.replace(".csv","_rain.csv")
        rain_path = os.path.join(rain_state, rain_file)

        lat, lon = extract_lat_lon(os.path.join(water_state, file))

        today = datetime.now().strftime("%Y%m%d")

        if os.path.exists(rain_path):

            last_date = get_last_rain_date(rain_path)

            if not last_date:
                print(file, "skipped (bad rain csv)")
                continue

            start_date = (last_date + timedelta(days=1)).strftime("%Y%m%d")

        else:

            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

        print(file, "fetching", start_date, "→", today)

        data = fetch_rainfall(lat, lon, start_date, today)

        if not data:
            continue

        lines = data.splitlines()

        if len(lines) <= 1:
            continue

        mode = "a" if os.path.exists(rain_path) else "w"

        with open(rain_path, mode, newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            if mode == "w":
                for line in lines:
                    writer.writerow(line.split(","))
            else:
                for line in lines[1:]:
                    writer.writerow(line.split(","))

        time.sleep(REQUEST_SLEEP)

deduplicate_rain_csv()

print("\n===== NASA UPDATE COMPLETE =====\n")

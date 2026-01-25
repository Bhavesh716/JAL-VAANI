import os
import csv
import time
import requests
from datetime import datetime, timedelta

ROOT = ".."

WATER_ROOT = os.path.join(ROOT, "WATER_DATA")
RAIN_ROOT  = os.path.join(ROOT, "RAIN_DATA")

REQUEST_SLEEP = 1.2
MAX_RETRIES = 5
RETRY_SLEEP = 8

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


def get_last_rain_date(file):

    try:
        with open(file,"r") as f:
            rows = f.readlines()

        if len(rows) <= 2:
            return None

        last = rows[-1].split(",")[0]
        return datetime.strptime(last,"%Y%m%d")

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

    for attempt in range(MAX_RETRIES):

        try:
            r = session.get(BASE_URL, params=params, timeout=60)
            if r.status_code == 200:
                return r.text

        except:
            pass

        time.sleep(RETRY_SLEEP * (attempt + 1))

    return None


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

        last_date = None

        if os.path.exists(rain_path):
            last_date = get_last_rain_date(rain_path)

        if last_date:
            start_date = (last_date + timedelta(days=1)).strftime("%Y%m%d")
        else:
            start_date = "20240101"

        end_date = datetime.now().strftime("%Y%m%d")

        print(file,"fetching",start_date,"→",end_date)

        data = fetch_rainfall(lat, lon, start_date, end_date)

        if not data:
            continue

        mode = "a" if os.path.exists(rain_path) else "w"

        with open(rain_path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n".join(data.splitlines()[1:]))
            else:
                f.write(data)

        time.sleep(REQUEST_SLEEP)

print("\n===== NASA UPDATE COMPLETE =====\n")

import csv
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS = os.path.join(ROOT, "OUTPUTS")
WATER_DATA = os.path.join(ROOT, "WATER_DATA")
RAIN_DATA = os.path.join(ROOT, "RAIN_DATA")


def normalize(s):
    return s.lower().replace(" ", "").replace("-", "").strip()


# ---------------- BLOCKED DISTRICTS ----------------

def check_blocked(state, district):

    state = normalize(state)
    district = normalize(district)

    no_station = os.path.join(OUTPUTS, "no_station_districts.csv")
    inactive = os.path.join(OUTPUTS, "inactive_districts.csv")

    # no station check
    with open(no_station, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if normalize(row["state"]) == state and normalize(row["district"]) == district:
                return True, "NO_STATION"

    # inactive check
    with open(inactive, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if normalize(row["state"]) == state and normalize(row["district"]) == district:
                return True, "INACTIVE"

    return False, ""


# ---------------- WATER LEVEL ----------------

def get_latest_water(state, district):

    file_path = os.path.join(WATER_DATA, state, district.replace(" ", "_") + ".csv")

    if not os.path.exists(file_path):
        return None, None

    with open(file_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    for row in reversed(rows):

        if len(row) < 10:
            continue

        try:
            wl = float(row[6])
            dt = row[9]
            return wl, dt
        except:
            continue

    return None, None


# ---------------- RAIN + TEMP ----------------

def get_latest_rain_and_temp(state, district):

    file_path = os.path.join(RAIN_DATA, state, district.replace(" ", "_") + "_rain.csv")

    if not os.path.exists(file_path):
        print("RAIN FILE NOT FOUND:", file_path)
        return None, None

    with open(file_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    data_rows = []

    for row in rows:

        if len(row) < 4:
            continue

        # numeric date row
        if row[0].isdigit():

            try:
                rain = float(row[-2])
                temp = float(row[-1])

                data_rows.append((rain, temp))

            except:
                continue

    if not data_rows:
        print("NO VALID RAIN DATA FOUND")
        return None, None

    return data_rows[-1]




# ---------------- SOIL TYPE ----------------

def get_soil_type(district):

    path = os.path.join(OUTPUTS, "soil_mapping.csv")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if normalize(row["district"]) == normalize(district):
                return row["soil_type"].lower()

    return "unknown"


# ---------------- URBAN FLAG ----------------

def is_urban(district):

    path = os.path.join(OUTPUTS, "urban_mapping.csv")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if normalize(row["district"]) == normalize(district):
                return int(row["urban"])

    return 0


# ---------------- EVAPOTRANSPIRATION ----------------

def calculate_evapo(temp):

    return round(temp * 0.5, 2)


# ---------------- RECHARGE ----------------

def calculate_recharge(rain, evapo, soil, urban):

    effective = max(0, rain - evapo)

    if urban == 1:
        factor = 0.15

    else:
        if soil in ["black", "alluvial"]:
            factor = 0.30
        elif soil in ["red", "laterite"]:
            factor = 0.25
        elif soil == "sandy":
            factor = 0.20
        else:
            factor = 0.25

    return round(effective * factor, 2)


# ---------------- MAIN FUNCTION ----------------

def get_district_stats(state, district):

    blocked, reason = check_blocked(state, district)

    if blocked:

        if reason == "NO_STATION":
            return {
                "status": "blocked",
                "reason": "No monitoring station in this district"
            }

        if reason == "INACTIVE":
            return {
                "status": "blocked",
                "reason": "Station inactive / insufficient data"
            }

    wl, wl_time = get_latest_water(state, district)

    rain, temp = get_latest_rain_and_temp(state, district)

    if wl is None or rain is None or temp is None:
        return {
            "status": "error",
            "reason": "Data missing for district"
        }

    evapo = calculate_evapo(temp)

    soil = get_soil_type(district)

    urban = is_urban(district)

    recharge = calculate_recharge(rain, evapo, soil, urban)

    return {
        "status": "ok",
        "water_level": wl,
        "rainfall": rain,
        "evapotranspiration": evapo,
        "recharge": recharge,
        "soil_type": soil,
        "urban": urban,
        "last_updated": wl_time
    }

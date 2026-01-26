import requests
import csv
import time
from datetime import datetime, timedelta
import os
import sys

ROOT = ".."
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")

BASE_URL = "https://indiawris.gov.in/Dataset/Ground Water Level"

AGENCY = "CGWB"
PAGE_SIZE = 1000

REQUEST_SLEEP = 1
DISTRICT_COOLDOWN = 3
RETRY_SLEEP = 5
MAX_RETRIES = 3

STATES = {
    "maharashtra": ["Amaravati","Amravati","Aurangabad","Beed","Bhandara","Buldana","Chandrapur","Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon","Jalna","Kolhapur","Latur","Mumbai city","Mumbai suburban","Nagpur","Nanded","Nandurbar","Nashik","Osmanabad","Palghar","Parbhani","Pune","Raigad","Ratnagiri","Sangli","Satara","Sindudurg","Solapur","Thane","Wardha","Washim","Yavatmal"],
    "rajasthan": ["Ajmer","Alwar","Banswara","Baran","Barmer","Bharatpur","Bhilwara","Bikaner","Bundi","Chittorgarh","Churu","Dausa","Dholpur","Dungarpur","Ganganagar","Hanumangarh","Jaipur","Jaisalmer","Jalore","Jhalawar","Jhunjhunu","Jhunjhunun","Jodhpur","Karauli","Kota","Nagaur","Pali","Pratapgarh","Rajsamand","Sawai madhopur","Sikar","Sirohi","Tonk","Udaipur"],
    "uttar pradesh": ["Agra","Aligarh","Allahbad","Ambedkar nagar","Auraiya","Ayodhya","Azamgarh","Baghpat","Bahraich","Ballia","Balrampur","Banda","Barabanki","Bareilly","Basti","Bhadohi","Bijnor","Budaun","Buland shahar","Chandauli","Chitrakoot","Deoria","Etah","Etawah","Farrukhabad","Fatehpur","Firozabad","Gautam buddha nagar","G.b.nagar","Ghaziabad","Ghazipur","Gonda","Gorakhpur","Hamirpur","Hardoi","Hathras","Jalaun","Jaunpur","jhansi","Jyotiba phule nagar","Kannauj","Kanpur dehat","Kanpur nagar","Kaushambi","Kheri","Kushinagar","Lalitpur","Lucknow","Maharajganj","mahoba","Mainpuri","Mathura","Mau","Meerut","Mirzapur","Moradabad","Muzaffarnagar","Pilibhit","Pratapgarh","Praygraj","Raibareli","Rampur","Saharanpur","Sant kabir nagar","Sant ravidas nagar","Shahjhanpur","Shrawasti","Siddharthnagar","Sitapur","Sonbhadra","Sultanpur","Unnao","Varanasi"],
    "madhya pradesh": ["Agar malwa","Alirajpur","Anuppur","Ashok nagar","Balaghat","Barwani","Betul","Bhind","Bhopal","Burhanpur","Chhatarpur","Chhindwara","Damoh","Datia","Dewas","Dhar","Dindori","East nimar","Guna","Gwalior","Harda","Hoshangabad","Indore","Jabalpur","Jhabua","Katni","Mandla","Mandsaur","Morena","Narsimhapur","Neemuch","Panna","Raisen","Rajgarh","Rajnandgaon","Ratlam","Rewa","Sagar","Satna","Sehore","Seoni","Shahdol","Shajapur","Sheopur","Shivpuri","Sidhi","Singrauli","Tikamgarh","Ujjain","Umaria","Vidisha","West nimar"],
    "gujarat": ["ahmedabad","amreli","anand","aravalli","banaskantha","bharuch","bhavnagar","chhota udaipur","daman","dang","devbhumi dwarka","diu","dohad","gandhinagar","jamnagar","junagadh","kachchh","kheda","mehsana","narmada","navsari","panchmahals","patan","porbandar","rajkot","sabarkantha","surat","surendranagar","vadodara","valsad"]
}

def safe_print(msg):
    print(msg)
    sys.stdout.flush()

def fetch_page_safe(state, district, start, end, page):

    params = {
        "stateName": state.replace("_", " "),
        "districtName": district,
        "agencyName": AGENCY,
        "startdate": start,
        "enddate": end,
        "download": "false",
        "page": page,
        "size": PAGE_SIZE
    }

    for _ in range(MAX_RETRIES):
        try:
            r = requests.post(BASE_URL, params=params, timeout=40)
            if r.status_code == 200:
                return r.json()
        except:
            pass

        time.sleep(RETRY_SLEEP)

    return {"data": []}

def parse_api_datetime(t):

    try:
        if isinstance(t, dict):
            return datetime(
                t["year"],
                t["monthValue"],
                t["dayOfMonth"],
                t.get("hour", 0),
                t.get("minute", 0)
            )
        else:
            return datetime.fromisoformat(t.replace("Z", ""))
    except:
        return None

def read_csv_station_and_last_dt(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        if len(rows) <= 1:
            return None, None

        for row in reversed(rows):

            if not row:
                continue

            if len(row) < 10:
                continue

            try:
                station_code = row[0].strip()
                last_dt = datetime.strptime(row[9].strip(), "%Y-%m-%d %H:%M:%S")
                return station_code, last_dt
            except:
                continue

        return None, None

    except:
        return None, None


def update_history(state, district):

    safe_print(f"\nSTARTING {state}/{district}")

    state_folder = os.path.join(WATER_ROOT, state)
    os.makedirs(state_folder, exist_ok=True)

    file_path = os.path.join(state_folder, district.replace(" ", "_") + ".csv")

    today = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(file_path):

        station_code, last_dt = read_csv_station_and_last_dt(file_path)

        if not station_code or not last_dt:
            safe_print(f"{district} skipped (bad csv)")
            return

        start_date = (last_dt + timedelta(hours=1)).strftime("%Y-%m-%d")

    else:

        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        data = fetch_page_safe(state, district, start_date, today, 0)
        records = data.get("data", [])

        if not records:
            safe_print(f"{district} skipped (no data last 7 days)")
            return

        station_code = records[0].get("stationCode")

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "stationCode","stationName","latitude","longitude",
                "state","district","water_level","wellDepth",
                "aquiferType","datetime","month","sin_month","cos_month"
            ])

    safe_print(f"{district} fetching {start_date} → {today}")

    page = 0
    new_rows = 0

    while True:

        data = fetch_page_safe(state, district, start_date, today, page)
        records = data.get("data", [])

        if not records:
            break

        with open(file_path, "a", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            for r in records:

                if r.get("stationCode") != station_code:
                    continue

                dt = parse_api_datetime(r.get("dataTime"))
                if not dt:
                    continue

                month = dt.month
                sin_m = round(__import__("math").sin(2 * 3.14159 * month / 12), 8)
                cos_m = round(__import__("math").cos(2 * 3.14159 * month / 12), 8)

                writer.writerow([
                    station_code,
                    r.get("stationName",""),
                    r.get("latitude",""),
                    r.get("longitude",""),
                    state.replace("_"," "),
                    district,
                    r.get("dataValue",""),
                    r.get("wellDepth",""),
                    r.get("wellAquiferType",""),
                    dt.strftime("%Y-%m-%d %H:%M:%S"),
                    month,
                    sin_m,
                    cos_m
                ])

                new_rows += 1

        if len(records) < PAGE_SIZE:
            break

        page += 1
        time.sleep(REQUEST_SLEEP)

    safe_print(f"{district} appended rows: {new_rows}")

def deduplicate_all_csv():

    safe_print("\n===== DUPLICATION CLEANUP STARTED =====")

    for root, _, files in os.walk(WATER_ROOT):

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
                    key = (row[0], row[9])
                    if key not in seen:
                        seen.add(key)
                        unique_rows.append(row)

                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(unique_rows)

                safe_print(f"{file} cleaned: {len(data)} → {len(unique_rows)}")

            except Exception as e:
                safe_print(f"{file} cleanup failed")

    safe_print("\n===== DUPLICATION CLEANUP DONE =====")

print("\n===== WRIS INCREMENTAL UPDATE STARTED =====")

for state in STATES:
    for district in STATES[state]:

        try:
            update_history(state, district)
        except Exception as e:
            safe_print("FAILED:", district, e)

        time.sleep(DISTRICT_COOLDOWN)

deduplicate_all_csv()

print("\n===== WRIS UPDATE COMPLETE =====")

import requests
import csv
import time
from collections import Counter
from datetime import datetime, timedelta
import os
import sys

ROOT = ".."
WATER_ROOT = os.path.join(ROOT, "WATER_DATA")

BASE_URL = "https://indiawris.gov.in/Dataset/Ground Water Level"

AGENCY = "CGWB"
PAGE_SIZE = 1000

REQUEST_SLEEP = 1.5
DISTRICT_COOLDOWN = 20
RETRY_SLEEP = 10
MAX_RETRIES = 8

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


def get_last_datetime(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        if len(rows) <= 1:
            return None

        last_row = rows[-1]
        return datetime.strptime(last_row[-1], "%Y-%m-%d %H:%M:%S")

    except:
        return None


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

    for attempt in range(MAX_RETRIES):

        try:
            r = requests.post(BASE_URL, params=params, timeout=40)

            if r.status_code == 200:
                return r.json()

        except:
            pass

        time.sleep(RETRY_SLEEP * (attempt + 1))

    return {"data": []}


def parse_datetime_safe(t):

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


def find_best_well(state, district):

    counter = Counter()
    meta_cache = {}

    page = 0

    start_scan = "2024-01-01"
    end_scan = datetime.now().strftime("%Y-%m-%d")

    while True:

        data = fetch_page_safe(state, district, start_scan, end_scan, page)
        records = data.get("data", [])

        if not records:
            break

        for r in records:
            code = r.get("stationCode")

            if not code:
                continue

            counter[code] += 1
            meta_cache[code] = r

        page += 1
        time.sleep(REQUEST_SLEEP)

    if not counter:
        return None, None

    best = counter.most_common(1)[0][0]
    return best, meta_cache[best]


def update_history(state, district, station_code, meta):

    state_folder = os.path.join(WATER_ROOT, state)
    os.makedirs(state_folder, exist_ok=True)

    file_path = os.path.join(state_folder, district.replace(" ", "_") + ".csv")

    now_str = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(file_path):
        last_dt = get_last_datetime(file_path)

        if not last_dt:
            start_date = "2024-01-01"
        else:
            start_date = (last_dt + timedelta(minutes=1)).strftime("%Y-%m-%d")

    else:
        start_date = "2024-01-01"

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "stationCode","stationName","latitude","longitude",
                "state","district","water_level","wellDepth",
                "aquiferType","datetime"
            ])

    safe_print(f"{district} updating from {start_date} → {now_str}")

    page = 0
    new_rows = 0

    while True:

        data = fetch_page_safe(state, district, start_date, now_str, page)
        records = data.get("data", [])

        if not records:
            break

        with open(file_path, "a", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            for r in records:

                if r.get("stationCode") != station_code:
                    continue

                dt = parse_datetime_safe(r.get("dataTime"))

                if not dt:
                    continue

                writer.writerow([
                    station_code,
                    meta.get("stationName",""),
                    meta.get("latitude",""),
                    meta.get("longitude",""),
                    state.replace("_"," "),
                    district,
                    r.get("dataValue",""),
                    meta.get("wellDepth",""),
                    meta.get("wellAquiferType",""),
                    dt.strftime("%Y-%m-%d %H:%M:%S")
                ])

                new_rows += 1

        page += 1
        time.sleep(REQUEST_SLEEP)

    safe_print(f"{district} appended rows: {new_rows}")


print("\n===== WRIS INCREMENTAL UPDATE STARTED =====\n")

for state in STATES:

    for district in STATES[state]:

        try:

            well, meta = find_best_well(state, district)

            if not well:
                continue

            update_history(state, district, well, meta)

        except Exception as e:
            safe_print("FAILED:", district, e)

        time.sleep(DISTRICT_COOLDOWN)

print("\n===== WRIS UPDATE COMPLETE =====\n")

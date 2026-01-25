import os
import csv

# ---------------- PATH CONFIG ----------------

ROOT = ".."

WATER_ROOT = os.path.join(ROOT, "WATER_DATA")
OUTPUT_DIR = os.path.join(ROOT, "OUTPUTS")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- DISTRICT LIST ----------------

STATES = {

    "maharashtra": ["Amaravati","Amravati","Aurangabad","Beed","Bhandara","Buldana","Chandrapur","Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon","Jalna","Kolhapur","Latur","Mumbai city","Mumbai suburban","Nagpur","Nanded","Nandurbar","Nashik","Osmanabad","Palghar","Parbhani","Pune","Raigad","Ratnagiri","Sangli","Satara","Sindudurg","Solapur","Thane","Wardha","Washim","Yavatmal"],

    "rajasthan": ["Ajmer","Alwar","Banswara","Baran","Barmer","Bharatpur","Bhilwara","Bikaner","Bundi","Chittorgarh","Churu","Dausa","Dholpur","Dungarpur","Ganganagar","Hanumangarh","Jaipur","Jaisalmer","Jalore","Jhalawar","Jhunjhunu","Jhunjhunun","Jodhpur","Karauli","Kota","Nagaur","Pali","Pratapgarh","Rajsamand","Sawai madhopur","Sikar","Sirohi","Tonk","Udaipur"],

    "uttar pradesh": ["Agra","Aligarh","Allahbad","Ambedkar nagar","Auraiya","Ayodhya","Azamgarh","Baghpat","Bahraich","Ballia","Balrampur","Banda","Barabanki","Bareilly","Basti","Bhadohi","Bijnor","Budaun","Buland shahar","Chandauli","Chitrakoot","Deoria","Etah","Etawah","Farrukhabad","Fatehpur","Firozabad","Gautam buddha nagar","G.b.nagar","Ghaziabad","Ghazipur","Gonda","Gorakhpur","Hamirpur","Hardoi","Hathras","Jalaun","Jaunpur","Jhansi","Jyotiba phule nagar","Kannauj","Kanpur dehat","Kanpur nagar","Kaushambi","Kheri","Kushinagar","Lalitpur","Lucknow","Maharajganj","Mahoba","Mainpuri","Mathura","Mau","Meerut","Mirzapur","Moradabad","Muzaffarnagar","Pilibhit","Pratapgarh","Praygraj","Raibareli","Rampur","Saharanpur","Sant kabir nagar","Sant ravidas nagar","Shahjhanpur","Shrawasti","Siddharthnagar","Sitapur","Sonbhadra","Sultanpur","Unnao","Varanasi"],

    "madhya pradesh": ["Agar malwa","Alirajpur","Anuppur","Ashok nagar","Balaghat","Barwani","Betul","Bhind","Bhopal","Burhanpur","Chhatarpur","Chhindwara","Damoh","Datia","Dewas","Dhar","Dindori","East nimar","Guna","Gwalior","Harda","Hoshangabad","Indore","Jabalpur","Jhabua","Katni","Mandla","Mandsaur","Morena","Narsimhapur","Neemuch","Panna","Raisen","Rajgarh","Rajnandgaon","Ratlam","Rewa","Sagar","Satna","Sehore","Seoni","Shahdol","Shajapur","Sheopur","Shivpuri","Sidhi","Singrauli","Tikamgarh","Ujjain","Umaria","Vidisha","West nimar"],

    "gujarat": ["ahmedabad","amreli","anand","aravalli","banaskantha","bharuch","bhavnagar","chhota udaipur","daman","dang","devbhumi dwarka","diu","dohad","gandhinagar","jamnagar","junagadh","kachchh","kheda","mehsana","narmada","navsari","panchmahals","patan","porbandar","rajkot","sabarkantha","surat","surendranagar","vadodara","valsad"]
}

# ---------------- URBAN CORE ----------------

URBAN_SET = set([
    "Mumbai city","Mumbai suburban","Pune","Nagpur","Nashik","Thane","Aurangabad","Solapur","Kolhapur",
    "Jaipur","Jodhpur","Kota","Udaipur","Ajmer","Bikaner",
    "Lucknow","Kanpur nagar","Ghaziabad","Gautam buddha nagar","Meerut","Agra","Varanasi","Praygraj","Bareilly","Gorakhpur",
    "Bhopal","Indore","Jabalpur","Gwalior","Ujjain",
    "ahmedabad","surat","vadodara","rajkot","gandhinagar","bhavnagar"
])


# ---------------- OUTPUT CONTAINERS ----------------

soil_rows = []
urban_rows = []
inactive_rows = []
no_station_rows = []


# ---------------- SOIL RULE ENGINE ----------------

def assign_soil(state, d):

    d = d.lower()

    if state == "rajasthan":
        if d in ["barmer","jaisalmer","bikaner","churu","nagaur"]:
            return "sandy"
        if d in ["banswara","dungarpur","pratapgarh","udaipur"]:
            return "red"
        if d in ["kota","jhalawar","baran"]:
            return "black"
        return "alluvial"

    if state == "maharashtra":
        if d in ["ratnagiri","sindudurg","raigad","palghar","thane","mumbai city","mumbai suburban"]:
            return "laterite"
        if d in ["gadchiroli","chandrapur","gondia"]:
            return "red"
        return "black"

    if state == "uttar pradesh":
        if d in ["jhansi","lalitpur","mahoba","chitrakoot","banda"]:
            return "red"
        if d in ["bahraich","shrawasti","kheri","pilibhit"]:
            return "sandy"
        return "alluvial"

    if state == "madhya pradesh":
        if d in ["balaghat","mandla","dindori","shahdol","anuppur"]:
            return "red"
        return "black"

    if state == "gujarat":
        if d in ["kachchh","banaskantha","patan","surendranagar"]:
            return "sandy"
        if d in ["dang","valsad","navsari"]:
            return "laterite"
        if d in ["dohad","chhota udaipur","aravalli"]:
            return "red"
        return "black"


# ---------------- MAIN LOOP ----------------

for state in STATES:

    state_folder = os.path.join(WATER_ROOT, state)

    for d in STATES[state]:

        soil = assign_soil(state, d)
        soil_rows.append([d, soil])

        urban = 1 if d in URBAN_SET else 0
        urban_rows.append([d, urban])

        csv_file = os.path.join(state_folder, d.replace(" ", "_") + ".csv")

        if not os.path.exists(csv_file):
            no_station_rows.append([d, state])
            continue

        with open(csv_file, "r", encoding="utf-8") as f:
            row_count = sum(1 for _ in f) - 1

        if row_count > 0 and row_count < 50:
            inactive_rows.append([d, state, row_count])


# ---------------- SAVE FILES ----------------

with open(os.path.join(OUTPUT_DIR, "soil_mapping.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["district","soil_type"])
    w.writerows(soil_rows)

with open(os.path.join(OUTPUT_DIR, "urban_mapping.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["district","urban"])
    w.writerows(urban_rows)

with open(os.path.join(OUTPUT_DIR, "inactive_districts.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["district","state","records"])
    w.writerows(inactive_rows)

with open(os.path.join(OUTPUT_DIR, "no_station_districts.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["district","state"])
    w.writerows(no_station_rows)


print("\nALL STATIC MAP FILES GENERATED SUCCESSFULLY")

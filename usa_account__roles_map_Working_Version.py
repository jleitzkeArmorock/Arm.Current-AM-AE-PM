import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# --------------------------
# 0) Output folder
# --------------------------
output_folder = "maps_output"
os.makedirs(output_folder, exist_ok=True)
out_html = os.path.join(output_folder, "leaflet_map.html")

# --------------------------
# 1) Your data
# --------------------------
data = {
    "Account Executive": [
        "Scott Kear", "-", "Austin Black", "Nathan Savage", None, None, None,
        None, None, "Matt Bustin", "Scott Larson", "Jamie Martin", "Jared Johnston",
        "-", "-", "Oak Andrews", "Phil Beohm", "Sean Souso",
        "Antoinette Norton", None, None, "Ryan Hancock", "Gary Carter", None, "Mckay Worthen"
    ],
    "Account Manager": [
        "Tony Deleon", "Sam Belvedere", "Matt Kirchenbauer", "Connor Woodward", None, 
        None, "Connor Woodward", "Anna Sappleton", "Kirby Danuser", "Noah Baldwin", 
        "Noah Baldwin", "Kirby Danuser", "Alex Escribano", "Sophia Vera", "Anna Sappleton",
        "Bob Owen", "Bob Owen", "Kirby Danuser", "Lisa Schalabba", "Austin Woodward",
        "Izzy", "Ryan Yohe", "Ryan Yohe", "Dalton", "Mike Stewart"
    ],
    "State": [
        "TX", "TX", "TX", "TX", "TX", "OK/KS/MO", "GA/AL", "GA/AL", "AR/MS/N. LA", 
        "IL/IA/WI", "MN", "TN/KY", "FL", "FL", "FL", "Indy/MI", "PA/OH", "VA/DC",
        "NC", "AZ", "OR-WA", "S. CA", "N. CA", "CO", "UT/ID"
    ],
    "Project Manager": [
        "Tammy Vaughn", "Tammy Vaughn", "Tammy Vaughn", "Tammy Vaughn", None, "Tammy Vaughn",
        "Frank Uzzolino", "Frank Uzzolino", "Tammy Vaughn", "Frank Uzzolino", "Frank Uzzolino",
        "Frank Uzzolino", "Edwin Dominguez", "Edwin Dominguez", "Frank Uzzolino", "Frank Uzzolino",
        "Frank Uzzolino", "Frank Uzzolino", "Frank Uzzolino", "Mike Klug", "Mike Klug", "Mike Klug",
        "Mike Klug", "Mike Klug", "Mike Klug"
    ]
}
df = pd.DataFrame(data)
# Treat "-" as missing everywhere (so it doesn't show in hovers)
df.replace({"-": None}, inplace=True)
# Add NV with AM=Dalton and add Mike B as AE to AZ, TX, CA, NV
supplement = pd.DataFrame([
    {"State": "NV", "Account Executive": None,     "Account Manager": "Dalton", "Project Manager": None},
    {"State": "AZ", "Account Executive": "Mike B", "Account Manager": None,     "Project Manager": None},
    {"State": "TX", "Account Executive": "Mike B", "Account Manager": None,     "Project Manager": None},
    {"State": "CA", "Account Executive": "Mike B", "Account Manager": None,     "Project Manager": None},
    {"State": "NV", "Account Executive": "Mike B", "Account Manager": None,     "Project Manager": None},
    {"State": "IN", "Account Executive": "Oak Andrews", "Account Manager": "Bob Owen", "Project Manager": "Frank Uzzolino"},
])
df = pd.concat([df, supplement], ignore_index=True)

# --------------------------
# 2) Normalize & expand states
# --------------------------
VALID = {
    "AL","AK","AZ","AR","CA","CO","CT","DC","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY",
    "LA","MA","MD","ME","MI","MN","MO","MS","MT","NC","ND","NE","NH","NJ","NM","NV","NY",
    "OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VA","VT","WA","WI","WV","WY"
}
ALIASES = {
    "NLA":"LA","SCA":"CA","NCA":"CA","INDY":"IN","ORWA":"OR/WA"
}

def split_to_codes(s: str):
    s = (s or "").upper().replace(".", "").replace(" ", "")
    s = s.replace("-", "/")  # e.g., OR-WA
    # apply simple alias cleanup
    s = ALIASES.get(s, s)
    parts = s.split("/")
    out = []
    for p in parts:
        if p in VALID:
            out.append(p)
    return out

def expand_states(row):
    codes = split_to_codes(row["State"])
    rows = []
    for code in codes:
        rows.append({
            "State": code,
            "Account Executive": row["Account Executive"],
            "Account Manager": row["Account Manager"],
            "Project Manager": row["Project Manager"]
        })
    return pd.DataFrame(rows)

df_expanded = pd.concat([expand_states(r) for _, r in df.iterrows()], ignore_index=True)

# --------------------------
# 3) Group per state & build hover
# --------------------------
df_grouped = df_expanded.groupby("State", as_index=False).agg({
    "Account Executive": lambda x: ", ".join([str(i) for i in x if pd.notna(i)]),
    "Account Manager":   lambda x: ", ".join([str(i) for i in x if pd.notna(i)]),
    "Project Manager":   lambda x: ", ".join(sorted(set([str(i) for i in x if pd.notna(i)])))
})
df_grouped["hover"] = df_grouped.apply(
    lambda r: f"State: {r['State']}<br>AE: {r['Account Executive']}<br>AM: {r['Account Manager']}<br>PM: {r['Project Manager']}",
    axis=1
)

# --------------------------
# 4) Approx state centroids (lat, lon) for states we need
# --------------------------
STATE_CENTERS = {
    "AL": (32.8067, -86.7911), "AZ": (33.7298, -111.4312), "AR": (34.9697, -92.3731),
    "CA": (36.1162, -119.6816), "CO": (39.0598, -105.3111), "CT": (41.5978, -72.7554),
    "DC": (38.9072, -77.0369), "FL": (27.7663, -81.6860),  "GA": (33.0406, -83.6431),
    "ID": (44.2405, -114.4788), "IL": (40.3495, -88.9861), "IN": (39.8494, -86.2583),
    "IA": (42.0115, -93.2105),  "KS": (38.5266, -96.7265), "KY": (37.6681, -84.6701),
    "LA": (31.1695, -91.8678),  "MD": (39.0639, -76.8021), "MI": (43.3266, -84.5361),
    "MN": (45.6945, -93.9002),  "MO": (38.4561, -92.2884), "MS": (32.7416, -89.6787),
    "NC": (35.6301, -79.8064),  "ND": (47.5289, -99.7840), "NE": (41.1254, -98.2681),
    "NH": (43.2200, -71.5505),  "NJ": (40.2989, -74.5210), "NM": (34.5000, -106.2485),
    "NV": (38.3135, -117.0556), "NY": (42.1657, -74.9481), "OH": (40.3888, -82.7649),
    "OK": (35.5653, -96.9289),  "OR": (44.5720, -122.0709), "PA": (40.5908, -77.2098),
    "SC": (33.8569, -80.9450),  "SD": (44.2998, -99.4388), "TN": (35.7478, -86.6923),
    "TX": (31.0545, -97.5635),  "UT": (40.1500, -111.8624), "VA": (37.7693, -78.1699),
    "VT": (44.0687, -72.6658),  "WA": (47.4009, -121.4905), "WI": (44.2685, -89.6165),
    "WV": (38.4912, -80.9545)
}

df_grouped["Lat"] = df_grouped["State"].map(lambda s: STATE_CENTERS.get(s, (37.0, -95.0))[0])
df_grouped["Lon"] = df_grouped["State"].map(lambda s: STATE_CENTERS.get(s, (37.0, -95.0))[1])

# --------------------------
# 5) Make Leaflet map
# --------------------------
m = folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="OpenStreetMap")

# Cluster for state-level markers (blue)
state_cluster = MarkerCluster(name="States").add_to(m)
for _, r in df_grouped.iterrows():
    folium.CircleMarker(
        location=[r["Lat"], r["Lon"]],
        radius=6,
        fill=True,
        color="#1f77b4",      # blue outline
        fill_color="#1f77b4", # blue fill
        fill_opacity=0.9,
        popup=folium.Popup(r["hover"], max_width=350),
        tooltip=f"{r['State']}"
    ).add_to(state_cluster)

# --------------------------
# 6) Extra city markers you requested (red)
# --------------------------
#extra_points = pd.DataFrame({
#    "Label": [
#        # California (2)
#        "Los Angeles", "Sacramento",
#        # Texas (5)
#        "Dallas A", "Dallas B", "West Texas (Midland)", "Austin", "Houston",
#        # Florida (3)
#        "Tampa", "Orlando", "Jacksonville"
#    ],
#    "Lat": [
#        34.0522, 38.5816,
#        32.7767, 32.7867, 31.9974, 30.2672, 29.7604,
#        27.9506, 28.5383, 30.3322
#    ],
#    "Lon": [
#        -118.2437, -121.4944,
#        -96.7970, -96.7070, -102.0779, -97.7431, -95.3698,
#        -82.4572, -81.3792, -81.6557
#    ]
#})
#city_cluster = MarkerCluster(name="Cities").add_to(m)
#for _, r in extra_points.iterrows():
#    folium.CircleMarker(
#        location=[r["Lat"], r["Lon"]],
#        radius=7,
#        fill=True,
#        color="#d62728",       # red outline
#        fill_color="#d62728",  # red fill
#        fill_opacity=0.95,
#        popup=folium.Popup(r["Label"], max_width=250),
#        tooltip=r["Label"]
#    ).add_to(city_cluster)

folium.LayerControl().add_to(m)

# --------------------------
# 7) Save
# --------------------------
m.save(out_html)
print(f"Leaflet map saved to: {out_html}")

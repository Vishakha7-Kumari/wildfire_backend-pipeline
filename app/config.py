import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "data", "wildfire_ensemble.pkl")
GEOJSON_PATH = os.path.join(BASE_DIR, "data", "india.geojson")

# Critical Regions
CRITICAL_REGIONS = [
    {"name": "Kashmir & Ladakh", "lat_min": 32.0, "lat_max": 37.5, "lon_min": 73.0, "lon_max": 80.5},
    {"name": "Himachal Pradesh", "lat_min": 30.3, "lat_max": 33.3, "lon_min": 75.5, "lon_max": 79.0},
    {"name": "Uttarakhand", "lat_min": 28.7, "lat_max": 31.5, "lon_min": 77.5, "lon_max": 81.0},
    {"name": "Sikkim", "lat_min": 27.0, "lat_max": 28.5, "lon_min": 88.0, "lon_max": 89.5},
    {"name": "Arunachal Pradesh", "lat_min": 26.5, "lat_max": 29.5, "lon_min": 91.5, "lon_max": 97.5}
]
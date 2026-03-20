import time
import threading
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import Point, shape
import json
from app.config import GEOJSON_PATH, CRITICAL_REGIONS
from app.services.weather import fetch_weather_batch

# Load India boundary
with open(GEOJSON_PATH) as f:
    geo = json.load(f)

india_polygon = shape(geo["features"][0]["geometry"])

# Cache
heatmap_cache = {"points": []}

def generate_heatmap():
    grid = set() # Using a set to prevent duplicate coordinates
    
    # 1. Base Grid (1.0 degree steps) for all of India
    lat = 8.0
    while lat <= 37.0:
        lon = 68.0
        while lon <= 97.0:
            if india_polygon.intersects(Point(lon, lat)):
                grid.add((round(lat, 4), round(lon, 4)))
            lon += 1.0
        lat += 1.0

    # 2. Dense Grid (0.5 degree steps) forced over Critical Regions
    for region in CRITICAL_REGIONS:
        lat = region["lat_min"]
        while lat <= region["lat_max"]:
            lon = region["lon_min"]
            while lon <= region["lon_max"]:
                if india_polygon.intersects(Point(lon, lat)):
                    grid.add((round(lat, 4), round(lon, 4)))
                lon += 1.0 # Tighter spacing creates more heatmap points
            lat += 1.0

    # Convert the set back to a list
    grid_list = list(grid)
    print("grid candidates:", len(grid_list))

    chunk_size = 30
    chunks = [grid_list[i:i + chunk_size] for i in range(0, len(grid_list), chunk_size)]

    points = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_weather_batch, chunks)
        for r in results:
            points.extend(r)

    print("points generated:", len(points))
    heatmap_cache["points"] = points
    print("Heatmap updated:", len(points))

def heatmap_worker():
    while True:
        generate_heatmap()
        time.sleep(900)
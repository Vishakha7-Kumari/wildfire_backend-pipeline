from fastapi import FastAPI
from fastapi.responses import Response
import numpy as np
import joblib
import math
import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from shapely.geometry import Point, shape
from PIL import Image, ImageDraw, ImageFilter
import mercantile
import io
import os

app = FastAPI()

# =========================
# ✅ PATH HANDLING (FIXED)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "wildfire_ensemble.pkl")
geojson_path = os.path.join(BASE_DIR, "india.geojson")

# Load ML model
model = joblib.load(model_path)

# Load India boundary
with open(geojson_path) as f:
    geo = json.load(f)

india_polygon = shape(geo["features"][0]["geometry"])

# Cache
heatmap_cache = {"points": []}

# Critical Regions
CRITICAL_REGIONS = [
    {"name": "Kashmir & Ladakh", "lat_min": 32.0, "lat_max": 37.5, "lon_min": 73.0, "lon_max": 80.5},
    {"name": "Himachal Pradesh", "lat_min": 30.3, "lat_max": 33.3, "lon_min": 75.5, "lon_max": 79.0},
    {"name": "Uttarakhand", "lat_min": 28.7, "lat_max": 31.5, "lon_min": 77.5, "lon_max": 81.0},
    {"name": "Sikkim", "lat_min": 27.0, "lat_max": 28.5, "lon_min": 88.0, "lon_max": 89.5},
    {"name": "Arunachal Pradesh", "lat_min": 26.5, "lat_max": 29.5, "lon_min": 91.5, "lon_max": 97.5}
]

# =========================
# UTILITY FUNCTIONS
# =========================
def month_features(month):
    sin = math.sin(2 * math.pi * month / 12)
    cos = math.cos(2 * math.pi * month / 12)
    return sin, cos


def apply_snowy_region_filter(lat, lon, temp, original_risk):
    if temp > 15.0:
        return original_risk

    for region in CRITICAL_REGIONS:
        if region["lat_min"] <= lat <= region["lat_max"] and region["lon_min"] <= lon <= region["lon_max"]:
            return 0.0

    return original_risk


# =========================
# WEATHER + PREDICTION
# =========================
def fetch_weather_batch(points_chunk):
    lats = ",".join([str(p[0]) for p in points_chunk])
    lons = ",".join([str(p[1]) for p in points_chunk])

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        results = []
        month = datetime.now().month
        month_sin, month_cos = month_features(month)

        locations_data = data if isinstance(data, list) else [data]

        for i, loc in enumerate(locations_data):
            if "current" not in loc:
                continue

            current = loc["current"]
            temp = current["temperature_2m"]
            humidity = current["relative_humidity_2m"]
            wind = current["wind_speed_10m"]

            lat = points_chunk[i][0]
            lon = points_chunk[i][1]

            sample = [[lat, lon, month_sin, month_cos, temp, humidity, wind, 2]]

            prob = model.predict_proba(sample)[0][1]
            raw_risk = prob * 100

            risk = apply_snowy_region_filter(lat, lon, temp, raw_risk)

            results.append({"lat": lat, "lon": lon, "risk": risk})

        return results

    except Exception as e:
        print("Batch weather error:", e)
        return []


# =========================
# HEATMAP GENERATION
# =========================
def generate_heatmap():
    grid = set()

    # Base grid
    lat = 8.0
    while lat <= 37.0:
        lon = 68.0
        while lon <= 97.0:
            if india_polygon.intersects(Point(lon, lat)):
                grid.add((round(lat, 4), round(lon, 4)))
            lon += 1.0
        lat += 1.0

    # Dense grid for mountains
    for region in CRITICAL_REGIONS:
        lat = region["lat_min"]
        while lat <= region["lat_max"]:
            lon = region["lon_min"]
            while lon <= region["lon_max"]:
                if india_polygon.intersects(Point(lon, lat)):
                    grid.add((round(lat, 4), round(lon, 4)))
                lon += 1.0
            lat += 1.0

    grid_list = list(grid)
    print("grid candidates:", len(grid_list))

    chunk_size = 30
    chunks = [grid_list[i:i + chunk_size] for i in range(0, len(grid_list), chunk_size)]

    points = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_weather_batch, chunks)
        for r in results:
            points.extend(r)

    heatmap_cache["points"] = points
    print("Heatmap updated:", len(points))


def heatmap_worker():
    while True:
        generate_heatmap()
        time.sleep(900)


# =========================
# FASTAPI EVENTS
# =========================
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=heatmap_worker)
    thread.daemon = True
    thread.start()


@app.get("/india_heatmap")
def india_heatmap():
    return heatmap_cache


# =========================
# TILE GENERATION
# =========================
def risk_to_color(risk):
    if risk < 5:
        return (0, 180, 0, 120)
    elif risk < 20:
        return (255, 220, 0, 120)
    elif risk < 50:
        return (255, 140, 0, 120)
    elif risk < 80:
        return (220, 0, 0, 120)
    else:
        return (150, 0, 200, 140)


@app.get("/tiles/{z}/{x}/{y}.png")
def wildfire_tile(z: int, x: int, y: int, response: Response):
    bounds = mercantile.bounds(x, y, z)

    lat_margin = (bounds.north - bounds.south) * 0.5
    lon_margin = (bounds.east - bounds.west) * 0.5

    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for p in heatmap_cache["points"]:
        lat = p["lat"]
        lon = p["lon"]
        risk = p["risk"]

        if (bounds.south - lat_margin <= lat <= bounds.north + lat_margin) and \
           (bounds.west - lon_margin <= lon <= bounds.east + lon_margin):

            px = int((lon - bounds.west) / (bounds.east - bounds.west) * 256)
            py = int((bounds.north - lat) / (bounds.north - bounds.south) * 256)

            r = 35
            draw.ellipse([px - r, py - r, px + r, py + r], fill=risk_to_color(risk))

    img = img.filter(ImageFilter.GaussianBlur(radius=15))

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    headers = {"Cache-Control": "public, max-age=900"}
    return Response(content=buf.getvalue(), media_type="image/png", headers=headers)


# =========================
# SINGLE PREDICTION API
# =========================
@app.get("/predict")
def predict(lat: float, lon: float):

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        r = requests.get(url, timeout=6)
        data = r.json()

        weather = data.get("current", {})
        temp = weather.get("temperature_2m", 30)
        humidity = weather.get("relative_humidity_2m", 40)
        wind = weather.get("wind_speed_10m", 5)

    except Exception as e:
        print("predict weather error:", e)
        temp, humidity, wind = 30, 40, 5

    month = datetime.now().month
    month_sin, month_cos = month_features(month)

    sample = [[lat, lon, month_sin, month_cos, temp, humidity, wind, 2]]

    prob = model.predict_proba(sample)[0][1]
    raw_risk = prob * 100

    final_risk = apply_snowy_region_filter(lat, lon, temp, raw_risk)

    return {
        "wildfire_risk": final_risk,
        "temperature": temp,
        "humidity": humidity,
        "wind": wind
    }
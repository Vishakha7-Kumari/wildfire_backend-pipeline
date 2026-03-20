from fastapi import APIRouter
import requests
from datetime import datetime
from app.utils.features import month_features
from app.models.wildfire_model import model
from app.utils.filters import apply_snowy_region_filter

router = APIRouter()

@router.get("/predict")
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

        temp = 30
        humidity = 40
        wind = 5

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
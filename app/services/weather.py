import requests
from datetime import datetime
from app.utils.features import month_features
from app.models.wildfire_model import model
from app.utils.filters import apply_snowy_region_filter

def fetch_weather_batch(points_chunk):
    """Fetches weather for multiple coordinates in a single API call to avoid rate limits."""
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
            
            # Apply the snowy region override filter here
            risk = apply_snowy_region_filter(lat, lon, temp, raw_risk)
            
            results.append({"lat": lat, "lon": lon, "risk": risk})
            
        return results
    except Exception as e:
        print("Batch weather error:", e)
        return []
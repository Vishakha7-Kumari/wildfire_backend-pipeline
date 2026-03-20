from app.config import CRITICAL_REGIONS

def apply_snowy_region_filter(lat, lon, temp, original_risk):
    """
    Forces the wildfire risk to 0.0 (Green) for high-altitude 
    regions if the temperature is cold enough.
    """
    # If it's genuinely hot, trust the model's prediction even in the mountains
    if temp > 15.0: 
        return original_risk

    # Check if the coordinate falls inside any of our critical mountainous regions
    for region in CRITICAL_REGIONS:
        if region["lat_min"] <= lat <= region["lat_max"] and region["lon_min"] <= lon <= region["lon_max"]:
            return 0.0

    return original_risk

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
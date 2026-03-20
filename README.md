# Wildfire Risk Prediction API

A FastAPI application that provides wildfire risk predictions for India, including heatmap generation and tile serving for mapping applications.

## Features

- **Risk Prediction**: Predict wildfire risk for specific coordinates based on weather data and ML model
- **Heatmap Generation**: Automatically generates and updates wildfire risk heatmaps across India
- **Tile Serving**: Serves PNG tiles for overlay on maps (e.g., OpenStreetMap)
- **Real-time Weather**: Fetches current weather data from Open-Meteo API

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and startup
│   ├── config.py            # Configuration and constants
│   ├── models/
│   │   ├── __init__.py
│   │   └── wildfire_model.py # ML model loading
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── heatmap.py        # Heatmap data endpoint
│   │   ├── tiles.py          # Map tile endpoint
│   │   └── predict.py        # Risk prediction endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── weather.py        # Weather fetching service
│   │   └── heatmap.py        # Heatmap generation service
│   └── utils/
│       ├── __init__.py
│       ├── features.py       # Feature engineering
│       └── filters.py        # Risk filters and color mapping
├── data/
│   ├── india.geojson         # India boundary data
│   └── wildfire_ensemble.pkl # Trained ML model
├── requirements.txt
├── run.py                   # Application entry point
└── README.md
```

## Setup

1. **Clone or download the project**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Place data files**:
   - Put `india.geojson` in the `data/` directory
   - Put `wildfire_ensemble.pkl` in the `data/` directory

4. **Run the application**:
   ```bash
   python run.py
   ```

   The API will be available at `http://localhost:8000`

## API Endpoints

### GET /predict
Predict wildfire risk for a specific location.

**Parameters**:
- `lat` (float): Latitude
- `lon` (float): Longitude

**Response**:
```json
{
  "wildfire_risk": 25.5,
  "temperature": 28.5,
  "humidity": 45,
  "wind": 3.2
}
```

### GET /india_heatmap
Get the current heatmap data points.

**Response**:
```json
{
  "points": [
    {"lat": 28.6139, "lon": 77.2090, "risk": 15.2},
    ...
  ]
}
```

### GET /tiles/{z}/{x}/{y}.png
Get a map tile with wildfire risk overlay.

**Parameters**:
- `z` (int): Zoom level
- `x` (int): Tile X coordinate
- `y` (int): Tile Y coordinate

**Response**: PNG image

## How It Works

1. **Model**: Uses a trained ensemble model to predict wildfire risk based on location, month, temperature, humidity, and wind speed.

2. **Heatmap**: Periodically generates risk predictions across a grid covering India, with denser coverage in mountainous regions.

3. **Filters**: Applies special filters for high-altitude areas where cold temperatures reduce wildfire risk.

4. **Tiles**: Renders heatmap data as semi-transparent colored circles on map tiles, suitable for overlay on mapping services.

## Dependencies

- FastAPI: Web framework
- NumPy: Numerical computations
- Joblib: Model loading
- Requests: HTTP client for weather API
- Shapely: Geometric operations for boundary checking
- Pillow: Image processing for tiles
- Mercantile: Map tile utilities

## Notes

- The heatmap updates every 15 minutes in the background.
- Weather data is fetched from Open-Meteo API.
- Model predictions are in percentage risk (0-100).
- Tiles use RGBA PNG format for transparency.
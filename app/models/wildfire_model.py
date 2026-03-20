import joblib
from app.config import MODEL_PATH

# Load ML model
model = joblib.load(MODEL_PATH)
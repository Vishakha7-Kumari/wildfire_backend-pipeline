from fastapi import FastAPI
import threading
from app.routes.heatmap import router as heatmap_router
from app.routes.tiles import router as tiles_router
from app.routes.predict import router as predict_router
from app.services.heatmap import heatmap_worker

app = FastAPI()

# Include routers
app.include_router(heatmap_router)
app.include_router(tiles_router)
app.include_router(predict_router)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=heatmap_worker)
    thread.daemon = True
    thread.start()
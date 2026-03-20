from fastapi import APIRouter
from app.services.heatmap import heatmap_cache

router = APIRouter()

@router.get("/india_heatmap")
def india_heatmap():
    return heatmap_cache
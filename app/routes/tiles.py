from fastapi import APIRouter
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFilter
import mercantile
import io
from app.services.heatmap import heatmap_cache
from app.utils.filters import risk_to_color

router = APIRouter()

@router.get("/tiles/{z}/{x}/{y}.png")
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
            draw.ellipse(
                [px - r, py - r, px + r, py + r],
                fill=risk_to_color(risk)
            )

    img = img.filter(ImageFilter.GaussianBlur(radius=15))

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    headers = {"Cache-Control": "public, max-age=900"}
    return Response(content=buf.getvalue(), media_type="image/png", headers=headers)
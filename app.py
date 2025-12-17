"""
FastAPI application for visualizing Voronoi diagrams of metro stations
"""
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
import json
from voronoi_generator import VoronoiMapGenerator

app = FastAPI(
    title="Metro Voronoi Diagrams",
    description="Visualize metro station coverage using Voronoi diagrams",
    version="1.0.0"
)

# Initialize generator
generator = VoronoiMapGenerator()

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "metro-voronoi-diagrams"}

# Pre-rendered cities (popular ones)
POPULAR_CITIES = [
    "São Paulo, Brazil",
    "Rio de Janeiro, Brazil",
    "Tokyo, Japan",
    "London, United Kingdom",
    "New York City, USA",
    "Paris, France",
    "Mexico City, Mexico",
    "Seoul, South Korea",
]

# File to track generation status
STATUS_FILE = "generation_status.json"


def load_status():
    """Load map generation status"""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_status(status):
    """Save map generation status"""
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main page"""
    return FileResponse("static/index.html")


@app.get("/api/popular-cities")
async def get_popular_cities():
    """Return list of popular pre-rendered cities"""
    status = load_status()
    cities_with_status = []

    for city in POPULAR_CITIES:
        city_slug = generator._get_city_slug(city)
        is_ready = status.get(city_slug, {}).get("ready", False)
        cities_with_status.append({
            "name": city,
            "slug": city_slug,
            "ready": is_ready
        })

    return {"cities": cities_with_status}


@app.post("/api/generate-map")
async def generate_map(request: Request, background_tasks: BackgroundTasks):
    """
    Generate or return Voronoi map for a city
    """
    data = await request.json()
    city = data.get("city", "").strip()
    force_regenerate = data.get("force_regenerate", False)

    if not city:
        raise HTTPException(status_code=400, detail="City name cannot be empty")

    try:
        # Check if already exists in cache
        cached_map = generator.get_cached_map(city)

        if cached_map and not force_regenerate:
            city_slug = generator._get_city_slug(city)
            return {
                "city": city,
                "map_url": f"/api/map/{city_slug}",
                "cached": True,
                "message": "Map loaded from cache"
            }

        # Generate new map
        output_file, city_slug = generator.generate_map(city, force_regenerate)

        # Update status
        status = load_status()
        status[city_slug] = {"ready": True, "city": city}
        save_status(status)

        return {
            "city": city,
            "map_url": f"/api/map/{city_slug}",
            "cached": False,
            "message": "Map generated successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating map: {str(e)}")


@app.get("/api/map/{city_slug}")
async def get_map(city_slug: str):
    """Return the map HTML file"""
    map_file = os.path.join(generator.maps_dir, f"{city_slug}_voronoi.html")

    if not os.path.exists(map_file):
        raise HTTPException(status_code=404, detail="Map not found")

    return FileResponse(map_file, media_type="text/html")


@app.post("/api/prerender-popular")
async def prerender_popular_cities(background_tasks: BackgroundTasks):
    """
    Pre-render all popular cities in background
    """
    def prerender():
        status = load_status()
        for city in POPULAR_CITIES:
            try:
                print(f"Pre-rendering {city}...")
                output_file, city_slug = generator.generate_map(city, force_regenerate=False)
                status[city_slug] = {"ready": True, "city": city}
                save_status(status)
            except Exception as e:
                print(f"Error pre-rendering {city}: {e}")
                status[city_slug] = {"ready": False, "city": city, "error": str(e)}
                save_status(status)

    background_tasks.add_task(prerender)

    return {"message": "Pre-rendering started in background"}


# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")


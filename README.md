# Metro Voronoi Diagrams

Interactive visualization of Voronoi diagrams for metro stations in cities around the world.

## Description

This project creates interactive maps showing metro station coverage using Voronoi diagrams. Each colored region on the map represents the area where that specific station is the closest "as the crow flies".

### What are Voronoi Diagrams?

A Voronoi diagram divides a space into regions based on distance to a set of points. In our case:
- **Points**: Metro stations
- **Regions**: Areas where each station is the closest
- **Purpose**: Visualize station distribution and coverage

## Features

- **Any city in the world** with metro data on OpenStreetMap
- **Interactive visualization** with distinct colors for each station
- **Click-to-measure**: Click anywhere on the map to see distance and walking time to nearest station
- **Smart coloring**: Adjacent regions automatically get different colors using graph coloring algorithm
- **Caching system** to avoid unnecessary regeneration
- **REST API** for programmatic integration
- **Modern Vue.js frontend** with fallback to legacy HTML interface
- **Pre-rendering** of popular cities
- **Docker support** for easy deployment

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Fork the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running Locally

Start the server:
```bash
python run.py
```

Or manually:
```bash
uvicorn app:app --reload
```

The server will automatically open your browser at: `http://localhost:8000`

### Running with Docker

Build and run:
```bash
docker build -t metro-voronoi .
docker run -p 8000:8000 metro-voronoi
```

Access at: `http://localhost:8000`

## API Usage

### Main Endpoints

- `GET /` - Main web interface (Vue.js or legacy HTML)
- `GET /health` - Health check endpoint
- `GET /api/popular-cities` - List of pre-configured cities with generation status
- `POST /api/generate-map` - Generate or return cached map
  - Body: `{"city": "City Name, Country", "force_regenerate": false}`
- `GET /api/map/{city_slug}` - Return generated map HTML
- `POST /api/prerender-popular` - Start background pre-rendering of popular cities

### Interactive Documentation

Access Swagger documentation at: `http://localhost:8000/docs`

## Architecture

```
.
├── app.py                  # FastAPI application with API endpoints
├── voronoi_generator.py    # Core map generation logic
├── run.py                  # Development startup script
├── requirements.txt        # Python dependencies
├── Dockerfile              # Multi-stage Docker build
├── frontend/               # Vue.js frontend application
│   ├── src/                # Vue components and services
│   ├── dist/               # Built frontend (production)
│   └── package.json        # Node.js dependencies
├── static/                 # Legacy HTML interface (fallback)
├── maps/                   # Generated maps (HTML files)
├── cache/                  # OSM data cache (JSON)
└── generation_status.json  # Map generation status tracking
```

## Technologies

### Backend
- **Framework**: FastAPI with Uvicorn
- **Geospatial**: OSMnx, GeoPandas, Shapely
- **Visualization**: Folium (Leaflet.js)
- **Data**: OpenStreetMap via Overpass API

### Frontend
- **Modern**: Vue.js 3 with TypeScript
- **Legacy**: HTML5, CSS3, Vanilla JavaScript
- **Build**: Vite

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Base Image**: OSGeo GDAL (Ubuntu) for geospatial support

## How It Works

### Map Generation Process

1. **Data Fetching**: Downloads metro station data from OpenStreetMap using OSMnx
2. **Deduplication**: Merges duplicate stations (same name) into single points at their centroid
3. **Voronoi Creation**: Generates Voronoi diagram using Shapely
4. **Clipping**: Clips polygons to city boundaries
5. **Coloring**: Applies graph coloring algorithm to ensure adjacent regions have different colors
6. **Visualization**: Creates interactive Folium map with:
   - Colored Voronoi regions
   - Subway and train lines
   - Station markers
   - Click-to-measure functionality

### Interactive Features

- **Click anywhere** on the map to see:
  - Nearest station name
  - Distance in meters
  - Estimated walking time
  - Visual line connecting clicked point to station

## Pre-configured Cities

- São Paulo, Brazil
- Rio de Janeiro, Brazil
- Tokyo, Japan
- London, United Kingdom
- New York City, USA
- Paris, France
- Mexico City, Mexico
- Seoul, South Korea

## Troubleshooting

**City not found**: Not all cities have metro data on OpenStreetMap. Try searching for the city on OpenStreetMap first.

**Memory error**: Very large cities may consume significant memory during generation. Consider using Docker with increased memory limits.

**Corrupted cache**: Delete files in `cache/` and `maps/` directories to force regeneration.

**Frontend not loading**: If Vue frontend is not built, the application falls back to legacy HTML interface. Build frontend with `cd frontend && npm install && npm run build`.

## Development

### Frontend Development

The project includes a modern Vue.js frontend. To develop:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` and proxies API calls to backend.

### Building Frontend

```bash
cd frontend
npm run build
```

Built files are placed in `frontend/dist/` and served by FastAPI in production.

## Deployment

### Railway / Cloud Platforms

The application includes:
- `railway.json` for Railway deployment configuration
- `runtime.txt` for Python version specification
- Health check endpoint at `/health`
- Automatic port detection via `$PORT` environment variable

### Environment Variables

- `PORT`: Server port (default: 8000)

## License

MIT License

## Acknowledgments

- OpenStreetMap contributors for geospatial data
- OSMnx developers for excellent geospatial tools
- FastAPI community
- Vue.js team

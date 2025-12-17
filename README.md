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
- **Caching system** to avoid unnecessary regeneration
- **REST API** for programmatic integration
- **Responsive web interface**
- **Pre-rendering** of popular cities

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running

Start the server:
```bash
python run.py
```

Or manually:
```bash
uvicorn app:app --reload
```

Open your browser at: `http://localhost:8000`

## API Usage

### Main Endpoints

- `GET /` - Main web interface
- `GET /api/popular-cities` - List of pre-configured cities
- `POST /api/generate-map` - Generate or return cached map
- `GET /api/map/{city_slug}` - Return generated map HTML
- `POST /api/prerender-popular` - Start background pre-rendering

### Interactive Documentation

Access Swagger documentation at: `http://localhost:8000/docs`

## Architecture

```
.
├── app.py                  # FastAPI application
├── voronoi_generator.py    # Map generation logic
├── run.py                  # Startup script
├── main.py                 # Original script (reference)
├── requirements.txt        # Dependencies
├── static/                 # Frontend files
├── maps/                   # Generated maps (HTML)
├── cache/                  # OSM data cache
└── data/                   # Intermediate data
```

## Technologies

- **Backend**: FastAPI, Python 3.8+
- **Geospatial**: OSMnx, GeoPandas, Shapely
- **Visualization**: Folium (Leaflet.js)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

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

**City not found**: Not all cities have metro data on OpenStreetMap.

**Memory error**: Very large cities may consume a lot of memory.

**Corrupted cache**: Delete files in `cache/` and `maps/` to force regeneration.

## License

MIT License

## Acknowledgments

- OpenStreetMap contributors
- OSMnx developers
- FastAPI community

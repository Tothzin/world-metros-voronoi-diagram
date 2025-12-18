"""
Module for generating Voronoi diagrams of metro stations
"""
import os
from typing import Optional, Tuple, List, Dict
import osmnx as ox
import geopandas as gpd
import folium
from shapely.ops import voronoi_diagram
from shapely.strtree import STRtree

# Paleta de cores para coloração de grafos (distinguíveis e agradáveis)
VORONOI_COLORS = [
    "#e41a1c",  # vermelho
    "#377eb8",  # azul
    "#4daf4a",  # verde
    "#984ea3",  # roxo
    "#ff7f00",  # laranja
    "#ffff33",  # amarelo
    "#a65628",  # marrom
    "#f781bf",  # rosa
]


def _assign_colors_to_polygons(gdf: gpd.GeoDataFrame) -> List[str]:
    """
    Assign colors to polygons so that adjacent polygons have different colors.
    Uses a greedy graph coloring algorithm.

    Args:
        gdf: GeoDataFrame with polygon geometries

    Returns:
        List of color hex codes, one per polygon
    """
    n = len(gdf)
    if n == 0:
        return []

    # Build adjacency list (find which polygons touch each other)
    adjacency: Dict[int, set] = {i: set() for i in range(n)}

    for i in range(n):
        for j in range(i + 1, n):
            # Two polygons are adjacent if they touch or intersect
            if gdf.geometry.iloc[i].touches(gdf.geometry.iloc[j]) or \
               gdf.geometry.iloc[i].intersects(gdf.geometry.iloc[j]):
                adjacency[i].add(j)
                adjacency[j].add(i)

    # Greedy graph coloring
    colors_assigned: Dict[int, int] = {}

    for i in range(n):
        # Find colors used by adjacent polygons
        neighbor_colors = {
            colors_assigned[neighbor]
            for neighbor in adjacency[i]
            if neighbor in colors_assigned
        }

        # Assign the first available color not used by neighbors
        for color_idx in range(len(VORONOI_COLORS)):
            if color_idx not in neighbor_colors:
                colors_assigned[i] = color_idx
                break
        else:
            # Fallback: if we run out of colors (shouldn't happen with 8 colors)
            colors_assigned[i] = i % len(VORONOI_COLORS)

    return [VORONOI_COLORS[colors_assigned[i]] for i in range(n)]


class VoronoiMapGenerator:
    """Generator for Voronoi maps of metro stations"""

    def __init__(self, cache_dir: str = "cache", maps_dir: str = "maps"):
        self.cache_dir = cache_dir
        self.maps_dir = maps_dir
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(maps_dir, exist_ok=True)

    def _get_city_slug(self, city_name: str) -> str:
        """Convert city name to file slug"""
        return city_name.lower().replace(",", "").replace(" ", "_")

    def _fetch_stations(self, city: str) -> gpd.GeoDataFrame:
        """Download metro stations from the city using OSM"""
        station_tags = {
            "railway": "station",
            "station": "subway"
        }

        print(f"Downloading stations from {city}...")
        gdf = ox.features_from_place(city, station_tags)

        # Filter only points with names
        stations = gdf[gdf.geometry.type == "Point"][["name", "geometry"]]
        stations = stations.dropna(subset=["name"])
        stations["linha"] = "unknown"

        print(f"{len(stations)} stations found")

        if len(stations) == 0:
            raise ValueError(f"No metro stations found for {city}")

        return stations

    def _fetch_subway_lines(self, city: str) -> gpd.GeoDataFrame:
        """Download subway lines from the city"""
        print("Downloading subway lines...")

        line_tags = {
            "railway": "subway"
        }

        lines_gdf = ox.features_from_place(city, line_tags)

        # Filter only lines
        lines_gdf = lines_gdf[
            lines_gdf.geometry.type.isin(["LineString", "MultiLineString"])
        ]

        lines_gdf = lines_gdf.to_crs(epsg=4326)

        print(f"{len(lines_gdf)} subway line geometries found")

        return lines_gdf

    def _fetch_train_lines(self, city: str) -> gpd.GeoDataFrame:
        """Download train/rail lines from the city"""
        print("Downloading train lines...")

        line_tags = {
            "railway": ["rail", "light_rail"]
        }

        try:
            lines_gdf = ox.features_from_place(city, line_tags)

            # Filter only lines
            lines_gdf = lines_gdf[
                lines_gdf.geometry.type.isin(["LineString", "MultiLineString"])
            ]

            lines_gdf = lines_gdf.to_crs(epsg=4326)

            print(f"{len(lines_gdf)} train line geometries found")

            return lines_gdf
        except Exception:
            return gpd.GeoDataFrame()

    def _create_voronoi(
        self,
        stations: gpd.GeoDataFrame,
        city: str
    ) -> gpd.GeoDataFrame:
        """Create Voronoi polygons for the stations"""
        # Reproject to UTM
        stations_utm = stations.to_crs(stations.estimate_utm_crs())

        # Create Voronoi diagram
        points = stations_utm.geometry.union_all()
        vor = voronoi_diagram(points)

        # Get city boundaries
        city_gdf = ox.geocode_to_gdf(city).to_crs(stations_utm.crs)
        city_geom = city_gdf.geometry.iloc[0]

        # Clip polygons by city boundaries
        vor_polys = [
            poly.intersection(city_geom)
            for poly in vor.geoms
            if not poly.is_empty
        ]

        # Associate each polygon with the nearest station
        geoms = stations_utm.geometry.tolist()
        tree = STRtree(geoms)

        records = []
        for poly in vor_polys:
            centroid = poly.centroid
            idx = tree.nearest(centroid)

            records.append({
                "name": stations_utm.iloc[idx]["name"],
                "linha": stations_utm.iloc[idx]["linha"],
                "geometry": poly
            })

        voronoi_gdf = gpd.GeoDataFrame(records, crs=stations_utm.crs)
        voronoi_gdf = voronoi_gdf.to_crs(epsg=4326)

        return voronoi_gdf, city_gdf

    def _create_map(
        self,
        voronoi_gdf: gpd.GeoDataFrame,
        stations: gpd.GeoDataFrame,
        subway_lines_gdf: gpd.GeoDataFrame,
        train_lines_gdf: gpd.GeoDataFrame,
        city_gdf: gpd.GeoDataFrame
    ) -> folium.Map:
        """Create Folium map with Voronoi, stations and lines"""
        city_center = city_gdf.to_crs(epsg=4326).geometry.centroid.iloc[0]

        m = folium.Map(
            location=[city_center.y, city_center.x],
            zoom_start=11
        )

        # Assign colors to polygons (adjacent polygons get different colors)
        polygon_colors = _assign_colors_to_polygons(voronoi_gdf)

        # Add color column to GeoDataFrame for styling
        voronoi_gdf = voronoi_gdf.copy()
        voronoi_gdf["_fill_color"] = polygon_colors

        # Add Voronoi polygons
        folium.GeoJson(
            voronoi_gdf,
            style_function=lambda x: {
                "fillColor": x["properties"].get("_fill_color", "#3186cc"),
                "color": "#000000",
                "weight": 0.7,
                "fillOpacity": 0.4,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["name"],
                aliases=["Station"]
            ),
            name="Coverage areas"
        ).add_to(m)

        # Add train lines (gray, below subway)
        if len(train_lines_gdf) > 0:
            folium.GeoJson(
                train_lines_gdf,
                style_function=lambda x: {
                    "color": "#555555",
                    "weight": 2.5,
                    "opacity": 0.8
                },
                name="Train lines"
            ).add_to(m)

        # Add subway lines (cyan, on top)
        if len(subway_lines_gdf) > 0:
            folium.GeoJson(
                subway_lines_gdf,
                style_function=lambda x: {
                    "color": "#17becf",
                    "weight": 3,
                    "opacity": 0.9
                },
                name="Subway lines"
            ).add_to(m)

        # Add station points
        for _, row in stations.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=2,
                fill=True,
                fill_opacity=1,
                color="black"
            ).add_to(m)

        folium.LayerControl().add_to(m)

        return m

    def generate_map(self, city: str, force_regenerate: bool = False) -> Tuple[str, str]:
        """
        Generate Voronoi map for a city

        Args:
            city: City name (e.g., "Rio de Janeiro, Brazil")
            force_regenerate: If True, regenerate even if already in cache

        Returns:
            Tuple (file_path, city_slug)
        """
        city_slug = self._get_city_slug(city)
        output_file = os.path.join(self.maps_dir, f"{city_slug}_voronoi.html")

        # Check if already exists in cache
        if os.path.exists(output_file) and not force_regenerate:
            print(f"Map already exists in cache: {output_file}")
            return output_file, city_slug

        try:
            # Download data
            stations = self._fetch_stations(city)

            # Try to download subway lines (may fail in some cities)
            try:
                subway_lines_gdf = self._fetch_subway_lines(city)
            except Exception as e:
                print(f"Warning: Could not download subway lines: {e}")
                subway_lines_gdf = gpd.GeoDataFrame()

            # Try to download train lines (may fail in some cities)
            try:
                train_lines_gdf = self._fetch_train_lines(city)
            except Exception as e:
                print(f"Warning: Could not download train lines: {e}")
                train_lines_gdf = gpd.GeoDataFrame()

            # Create Voronoi
            voronoi_gdf, city_gdf = self._create_voronoi(stations, city)

            # Create map
            m = self._create_map(
                voronoi_gdf, stations, subway_lines_gdf, train_lines_gdf, city_gdf
            )

            # Save
            m.save(output_file)
            print(f"Voronoi map saved to {output_file}")

            return output_file, city_slug

        except Exception as e:
            raise Exception(f"Error generating map for {city}: {str(e)}")

    def get_cached_map(self, city: str) -> Optional[str]:
        """Return cached map path, if it exists"""
        city_slug = self._get_city_slug(city)
        output_file = os.path.join(self.maps_dir, f"{city_slug}_voronoi.html")

        if os.path.exists(output_file):
            return output_file
        return None


"""
Module for generating Voronoi diagrams of metro stations
"""
import os
from typing import Optional, Tuple
import osmnx as ox
import geopandas as gpd
import folium
from shapely.ops import voronoi_diagram
from shapely.strtree import STRtree


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

        print(f"{len(lines_gdf)} line geometries found")

        return lines_gdf

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
        lines_gdf: gpd.GeoDataFrame,
        city_gdf: gpd.GeoDataFrame
    ) -> folium.Map:
        """Create Folium map with Voronoi, stations and lines"""
        city_center = city_gdf.to_crs(epsg=4326).geometry.centroid.iloc[0]

        m = folium.Map(
            location=[city_center.y, city_center.x],
            zoom_start=11
        )

        # Add Voronoi polygons
        folium.GeoJson(
            voronoi_gdf,
            style_function=lambda x: {
                "fillColor": "#3186cc",
                "color": "#000000",
                "weight": 0.4,
                "fillOpacity": 0.3,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["name"],
                aliases=["Station"]
            ),
            name="Coverage areas"
        ).add_to(m)

        # Add subway lines
        if len(lines_gdf) > 0:
            folium.GeoJson(
                lines_gdf,
                style_function=lambda x: {
                    "color": "#ff0000",
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

            # Try to download lines (may fail in some cities)
            try:
                lines_gdf = self._fetch_subway_lines(city)
            except Exception as e:
                print(f"Warning: Could not download subway lines: {e}")
                lines_gdf = gpd.GeoDataFrame()

            # Create Voronoi
            voronoi_gdf, city_gdf = self._create_voronoi(stations, city)

            # Create map
            m = self._create_map(voronoi_gdf, stations, lines_gdf, city_gdf)

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


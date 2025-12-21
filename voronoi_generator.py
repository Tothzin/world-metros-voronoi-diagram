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

# Version for cache invalidation (increment when algorithm changes)
MAP_VERSION = "v2"  # v2: fixed duplicate station merging

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

        print(f"{len(stations)} raw stations found")

        if len(stations) == 0:
            raise ValueError(f"No metro stations found for {city}")

        # Merge duplicate stations (same name) into a single point at their centroid
        # This handles cases like multiple entries for "Lapa" station in São Paulo
        print(f"Merging duplicate station names...")
        stations = stations.dissolve(by="name", aggfunc="first")
        stations = stations.reset_index()

        # Ensure all geometries are Points (dissolve might create MultiPoint)
        # Convert to centroid to get a single point
        def ensure_point(geom):
            if geom.geom_type == 'MultiPoint':
                return geom.centroid
            elif geom.geom_type == 'Point':
                return geom
            else:
                return geom.centroid

        stations["geometry"] = stations.geometry.apply(ensure_point)

        print(f"{len(stations)} unique stations after merging duplicates")

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

        # Add interactive click functionality
        self._add_click_interactivity(m, stations)

        return m

    def _add_click_interactivity(self, m: folium.Map, stations: gpd.GeoDataFrame):
        """Add click event to show distance to nearest station"""
        import json

        # Prepare station data for JavaScript
        stations_data = []
        for _, row in stations.iterrows():
            stations_data.append({
                'name': row['name'],
                'lat': row.geometry.y,
                'lng': row.geometry.x
            })

        # Convert to JSON string for embedding in JavaScript
        stations_json = json.dumps(stations_data)

        # Get the map variable name from Folium
        map_id = m.get_name()

        # Add custom JavaScript for click handling
        click_script = f"""
        <script>
        (function() {{
            // Wait for map to be ready
            function initClickHandler() {{
                if (typeof {map_id} === 'undefined') {{
                    setTimeout(initClickHandler, 100);
                    return;
                }}

                console.log('Interactive map loaded! Click anywhere to see distance to nearest station.');
                var stations = {stations_json};
                console.log('Loaded ' + stations.length + ' stations');
                var currentMarker = null;
                var currentLine = null;

                // Haversine formula to calculate distance in meters
                function calculateDistance(lat1, lng1, lat2, lng2) {{
                    var R = 6371000; // Earth radius in meters
                    var dLat = (lat2 - lat1) * Math.PI / 180;
                    var dLng = (lng2 - lng1) * Math.PI / 180;
                    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                            Math.sin(dLng/2) * Math.sin(dLng/2);
                    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                    return R * c;
                }}

                // Find nearest station
                function findNearestStation(lat, lng) {{
                    var nearest = null;
                    var minDistance = Infinity;

                    stations.forEach(function(station) {{
                        var distance = calculateDistance(lat, lng, station.lat, station.lng);
                        if (distance < minDistance) {{
                            minDistance = distance;
                            nearest = station;
                        }}
                    }});

                    return {{
                        station: nearest,
                        distance: Math.round(minDistance)
                    }};
                }}

                // Handle map click
                {map_id}.on('click', function(e) {{
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;

                    // Remove previous marker and line
                    if (currentMarker) {{
                        {map_id}.removeLayer(currentMarker);
                    }}
                    if (currentLine) {{
                        {map_id}.removeLayer(currentLine);
                    }}

                    // Find nearest station
                    var result = findNearestStation(lat, lng);
                    var walkingTime = Math.round(result.distance / 80); // ~80m/min walking speed

                    // Add dotted line to nearest station
                    currentLine = L.polyline(
                        [[lat, lng], [result.station.lat, result.station.lng]],
                        {{
                            color: '#333',
                            weight: 1.5,
                            opacity: 0.7,
                            dashArray: '5, 8',
                            lineCap: 'round'
                        }}
                    ).addTo({map_id});

                    // Add marker at clicked location
                    currentMarker = L.marker([lat, lng], {{
                        icon: L.divIcon({{
                            className: 'custom-marker',
                            html: '<div style="background: #e74c3c; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>',
                            iconSize: [12, 12],
                            iconAnchor: [6, 6]
                        }})
                    }}).addTo({map_id});

                    // Add popup
                    var popupContent = `
                        <div style="font-family: Georgia, serif; min-width: 180px;">
                            <div style="font-size: 14px; font-weight: bold; margin-bottom: 8px; color: #333;">
                                Clicked Location
                            </div>
                            <hr style="margin: 8px 0; border: none; border-top: 1px solid #ddd;">
                            <div style="font-size: 13px; line-height: 1.6;">
                                <div style="margin-bottom: 4px;">
                                    <span style="font-weight: bold;">Nearest Station:</span> ${{result.station.name}}
                                </div>
                                <div style="margin-bottom: 4px;">
                                    <span style="font-weight: bold;">Distance:</span> ${{result.distance}}m
                                </div>
                                <div>
                                    <span style="font-weight: bold;">Walking Time:</span> ~${{walkingTime}} min
                                </div>
                            </div>
                        </div>
                    `;

                    currentMarker.bindPopup(popupContent, {{
                        maxWidth: 250,
                        className: 'custom-popup'
                    }}).openPopup();
                }});
            }}

            // Start initialization
            initClickHandler();
        }})();
        </script>

        <style>
        .custom-popup .leaflet-popup-content-wrapper {{
            border-radius: 8px;
            box-shadow: 0 3px 14px rgba(0,0,0,0.3);
        }}
        .custom-popup .leaflet-popup-content {{
            margin: 12px;
        }}
        </style>
        """

        # Add the script to the map
        m.get_root().html.add_child(folium.Element(click_script))

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
        output_file = os.path.join(self.maps_dir, f"{city_slug}_voronoi_{MAP_VERSION}.html")

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
        output_file = os.path.join(self.maps_dir, f"{city_slug}_voronoi_{MAP_VERSION}.html")

        if os.path.exists(output_file):
            return output_file
        return None


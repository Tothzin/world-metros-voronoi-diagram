import os
import osmnx as ox
import geopandas as gpd
import folium
from shapely.ops import voronoi_diagram
from shapely.strtree import STRtree

# =========================
# CONFIGURAÇÃO
# =========================
CITY = "Tokyo, Japan"

os.makedirs("data", exist_ok=True)
os.makedirs("maps", exist_ok=True)

# =========================
# 1. BAIXAR ESTAÇÕES
# =========================
station_tags = {
    "railway": "station",
    "station": "subway"
}

print("Baixando estações...")
gdf = ox.features_from_place(CITY, station_tags)

stations = gdf[gdf.geometry.type == "Point"][["name", "geometry"]]
stations = stations.dropna(subset=["name"])
stations["linha"] = "desconhecida"

print(f"{len(stations)} estações encontradas")

stations.to_file("data/stations.geojson", driver="GeoJSON")
print("Salvo em data/stations.geojson")

# =========================
# 2. REPROJETAR (CRS AUTOMÁTICO)
# =========================
stations_utm = stations.to_crs(stations.estimate_utm_crs())

# =========================
# 3. VORONOI
# =========================
points = stations_utm.geometry.union_all()
vor = voronoi_diagram(points)

city = ox.geocode_to_gdf(CITY).to_crs(stations_utm.crs)
city_geom = city.geometry.iloc[0]

vor_polys = [
    poly.intersection(city_geom)
    for poly in vor.geoms
    if not poly.is_empty
]

# =========================
# 4. ASSOCIAR ESTAÇÃO AO POLÍGONO
# =========================
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

# =========================
# 3.5 BAIXAR LINHAS DE METRÔ (APENAS VISUAL)
# =========================
print("Baixando linhas de metrô...")

line_tags = {
    "railway": "subway"
}

lines_gdf = ox.features_from_place(CITY, line_tags)

lines_gdf = lines_gdf[
    lines_gdf.geometry.type.isin(["LineString", "MultiLineString"])
]

lines_gdf = lines_gdf.to_crs(epsg=4326)

print(f"{len(lines_gdf)} geometrias de linhas encontradas")

# =========================
# 5. MAPA
# =========================
city_center = city.to_crs(epsg=4326).geometry.centroid.iloc[0]

m = folium.Map(
    location=[city_center.y, city_center.x],
    zoom_start=11
)

# Voronoi
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
        aliases=["Estação"]
    ),
    name="Áreas de influência"
).add_to(m)

# Linhas de metrô (por cima)
folium.GeoJson(
    lines_gdf,
    style_function=lambda x: {
        "color": "#ff0000",
        "weight": 3,
        "opacity": 0.9
    },
    name="Linhas de metrô"
).add_to(m)

# Pontos das estações
for _, row in stations.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=2,
        fill=True,
        fill_opacity=1,
        color="black"
    ).add_to(m)

folium.LayerControl().add_to(m)

city_slug = CITY.lower().replace(",", "").replace(" ", "_")
output_file = f"maps/{city_slug}_voronoi.html"

m.save(output_file)
print(f"Mapa Voronoi salvo em {output_file}")

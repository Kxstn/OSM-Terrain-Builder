import time
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
import geopandas as gpd
import osmnx as ox

"""Geodata download module.

This module downloads the building footprints and water bodies from OpenStreetMaps
with specified bounding boxes.
"""

def download_buildings(bounds, max_attempts=3):
    """
    Downloads the building footprints with specified bounds
    --------
    Args:
        bounds (dict): A dictonary containing the bounding box coordinates with 
            the keys of 'west', 'south', 'east', 'north'.
        max_attempts (int): Maximum retry attempts im we get a failed connection.
    Returns:
        buildings (): A Pandas GeoDataFrame containing the footprints.
    """

    area = box(
        bounds["west"],
        bounds["south"],
        bounds["east"],
        bounds["north"],
    )

    last_error = None

    for attempt in range(max_attempts):
        try:
            buildings = ox.features_from_polygon(
                area,
                tags={"building": True},
            )
            break

        except Exception as exc:
            last_error = exc

            if attempt == max_attempts - 1:
                raise RuntimeError(
                    f"Building download failed after {max_attempts} attempts. "
                    "The OpenStreetMap service may be temporarily unavailable."
                ) from last_error

            time.sleep(2 ** (attempt + 1))

    if buildings.empty:
        return buildings

    buildings = buildings[
        buildings.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    if not buildings.empty:
        buildings = buildings.to_crs(buildings.estimate_utm_crs())

    return buildings

def download_water(bounds, max_attempts=3):
    """
    Download mapped water polygons inside the selected area.
    --------
    Args:
        bounds (dict): A dictonary containing the bounding box coordinates with 
            the keys of 'west', 'south', 'east', 'north'.
        max_attempts (int): Maximum retry attempts im we get a failed connection.
    Returns:
        water (): A Pandas GeoDataFrame containing water bodies.
    """


    area = box(
        bounds["west"],
        bounds["south"],
        bounds["east"],
        bounds["north"],
    )

    water_tags = {
        "natural": ["water"],
        "landuse": ["reservoir"],
    }

    for attempt in range(max_attempts):
        try:
            water = ox.features_from_polygon(area, tags=water_tags)
            break
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"Could not download water features: {e}")
                return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            time.sleep(2)

    if water.empty:
        return water

    water = water[
        water.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    if water.empty:
        return water

    water = water[
        ~water.geometry.normalize().wkb.duplicated()
    ].copy()

    water["geometry"] = water.geometry.intersection(area)
    water = water[~water.geometry.is_empty].copy()

    if not water.empty:
        water = water.to_crs(water.estimate_utm_crs())

    return water

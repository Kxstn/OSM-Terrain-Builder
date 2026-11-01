
from pathlib import Path
import requests
import rasterio
from rasterio.io import MemoryFile

from osm_terrain.config import OPENTOPOGRAPHY_API_KEY, API_URL

"""Elevation Data Acquisition Module.

This module provides utilities for downloading, validating, and saving Digital 
Elevation Model (DEM) GeoTIFF datasets from the OpenTopography API for given 
geographic bounding boxes.
"""

def download_elevation(
    south: float,
    west: float,
    north: float,
    east: float,
    output_path: str | Path,
    dem_type: str = "COP30",
) -> Path:
    """
    Download a DEM GeoTIFF for a geographic bounding box.
    --------
    Args:
        south, west, north, east (float): The latitudes and longitudes used to determine
                                        the area to download.
        output_path (Path): The location of where to safe the .tif file.
        dem_type (): The Resolution of Digital elevation model to be used to 
                    get the height map data.
    """

    if not OPENTOPOGRAPHY_API_KEY:
        raise RuntimeError(
            "Missing API key."
        )

    if not (-90 <= south < north <= 90):
        raise ValueError("Require -90 <= south < north <= 90.")

    if not (-180 <= west < east <= 180):
        raise ValueError(
            "Require -180 <= west < east <= 180. "
            "Antimeridian-crossing areas need separate requests."
        )

    params = {
        "demtype": dem_type,
        "south": south,
        "west": west,
        "north": north,
        "east": east,
        "outputFormat": "GTiff",
        "API_Key": OPENTOPOGRAPHY_API_KEY,
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=(10, 180),
        )
        response.raise_for_status()

        if not response.content:
            raise RuntimeError("The API returned an empty response.")

        # Validate the response before writing it to disk.
        with MemoryFile(response.content) as memory_file:
            with memory_file.open() as dataset:
                if dataset.driver != "GTiff":
                    raise RuntimeError(
                        f"Expected GeoTIFF, got {dataset.driver}."
                    )

                if dataset.width < 2 or dataset.height < 2:
                    raise RuntimeError(
                        "The downloaded raster is too small."
                    )

                if dataset.count < 1:
                    raise RuntimeError(
                        "The raster contains no data bands."
                    )

                print(
                    f"Raster size: {dataset.width} x "
                    f"{dataset.height} pixels"
                )
                print(f"CRS: {dataset.crs}")
                print(f"Bounds: {dataset.bounds}")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(response.content)

        print(f"Saved elevation raster to: {output.resolve()}")
        return output

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Elevation download failed: {exc}"
        ) from exc

    except rasterio.errors.RasterioError as exc:
        raise RuntimeError(
            "The API response could not be read as a valid raster. "
            "Check your API key, dataset name, bounds, and API limits."
        ) from exc
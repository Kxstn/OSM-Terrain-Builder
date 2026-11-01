# OSM Terrain Builder

Create printable 3D terrain models from elevation data and OpenStreetMap features.

Pick an area, fetch elevation and OSM data (roads, buildings, water, ...), and export a mesh (e.g. STL) that is ready for 3D printing. An interactive [Streamlit](https://streamlit.io/) front end lets you preview the area on a map and the resulting model in 3D.

> **Status:** early version (`0.1`)

## Features

- Select an area of interest on an interactive map (Folium)
- Load elevation rasters (Rasterio) and OpenStreetMap features (OSMnx, GeoPandas)
- Build a watertight terrain mesh (Trimesh, NumPy, SciPy, Shapely)
- Preview the model in the browser (streamlit-stl)
- Export to a printable format such as STL

## Requirements

- Python 3.10 or newer
- [Conda](https://docs.conda.io/) (Miniconda or Anaconda)

## Installation

The geospatial stack (GDAL, PROJ and GEOS via Rasterio, GeoPandas and Shapely) is much easier to install with conda than with pip alone, so conda is the recommended setup.

### 1. Clone the repository

```bash
git clone https://github.com/Kxstn/OSM-Terrain-Builder.git
cd osm-terrain-builder
```

### 2. Create the environment

```bash
conda create -n osm-terrain-builder python=3.11
conda activate osm-terrain-builder
```

### 3. Install the geospatial dependencies with conda

```bash
conda install geopandas rasterio shapely pyproj numpy scipy pandas matplotlib
```

### 4. Install the project

From the repository root:

```bash
pip install -e .
```
## Usage

Start the Streamlit app:

```bash
streamlit run src/osm_terrain/app.py
```

<!-- Adjust the path above to your actual entry point. -->

Then open the URL shown in the terminal (usually <http://localhost:8501>).

Typical workflow:

1. Choose an area on the map.
2. Select the elevation source and the OSM features to include.
3. Set the model scale, vertical exaggeration and base thickness.
4. Preview the model, then export it for printing.

## Project structure

```
.
├── pyproject.toml
├── LICENSE
├── README.md
└── src/
    └── osm_terrain_builder/
```

## Development

Build a wheel and source distribution:

```bash
pip install build
python -m build
```

The output is written to `dist/`.

## Configuration

The project uses `python-dotenv`. If any API keys or settings are required, create a `.env` file in the project root:

```env
# Example
# SOME_API_KEY=your_key_here
```

## Troubleshooting

- **Rasterio or GeoPandas fail to install or import:** install them with conda rather than pip, and use a single conda channel per environment, as mixing channels can cause conflicts.
- **Overpass / OSM requests are slow or time out:** use a smaller area. OSMnx queries the public Overpass API, which has rate limits.
- **Model is too large to print:** reduce the area, or lower the vertical exaggeration and resolution.
- **`ModuleNotFoundError` after a fresh install:** a direct dependency may be missing from `pyproject.toml`. Please open an issue.

## Data attribution

- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the [ODbL](https://opendatacommons.org/licenses/odbl/).
- Elevation data: add the source and license of your DEM here.

## License

MIT License. See [LICENSE](LICENSE).
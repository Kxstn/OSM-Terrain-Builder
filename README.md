# OSM Terrain Builder

Create printable 3D terrain models from elevation data and OpenStreetMap features.

Pick an area, fetch elevation and OSM data (roads, buildings, water, ...), and export a mesh (e.g. STL) that is ready for 3D printing. An interactive [Streamlit](https://streamlit.io/) front end lets you preview the area on a map and the resulting model in 3D.

> **Status:** early version (`0.1`)

## Features

- Select an area of interest on an interactive map (Folium)
- Download elevation data (Copernicus GLO-30 via the OpenTopography API) and OpenStreetMap features (OSMnx, GeoPandas)
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
cd OSM-Terrain-Builder
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

Elevation data is downloaded from the [OpenTopography](https://opentopography.org/) Global DEM API, which requires a free API key.

1. Create an account at <https://portal.opentopography.org/> and request an API key in the "My Account" section.
2. Create a `.env` file in the project root (it is listed in `.gitignore`, so it won't be committed):

```env
OPENTOPOGRAPHY_API_KEY=your_key_here
```

The app uses the `COP30` dataset (Copernicus GLO-30, 30 m resolution).

## Troubleshooting

- **Rasterio or GeoPandas fail to install or import:** install them with conda rather than pip, and use a single conda channel per environment, as mixing channels can cause conflicts.
- **Overpass / OSM requests are slow or time out:** use a smaller area. OSMnx queries the public Overpass API, which has rate limits.
- **OpenTopography request fails or is rejected:** check that your API key is set in `.env`. The free key has a daily request limit (currently 50 calls per 24 hours for non-academic accounts) and 30 m datasets have a maximum area per request, so try a smaller area.
- **Model is too large to print:** reduce the area, or lower the vertical exaggeration and resolution.
- **`ModuleNotFoundError` after a fresh install:** a direct dependency may be missing from `pyproject.toml`. Please open an issue.

## Data attribution

- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the [ODbL](https://opendatacommons.org/licenses/odbl/).
- Elevation data: Copernicus DEM GLO-30 (COP30), © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA. Accessed via the [OpenTopography](https://opentopography.org/) API.

## License

MIT License. See [LICENSE](LICENSE).

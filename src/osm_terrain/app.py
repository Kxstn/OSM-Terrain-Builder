import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import json
import os

from osm_terrain.terrain.mesh import create_terrain_mesh
from osm_terrain.downloads.elevation import download_elevation
from osm_terrain.downloads.osm_features import (
    download_buildings,
    download_water,
)

"""Main Project File and Streamlit Module

This module is the main entrypoint for the project and also the prototype
Streamlit UI. Here all Modules are run and then used for the .stl file.

This file is still work in progress and prone to changes.
"""

st.set_page_config(page_title="OSM Area Selector", layout="wide")
st.title("OpenStreetMap Area Selector")
st.write("Draw a rectangle on the map to get its geographic bounds.")

#Model settings 
st.sidebar.header("3D Model Settings")

st.sidebar.divider()
st.sidebar.header("Map Features")

include_buildings = st.sidebar.checkbox(
    "Buildings",
    value=False,
)

include_roads = st.sidebar.checkbox(
    "Roads",
    value=False,
)

include_water = st.sidebar.checkbox(
    "Water",
    value=False,
)

if include_roads:
    road_width_mm = st.sidebar.slider(
        "Road width (mm)",
        min_value=0.5,
        max_value=4.0,
        value=1.0,
        step=0.5,
    )
else:
    road_width_mm = 1.0

if include_buildings:
    building_height_mm = st.sidebar.slider(
        "Building height (mm)",
        min_value=0.5,
        max_value=15.0,
        value=3.0,
        step=0.5,
    )
else:
    building_height_mm = 3.0

terrain_size_cm = st.sidebar.selectbox(
    "Terrain size (cm)",
    options=[10, 15, 20, 25],
    index=1,
    help="Sets the target maximum width or depth of the terrain."
)

base_thickness_mm = st.sidebar.slider(
    "Base thickness (mm)",
    min_value=1.0,
    max_value=10.0,
    value=3.0,
    step=0.5,
)

st.sidebar.divider()
st.sidebar.subheader("Current settings")
st.sidebar.write(f"Terrain target size: {terrain_size_cm} cm")
st.sidebar.write(f"Base thickness: {base_thickness_mm} mm")

m = folium.Map(
    location=[51.5, 10.0],
    zoom_start=6,
    control_scale=True,
)

Draw(
    export=False,
    draw_options={
        "polyline": False,
        "polygon": False,
        "circle": False,
        "marker": False,
        "circlemarker": False,
        "rectangle": True,
    },
    edit_options={"edit": True, "remove": True},
).add_to(m)

map_data = st_folium(
    m,
    height=600,
    width=None,
    key="area_selector_map",
    returned_objects=["all_drawings"],
)

drawings = map_data.get("all_drawings") or []

if not drawings:
    st.info("Draw a rectangle on the map to selects its coordinates.")
else:
    feature = drawings[-1]
    geometry = feature.get("geometry", {})

    if geometry.get("type") == "Polygon":

        ring = geometry.get("coordinates", [[]])[0]

        if ring:
            longitudes = [point[0] for point in ring]
            latitudes = [point[1] for point in ring]

            bounds = {
                "south": min(latitudes),
                "west": min(longitudes),
                "north": max(latitudes),
                "east": max(longitudes),
            }

            st.subheader("Selected area")

            col1, col2 = st.columns(2)
            col1.metric("South latitude", f"{bounds['south']:.6f}")
            col1.metric("West longitude", f"{bounds['west']:.6f}")
            col2.metric("North latitude", f"{bounds['north']:.6f}")
            col2.metric("East longitude", f"{bounds['east']:.6f}")

            st.caption(
                "GeoJSON stores coordinates as longitude/latitude."
            )

            st.code(
                "bounds = " + repr(bounds),
                language="python",
            )

            st.download_button(
                "Download bounds as JSON",
                data=json.dumps(bounds, indent=2),
                file_name="selected_area_bounds.json",
                mime="application/json",
            )
            
            if st.button("Download Elevation Data"):
                os.makedirs("data", exist_ok=True)

                with st.spinner("Downloading elevation data..."):
                    result = download_elevation(
                        bounds["south"],
                        bounds["west"],
                        bounds["north"],
                        bounds["east"],
                        output_path="data/elevation_test.tif",
                    )

                st.success("Elevation download finished.")

            if include_buildings and st.button("Test building download"):
                try:
                    with st.spinner("Downloading building footprints..."):
                        buildings = download_buildings(bounds)

                    st.success(
                        f"Found {len(buildings)} building footprints."
                    )

                    if not buildings.empty:
                        st.write("Coordinate system:", buildings.crs)
                        st.dataframe(
                            buildings.drop(columns="geometry").head()
                        )

                except Exception as e:
                    st.error(f"Building download failed: {e}")


if st.button("Generate 3D Model"):
    try:
        buildings = None

        if include_buildings:
            with st.spinner("Downloading building footprints..."):
                buildings = download_buildings(bounds)

            st.info(f"Downloaded {len(buildings)} building footprints.")

        water = None

        if include_water:
            with st.spinner("Downloading water bodies from OpenStreetMap..."):
                water = download_water(bounds)

            if water is not None and not water.empty:
                st.success(f"Found {len(water)} water features.")
            else:
                st.info("No mapped water bodies found in this area.")

        with st.spinner("Generating terrain mesh..."):
            solid_mesh = create_terrain_mesh(
                input_path="data/elevation_test.tif",
                output_path="terrain_with_base.stl",
                terrain_size_cm=float(terrain_size_cm),
                base_thickness_mm=float(base_thickness_mm),
                border_margin_mm=5.0,
                buildings=buildings,
                building_height_mm=float(building_height_mm),
            )

        st.success("3D model generated successfully.")
        st.write("Dimensions (mm):", solid_mesh.extents)
        st.write("Watertight:", solid_mesh.is_watertight)

        with open("terrain_with_base.stl", "rb") as stl_file:
            st.download_button(
                "Download STL",
                data=stl_file,
                file_name="terrain_with_base.stl",
                mime="model/stl",
            )

    except FileNotFoundError:
        st.error(f"Elevation data not found. Download elevation data first.")

    except Exception as e:
        st.error(f"3D model generation failed: {e}")

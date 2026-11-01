import rasterio
import rasterio.features
import rasterio.warp
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter

from osm_terrain.terrain.scaling import calculate_vertical_scale
from osm_terrain.features.buildings import create_buildings_mesh

"""3D Model or Mesh creation module.

This module serves as the primary component for generating 3D printable meshes 
from geospatial elevation data and vector features. It handles raster processing, 
vertical relief scaling, solid base generation, mesh consolidation, and optional 
building extrusion into a watertight 3D model.

Typical usage example:
    
    mesh = create_terrain_mesh(
        input_path="data/elevation.tif",
        output_path="output/terrain.stl",
        terrain_size_cm=15.0,
        base_thickness_mm=3.0
    )
"""

def create_terrain_mesh(
    input_path="data/elevation.tif",
    output_path="terrain_with_base.stl",
    terrain_size_cm=15.0,
    base_thickness_mm=3.0,
    border_margin_mm=5.0,
    buildings=None,
    building_height_mm=3.0,
):
    """Creates a 3D printable solid mesh from a raster elevation file (.tif).

    This function reads elevation and geospatial data using rasterio, calculates
    a vertically scaled heightmap, generates a triangulated surface mesh, and 
    constructs a solid base. 
    Optionally, building geometries can be integrated on top 
    of the terrain before exporting the final solid model as an STL file.

    Args:
        input_path (str, optional): Path to the input elevation raster file 
            (GeoTIFF format). Defaults to "data/elevation.tif".
        output_path (str, optional): File path where the final exported 3D mesh 
            (.stl) will be saved. Defaults to "terrain_with_base.stl".
        terrain_size_cm (float, optional): Target size of the printed terrain model 
            along its longest dimension in centimeters. Defaults to 15.0.
        base_thickness_mm (float, optional): Thickness of the solid base underneath 
            the terrain in millimeters. Defaults to 3.0.
        border_margin_mm (float, optional): Extra margin added to expand the footprint 
            of the base on each side in millimeters. Defaults to 5.0.
        buildings (GeoDataFrame or list, optional): Optional building footprint data 
            to overlay and extrude on the terrain mesh. Defaults to None.
        building_height_mm (float, optional): Extrusion height for the buildings 
            in millimeters. Defaults to 3.0.

    Returns:
        trimesh.Trimesh: The finalized, watertight solid 3D mesh object containing 
        the terrain, solid base, and optional buildings, ready for 3D printing.
    """

    with rasterio.open(input_path) as data:
        
        mask = data.dataset_mask()
        elevation = data.read(1, masked=True).astype(np.float32)

        raster_transform = data.transform
        raster_crs = data.crs

        # Extract feature shapes and values from the array.
        for geom, val in rasterio.features.shapes(
                mask, transform=data.transform):

            # Transform shapes from the dataset's own coordinate reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                data.crs, 'EPSG:4326', geom, precision=6)

            # Print GeoJSON shapes to stdout.
            print(geom)

        heightmap, vertical_scale, relief_m = calculate_vertical_scale(
            elevation,
            max_print_height_mm=30.0,
        )

        rows, cols = heightmap.shape

        x = np.tile(np.arange(cols), (rows, 1))

        y = np.tile(
            np.arange(rows - 1, -1, -1).reshape(-1, 1),
            (1, cols)
        )

        vertices = np.column_stack((
            x.ravel(),
            y.ravel(),
            np.asarray(heightmap).ravel()
        ))

        print("Vertices shape:", vertices.shape)

        faces = []

        for row in range(rows - 1):
            for col in range(cols - 1):
                # Get the indices of the four corner vertices
                top_left = row * cols + col
                top_right = top_left + 1
                bottom_left = (row + 1) * cols + col
                bottom_right = bottom_left + 1

                # Split the grid cell into two triangles
                faces.append([top_left, bottom_left, top_right])
                faces.append([top_right, bottom_left, bottom_right])

        faces = np.array(faces, dtype=np.int64)
        mesh = trimesh.Trimesh(
            vertices=vertices,
            faces=faces,
            process=False
        )

        target_size_mm = terrain_size_cm * 10.0

        width = mesh.extents[0]
        depth = mesh.extents[1]

        scale_xy = min(
            target_size_mm / width,
            target_size_mm / depth
        )

        mesh.vertices[:, 0] *= scale_xy
        mesh.vertices[:, 1] *= scale_xy

        terrain_vertices = mesh.vertices.copy()
        terrain_vertices[:, 2] += base_thickness_mm

        n = len(terrain_vertices)

        bottom_vertices = mesh.vertices.copy()
        bottom_vertices[:, 2] = 0.0

        rows, cols = heightmap.shape

        bottom_grid = bottom_vertices.reshape(rows, cols, 3)

        bottom_grid[:, 0, 0] -= border_margin_mm
        bottom_grid[:, -1, 0] += border_margin_mm

        bottom_grid[0, :, 1] += border_margin_mm
        bottom_grid[-1, :, 1] -= border_margin_mm

        bottom_vertices = bottom_grid.reshape(-1, 3)

        outer_top_vertices = bottom_vertices.copy()
        outer_top_vertices[:, 2] = base_thickness_mm

        all_vertices = np.vstack((
            terrain_vertices,
            bottom_vertices,
            outer_top_vertices
        ))

        top_faces = mesh.faces.copy()

        bottom_faces = mesh.faces[:, ::-1] + n

        all_edges = np.vstack((
            mesh.faces[:, [0, 1]],
            mesh.faces[:, [1, 2]],
            mesh.faces[:, [2, 0]]
        ))

        sorted_edges = np.sort(all_edges, axis=1)
        unique_edges, counts = np.unique(
            sorted_edges,
            axis=0,
            return_counts=True
        )

        boundary_edges = unique_edges[counts == 1]

        border_faces = []
        side_faces = []

        for a, b in boundary_edges:
            # Connect the terrain edge to the outer edge
            border_faces.append([a, b, b + 2*n])
            border_faces.append([a, b + 2*n, a + 2*n])

            # Connect the outer edge down to the bottom
            side_faces.append([a + 2*n, b + 2*n, b + n])
            side_faces.append([a + 2*n, b + n, a + n])

        all_faces = np.vstack((
            top_faces,
            bottom_faces,
            np.array(border_faces, dtype=np.int64),
            np.array(side_faces, dtype=np.int64)
        ))

        solid_mesh = trimesh.Trimesh(
            vertices=all_vertices,
            faces=all_faces,
            process=True
        )

        # Repair consistent face orientation
        trimesh.repair.fix_normals(solid_mesh)

        # Add optional building geometry above the terrain.
        building_mesh = create_buildings_mesh(
            buildings=buildings,
            raster_transform=raster_transform,
            raster_crs=raster_crs,
            heightmap=heightmap,
            scale_xy=scale_xy,
            base_thickness_mm=base_thickness_mm,
            building_height_mm=building_height_mm,
        )

        if building_mesh is not None:
            solid_mesh = trimesh.util.concatenate([
                solid_mesh,
                building_mesh,
            ])

        solid_mesh.export(output_path)
        return solid_mesh

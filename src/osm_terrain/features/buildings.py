import numpy as np
import trimesh

from shapely.ops import transform as transform_geometry, triangulate
from shapely.geometry import Polygon, MultiPolygon, box

"""Building mesh creation module

This module creates the building meshes from a given building footprint file.
In creation this module also accounts for the scaling of the overall model
so the buildings fit the terrain mesh.
"""

def create_buildings_mesh(
    buildings,
    raster_transform,
    raster_crs,
    heightmap,
    scale_xy,
    base_thickness_mm,
    building_height_mm=3.0,
):
    """
    Creates 3D building meshes from given building footprints, aligning them 
    with a terrain heightmap and scaling them to fit the model space.

    Args:
        buildings (gpd.GeoDataFrame): GeoDataFrame containing the building footprint geometries.
        raster_transform (Affine): Affine transformation mapping pixel coordinates to CRS coordinates.
        raster_crs: Coordinate Reference System of the heightmap and raster transform.
        heightmap (np.ndarray): 2D array representing terrain elevations.
        scale_xy (float): Scaling factor to convert pixel coordinates into model units.
        base_thickness_mm (float): Base thickness offset added to the ground elevation.
        building_height_mm (float, optional): Height of the buildings. Defaults to 3.0.

    Returns:
        trimesh.Trimesh or None: A combined 3D trimesh object containing all valid 
                                 building meshes, or None if no meshes could be created.
    """

    if buildings is None or buildings.empty:
        return None

    rows, cols = heightmap.shape
    inverse_transform = ~raster_transform

    # Put building geometries in the elevation raster's CRS.
    buildings = buildings.to_crs(raster_crs)

    # Terrain vertices occupy pixel coordinates from 0 to cols-1 and 0 to rows-1.
    raster_bounds = box(0, 0, cols - 1, rows - 1)

    def to_pixel_coordinates(geom):
        def convert(x, y, z=None):
            col, row = inverse_transform * (x, y)
            return col, row

        return transform_geometry(convert, geom)

    all_meshes = []

    for geom in buildings.geometry:
        if geom is None or geom.is_empty:
            continue

        pixel_geom = to_pixel_coordinates(geom).intersection(raster_bounds)

        if pixel_geom.is_empty:
            continue

        polygons = (
            list(pixel_geom.geoms)
            if isinstance(pixel_geom, MultiPolygon)
            else [pixel_geom]
        )

        for polygon in polygons:
            if not isinstance(polygon, Polygon) or polygon.area < 0.05:
                continue

            center = polygon.representative_point()
            col = int(np.clip(round(center.x), 0, cols - 1))
            row = int(np.clip(round(center.y), 0, rows - 1))

            ground_z = float(heightmap[row, col])
            bottom_z = base_thickness_mm + ground_z
            top_z = bottom_z + building_height_mm

            # Triangulate the footprint, keeping triangles inside the polygon.
            triangles = [
                tri for tri in triangulate(polygon)
                if polygon.covers(tri.representative_point())
            ]

            if not triangles:
                continue

            vertices_xy = set()
            top_faces = []

            for tri in triangles:
                coords = list(tri.exterior.coords)[:-1]
                indices = []

                for px, py in coords:
                    key = (float(px), float(py))
                    if key not in vertices_xy:
                        vertices_xy.add(key)
                    indices.append(key)

                top_faces.append(indices)

            points = list(vertices_xy)
            point_index = {p: i for i, p in enumerate(points)}

            def model_xy(point):
                px, py = point
                return (
                    px * scale_xy,
                    (rows - 1 - py) * scale_xy,
                )

            bottom_vertices = []
            top_vertices = []

            for point in points:
                mx, my = model_xy(point)
                bottom_vertices.append([mx, my, bottom_z])
                top_vertices.append([mx, my, top_z])

            n = len(points)
            vertices = np.asarray(bottom_vertices + top_vertices)

            faces = []

            for tri_indices in top_faces:
                face = [point_index[p] for p in tri_indices]
                faces.append([face[0] + n, face[1] + n, face[2] + n])
                faces.append([face[2], face[1], face[0]])

            rings = [polygon.exterior, *polygon.interiors]

            for ring in rings:
                coords = list(ring.coords)

                for a, b in zip(coords[:-1], coords[1:]):
                    pa = (float(a[0]), float(a[1]))
                    pb = (float(b[0]), float(b[1]))

                    if pa not in point_index or pb not in point_index:
                        continue

                    ia = point_index[pa]
                    ib = point_index[pb]

                    faces.append([ia, ib, ib + n])
                    faces.append([ia, ib + n, ia + n])

            building_mesh = trimesh.Trimesh(
                vertices=vertices,
                faces=np.asarray(faces, dtype=np.int64),
                process=True,
            )

            if not building_mesh.is_empty:
                trimesh.repair.fix_normals(building_mesh)
                all_meshes.append(building_mesh)

    if not all_meshes:
        return None

    return trimesh.util.concatenate(all_meshes)
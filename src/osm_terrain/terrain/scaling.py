import numpy as np
from scipy.ndimage import gaussian_filter

"""Terrain Scaling and Normalization Module.

This module handles the vertical scaling and normalization of elevation 
data for 3D terrain printing. It calculates adaptive vertical scales based on 
statistical measures (percentiles) and applies filtering to suppress 
noise while preserving the natural shape of peaks, ridges, and valleys.

Also this whole module is gathered through stack overflow and stitched together
with the help of claude, because normalization and scaling is pain.
So expect jank and more comments then usual.

Typical usage example:

    heightmap_mm, scale_factor, robust_relief_m = calculate_vertical_scale(
        elevation=elevation_data,
        max_print_height_mm=30.0
    )
"""

def calculate_vertical_scale(elevation, max_print_height_mm=30.0):
    """
    Calculate an adaptive vertical scale for terrain 3D printing.

    - Applies mild smoothing to reduce pixel-level noise.
    - Uses robust relief to estimate the terrain's overall character.
    - Preserves the relative shape of peaks, ridges, and valleys
      using linear scaling without clipping or nonlinear compression.

    Returns:
        heightmap_mm: terrain heights in millimetres
        scale_factor: vertical scale in mm per metre
        robust_relief_m: elevation range between the 2nd and 98th percentiles
    """

    values = np.ma.asarray(elevation, dtype=np.float64)
    valid_mask = ~np.ma.getmaskarray(values)
    data = values.filled(0.0)


    # Mild smoothing to reduce pixel noise while preserving terrain shape.
    smooth = gaussian_filter(data, sigma=0.8)

    # Measure the typical relief without letting isolated extremes dominate
    p02, p98 = np.percentile(smooth, [2, 98])
    robust_relief_m = float(p98 - p02)

    # Full elevation range: used for actual geometry, not clipped.
    z_min = float(np.min(smooth))
    z_max = float(np.max(smooth))
    full_relief_m = z_max - z_min

    if full_relief_m < 0.01:
        return np.zeros(values.shape, dtype=np.float32), 0.0, robust_relief_m

    # Analyze broad terrain shape. This filtered surface is used only
    # to guide scaling; it does not replace the terrain geometry.
    broad_surface = gaussian_filter(smooth, sigma=5.0)

    broad_low, broad_high = np.percentile(
        broad_surface, [2, 98]
    )
    broad_relief_m = float(broad_high - broad_low)

    # Determine target relief in millimetres.
    # Increase relief gradually for larger landscapes, with a hard
    # upper limit on the target robust relief.
    target_mm = 4.0 + 8.0 * np.log1p(
        max(robust_relief_m, 0.0) / 25.0
    )

    # Let broad terrain relief contribute modestly to the target.
    # This helps distinguish broad mountain systems from isolated bumps.
    shape_ratio = broad_relief_m / max(robust_relief_m, 1e-6)
    shape_factor = np.clip(shape_ratio, 0.5, 1.0)
    target_mm *= 0.85 + 0.15 * shape_factor

    target_mm = min(target_mm, max_print_height_mm)

    # Apply one linear scale to the full elevation range.
    # No percentile clipping and no nonlinear peak compression.
    scale_factor = target_mm / full_relief_m

    heightmap_mm = (
        (smooth - z_min) * scale_factor
    ).astype(np.float32)

    return heightmap_mm, scale_factor, robust_relief_m
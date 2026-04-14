"""MODIS ET processing: read HDF4 tiles, reproject, mosaic, compare.

Requires pyhdf with HDF4 DLLs. Add DLL directory before importing:
    import os
    os.add_dll_directory("path/to/pyhdf/dlls")
"""
import os
os.add_dll_directory(os.path.join(os.path.dirname(__file__), "..", ".venv", "Lib", "site-packages", "pyhdf"))

import re
import numpy as np
import xarray as xr
from pyhdf.SD import SD, SDC
from pathlib import Path
from scipy.stats import binned_statistic_2d


MODIS_GRID_RADIUS = 6371007.181
MODIS_TILE_SIZE = 1111950.5196666666
MODIS_NPIX = 2400


def parse_tile_coords(filename):
    m = re.search(r"\.h(\d+)v(\d+)\.", filename)
    return int(m.group(1)), int(m.group(2))


def read_modis_et_tile(filepath):
    """Read ET from a MODIS HDF4 tile, returning data + lat/lon arrays."""
    sd = SD(str(filepath), SDC.READ)
    et_raw = sd.select("ET_500m").get().astype(np.float64)
    sd.end()

    et_raw[et_raw >= 65535] = np.nan
    et_raw[et_raw > 30000] = np.nan
    et_mm = et_raw * 0.1  # mm/yr

    h, v = parse_tile_coords(filepath.name)
    x_ul = (h - 18) * MODIS_TILE_SIZE
    y_ul = (9 - v) * MODIS_TILE_SIZE
    pixel_size = MODIS_TILE_SIZE / MODIS_NPIX

    x = x_ul + (np.arange(MODIS_NPIX) + 0.5) * pixel_size
    y = y_ul - (np.arange(MODIS_NPIX) + 0.5) * pixel_size

    xx, yy = np.meshgrid(x, y)
    lat_2d = np.rad2deg(yy / MODIS_GRID_RADIUS)
    lon_2d = np.rad2deg(xx / (MODIS_GRID_RADIUS * np.cos(np.deg2rad(lat_2d))))

    return et_mm, lat_2d, lon_2d


def process_region_year(data_dir, region_name, year, lat_bounds, lon_bounds, resolution=0.05):
    """Process all MODIS tiles for a region/year into a single gridded DataArray."""
    pattern = f"MOD16A3GF.A{year}001.*.hdf"
    files = sorted(Path(data_dir).glob(pattern))
    print(f"  {region_name} {year}: {len(files)} tiles")

    all_et, all_lat, all_lon = [], [], []
    for f in files:
        et, lat2d, lon2d = read_modis_et_tile(f)
        all_et.append(et.ravel())
        all_lat.append(lat2d.ravel())
        all_lon.append(lon2d.ravel())
        valid_count = np.sum(~np.isnan(et))
        print(f"    {f.name}: {valid_count:,} valid pixels")

    et_all = np.concatenate(all_et)
    lat_all = np.concatenate(all_lat)
    lon_all = np.concatenate(all_lon)

    mask = (
        (lat_all >= lat_bounds[0]) & (lat_all <= lat_bounds[1]) &
        (lon_all >= lon_bounds[0]) & (lon_all <= lon_bounds[1]) &
        ~np.isnan(et_all)
    )
    print(f"    Valid pixels in region: {mask.sum():,}")

    lat_edges = np.arange(lat_bounds[0], lat_bounds[1] + resolution, resolution)
    lon_edges = np.arange(lon_bounds[0], lon_bounds[1] + resolution, resolution)

    result = binned_statistic_2d(
        lat_all[mask], lon_all[mask], et_all[mask],
        statistic="mean", bins=[lat_edges, lon_edges],
    )

    lat_c = 0.5 * (lat_edges[:-1] + lat_edges[1:])
    lon_c = 0.5 * (lon_edges[:-1] + lon_edges[1:])

    return xr.DataArray(
        result.statistic,
        dims=["lat", "lon"],
        coords={"lat": lat_c, "lon": lon_c},
        name="ET",
        attrs={"units": "mm/yr", "long_name": f"Evapotranspiration {year}"},
    )

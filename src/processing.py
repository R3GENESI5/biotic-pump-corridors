"""Data processing: loading, subsetting, anomaly computation.

Handles the different formats and conventions of each satellite product.
"""
import xarray as xr
import numpy as np
from pathlib import Path


# ---------------------------------------------------------------------------
# CERES loading
# ---------------------------------------------------------------------------

def load_ceres(files):
    """Load CERES EBAF NetCDF file(s) into an xarray Dataset.

    CERES EBAF uses dimensions: time, lat, lon
    Latitude runs -90 to 90, longitude runs 0 to 360 (or -180 to 180).
    """
    files = [str(f) for f in files]
    ds = xr.open_mfdataset(files, combine="by_coords")

    # Normalize longitude to -180..180 if needed
    if ds.lon.max() > 180:
        ds = ds.assign_coords(lon=(ds.lon + 180) % 360 - 180)
        ds = ds.sortby("lon")

    return ds


# ---------------------------------------------------------------------------
# Generic spatial/temporal operations
# ---------------------------------------------------------------------------

def subset_region(da, lat_range, lon_range):
    """Subset a DataArray to a lat/lon bounding box.

    Handles both ascending and descending latitude coordinates.
    """
    lat_min, lat_max = min(lat_range), max(lat_range)
    lon_min, lon_max = min(lon_range), max(lon_range)

    # Determine if latitude is ascending or descending
    if da.lat[0] > da.lat[-1]:
        lat_sel = slice(lat_max, lat_min)
    else:
        lat_sel = slice(lat_min, lat_max)

    return da.sel(lat=lat_sel, lon=slice(lon_min, lon_max))


def annual_mean(ds, variable, year):
    """Compute annual mean of a variable for a given year."""
    return (
        ds[variable]
        .sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
        .mean(dim="time")
    )


def seasonal_mean(ds, variable, year, months):
    """Compute mean over specific months of a year.

    Parameters
    ----------
    months : list of int
        e.g. [6,7,8] for JJA or [12,1,2] for DJF
    """
    data = ds[variable].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
    return data.sel(time=data.time.dt.month.isin(months)).mean(dim="time")


def climatological_mean(ds, variable, year_range):
    """Compute multi-year monthly climatology."""
    data = ds[variable].sel(
        time=slice(f"{year_range[0]}-01-01", f"{year_range[1]}-12-31")
    )
    return data.groupby("time.month").mean(dim="time")


def compute_anomaly(ds, variable, year, baseline_years):
    """Compute monthly anomaly relative to a baseline climatology.

    Returns the annual mean of the monthly anomalies for the target year.
    """
    clim = climatological_mean(ds, variable, baseline_years)
    year_data = ds[variable].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
    anomaly = year_data.groupby("time.month") - clim
    return anomaly.mean(dim="time")


def regional_timeseries(ds, variable, lat_range, lon_range):
    """Compute area-weighted regional mean time series.

    Uses cosine(latitude) weighting to account for grid cell area variation.
    """
    region = subset_region(ds[variable], lat_range, lon_range)
    weights = np.cos(np.deg2rad(region.lat))
    return region.weighted(weights).mean(dim=["lat", "lon"])


def cloud_radiative_effect(ds, olr_all_var="toa_lw_all_mon", olr_clr_var="toa_lw_clr_c_mon"):
    """Compute longwave cloud radiative effect (CRE).

    CRE_LW = OLR_clear - OLR_all
    Positive values mean clouds are reducing OLR (trapping longwave).
    A decrease in CRE suggests fewer/thinner clouds.
    """
    return ds[olr_clr_var] - ds[olr_all_var]

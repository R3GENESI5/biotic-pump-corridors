"""Data access via NASA earthaccess for satellite products.

Handles authentication, discovery, and download of:
- CERES EBAF (OLR, cloud radiative effect)
- MODIS (ET, NDVI)
- AIRS (column water vapor)
"""
import earthaccess
from pathlib import Path


def authenticate():
    """Login to NASA Earthdata. Stores credentials in ~/.netrc for reuse."""
    auth = earthaccess.login(persist=True)
    if auth.authenticated:
        print("Authenticated with NASA Earthdata")
    else:
        print("Authentication failed — check your Earthdata credentials")
        print("Register at: https://urs.earthdata.nasa.gov/users/new")
    return auth


def discover_products(keyword, limit=10):
    """Search for available data products by keyword.

    Useful when the exact short_name is uncertain.
    Example: discover_products("CERES EBAF")
    """
    datasets = earthaccess.search_datasets(keyword=keyword)
    print(f"Found {len(datasets)} datasets matching '{keyword}':\n")
    for ds in datasets[:limit]:
        umm = ds.get("umm", ds)
        short = umm.get("ShortName", "?")
        title = umm.get("EntryTitle", "?")
        print(f"  {short:40s} {title}")
    return datasets


def search_and_download(short_name, temporal, output_dir, bounding_box=None, count=None):
    """Search for granules and download them.

    Parameters
    ----------
    short_name : str
        NASA product short name (e.g. "CERES_EBAF_Edition4.2")
    temporal : tuple
        (start_date, end_date) as strings "YYYY-MM-DD"
    output_dir : str or Path
        Directory to save downloaded files
    bounding_box : tuple, optional
        (west_lon, south_lat, east_lon, north_lat) for spatial filtering
    count : int, optional
        Max number of granules to return

    Returns
    -------
    list of Path
        Paths to downloaded files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    kwargs = {"short_name": short_name, "temporal": temporal}
    if bounding_box:
        kwargs["bounding_box"] = bounding_box
    if count:
        kwargs["count"] = count

    results = earthaccess.search_data(**kwargs)
    print(f"Found {len(results)} granules for {short_name}")

    if not results:
        print("  Try discover_products() to find the correct short_name")
        return []

    files = earthaccess.download(results, str(output_dir))
    print(f"  Downloaded to {output_dir}")
    return [Path(f) for f in files]


def fetch_ceres(years, data_dir):
    """Download CERES EBAF monthly data covering the specified years.

    CERES EBAF is typically one large file spanning many years.
    Returns paths to downloaded NetCDF file(s).
    """
    temporal = (f"{min(years)}-01-01", f"{max(years)}-12-31")
    out = Path(data_dir) / "ceres"

    # Try the most common short_name variants (discovered via earthaccess)
    for short_name in [
        "CERES_EBAF",
        "CERES_EBAF-TOA",
    ]:
        files = search_and_download(short_name, temporal, out)
        if files:
            return files

    print("\nCould not find CERES EBAF product.")
    print("Run discover_products('CERES EBAF') to find the correct name.")
    return []


def fetch_modis_et(years, region_bounds, data_dir):
    """Download MODIS MOD16A2GF (ET) for a region and year range.

    Parameters
    ----------
    years : list of int
    region_bounds : dict with 'lat' and 'lon' tuples
    data_dir : str or Path
    """
    temporal = (f"{min(years)}-01-01", f"{max(years)}-12-31")
    lat = region_bounds["lat"]
    lon = region_bounds["lon"]
    bbox = (lon[0], lat[0], lon[1], lat[1])

    return search_and_download(
        short_name="MOD16A2GF",
        temporal=temporal,
        output_dir=Path(data_dir) / "modis_et",
        bounding_box=bbox,
    )


def fetch_airs_wv(years, data_dir):
    """Download AIRS monthly L3 water vapor data."""
    temporal = (f"{min(years)}-01-01", f"{max(years)}-12-31")
    return search_and_download(
        short_name="AIRS3STM",
        temporal=temporal,
        output_dir=Path(data_dir) / "airs",
    )

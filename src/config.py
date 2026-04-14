"""Configuration for the Biotic Pump satellite analysis.

Focal regions, data products, and comparison periods are defined here.
Adjust region boundaries based on your specific analysis needs.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# --- Focal regions ---
# These boundaries are initial estimates. Adjust based on the specific
# features visible in EUMETSAT composites and your domain knowledge.
REGIONS = {
    "maraba": {
        "name": "Marab\u00e1, Amazon",
        "bounds": {"lat": (-7.0, -3.0), "lon": (-52.0, -47.0)},
        "description": "Eastern Amazon — observed ET decline and OLR increase",
    },
    "congo": {
        "name": "Congo Basin",
        "bounds": {"lat": (-5.0, 5.0), "lon": (15.0, 30.0)},
        "description": "Central African rainforest — record drought 2023",
    },
    "tropical_atlantic": {
        "name": "Tropical Atlantic",
        "bounds": {"lat": (-10.0, 10.0), "lon": (-40.0, 0.0)},
        "description": "Ocean between Amazon and Congo — cloud cover anomalies",
    },
}

# --- Wider context region for global maps ---
GLOBAL_TROPICS = {
    "name": "Global Tropics",
    "bounds": {"lat": (-30.0, 30.0), "lon": (-180.0, 180.0)},
}

# --- Time periods ---
FOCUS_YEARS = [2019, 2023]
BASELINE_PERIOD = (2001, 2018)  # for climatological anomaly computation

# --- NASA Earthdata product identifiers ---
PRODUCTS = {
    "ceres_ebaf": {
        "short_name": "CERES_EBAF-TOA",
        "description": "CERES EBAF TOA monthly radiative fluxes (Ed4.2.1)",
        "variables": {
            "olr_all": "toa_lw_all_mon",          # all-sky outgoing longwave
            "olr_clr": "toa_lw_clr_c_mon",        # clear-sky outgoing longwave
            "cloud_area": "cldarea_total_daynight_mon",  # cloud fraction (%)
            "sw_all": "toa_sw_all_mon",            # reflected shortwave
        },
    },
    "modis_et": {
        "short_name": "MOD16A2GF",
        "version": "061",
        "description": "MODIS Terra 8-day gap-filled evapotranspiration (500m)",
        "variable": "ET_500m",
        "scale_factor": 0.1,  # raw values * 0.1 = mm/8day
    },
    "modis_ndvi": {
        "short_name": "MOD13A2",
        "version": "061",
        "description": "MODIS Terra 16-day NDVI (1km)",
        "variable": "1 km 16 days NDVI",
        "scale_factor": 0.0001,
    },
    "airs_wv": {
        "short_name": "AIRS3STM",
        "version": "7.0",
        "description": "AIRS monthly L3 standard retrievals",
        "variable": "TotH2OVap_A",  # ascending orbit total column water vapor
    },
}

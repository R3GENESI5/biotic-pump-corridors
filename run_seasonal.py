"""Seasonal decomposition of corridor collapse.

Splits the CERES and AIRS corridor signals into:
- Dry season (JJA = June-Aug, when the biotic pump is the primary moisture source)
- Wet season (DJF = Dec-Feb, when the ITCZ provides geophysical moisture)
- Transition (MAM, SON)

If the collapse is concentrated in the dry season, it strongly supports
the biotic pump mechanism — because that is when forest transpiration is
the dominant moisture driver, not the ITCZ.
"""
import sys
sys.path.insert(0, ".")

import os
os.add_dll_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   ".venv", "Lib", "site-packages", "pyhdf"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pyhdf.SD import SD, SDC
from pathlib import Path
import re

from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

# Corridor definition
LAT_BAND = (-6.0, 0.0)
LON_RANGE = (-62.0, -47.0)

LANDMARKS = {
    "Belem": (-1.4, -48.5),
    "Maraba": (-5.4, -49.1),
    "Altamira": (-3.2, -52.2),
    "Manaus": (-3.1, -60.0),
}

# Amazon seasons
SEASONS = {
    "Dry (JJA)": [6, 7, 8],
    "Wet (DJF)": [12, 1, 2],
    "Dry-to-Wet (SON)": [9, 10, 11],
    "Wet-to-Dry (MAM)": [3, 4, 5],
}

SEASON_COLORS = {
    "Dry (JJA)": "#e76f51",
    "Wet (DJF)": "#264653",
    "Dry-to-Wet (SON)": "#e9c46a",
    "Wet-to-Dry (MAM)": "#2a9d8f",
}


def lat_slice(da, lat_range):
    lo, hi = min(lat_range), max(lat_range)
    if da.lat[0] > da.lat[-1]:
        return slice(hi, lo)
    return slice(lo, hi)


def seasonal_mean(da, year, months):
    """Compute mean over specific months, handling DJF crossing year boundary."""
    if 12 in months and 1 in months:
        # DJF: Dec of previous year + Jan-Feb of current year
        dec = da.sel(time=slice(f"{year-1}-12-01", f"{year-1}-12-31"))
        jf = da.sel(time=slice(f"{year}-01-01", f"{year}-02-28"))
        combined = xr.concat([dec, jf], dim="time")
        return combined.mean(dim="time")
    else:
        start_month = min(months)
        end_month = max(months)
        subset = da.sel(time=slice(f"{year}-{start_month:02d}-01",
                                    f"{year}-{end_month:02d}-28"))
        return subset.mean(dim="time")


def corridor_transect(da, lat_band, lon_range):
    """Compute area-weighted mean along longitude within lat band."""
    corridor = da.sel(lat=lat_slice(da, lat_band),
                      lon=slice(lon_range[0], lon_range[1]))
    weights = np.cos(np.deg2rad(corridor.lat))
    return corridor.weighted(weights).mean(dim="lat")


# ===========================================================================
# Load CERES
# ===========================================================================
print("Loading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

CERES_VARS = {
    "toa_lw_all_mon": {"label": "OLR", "units": "W/m2"},
    "cldarea_total_daynight_mon": {"label": "Cloud Fraction", "units": "%"},
    "cre_lw": {"label": "LW Cloud Radiative Effect", "units": "W/m2"},
}

# ===========================================================================
# Load AIRS water vapor
# ===========================================================================
print("Loading AIRS...")


def read_airs_wv(filepath):
    sd = SD(str(filepath), SDC.READ)
    sds = sd.select("TotH2OVap_A")
    data = sds.get().astype(np.float64)
    attrs = sds.attributes()
    sd.end()
    fill = attrs.get("_FillValue", -9999)
    data[data == fill] = np.nan
    lat = np.arange(-89.5, 90, 1.0)
    lon = np.arange(-179.5, 180, 1.0)
    m = re.search(r"AIRS\.(\d{4})\.(\d{2})\.", filepath.name)
    year, month = int(m.group(1)), int(m.group(2))
    return xr.DataArray(data, dims=["lat", "lon"],
                        coords={"lat": lat, "lon": lon},
                        attrs={"year": year, "month": month})


def load_airs_year(data_dir, year):
    files = sorted(Path(data_dir).glob(f"AIRS.{year}.*.hdf"))
    monthly = []
    times = []
    for f in files:
        da = read_airs_wv(f)
        m = da.attrs["month"]
        times.append(np.datetime64(f"{year}-{m:02d}-01"))
        monthly.append(da)
    ds = xr.concat(monthly, dim="time")
    ds["time"] = times
    return ds


airs_2019 = load_airs_year("data/airs", 2019)
airs_2023 = load_airs_year("data/airs", 2023)

# ===========================================================================
# Figure 1: Seasonal transects for each variable (CERES + AIRS)
# ===========================================================================
print("\n--- Seasonal corridor decomposition ---")

all_vars = list(CERES_VARS.items()) + [
    ("airs_wv", {"label": "Column Water Vapor (AIRS)", "units": "kg/m2"})
]

fig, axes = plt.subplots(len(all_vars), 1, figsize=(14, 4 * len(all_vars)), sharex=True)

for i, (var, info) in enumerate(all_vars):
    ax = axes[i]

    for season_name, months in SEASONS.items():
        color = SEASON_COLORS[season_name]

        if var == "airs_wv":
            s19 = seasonal_mean(airs_2019, 2019, months)
            s23 = seasonal_mean(airs_2023, 2023, months)
        else:
            s19 = seasonal_mean(ceres[var], 2019, months)
            s23 = seasonal_mean(ceres[var], 2023, months)

        t19 = corridor_transect(s19, LAT_BAND, LON_RANGE)
        t23 = corridor_transect(s23, LAT_BAND, LON_RANGE)
        diff = t23 - t19

        diff.plot(ax=ax, color=color, linewidth=2, label=season_name)

    ax.axhline(0, color="black", linewidth=0.5)

    for name, (lt, ln) in LANDMARKS.items():
        ax.axvline(ln, color="gray", alpha=0.3, linewidth=0.8)
        if i == 0:
            ax.text(ln, ax.get_ylim()[1], f" {name}", rotation=45,
                    fontsize=8, ha="left", va="bottom", color="#555")

    ax.set_title(f"{info['label']} change (2023 - 2019) by season", fontsize=11)
    ax.set_ylabel(f"delta {info['units']}")
    ax.legend(fontsize=9, ncol=2)
    ax.grid(alpha=0.3)
    ax.set_xlabel("")

axes[-1].set_xlabel("Longitude")

fig.suptitle("Seasonal Decomposition of Corridor Changes\n"
             "If dry season (orange) dominates, the biotic pump is implicated",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_seasonal_transects.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_seasonal_transects.png")


# ===========================================================================
# Figure 2: Bar chart — seasonal contribution per segment
# ===========================================================================
print("\n--- Seasonal bar chart by segment ---")

segments = {
    "Coast\n(Belem)": slice(-50, -47),
    "Mid\n(Maraba)": slice(-53, -49),
    "Interior\n(Manaus)": slice(-62, -58),
}

fig, axes = plt.subplots(len(all_vars), 1, figsize=(12, 4 * len(all_vars)))

for i, (var, info) in enumerate(all_vars):
    ax = axes[i]
    x = np.arange(len(segments))
    width = 0.2
    offsets = np.arange(len(SEASONS)) * width - (len(SEASONS) - 1) * width / 2

    for j, (season_name, months) in enumerate(SEASONS.items()):
        color = SEASON_COLORS[season_name]
        vals = []
        for seg_name, lon_slice in segments.items():
            if var == "airs_wv":
                s19 = seasonal_mean(airs_2019, 2019, months)
                s23 = seasonal_mean(airs_2023, 2023, months)
            else:
                s19 = seasonal_mean(ceres[var], 2019, months)
                s23 = seasonal_mean(ceres[var], 2023, months)

            v19 = float(s19.sel(lat=lat_slice(s19, LAT_BAND), lon=lon_slice).mean(skipna=True))
            v23 = float(s23.sel(lat=lat_slice(s23, LAT_BAND), lon=lon_slice).mean(skipna=True))
            vals.append(v23 - v19)

        ax.bar(x + offsets[j], vals, width, label=season_name, color=color, alpha=0.85)

    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(segments.keys(), fontsize=10)
    ax.set_ylabel(f"delta {info['units']}")
    ax.set_title(f"{info['label']}", fontsize=11)
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3, axis="y")

fig.suptitle("Seasonal Breakdown by Corridor Segment (2023 - 2019)\n"
             "Which season drove the change at each location?",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_seasonal_bars.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_seasonal_bars.png")


# ===========================================================================
# Summary table
# ===========================================================================
print("\n=== SEASONAL SUMMARY ===\n")
print(f"{'Variable':30s} {'Season':20s} {'Coast':>8s} {'Mid':>8s} {'Interior':>8s}")
print("-" * 80)

for var, info in all_vars:
    for season_name, months in SEASONS.items():
        vals = []
        for seg_name, lon_slice in segments.items():
            if var == "airs_wv":
                s19 = seasonal_mean(airs_2019, 2019, months)
                s23 = seasonal_mean(airs_2023, 2023, months)
            else:
                s19 = seasonal_mean(ceres[var], 2019, months)
                s23 = seasonal_mean(ceres[var], 2023, months)

            v19 = float(s19.sel(lat=lat_slice(s19, LAT_BAND), lon=lon_slice).mean(skipna=True))
            v23 = float(s23.sel(lat=lat_slice(s23, LAT_BAND), lon=lon_slice).mean(skipna=True))
            vals.append(v23 - v19)

        print(f"{info['label']:30s} {season_name:20s} {vals[0]:+8.2f} {vals[1]:+8.2f} {vals[2]:+8.2f}")
    print()

print("=== DONE ===")

"""NDVI analysis to separate deforestation from drought.

Key question: Did ET drop because trees were cut, or because intact
forest was drought-stressed and transpired less?

If NDVI dropped in areas that remained forested (NDVI still > 0.6),
that's drought-driven transpiration suppression — the biotic pump
failing — not just deforestation arithmetic.
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
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import re
from pyhdf.SD import SD, SDC
from pathlib import Path
from scipy import stats

OUTPUT_DIR = Path("outputs")

WIDE_AMAZON = {"lat": (-10.0, 2.0), "lon": (-65.0, -45.0)}
CONGO = {"lat": (-5.0, 5.0), "lon": (15.0, 30.0)}


def read_ndvi_cmg(filepath):
    """Read MODIS CMG 0.05-degree monthly NDVI."""
    sd = SD(str(filepath), SDC.READ)
    ndvi_raw = sd.select("CMG 0.05 Deg Monthly NDVI").get().astype(np.float64)
    sd.end()

    ndvi_raw[ndvi_raw == -3000] = np.nan  # fill value
    ndvi = ndvi_raw / 10000.0  # scale factor

    # Global 0.05-degree grid: 3600 lat x 7200 lon
    # Lat: 90 to -90 (descending), Lon: -180 to 180
    lat = np.linspace(90 - 0.025, -90 + 0.025, 3600)
    lon = np.linspace(-180 + 0.025, 180 - 0.025, 7200)

    return xr.DataArray(ndvi, dims=["lat", "lon"],
                        coords={"lat": lat, "lon": lon},
                        attrs={"units": "NDVI"})


def load_annual_ndvi(data_dir, year):
    """Load all monthly NDVI files for a year and compute annual mean."""
    files = sorted([f for f in Path(data_dir).glob("MOD13C2.A*.hdf")
                     if f"A{year}" in f.name])
    print(f"  {year}: {len(files)} files")
    monthly = [read_ndvi_cmg(f) for f in files]
    return xr.concat(monthly, dim="time").mean(dim="time")


def subset(da, lat_range, lon_range):
    lat_min, lat_max = min(lat_range), max(lat_range)
    lon_min, lon_max = min(lon_range), max(lon_range)
    if da.lat[0] > da.lat[-1]:
        return da.sel(lat=slice(lat_max, lat_min), lon=slice(lon_min, lon_max))
    return da.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))


# ===========================================================================
# Load NDVI
# ===========================================================================
print("Loading MODIS NDVI...")
ndvi_2019 = load_annual_ndvi("data/modis_ndvi", 2019)
ndvi_2023 = load_annual_ndvi("data/modis_ndvi", 2023)

# ===========================================================================
# Figure 1: NDVI comparison maps — both regions
# ===========================================================================
print("\n--- NDVI comparison maps ---")

for region_name, bounds in [("Eastern Amazon", WIDE_AMAZON), ("Congo Basin", CONGO)]:
    d19 = subset(ndvi_2019, bounds["lat"], bounds["lon"])
    d23 = subset(ndvi_2023, bounds["lat"], bounds["lon"])

    # Coarsen to ~0.25 degree for cleaner maps
    d19_c = d19.coarsen(lat=5, lon=5, boundary="trim").mean()
    d23_c = d23.coarsen(lat=5, lon=5, boundary="trim").mean()
    diff_c = d23_c - d19_c

    proj = ccrs.PlateCarree()
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), subplot_kw={"projection": proj})

    vmin = float(min(d19_c.min(skipna=True), d23_c.min(skipna=True)))
    vmax = float(max(d19_c.max(skipna=True), d23_c.max(skipna=True)))

    for ax in axes:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
        ax.add_feature(cfeature.RIVERS, linewidth=0.3, alpha=0.5)

    im1 = d19_c.plot(ax=axes[0], transform=proj, cmap="YlGn", vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[0].set_title("2019"); plt.colorbar(im1, ax=axes[0], shrink=0.7, label="NDVI", pad=0.02)
    im2 = d23_c.plot(ax=axes[1], transform=proj, cmap="YlGn", vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[1].set_title("2023"); plt.colorbar(im2, ax=axes[1], shrink=0.7, label="NDVI", pad=0.02)
    ma = float(max(abs(diff_c.min(skipna=True)), abs(diff_c.max(skipna=True)))) or 0.01
    im3 = diff_c.plot(ax=axes[2], transform=proj, cmap="BrBG", vmin=-ma, vmax=ma, add_colorbar=False)
    axes[2].set_title("2023 - 2019"); plt.colorbar(im3, ax=axes[2], shrink=0.7, label="delta NDVI", pad=0.02)

    fig.suptitle(f"{region_name}: NDVI (vegetation greenness)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    safe = region_name.lower().replace(" ", "_")
    fname = f"ndvi_{safe}.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")

    mean_diff = float(diff_c.mean(skipna=True))
    print(f"  {region_name} mean NDVI change: {mean_diff:+.4f}")


# ===========================================================================
# Figure 2: Key analysis — NDVI change in FORESTED areas only
# ===========================================================================
print("\n--- NDVI change in forested areas (NDVI > 0.6 in 2019) ---")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

for i, (region_name, bounds) in enumerate([("Eastern Amazon", WIDE_AMAZON),
                                             ("Congo Basin", CONGO)]):
    ax = axes[i]

    d19 = subset(ndvi_2019, bounds["lat"], bounds["lon"])
    d23 = subset(ndvi_2023, bounds["lat"], bounds["lon"])
    diff = d23 - d19

    # Coarsen to 1 degree to match CERES
    d19_1deg = d19.coarsen(lat=20, lon=20, boundary="trim").mean()
    d23_1deg = d23.coarsen(lat=20, lon=20, boundary="trim").mean()
    diff_1deg = d23_1deg - d19_1deg

    # Classify by 2019 forest status
    forest_mask = d19_1deg > 0.6  # dense forest in 2019
    nonforest_mask = (d19_1deg > 0.2) & (d19_1deg <= 0.6)  # savanna/degraded

    forest_diff = diff_1deg.where(forest_mask).values.ravel()
    nonforest_diff = diff_1deg.where(nonforest_mask).values.ravel()

    forest_v = forest_diff[~np.isnan(forest_diff)]
    nonforest_v = nonforest_diff[~np.isnan(nonforest_diff)]

    # Histogram
    bins = np.arange(-0.08, 0.08, 0.005)
    ax.hist(forest_v, bins=bins, alpha=0.7, color="#2a9d8f", label=f"Forest (NDVI>0.6, n={len(forest_v)})", density=True)
    ax.hist(nonforest_v, bins=bins, alpha=0.5, color="#e9c46a", label=f"Non-forest (0.2-0.6, n={len(nonforest_v)})", density=True)

    ax.axvline(0, color="black", linewidth=0.5)
    ax.axvline(np.mean(forest_v), color="#2a9d8f", linewidth=2, linestyle="--",
               label=f"Forest mean: {np.mean(forest_v):+.4f}")
    if len(nonforest_v) > 0:
        ax.axvline(np.mean(nonforest_v), color="#e9c46a", linewidth=2, linestyle="--",
                   label=f"Non-forest mean: {np.mean(nonforest_v):+.4f}")

    ax.set_title(region_name, fontsize=12, fontweight="bold")
    ax.set_xlabel("NDVI change (2023 - 2019)")
    ax.set_ylabel("Density")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)

    # Statistics
    print(f"\n  {region_name}:")
    print(f"    Forest cells (NDVI>0.6):     n={len(forest_v)}, mean change={np.mean(forest_v):+.4f}")
    if len(nonforest_v) > 0:
        print(f"    Non-forest (0.2-0.6):        n={len(nonforest_v)}, mean change={np.mean(nonforest_v):+.4f}")
    pct_neg = 100 * np.sum(forest_v < 0) / len(forest_v)
    print(f"    Forest cells with NDVI decline: {pct_neg:.1f}%")

    # T-test: is forest NDVI change significantly different from zero?
    t_stat, p_val = stats.ttest_1samp(forest_v, 0)
    print(f"    T-test (forest change != 0): t={t_stat:.3f}, p={p_val:.6f}")

fig.suptitle("NDVI Change in Forested vs Non-Forested Areas\n"
             "If forests that remained green (NDVI>0.6 in 2019) still show NDVI decline,\n"
             "the ET drop is drought-driven, not deforestation",
             fontsize=12, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "ndvi_forest_vs_nonforest.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nSaved: ndvi_forest_vs_nonforest.png")

# ===========================================================================
# Figure 3: NDVI change vs ET change scatter (wide Amazon)
# ===========================================================================
print("\n--- NDVI vs ET scatter ---")

from src.modis_et import process_region_year

et_19 = process_region_year("data/modis_et", "Amazon", 2019,
                              WIDE_AMAZON["lat"], WIDE_AMAZON["lon"], resolution=1.0)
et_23 = process_region_year("data/modis_et", "Amazon", 2023,
                              WIDE_AMAZON["lat"], WIDE_AMAZON["lon"], resolution=1.0)
et_diff = et_23 - et_19

# NDVI at 1-degree
ndvi_d19 = subset(ndvi_2019, WIDE_AMAZON["lat"], WIDE_AMAZON["lon"]).coarsen(lat=20, lon=20, boundary="trim").mean()
ndvi_d23 = subset(ndvi_2023, WIDE_AMAZON["lat"], WIDE_AMAZON["lon"]).coarsen(lat=20, lon=20, boundary="trim").mean()
ndvi_diff = ndvi_d23 - ndvi_d19

# Align grids
ndvi_on_et = ndvi_diff.interp(lat=et_diff.lat, lon=et_diff.lon, method="nearest")

n_flat = ndvi_on_et.values.ravel()
e_flat = et_diff.values.ravel()
valid = ~np.isnan(n_flat) & ~np.isnan(e_flat)

fig, ax = plt.subplots(figsize=(8, 7))
ax.scatter(n_flat[valid], e_flat[valid], s=40, c="#264653", alpha=0.6,
           edgecolors="black", linewidth=0.2)

slope, intercept, r_val, p_val, _ = stats.linregress(n_flat[valid], e_flat[valid])
x_line = np.linspace(n_flat[valid].min(), n_flat[valid].max(), 100)
ax.plot(x_line, slope * x_line + intercept, "r--", linewidth=2,
        label=f"r = {r_val:.3f}, p = {p_val:.4f}, n = {valid.sum()}")

ax.axhline(0, color="gray", linewidth=0.5)
ax.axvline(0, color="gray", linewidth=0.5)
ax.set_xlabel("NDVI change (2023 - 2019)", fontsize=11)
ax.set_ylabel("ET change (mm/yr)", fontsize=11)
ax.set_title("NDVI vs ET Change: Eastern Amazon\n"
             "Positive correlation = greenness and ET co-vary (drought signal)",
             fontsize=11, fontweight="bold")
ax.legend(fontsize=10)
ax.grid(alpha=0.2)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "ndvi_vs_et_scatter.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: ndvi_vs_et_scatter.png")
print(f"  r = {r_val:.4f}, p = {p_val:.6f}")

print("\n=== DONE ===")

"""Wider Amazon analysis region.

Expand from the small Maraba box (4x5 deg, 20 CERES cells) to the
full eastern Amazon (10S-2N, 65W-45W) — roughly 240 CERES cells.

This gives proper statistical power for the scatter plot and allows
us to see the full spatial structure of the biotic pump breakdown.
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
from scipy import stats
from pathlib import Path
from src.processing import load_ceres, subset_region, annual_mean, cloud_radiative_effect
from src.modis_et import process_region_year

OUTPUT_DIR = Path("outputs")

# Wider region
WIDE_AMAZON = {"name": "Eastern Amazon", "lat": (-10.0, 2.0), "lon": (-65.0, -45.0)}

# ===========================================================================
# Load CERES
# ===========================================================================
print("Loading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

olr_2019 = annual_mean(ceres, "toa_lw_all_mon", 2019)
olr_2023 = annual_mean(ceres, "toa_lw_all_mon", 2023)
cld_2019 = annual_mean(ceres, "cldarea_total_daynight_mon", 2019)
cld_2023 = annual_mean(ceres, "cldarea_total_daynight_mon", 2023)
cre_2019 = ceres["cre_lw"].sel(time=slice("2019","2019")).mean(dim="time")
cre_2023 = ceres["cre_lw"].sel(time=slice("2023","2023")).mean(dim="time")

lat_r = WIDE_AMAZON["lat"]
lon_r = WIDE_AMAZON["lon"]

# ===========================================================================
# Figure 1: Wide Amazon comparison maps (OLR, Cloud, CRE)
# ===========================================================================
print("\n--- Wide Amazon comparison maps ---")

for var_2019, var_2023, label, units, cmap in [
    (olr_2019, olr_2023, "OLR", "W/m2", "inferno"),
    (cld_2019, cld_2023, "Cloud Fraction", "%", "YlGnBu"),
    (cre_2019, cre_2023, "LW Cloud Radiative Effect", "W/m2", "YlGnBu"),
]:
    d19 = subset_region(var_2019, lat_r, lon_r)
    d23 = subset_region(var_2023, lat_r, lon_r)
    diff = d23 - d19

    proj = ccrs.PlateCarree()
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), subplot_kw={"projection": proj})
    vmin = float(min(d19.min(), d23.min()))
    vmax = float(max(d19.max(), d23.max()))

    for ax in axes:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
        ax.add_feature(cfeature.RIVERS, linewidth=0.4, alpha=0.6, color="#4a90d9")
        # Draw corridor
        ax.plot([-48.5, -60], [-1.4, -3.1], "k--", linewidth=2, alpha=0.5, transform=proj)
        for nm, (lt, ln) in [("Belem",(-1.4,-48.5)),("Maraba",(-5.4,-49.1)),("Manaus",(-3.1,-60))]:
            ax.plot(ln, lt, "ko", markersize=4, transform=proj)
            ax.text(ln+0.5, lt+0.3, nm, fontsize=7, transform=proj)

    im1 = d19.plot(ax=axes[0], transform=proj, cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[0].set_title("2019"); plt.colorbar(im1, ax=axes[0], shrink=0.7, label=units, pad=0.02)
    im2 = d23.plot(ax=axes[1], transform=proj, cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[1].set_title("2023"); plt.colorbar(im2, ax=axes[1], shrink=0.7, label=units, pad=0.02)
    ma = float(max(abs(diff.min()), abs(diff.max()))) or 1
    im3 = diff.plot(ax=axes[2], transform=proj, cmap="RdBu_r", vmin=-ma, vmax=ma, add_colorbar=False)
    axes[2].set_title("2023 - 2019"); plt.colorbar(im3, ax=axes[2], shrink=0.7, label=f"delta {units}", pad=0.02)

    safe = label.lower().replace(" ", "_")
    fig.suptitle(f"Eastern Amazon (10S-2N, 65W-45W): {label}", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    fname = f"wide_amazon_{safe}.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")

    # Regional stats
    mean_diff = float(diff.mean())
    n_cells = int((~diff.isnull()).sum())
    print(f"  {label}: mean change = {mean_diff:+.2f} {units}, {n_cells} grid cells")


# ===========================================================================
# Figure 2: MODIS ET for the wider region
# ===========================================================================
print("\n--- Wide Amazon MODIS ET ---")
print("  Processing ET at 1-degree resolution (this uses all downloaded tiles)...")

et_wide_2019 = process_region_year("data/modis_et", "Eastern Amazon", 2019,
                                     lat_r, lon_r, resolution=1.0)
et_wide_2023 = process_region_year("data/modis_et", "Eastern Amazon", 2023,
                                     lat_r, lon_r, resolution=1.0)
et_diff = et_wide_2023 - et_wide_2019

print(f"  ET 2019 mean: {float(et_wide_2019.mean(skipna=True)):.1f} mm/yr")
print(f"  ET 2023 mean: {float(et_wide_2023.mean(skipna=True)):.1f} mm/yr")
print(f"  ET change: {float(et_diff.mean(skipna=True)):+.1f} mm/yr")


# ===========================================================================
# Figure 3: ET vs OLR scatter — wider region (more grid cells)
# ===========================================================================
print("\n--- ET vs OLR scatter (wide region) ---")

olr_diff = subset_region(olr_2023 - olr_2019, lat_r, lon_r)
cld_diff = subset_region(cld_2023 - cld_2019, lat_r, lon_r)
cre_diff = subset_region(cre_2023 - cre_2019, lat_r, lon_r)

# Interpolate ET to CERES grid
et_on_ceres = et_diff.interp(lat=olr_diff.lat, lon=olr_diff.lon, method="nearest")

# Flatten
et_flat = et_on_ceres.values.ravel()
olr_flat = olr_diff.values.ravel()
cld_flat = cld_diff.values.ravel()
cre_flat = cre_diff.values.ravel()

valid = ~np.isnan(et_flat) & ~np.isnan(olr_flat) & ~np.isnan(cld_flat)
print(f"  Valid grid cells: {valid.sum()}")

et_v = et_flat[valid]
olr_v = olr_flat[valid]
cld_v = cld_flat[valid]
cre_v = cre_flat[valid]

# Three-panel scatter
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

scatter_pairs = [
    (olr_v, "OLR change (W/m2)", "RdBu_r"),
    (cld_v, "Cloud fraction change (%)", "BrBG"),
    (cre_v, "CRE change (W/m2)", "BrBG"),
]

for i, (y_data, ylabel, cmap) in enumerate(scatter_pairs):
    ax = axes[i]
    valid2 = ~np.isnan(y_data)
    et_vv = et_v[valid2]
    y_vv = y_data[valid2]

    sc = ax.scatter(et_vv, y_vv, c=cld_v[valid2], cmap="RdYlBu",
                     s=40, edgecolors="black", linewidth=0.2, alpha=0.7,
                     vmin=-8, vmax=8)

    slope, intercept, r_val, p_val, _ = stats.linregress(et_vv, y_vv)
    x_line = np.linspace(et_vv.min(), et_vv.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, "k--", linewidth=2,
            label=f"r = {r_val:.3f}, p = {p_val:.4f}\nn = {len(et_vv)}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.axvline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("ET change (mm/yr)", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.2)

    # Quadrant analysis
    if "OLR" in ylabel:
        pump_fail = np.sum((et_vv < 0) & (y_vv > 0))
        pump_work = np.sum((et_vv > 0) & (y_vv < 0))
    else:
        pump_fail = np.sum((et_vv < 0) & (y_vv < 0))
        pump_work = np.sum((et_vv > 0) & (y_vv > 0))
    total = len(et_vv)
    ax.set_title(f"ET vs {ylabel.split('(')[0].strip()}\n"
                 f"Predicted quadrant: {pump_fail}/{total} ({100*pump_fail/total:.0f}%)",
                 fontsize=10, fontweight="bold")

    print(f"  ET vs {ylabel.split('(')[0].strip()}: r={r_val:.4f}, p={p_val:.4f}, n={len(et_vv)}")

plt.colorbar(sc, ax=axes, label="Cloud fraction change (%)", shrink=0.8,
             orientation="horizontal", pad=0.12, aspect=40)

fig.suptitle("Eastern Amazon (10S-2N, 65W-45W): ET vs Atmospheric Response\n"
             "Each point = 1-degree grid cell | Color = cloud change",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "wide_amazon_scatter.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: wide_amazon_scatter.png")

print("\n=== DONE ===")

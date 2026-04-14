"""ET vs OLR spatial scatter — the mechanistic link.

For each grid cell in the focal regions, plot:
  x = change in ET (2023 - 2019)
  y = change in OLR (2023 - 2019)

If the biotic pump mechanism is real, we expect a strong negative
correlation: where ET drops, OLR rises (less condensation -> less
cloud -> more longwave escaping).

This requires regridding MODIS ET (0.05 deg) to CERES resolution (1 deg)
so the pixels align.
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
from pathlib import Path
from scipy import stats

from src.processing import load_ceres, subset_region, annual_mean, cloud_radiative_effect
from src.modis_et import process_region_year

OUTPUT_DIR = Path("outputs")

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

# ===========================================================================
# Load MODIS ET (already processed)
# ===========================================================================
print("Processing MODIS ET...")
regions = {
    "maraba": {"name": "Maraba, Amazon", "lat": (-7.0, -3.0), "lon": (-52.0, -47.0)},
    "congo":  {"name": "Congo Basin",    "lat": (-5.0, 5.0),   "lon": (15.0, 30.0)},
}

et_data = {}
for key, r in regions.items():
    for year in [2019, 2023]:
        # Process at 1-degree resolution to match CERES
        et_data[(key, year)] = process_region_year(
            "data/modis_et", r["name"], year, r["lat"], r["lon"],
            resolution=1.0  # match CERES 1-degree grid
        )


def lat_slice(da, lr):
    lo, hi = min(lr), max(lr)
    return slice(hi, lo) if da.lat[0] > da.lat[-1] else slice(lo, hi)


# ===========================================================================
# Build scatter data for each region
# ===========================================================================
print("\n=== Building ET vs OLR scatter data ===\n")

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

for idx, (key, r) in enumerate(regions.items()):
    ax = axes[idx]

    # ET difference
    et_diff = et_data[(key, 2023)] - et_data[(key, 2019)]

    # CERES differences — subset to region
    lat_r, lon_r = r["lat"], r["lon"]
    olr_diff = subset_region(olr_2023 - olr_2019, lat_r, lon_r)
    cld_diff = subset_region(cld_2023 - cld_2019, lat_r, lon_r)
    cre_diff = subset_region(cre_2023 - cre_2019, lat_r, lon_r)

    # Align grids — interpolate ET to CERES grid
    et_on_ceres = et_diff.interp(lat=olr_diff.lat, lon=olr_diff.lon, method="nearest")

    # Flatten and remove NaN
    et_flat = et_on_ceres.values.ravel()
    olr_flat = olr_diff.values.ravel()
    cld_flat = cld_diff.values.ravel()

    valid = ~np.isnan(et_flat) & ~np.isnan(olr_flat)
    et_v = et_flat[valid]
    olr_v = olr_flat[valid]
    cld_v = cld_flat[valid]

    print(f"{r['name']}: {valid.sum()} valid grid cells")

    if valid.sum() < 3:
        ax.text(0.5, 0.5, "Insufficient data", transform=ax.transAxes,
                ha="center", fontsize=14)
        continue

    # Scatter: ET change vs OLR change
    sc = ax.scatter(et_v, olr_v, c=cld_v, cmap="RdYlBu", s=80,
                     edgecolors="black", linewidth=0.3, alpha=0.8,
                     vmin=-8, vmax=8)
    plt.colorbar(sc, ax=ax, label="Cloud fraction change (%)", shrink=0.8)

    # Linear regression
    slope, intercept, r_val, p_val, std_err = stats.linregress(et_v, olr_v)
    x_line = np.linspace(et_v.min(), et_v.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, "k--", linewidth=2,
            label=f"r = {r_val:.3f}, p = {p_val:.4f}\nslope = {slope:.4f}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.axvline(0, color="gray", linewidth=0.5, alpha=0.5)

    ax.set_xlabel("ET change (mm/yr)", fontsize=11)
    ax.set_ylabel("OLR change (W/m2)", fontsize=11)
    ax.set_title(f"{r['name']}", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.2)

    # Annotate quadrants
    ax.text(0.02, 0.98, "ET up, OLR up\n(unexpected)", transform=ax.transAxes,
            fontsize=7, color="#888", va="top", ha="left")
    ax.text(0.98, 0.98, "ET down, OLR up\n(pump failure)", transform=ax.transAxes,
            fontsize=7, color="#e63946", va="top", ha="right", fontweight="bold")
    ax.text(0.02, 0.02, "ET up, OLR down\n(pump working)", transform=ax.transAxes,
            fontsize=7, color="#2a9d8f", va="bottom", ha="left", fontweight="bold")
    ax.text(0.98, 0.02, "ET down, OLR down\n(unexpected)", transform=ax.transAxes,
            fontsize=7, color="#888", va="bottom", ha="right")

    # Print stats
    print(f"  Correlation: r = {r_val:.4f}")
    print(f"  P-value: {p_val:.6f}")
    print(f"  Slope: {slope:.4f} W/m2 per mm/yr ET change")
    print(f"  Points in 'pump failure' quadrant (ET<0, OLR>0): "
          f"{np.sum((et_v < 0) & (olr_v > 0))}/{len(et_v)} "
          f"({100*np.sum((et_v < 0) & (olr_v > 0))/len(et_v):.0f}%)")
    print()


fig.suptitle("ET vs OLR Change (2023 - 2019) at 1-degree Resolution\n"
             "Each point = one grid cell | Color = cloud fraction change\n"
             "Negative correlation = biotic pump mechanism",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "et_olr_scatter.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: et_olr_scatter.png")


# ===========================================================================
# Also: ET vs Cloud, and ET vs CRE scatters for Maraba
# ===========================================================================
print("\n--- Additional scatter plots (Maraba only) ---")

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

key = "maraba"
r = regions[key]
et_diff = et_data[(key, 2023)] - et_data[(key, 2019)]
lat_r, lon_r = r["lat"], r["lon"]

pairs = [
    ("toa_lw_all_mon", "OLR change (W/m2)", "RdBu_r"),
    ("cldarea_total_daynight_mon", "Cloud fraction change (%)", "BrBG"),
    ("cre_lw", "CRE change (W/m2)", "BrBG"),
]

for i, (var, ylabel, cmap) in enumerate(pairs):
    ax = axes[i]

    if var == "cre_lw":
        v_2019 = cre_2019
        v_2023 = cre_2023
    else:
        v_2019 = ceres[var].sel(time=slice("2019","2019")).mean(dim="time")
        v_2023 = ceres[var].sel(time=slice("2023","2023")).mean(dim="time")

    v_diff = subset_region(v_2023 - v_2019, lat_r, lon_r)
    et_on_grid = et_diff.interp(lat=v_diff.lat, lon=v_diff.lon, method="nearest")

    et_f = et_on_grid.values.ravel()
    v_f = v_diff.values.ravel()
    valid = ~np.isnan(et_f) & ~np.isnan(v_f)

    if valid.sum() < 3:
        continue

    et_fv = et_f[valid]
    v_fv = v_f[valid]

    ax.scatter(et_fv, v_fv, s=80, c="#264653", alpha=0.7, edgecolors="black", linewidth=0.3)

    slope, intercept, r_val, p_val, std_err = stats.linregress(et_fv, v_fv)
    x_line = np.linspace(et_fv.min(), et_fv.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, "r--", linewidth=2,
            label=f"r = {r_val:.3f}, p = {p_val:.4f}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.axvline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("ET change (mm/yr)", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.2)

    var_label = ylabel.split("(")[0].strip()
    ax.set_title(f"ET vs {var_label}", fontsize=11, fontweight="bold")
    print(f"  ET vs {var_label}: r={r_val:.4f}, p={p_val:.6f}")

fig.suptitle("Maraba, Amazon: ET Change vs Atmospheric Response (per grid cell)\n"
             "Testing the mechanistic chain: ET down -> clouds thin -> OLR up -> CRE down",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "et_scatter_trio.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: et_scatter_trio.png")

print("\n=== DONE ===")

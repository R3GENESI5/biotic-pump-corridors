"""Multi-year corridor time series (2001-2025).

Shows how the Belem-Manaus corridor has evolved over 25 years.
Key question: Is 2023 an isolated event, or part of a degrading trend?
"""
import sys
sys.path.insert(0, ".")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pathlib import Path
from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

LAT_BAND = (-6.0, 0.0)
SEGMENTS = {
    "Coast (Belem)": slice(-50, -47),
    "Mid (Maraba-Altamira)": slice(-53, -49),
    "Interior (Manaus)": slice(-62, -58),
}
SEGMENT_COLORS = {
    "Coast (Belem)": "#2a9d8f",
    "Mid (Maraba-Altamira)": "#e9c46a",
    "Interior (Manaus)": "#e76f51",
}

HIGHLIGHT_YEARS = [2005, 2010, 2015, 2016, 2019, 2023]
# 2005, 2010, 2015-16: known Amazon drought years


def lat_slice(da, lat_range):
    lo, hi = min(lat_range), max(lat_range)
    if da.lat[0] > da.lat[-1]:
        return slice(hi, lo)
    return slice(lo, hi)


# ===========================================================================
# Load CERES
# ===========================================================================
print("Loading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

VARIABLES = {
    "toa_lw_all_mon": {"label": "OLR", "units": "W/m2"},
    "cldarea_total_daynight_mon": {"label": "Cloud Fraction", "units": "%"},
    "cre_lw": {"label": "LW Cloud Radiative Effect", "units": "W/m2"},
}

# Determine year range
years = sorted(set(ceres.time.dt.year.values))
# Only use complete years
years = [y for y in years if y >= 2001 and y <= 2025]
print(f"Year range: {years[0]}-{years[-1]} ({len(years)} years)")


# ===========================================================================
# Figure 1: Annual mean time series per segment
# ===========================================================================
print("\n--- Multi-year segment time series ---")

fig, axes = plt.subplots(len(VARIABLES), 1, figsize=(16, 4 * len(VARIABLES)), sharex=True)

for i, (var, info) in enumerate(VARIABLES.items()):
    ax = axes[i]

    for seg_name, lon_slice in SEGMENTS.items():
        color = SEGMENT_COLORS[seg_name]
        annual_vals = []

        for year in years:
            data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
            segment = data.sel(lat=lat_slice(data, LAT_BAND), lon=lon_slice)
            weights = np.cos(np.deg2rad(segment.lat))
            val = float(segment.weighted(weights).mean(dim=["lat", "lon"]).mean(dim="time"))
            annual_vals.append(val)

        ax.plot(years, annual_vals, "o-", color=color, linewidth=1.5,
                markersize=3, label=seg_name)

    # Highlight drought years
    for year in HIGHLIGHT_YEARS:
        if year in years:
            ax.axvline(year, color="gray", alpha=0.2, linewidth=1)
            if i == 0:
                ax.text(year, ax.get_ylim()[1], str(year), fontsize=7,
                        ha="center", va="bottom", color="#888", rotation=45)

    ax.set_title(info["label"], fontsize=12)
    ax.set_ylabel(info["units"])
    ax.legend(fontsize=9, loc="best")
    ax.grid(alpha=0.3)

axes[-1].set_xlabel("Year")
fig.suptitle("Belem-Manaus Corridor: Annual Mean Time Series (2001-2025)\n"
             "Gray lines mark known Amazon drought years",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_multiyear_timeseries.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_multiyear_timeseries.png")


# ===========================================================================
# Figure 2: Coast-to-interior gradient over time
# ===========================================================================
print("\n--- Gradient evolution ---")

fig, axes = plt.subplots(len(VARIABLES), 1, figsize=(16, 4 * len(VARIABLES)), sharex=True)

for i, (var, info) in enumerate(VARIABLES.items()):
    ax = axes[i]

    coast_vals = []
    interior_vals = []
    gradient_vals = []

    for year in years:
        data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
        lat_sl = lat_slice(data, LAT_BAND)

        coast = data.sel(lat=lat_sl, lon=SEGMENTS["Coast (Belem)"])
        wc = np.cos(np.deg2rad(coast.lat))
        c_val = float(coast.weighted(wc).mean(dim=["lat", "lon"]).mean(dim="time"))

        interior = data.sel(lat=lat_sl, lon=SEGMENTS["Interior (Manaus)"])
        wi = np.cos(np.deg2rad(interior.lat))
        i_val = float(interior.weighted(wi).mean(dim=["lat", "lon"]).mean(dim="time"))

        coast_vals.append(c_val)
        interior_vals.append(i_val)
        gradient_vals.append(i_val - c_val)

    gradient_vals = np.array(gradient_vals)

    # Bar chart with color coding
    colors = ["#e63946" if g > np.mean(gradient_vals) else "#457b9d" for g in gradient_vals]
    if "cld" in var or "cre" in var:
        # For cloud/CRE, flip interpretation (lower = worse)
        colors = ["#e63946" if g < np.mean(gradient_vals) else "#457b9d" for g in gradient_vals]

    ax.bar(years, gradient_vals, color=colors, alpha=0.7, edgecolor="white", linewidth=0.3)

    # Add trend line
    z = np.polyfit(years, gradient_vals, 1)
    trend = np.poly1d(z)
    ax.plot(years, trend(years), "k--", linewidth=1.5,
            label=f"Trend: {z[0]:+.3f}/yr")

    # Highlight drought years
    for year in HIGHLIGHT_YEARS:
        if year in years:
            ax.axvline(year, color="gray", alpha=0.2, linewidth=1)

    ax.set_title(f"{info['label']}: Interior - Coast gradient", fontsize=11)
    ax.set_ylabel(f"Gradient ({info['units']})")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")

axes[-1].set_xlabel("Year")
fig.suptitle("Coast-to-Interior Gradient Along Corridor (2001-2025)\n"
             "How the moisture pump signal has changed over 25 years",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_gradient_evolution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_gradient_evolution.png")


# ===========================================================================
# Figure 3: SON-only (critical transition season) time series
# ===========================================================================
print("\n--- SON-only multi-year ---")

fig, axes = plt.subplots(len(VARIABLES), 1, figsize=(16, 4 * len(VARIABLES)), sharex=True)

for i, (var, info) in enumerate(VARIABLES.items()):
    ax = axes[i]

    for seg_name, lon_slice in SEGMENTS.items():
        color = SEGMENT_COLORS[seg_name]
        son_vals = []

        for year in years:
            son = ceres[var].sel(time=slice(f"{year}-09-01", f"{year}-11-30"))
            if len(son.time) == 0:
                son_vals.append(np.nan)
                continue
            segment = son.sel(lat=lat_slice(son, LAT_BAND), lon=lon_slice)
            weights = np.cos(np.deg2rad(segment.lat))
            val = float(segment.weighted(weights).mean(dim=["lat", "lon"]).mean(dim="time"))
            son_vals.append(val)

        ax.plot(years, son_vals, "o-", color=color, linewidth=1.5,
                markersize=4, label=seg_name)

    for year in HIGHLIGHT_YEARS:
        if year in years:
            ax.axvline(year, color="gray", alpha=0.2, linewidth=1)

    ax.set_title(f"{info['label']} — SON only (dry-to-wet transition)", fontsize=11)
    ax.set_ylabel(info["units"])
    ax.legend(fontsize=9, loc="best")
    ax.grid(alpha=0.3)

axes[-1].set_xlabel("Year")
fig.suptitle("SON (Sept-Nov) Along Corridor: 2001-2025\n"
             "The critical season when the biotic pump should initiate the wet season",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_SON_multiyear.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_SON_multiyear.png")


# ===========================================================================
# Summary: key years
# ===========================================================================
print("\n=== KEY YEAR COMPARISON ===\n")
print(f"{'Variable':20s} {'Segment':25s}", end="")
for y in HIGHLIGHT_YEARS:
    print(f" {y:>8d}", end="")
print()
print("-" * (50 + 9 * len(HIGHLIGHT_YEARS)))

for var, info in VARIABLES.items():
    for seg_name, lon_slice in SEGMENTS.items():
        print(f"{info['label']:20s} {seg_name:25s}", end="")
        for year in HIGHLIGHT_YEARS:
            data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
            segment = data.sel(lat=lat_slice(data, LAT_BAND), lon=lon_slice)
            weights = np.cos(np.deg2rad(segment.lat))
            val = float(segment.weighted(weights).mean(dim=["lat", "lon"]).mean(dim="time"))
            print(f" {val:8.1f}", end="")
        print()
    print()

print("=== DONE ===")

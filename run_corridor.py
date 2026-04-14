"""Belem-Maraba-Manaus corridor analysis.

Tests whether the biotic pump moisture corridor from the Atlantic coast
to the interior Amazon is visible in CERES data, and whether it weakened
in 2023 compared to 2019.
"""
import sys
sys.path.insert(0, ".")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Corridor definition ---
LANDMARKS = {
    "Belem": (-1.4, -48.5),
    "Maraba": (-5.4, -49.1),
    "Tucurui": (-3.8, -49.7),
    "Altamira": (-3.2, -52.2),
    "Itaituba": (-4.3, -55.9),
    "Manaus": (-3.1, -60.0),
}

LAT_BAND = (-6.0, 0.0)
LON_RANGE = (-62.0, -47.0)

# --- Load CERES ---
print("Loading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

VARIABLES = {
    "toa_lw_all_mon": {"label": "Outgoing Longwave Radiation", "units": "W/m2"},
    "cldarea_total_daynight_mon": {"label": "Cloud Area Fraction", "units": "%"},
    "cre_lw": {"label": "LW Cloud Radiative Effect", "units": "W/m2"},
}

# Helper to select latitude correctly
def lat_slice(da, lat_range):
    lo, hi = min(lat_range), max(lat_range)
    if da.lat[0] > da.lat[-1]:
        return slice(hi, lo)
    return slice(lo, hi)


# ===========================================================================
# Figure 1: Longitude transects averaged over latitude band
# ===========================================================================
print("\n--- Corridor transects ---")
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

for i, (var, info) in enumerate(VARIABLES.items()):
    ax = axes[i]
    for year, color in [(2019, "#264653"), (2023, "#e63946")]:
        data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31")).mean(dim="time")
        corridor = data.sel(lat=lat_slice(data, LAT_BAND),
                            lon=slice(LON_RANGE[0], LON_RANGE[1]))
        weights = np.cos(np.deg2rad(corridor.lat))
        transect = corridor.weighted(weights).mean(dim="lat")
        transect.plot(ax=ax, color=color, linewidth=2, label=str(year))

    for name, (lat, lon) in LANDMARKS.items():
        if LON_RANGE[0] <= lon <= LON_RANGE[1]:
            ax.axvline(lon, color="gray", alpha=0.3, linewidth=0.8)
            if i == 0:
                ax.text(lon, ax.get_ylim()[1], f" {name}", rotation=45,
                        fontsize=8, ha="left", va="bottom", color="#555")

    ax.set_title(info["label"], fontsize=12)
    ax.set_ylabel(info["units"])
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_xlabel("")

axes[-1].set_xlabel("Longitude")
axes[-1].annotate("Coast (Belem) -->", xy=(-48.5, 0), xycoords=("data", "axes fraction"),
                  fontsize=9, color="#555")
axes[-1].annotate("<-- Interior (Manaus)", xy=(-61, 0), xycoords=("data", "axes fraction"),
                  fontsize=9, color="#555")

fig.suptitle("Belem - Maraba - Manaus Moisture Corridor\n"
             "Latitude band 6S-0N | CERES EBAF-TOA Ed4.2.1",
             fontsize=14, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_transects.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_transects.png")


# ===========================================================================
# Figure 2: Spatial maps along corridor (OLR, Clouds, CRE)
# ===========================================================================
print("\n--- Corridor spatial maps ---")

MAP_LAT = (-8, 2)
MAP_LON = (-63, -44)

for var, info in VARIABLES.items():
    d19 = ceres[var].sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
    d23 = ceres[var].sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")

    d19 = d19.sel(lat=lat_slice(d19, MAP_LAT), lon=slice(MAP_LON[0], MAP_LON[1]))
    d23 = d23.sel(lat=lat_slice(d23, MAP_LAT), lon=slice(MAP_LON[0], MAP_LON[1]))
    diff = d23 - d19

    proj = ccrs.PlateCarree()
    fig, axes = plt.subplots(1, 3, figsize=(20, 5), subplot_kw={"projection": proj})

    vmin = float(min(d19.min(), d23.min()))
    vmax = float(max(d19.max(), d23.max()))

    # Choose colormap
    if "cld" in var:
        cmap = "YlGnBu"
    elif "cre" in var:
        cmap = "YlGnBu"
    else:
        cmap = "inferno"

    for ax in axes:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
        ax.add_feature(cfeature.RIVERS, linewidth=0.4, alpha=0.6, color="#4a90d9")
        # Draw corridor path
        lons_path = [v[1] for v in LANDMARKS.values()]
        lats_path = [v[0] for v in LANDMARKS.values()]
        ax.plot(lons_path, lats_path, "k--", linewidth=1.5, alpha=0.6, transform=proj)
        # Mark cities
        for name, (lt, ln) in LANDMARKS.items():
            if name in ["Belem", "Maraba", "Manaus"]:
                ax.plot(ln, lt, "ko", markersize=5, transform=proj)
                ax.text(ln + 0.3, lt + 0.3, name, fontsize=8, transform=proj,
                        fontweight="bold")

    im1 = d19.plot(ax=axes[0], transform=proj, cmap=cmap,
                   vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[0].set_title("2019", fontsize=12)
    plt.colorbar(im1, ax=axes[0], shrink=0.7, label=info["units"], pad=0.02)

    im2 = d23.plot(ax=axes[1], transform=proj, cmap=cmap,
                   vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[1].set_title("2023", fontsize=12)
    plt.colorbar(im2, ax=axes[1], shrink=0.7, label=info["units"], pad=0.02)

    max_abs = float(max(abs(diff.min()), abs(diff.max())))
    if max_abs == 0:
        max_abs = 1
    im3 = diff.plot(ax=axes[2], transform=proj, cmap="RdBu_r",
                    vmin=-max_abs, vmax=max_abs, add_colorbar=False)
    axes[2].set_title("2023 - 2019", fontsize=12)
    plt.colorbar(im3, ax=axes[2], shrink=0.7, label=f"delta {info['units']}", pad=0.02)

    fig.suptitle(f"Belem-Manaus Corridor: {info['label']}",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()

    safe = var.replace("_mon", "").replace("_total_daynight", "")
    fname = f"corridor_map_{safe}.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")


# ===========================================================================
# Figure 3: Coast-to-interior gradient bar chart
# ===========================================================================
print("\n--- Coast-to-interior gradient ---")

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
lon_bins = np.arange(-62, -47, 1)
lon_centers = 0.5 * (lon_bins[:-1] + lon_bins[1:])
# Distance from Belem coast in km (negative lon = west = inland)
distance_km = ((-48.5) - lon_centers) * 111.0 * np.cos(np.deg2rad(3))

for i, (var, info) in enumerate(VARIABLES.items()):
    ax = axes[i]
    d19 = ceres[var].sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
    d23 = ceres[var].sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")

    d19_c = d19.sel(lat=lat_slice(d19, LAT_BAND))
    d23_c = d23.sel(lat=lat_slice(d23, LAT_BAND))

    diff_vals = []
    for j in range(len(lon_bins) - 1):
        s19 = d19_c.sel(lon=slice(lon_bins[j], lon_bins[j+1]))
        s23 = d23_c.sel(lon=slice(lon_bins[j], lon_bins[j+1]))
        w = np.cos(np.deg2rad(s19.lat))
        v19 = float(s19.weighted(w).mean())
        v23 = float(s23.weighted(w).mean())
        diff_vals.append(v23 - v19)

    diff_vals = np.array(diff_vals)
    colors = ["#e63946" if d > 0 else "#457b9d" for d in diff_vals]
    ax.bar(distance_km, diff_vals, width=distance_km[1] - distance_km[0],
           color=colors, alpha=0.8, edgecolor="white", linewidth=0.5)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel(f"delta {info['units']}")
    ax.set_title(f"{info['label']} change (2023 - 2019)", fontsize=11)
    ax.grid(alpha=0.3, axis="y")

    # Mark landmarks
    for name, (lt, ln) in LANDMARKS.items():
        if name in ["Belem", "Maraba", "Manaus"]:
            d = ((-48.5) - ln) * 111.0 * np.cos(np.deg2rad(3))
            ax.axvline(d, color="gray", alpha=0.4, linewidth=0.8)
            if i == 0:
                ax.text(d, ax.get_ylim()[1] * 0.85, f" {name}", fontsize=9, color="#555")

axes[-1].set_xlabel("Distance inland from Atlantic coast (km)")
fig.suptitle("How Satellite Signals Change Along the Belem-Manaus Corridor\n"
             "2023 vs 2019 | Positive OLR = more heat escaping | Negative cloud = fewer clouds",
             fontsize=12, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "corridor_gradient_bars.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: corridor_gradient_bars.png")


# ===========================================================================
# Summary numbers
# ===========================================================================
print("\n=== CORRIDOR SUMMARY ===\n")

for var, info in VARIABLES.items():
    d19 = ceres[var].sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
    d23 = ceres[var].sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")

    # Coastal strip (near Belem)
    coast_19 = float(d19.sel(lat=lat_slice(d19, LAT_BAND), lon=slice(-50, -47)).mean())
    coast_23 = float(d23.sel(lat=lat_slice(d23, LAT_BAND), lon=slice(-50, -47)).mean())

    # Mid-corridor (Maraba-Altamira)
    mid_19 = float(d19.sel(lat=lat_slice(d19, LAT_BAND), lon=slice(-53, -49)).mean())
    mid_23 = float(d23.sel(lat=lat_slice(d23, LAT_BAND), lon=slice(-53, -49)).mean())

    # Interior (near Manaus)
    int_19 = float(d19.sel(lat=lat_slice(d19, LAT_BAND), lon=slice(-62, -58)).mean())
    int_23 = float(d23.sel(lat=lat_slice(d23, LAT_BAND), lon=slice(-62, -58)).mean())

    print(f"{info['label']}:")
    print(f"  Coast (Belem area):     2019={coast_19:.1f}  2023={coast_23:.1f}  delta={coast_23-coast_19:+.2f}")
    print(f"  Mid (Maraba-Altamira):  2019={mid_19:.1f}  2023={mid_23:.1f}  delta={mid_23-mid_19:+.2f}")
    print(f"  Interior (Manaus area): 2019={int_19:.1f}  2023={int_23:.1f}  delta={int_23-int_19:+.2f}")
    grad_19 = int_19 - coast_19
    grad_23 = int_23 - coast_23
    print(f"  Coast-to-interior gradient: 2019={grad_19:+.2f}  2023={grad_23:+.2f}  shift={grad_23-grad_19:+.2f}")
    print()

print("=== DONE ===")

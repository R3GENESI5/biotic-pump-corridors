"""Congo Basin corridor analysis.

The Congo's moisture corridor runs from the Gulf of Guinea coast
eastward into the interior basin. This is the second major tropical
forest biotic pump after the Amazon.

Corridor: roughly along the equator from the Atlantic coast (~9E)
through Douala/Yaounde, across the Congo Basin to Kisangani (~25E).
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
from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

# --- Congo corridor definition ---
LANDMARKS = {
    "Douala": (4.0, 9.7),
    "Yaounde": (3.9, 11.5),
    "Ouesso": (1.6, 16.0),
    "Mbandaka": (0.0, 18.3),
    "Kisangani": (0.5, 25.2),
}

LAT_BAND = (-3.0, 5.0)
LON_RANGE = (8.0, 28.0)

SEGMENTS = {
    "Coast (Gulf of Guinea)": slice(8, 12),
    "Mid (W. Congo)": slice(15, 20),
    "Interior (E. Congo)": slice(22, 27),
}
SEGMENT_COLORS = {
    "Coast (Gulf of Guinea)": "#2a9d8f",
    "Mid (W. Congo)": "#e9c46a",
    "Interior (E. Congo)": "#e76f51",
}

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

HIGHLIGHT_YEARS = [2005, 2010, 2015, 2016, 2019, 2023]

MAP_LAT = (-6, 8)
MAP_LON = (5, 30)


def lat_slice(da, lat_range):
    lo, hi = min(lat_range), max(lat_range)
    if da.lat[0] > da.lat[-1]:
        return slice(hi, lo)
    return slice(lo, hi)


def seasonal_mean(da, year, months):
    if 12 in months and 1 in months:
        dec = da.sel(time=slice(f"{year-1}-12-01", f"{year-1}-12-31"))
        jf = da.sel(time=slice(f"{year}-01-01", f"{year}-02-28"))
        return xr.concat([dec, jf], dim="time").mean(dim="time")
    else:
        start_m, end_m = min(months), max(months)
        return da.sel(time=slice(f"{year}-{start_m:02d}-01",
                                  f"{year}-{end_m:02d}-28")).mean(dim="time")


def corridor_transect(da, lat_band, lon_range):
    corridor = da.sel(lat=lat_slice(da, lat_band),
                      lon=slice(lon_range[0], lon_range[1]))
    weights = np.cos(np.deg2rad(corridor.lat))
    return corridor.weighted(weights).mean(dim="lat")


# --- AIRS reader ---
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
        times.append(np.datetime64(f"{year}-{da.attrs['month']:02d}-01"))
        monthly.append(da)
    ds = xr.concat(monthly, dim="time")
    ds["time"] = times
    return ds


# ===========================================================================
# Load data
# ===========================================================================
print("Loading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

print("Loading AIRS...")
airs_2019 = load_airs_year("data/airs", 2019)
airs_2023 = load_airs_year("data/airs", 2023)

CERES_VARS = {
    "toa_lw_all_mon": {"label": "OLR", "units": "W/m2"},
    "cldarea_total_daynight_mon": {"label": "Cloud Fraction", "units": "%"},
    "cre_lw": {"label": "LW Cloud Radiative Effect", "units": "W/m2"},
}

ALL_VARS = list(CERES_VARS.items()) + [
    ("airs_wv", {"label": "Column Water Vapor (AIRS)", "units": "kg/m2"})
]

years = [y for y in sorted(set(ceres.time.dt.year.values)) if 2001 <= y <= 2025]

# ===========================================================================
# 1. Corridor transects 2019 vs 2023 (same as Amazon)
# ===========================================================================
print("\n--- Congo corridor transects ---")
fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True)

for i, (var, info) in enumerate(ALL_VARS):
    ax = axes[i]
    for year, color in [(2019, "#264653"), (2023, "#e63946")]:
        if var == "airs_wv":
            data = (airs_2019 if year == 2019 else airs_2023).mean(dim="time")
        else:
            data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31")).mean(dim="time")
        transect = corridor_transect(data, LAT_BAND, LON_RANGE)
        transect.plot(ax=ax, color=color, linewidth=2.5, label=str(year))

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
fig.suptitle("Congo Basin Moisture Corridor: Gulf of Guinea to Kisangani\n"
             "Latitude band 3S-5N | 2019 vs 2023",
             fontsize=14, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "congo_corridor_transects.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: congo_corridor_transects.png")

# ===========================================================================
# 2. Spatial maps along Congo corridor
# ===========================================================================
print("\n--- Congo corridor spatial maps ---")
for var, info in CERES_VARS.items():
    d19 = ceres[var].sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
    d23 = ceres[var].sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")
    d19 = d19.sel(lat=lat_slice(d19, MAP_LAT), lon=slice(MAP_LON[0], MAP_LON[1]))
    d23 = d23.sel(lat=lat_slice(d23, MAP_LAT), lon=slice(MAP_LON[0], MAP_LON[1]))
    diff = d23 - d19

    proj = ccrs.PlateCarree()
    fig, ax3 = plt.subplots(1, 3, figsize=(20, 5), subplot_kw={"projection": proj})
    vmin = float(min(d19.min(), d23.min()))
    vmax = float(max(d19.max(), d23.max()))
    cmap = "inferno" if "lw" in var and "cre" not in var else "YlGnBu"

    for ax in ax3:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
        ax.add_feature(cfeature.RIVERS, linewidth=0.4, alpha=0.6, color="#4a90d9")
        lons_p = [v[1] for v in LANDMARKS.values()]
        lats_p = [v[0] for v in LANDMARKS.values()]
        ax.plot(lons_p, lats_p, "k--", linewidth=1.5, alpha=0.6, transform=proj)
        for nm, (lt, ln) in LANDMARKS.items():
            if nm in ["Douala", "Mbandaka", "Kisangani"]:
                ax.plot(ln, lt, "ko", markersize=5, transform=proj)
                ax.text(ln + 0.3, lt + 0.3, nm, fontsize=8, transform=proj, fontweight="bold")

    im1 = d19.plot(ax=ax3[0], transform=proj, cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False)
    ax3[0].set_title("2019"); plt.colorbar(im1, ax=ax3[0], shrink=0.7, label=info["units"], pad=0.02)
    im2 = d23.plot(ax=ax3[1], transform=proj, cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False)
    ax3[1].set_title("2023"); plt.colorbar(im2, ax=ax3[1], shrink=0.7, label=info["units"], pad=0.02)
    ma = float(max(abs(diff.min()), abs(diff.max()))) or 1
    im3 = diff.plot(ax=ax3[2], transform=proj, cmap="RdBu_r", vmin=-ma, vmax=ma, add_colorbar=False)
    ax3[2].set_title("2023 - 2019"); plt.colorbar(im3, ax=ax3[2], shrink=0.7, label=f"delta {info['units']}", pad=0.02)

    fig.suptitle(f"Congo Corridor: {info['label']}", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    safe = var.replace("_mon", "").replace("_total_daynight", "")
    fname = f"congo_corridor_map_{safe}.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")

# ===========================================================================
# 3. Coast-to-interior gradient bars
# ===========================================================================
print("\n--- Congo gradient bars ---")
fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)
lon_bins = np.arange(8, 28, 1)
lon_centers = 0.5 * (lon_bins[:-1] + lon_bins[1:])
distance_km = (lon_centers - 9.7) * 111.0 * np.cos(np.deg2rad(2))

for i, (var, info) in enumerate(ALL_VARS):
    ax = axes[i]
    if var == "airs_wv":
        d19 = airs_2019.mean(dim="time")
        d23 = airs_2023.mean(dim="time")
    else:
        d19 = ceres[var].sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
        d23 = ceres[var].sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")

    diff_vals = []
    for j in range(len(lon_bins) - 1):
        s19 = d19.sel(lat=lat_slice(d19, LAT_BAND), lon=slice(lon_bins[j], lon_bins[j+1]))
        s23 = d23.sel(lat=lat_slice(d23, LAT_BAND), lon=slice(lon_bins[j], lon_bins[j+1]))
        w = np.cos(np.deg2rad(s19.lat))
        diff_vals.append(float(s23.weighted(w).mean()) - float(s19.weighted(w).mean()))

    diff_vals = np.array(diff_vals)
    colors_bar = ["#e63946" if d > 0 else "#457b9d" for d in diff_vals]
    if "cld" in var or "cre" in var or var == "airs_wv":
        colors_bar = ["#e63946" if d < 0 else "#457b9d" for d in diff_vals]

    ax.bar(distance_km, diff_vals, width=distance_km[1] - distance_km[0],
           color=colors_bar, alpha=0.8, edgecolor="white", linewidth=0.5)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel(f"delta {info['units']}")
    ax.set_title(f"{info['label']} change (2023 - 2019)", fontsize=11)
    ax.grid(alpha=0.3, axis="y")

axes[-1].set_xlabel("Distance inland from Gulf of Guinea coast (km)")
fig.suptitle("Congo Corridor: Change vs Distance from Coast (2023 - 2019)",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "congo_corridor_gradient_bars.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: congo_corridor_gradient_bars.png")

# ===========================================================================
# 4. Seasonal decomposition
# ===========================================================================
print("\n--- Congo seasonal decomposition ---")
fig, axes = plt.subplots(4, 1, figsize=(14, 16), sharex=True)

for i, (var, info) in enumerate(ALL_VARS):
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
        (t23 - t19).plot(ax=ax, color=color, linewidth=2, label=season_name)

    ax.axhline(0, color="black", linewidth=0.5)
    for name, (lt, ln) in LANDMARKS.items():
        ax.axvline(ln, color="gray", alpha=0.3, linewidth=0.8)
    ax.set_title(f"{info['label']} change by season", fontsize=11)
    ax.set_ylabel(f"delta {info['units']}")
    ax.legend(fontsize=9, ncol=2)
    ax.grid(alpha=0.3)
    ax.set_xlabel("")

axes[-1].set_xlabel("Longitude")
fig.suptitle("Congo Corridor: Seasonal Decomposition of Changes (2023 - 2019)",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "congo_corridor_seasonal.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: congo_corridor_seasonal.png")

# ===========================================================================
# 5. Multi-year time series + gradient evolution
# ===========================================================================
print("\n--- Congo multi-year ---")
fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
for i, (var, info) in enumerate(CERES_VARS.items()):
    ax = axes[i]
    for seg_name, lon_slice in SEGMENTS.items():
        color = SEGMENT_COLORS[seg_name]
        vals = []
        for year in years:
            data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
            seg = data.sel(lat=lat_slice(data, LAT_BAND), lon=lon_slice)
            w = np.cos(np.deg2rad(seg.lat))
            vals.append(float(seg.weighted(w).mean(dim=["lat", "lon"]).mean(dim="time")))
        ax.plot(years, vals, "o-", color=color, linewidth=1.5, markersize=3, label=seg_name)
    for y in HIGHLIGHT_YEARS:
        if y in years:
            ax.axvline(y, color="gray", alpha=0.2, linewidth=1)
    ax.set_title(info["label"], fontsize=12)
    ax.set_ylabel(info["units"])
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
axes[-1].set_xlabel("Year")
fig.suptitle("Congo Corridor: Annual Mean Time Series (2001-2025)", fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "congo_corridor_multiyear.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: congo_corridor_multiyear.png")

# Gradient evolution
print("\n--- Congo gradient evolution ---")
fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
for i, (var, info) in enumerate(CERES_VARS.items()):
    ax = axes[i]
    grads = []
    for year in years:
        data = ceres[var].sel(time=slice(f"{year}-01-01", f"{year}-12-31"))
        lat_sl = lat_slice(data, LAT_BAND)
        c = data.sel(lat=lat_sl, lon=SEGMENTS["Coast (Gulf of Guinea)"])
        wc = np.cos(np.deg2rad(c.lat))
        c_val = float(c.weighted(wc).mean(dim=["lat", "lon"]).mean(dim="time"))
        interior = data.sel(lat=lat_sl, lon=SEGMENTS["Interior (E. Congo)"])
        wi = np.cos(np.deg2rad(interior.lat))
        i_val = float(interior.weighted(wi).mean(dim=["lat", "lon"]).mean(dim="time"))
        grads.append(i_val - c_val)
    grads = np.array(grads)
    colors_g = ["#e63946" if g > np.mean(grads) else "#457b9d" for g in grads]
    if "cld" in var or "cre" in var:
        colors_g = ["#e63946" if g < np.mean(grads) else "#457b9d" for g in grads]
    ax.bar(years, grads, color=colors_g, alpha=0.7, edgecolor="white", linewidth=0.3)
    z = np.polyfit(years, grads, 1)
    ax.plot(years, np.poly1d(z)(years), "k--", linewidth=1.5, label=f"Trend: {z[0]:+.3f}/yr")
    ax.set_title(f"{info['label']}: Interior - Coast gradient", fontsize=11)
    ax.set_ylabel(f"Gradient ({info['units']})")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
axes[-1].set_xlabel("Year")
fig.suptitle("Congo Corridor: Coast-to-Interior Gradient (2001-2025)", fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "congo_corridor_gradient_evolution.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: congo_corridor_gradient_evolution.png")

# ===========================================================================
# Summary
# ===========================================================================
print("\n=== CONGO CORRIDOR SUMMARY ===\n")
for var, info in ALL_VARS:
    if var == "airs_wv":
        d19 = airs_2019.mean(dim="time")
        d23 = airs_2023.mean(dim="time")
    else:
        d19 = ceres[var].sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
        d23 = ceres[var].sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")

    print(f"{info['label']}:")
    for seg_name, lon_slice in SEGMENTS.items():
        v19 = float(d19.sel(lat=lat_slice(d19, LAT_BAND), lon=lon_slice).mean(skipna=True))
        v23 = float(d23.sel(lat=lat_slice(d23, LAT_BAND), lon=lon_slice).mean(skipna=True))
        print(f"  {seg_name:30s} 2019={v19:.1f}  2023={v23:.1f}  delta={v23-v19:+.2f}")
    print()

print("=== DONE ===")

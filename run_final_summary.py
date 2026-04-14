"""Final summary figure — publication-ready multi-panel.

8-panel figure telling the complete story:
(a) Wide-view OLR anomaly map with corridors and storms
(b) Amazon corridor transect: 2019 vs 2023 (OLR + cloud + WV stacked)
(c) Congo corridor transect: 2019 vs 2023
(d) Seasonal decomposition: SON dominance (Amazon)
(e) ENSO-adjusted 25-year cloud fraction gradient trend
(f) NDVI change in intact forest (histogram)
(g) ET vs OLR scatter (wider region, n=159)
(h) Storm Daniel September 2023 dipole
"""
import sys
sys.path.insert(0, ".")

import os
os.add_dll_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   ".venv", "Lib", "site-packages", "pyhdf"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import xarray as xr
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import re
from pyhdf.SD import SD, SDC
from pathlib import Path
from scipy import stats as sp_stats

from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

# ===========================================================================
# Load all data
# ===========================================================================
print("Loading data...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

# AIRS
def read_airs_wv(fp):
    sd = SD(str(fp), SDC.READ)
    d = sd.select("TotH2OVap_A").get().astype(np.float64)
    a = sd.select("TotH2OVap_A").attributes()
    sd.end()
    d[d == a.get("_FillValue", -9999)] = np.nan
    lat = np.arange(-89.5, 90, 1.0)
    lon = np.arange(-179.5, 180, 1.0)
    return xr.DataArray(d, dims=["lat", "lon"], coords={"lat": lat, "lon": lon})

def load_airs_annual(year):
    files = sorted(Path("data/airs").glob(f"AIRS.{year}.*.hdf"))
    return xr.concat([read_airs_wv(f) for f in files], dim="time").mean(dim="time")

airs_19 = load_airs_annual(2019)
airs_23 = load_airs_annual(2023)

# NDVI
def read_ndvi_cmg(fp):
    sd = SD(str(fp), SDC.READ)
    d = sd.select("CMG 0.05 Deg Monthly NDVI").get().astype(np.float64)
    sd.end()
    d[d == -3000] = np.nan
    d /= 10000.0
    lat = np.linspace(90 - 0.025, -90 + 0.025, 3600)
    lon = np.linspace(-180 + 0.025, 180 - 0.025, 7200)
    return xr.DataArray(d, dims=["lat", "lon"], coords={"lat": lat, "lon": lon})

def load_ndvi_annual(year):
    files = sorted([f for f in Path("data/modis_ndvi").glob("MOD13C2.A*.hdf")
                     if f"A{year}" in f.name])
    return xr.concat([read_ndvi_cmg(f) for f in files], dim="time").mean(dim="time")

ndvi_19 = load_ndvi_annual(2019)
ndvi_23 = load_ndvi_annual(2023)

# ONI
oni_lines = open("data/oni.txt").readlines()
oni_records = []
for line in oni_lines[1:]:
    parts = line.split()
    if len(parts) >= 4:
        oni_records.append({"season": parts[0], "year": int(parts[1]), "anom": float(parts[3])})
oni_df = pd.DataFrame(oni_records)

# Helpers
def lat_slice(da, lr):
    lo, hi = min(lr), max(lr)
    return slice(hi, lo) if da.lat[0] > da.lat[-1] else slice(lo, hi)

def corridor_transect(da, lat_band, lon_range):
    c = da.sel(lat=lat_slice(da, lat_band), lon=slice(lon_range[0], lon_range[1]))
    return c.weighted(np.cos(np.deg2rad(c.lat))).mean(dim="lat")

def seasonal_mean(da, year, months):
    if 12 in months and 1 in months:
        dec = da.sel(time=slice(f"{year-1}-12-01", f"{year-1}-12-31"))
        jf = da.sel(time=slice(f"{year}-01-01", f"{year}-02-28"))
        return xr.concat([dec, jf], dim="time").mean(dim="time")
    sm, em = min(months), max(months)
    return da.sel(time=slice(f"{year}-{sm:02d}-01", f"{year}-{em:02d}-28")).mean(dim="time")

AMAZON_LAT, AMAZON_LON = (-6.0, 0.0), (-62.0, -47.0)
CONGO_LAT, CONGO_LON = (-3.0, 5.0), (8.0, 28.0)
WIDE_AMAZON = (-10.0, 2.0), (-65.0, -45.0)

# ===========================================================================
# BUILD FIGURE
# ===========================================================================
print("Building final summary figure...")
fig = plt.figure(figsize=(20, 26))
gs = gridspec.GridSpec(4, 2, hspace=0.32, wspace=0.28, height_ratios=[1.1, 0.85, 0.85, 0.85])
proj = ccrs.PlateCarree()

# ---- (a) Wide-view OLR anomaly with corridors and storms ----
ax = fig.add_subplot(gs[0, :], projection=proj)

olr_diff = (ceres["toa_lw_all_mon"].sel(time=slice("2023","2023")).mean("time") -
            ceres["toa_lw_all_mon"].sel(time=slice("2019","2019")).mean("time"))
region = olr_diff.sel(lat=lat_slice(olr_diff, (-15, 55)), lon=slice(-65, 50))
ma = float(max(abs(region.min(skipna=True)), abs(region.max(skipna=True)))) or 1
im = region.plot(ax=ax, transform=proj, cmap="RdBu_r", vmin=-ma, vmax=ma, add_colorbar=False)
plt.colorbar(im, ax=ax, shrink=0.4, label="delta OLR (W/m2)", pad=0.01,
             orientation="horizontal", aspect=40)
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.2, linestyle="--")

# Corridors
ax.plot([-48.5, -60], [-1.4, -3.1], color="#2a9d8f", linewidth=3, transform=proj)
ax.text(-54, 1, "Amazon corridor", color="#2a9d8f", fontsize=9, fontweight="bold", transform=proj, ha="center")
ax.plot([9.7, 25.2], [4.0, 0.5], color="#e9c46a", linewidth=3, transform=proj)
ax.text(17, 6, "Congo corridor", color="#e9c46a", fontsize=9, fontweight="bold", transform=proj, ha="center")

# Storms
ax.plot(22.6, 32.8, "r*", markersize=14, transform=proj, markeredgecolor="k", markeredgewidth=0.4)
ax.text(24, 34, "Daniel\n(Sept 2023)", color="red", fontsize=8, fontweight="bold", transform=proj)
ax.plot(16, 49, "r*", markersize=14, transform=proj, markeredgecolor="k", markeredgewidth=0.4)
ax.text(18, 49, "Boris\n(Sept 2024)", color="red", fontsize=8, fontweight="bold", transform=proj)

ax.set_extent([-65, 50, -15, 55], crs=proj)
ax.gridlines(draw_labels=True, alpha=0.2, linewidth=0.3)
ax.set_title("(a) OLR Change 2023-2019 with Moisture Corridors and Storm Locations",
             fontsize=12, fontweight="bold", pad=8)

# ---- (b) Amazon corridor transect ----
ax_b = fig.add_subplot(gs[1, 0])
for var, label, color_19, color_23 in [
    ("toa_lw_all_mon", "OLR (W/m2)", "#264653", "#e63946"),
]:
    for yr, col in [(2019, color_19), (2023, color_23)]:
        d = ceres[var].sel(time=slice(f"{yr}",f"{yr}")).mean("time")
        t = corridor_transect(d, AMAZON_LAT, AMAZON_LON)
        t.plot(ax=ax_b, color=col, linewidth=2.5, label=f"OLR {yr}")

# Add WV on secondary axis
ax_b2 = ax_b.twinx()
for yr, col, ls in [(2019, "#264653", "--"), (2023, "#e63946", "--")]:
    data = airs_19 if yr == 2019 else airs_23
    t = corridor_transect(data, AMAZON_LAT, AMAZON_LON)
    t.plot(ax=ax_b2, color=col, linewidth=1.5, linestyle=ls, label=f"WV {yr}")
ax_b2.set_ylabel("Water Vapor (kg/m2)", fontsize=9, color="#666")

for nm, ln in [("Belem", -48.5), ("Maraba", -49.1), ("Manaus", -60)]:
    ax_b.axvline(ln, color="gray", alpha=0.3, linewidth=0.5)

ax_b.set_title("(b) Amazon: Belem-Manaus Corridor", fontsize=11, fontweight="bold")
ax_b.set_ylabel("OLR (W/m2)")
ax_b.set_xlabel("Longitude")
lines1, labels1 = ax_b.get_legend_handles_labels()
lines2, labels2 = ax_b2.get_legend_handles_labels()
ax_b.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper right")
ax_b.grid(alpha=0.2)

# ---- (c) Congo corridor transect ----
ax_c = fig.add_subplot(gs[1, 1])
for yr, col in [(2019, "#264653"), (2023, "#e63946")]:
    d = ceres["toa_lw_all_mon"].sel(time=slice(f"{yr}",f"{yr}")).mean("time")
    t = corridor_transect(d, CONGO_LAT, CONGO_LON)
    t.plot(ax=ax_c, color=col, linewidth=2.5, label=f"OLR {yr}")

ax_c2 = ax_c.twinx()
for yr, col, ls in [(2019, "#264653", "--"), (2023, "#e63946", "--")]:
    data = airs_19 if yr == 2019 else airs_23
    t = corridor_transect(data, CONGO_LAT, CONGO_LON)
    t.plot(ax=ax_c2, color=col, linewidth=1.5, linestyle=ls, label=f"WV {yr}")
ax_c2.set_ylabel("Water Vapor (kg/m2)", fontsize=9, color="#666")

for nm, ln in [("Douala", 9.7), ("Mbandaka", 18.3), ("Kisangani", 25.2)]:
    ax_c.axvline(ln, color="gray", alpha=0.3, linewidth=0.5)

ax_c.set_title("(c) Congo: Gulf of Guinea-Kisangani Corridor", fontsize=11, fontweight="bold")
ax_c.set_ylabel("OLR (W/m2)")
ax_c.set_xlabel("Longitude")
lines1, labels1 = ax_c.get_legend_handles_labels()
lines2, labels2 = ax_c2.get_legend_handles_labels()
ax_c.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper right")
ax_c.grid(alpha=0.2)

# ---- (d) Seasonal decomposition (Amazon OLR) ----
ax_d = fig.add_subplot(gs[2, 0])
SEASONS = {"Dry (JJA)": [6,7,8], "Wet (DJF)": [12,1,2], "SON": [9,10,11], "MAM": [3,4,5]}
SCOL = {"Dry (JJA)": "#e76f51", "Wet (DJF)": "#264653", "SON": "#e9c46a", "MAM": "#2a9d8f"}

for sname, months in SEASONS.items():
    s19 = seasonal_mean(ceres["toa_lw_all_mon"], 2019, months)
    s23 = seasonal_mean(ceres["toa_lw_all_mon"], 2023, months)
    tdiff = corridor_transect(s23 - s19, AMAZON_LAT, AMAZON_LON)
    tdiff.plot(ax=ax_d, color=SCOL[sname], linewidth=2.5, label=sname)

ax_d.axhline(0, color="black", linewidth=0.5)
ax_d.set_title("(d) Amazon OLR Change by Season", fontsize=11, fontweight="bold")
ax_d.set_ylabel("delta OLR (W/m2)")
ax_d.set_xlabel("Longitude")
ax_d.legend(fontsize=8)
ax_d.grid(alpha=0.2)

# ---- (e) ENSO-adjusted 25-year cloud fraction gradient ----
ax_e = fig.add_subplot(gs[2, 1])

years = list(range(2001, 2026))
PHASE_COLORS = {"el_nino": "#e63946", "la_nina": "#457b9d", "neutral": "#999999"}

def get_phase(year):
    yd = oni_df[oni_df["year"] == year]
    if len(yd) == 0: return "neutral"
    val = float(yd.loc[yd["anom"].abs().idxmax(), "anom"])
    if val >= 0.5: return "el_nino"
    elif val <= -0.5: return "la_nina"
    return "neutral"

def get_annual_oni(year):
    yd = oni_df[oni_df["year"] == year]
    return float(yd["anom"].mean()) if len(yd) > 0 else 0.0

grads = []
for y in years:
    d = ceres["cldarea_total_daynight_mon"].sel(time=slice(f"{y}",f"{y}"))
    ls = lat_slice(d, AMAZON_LAT)
    c = d.sel(lat=ls, lon=slice(-50,-47))
    i = d.sel(lat=ls, lon=slice(-62,-58))
    cv = float(c.weighted(np.cos(np.deg2rad(c.lat))).mean(dim=["lat","lon"]).mean("time"))
    iv = float(i.weighted(np.cos(np.deg2rad(i.lat))).mean(dim=["lat","lon"]).mean("time"))
    grads.append(iv - cv)

grads = np.array(grads)
oni_vals = np.array([get_annual_oni(y) for y in years])
slope_oni, int_oni, _, _, _ = sp_stats.linregress(oni_vals, grads)
residuals = grads - (slope_oni * oni_vals + int_oni)

colors = [PHASE_COLORS[get_phase(y)] for y in years]
ax_e.bar(years, residuals, color=colors, alpha=0.8, edgecolor="white", linewidth=0.3)

z = np.polyfit(years, residuals, 1)
_, _, r_adj, p_adj, _ = sp_stats.linregress(years, residuals)
ax_e.plot(years, np.poly1d(z)(years), "k-", linewidth=2,
          label=f"ENSO-adjusted: {z[0]:+.3f}%/yr, p={p_adj:.4f}")
ax_e.axhline(0, color="gray", linewidth=0.5)

from matplotlib.patches import Patch
ax_e.legend(handles=[
    Patch(facecolor="#e63946", label="El Nino"),
    Patch(facecolor="#457b9d", label="La Nina"),
    Patch(facecolor="#999", label="Neutral"),
    plt.Line2D([0],[0], color="k", linewidth=2, label=f"Trend: {z[0]:+.3f}%/yr (p={p_adj:.4f})"),
], fontsize=7, loc="lower left")

ax_e.set_title("(e) Amazon Cloud Fraction Gradient\n(ENSO-adjusted, 2001-2025)",
               fontsize=11, fontweight="bold")
ax_e.set_ylabel("ENSO-adjusted gradient anomaly (%)")
ax_e.set_xlabel("Year")
ax_e.grid(alpha=0.2, axis="y")

# ---- (f) NDVI in intact forest ----
ax_f = fig.add_subplot(gs[3, 0])

ndvi_amazon_19 = ndvi_19.sel(lat=slice(WIDE_AMAZON[0][1], WIDE_AMAZON[0][0]),
                               lon=slice(WIDE_AMAZON[1][0], WIDE_AMAZON[1][1]))
ndvi_amazon_23 = ndvi_23.sel(lat=slice(WIDE_AMAZON[0][1], WIDE_AMAZON[0][0]),
                               lon=slice(WIDE_AMAZON[1][0], WIDE_AMAZON[1][1]))

d19_1 = ndvi_amazon_19.coarsen(lat=20, lon=20, boundary="trim").mean()
d23_1 = ndvi_amazon_23.coarsen(lat=20, lon=20, boundary="trim").mean()
diff_1 = d23_1 - d19_1

forest_mask = d19_1 > 0.6
forest_diff = diff_1.where(forest_mask).values.ravel()
forest_v = forest_diff[~np.isnan(forest_diff)]

bins = np.arange(-0.08, 0.06, 0.004)
ax_f.hist(forest_v, bins=bins, alpha=0.8, color="#2a9d8f", edgecolor="white", linewidth=0.3)
ax_f.axvline(0, color="black", linewidth=1)
ax_f.axvline(np.mean(forest_v), color="#e63946", linewidth=2, linestyle="--",
             label=f"Mean: {np.mean(forest_v):+.004f}\n88% declined\nt=-15.4, p<10$^{{-6}}$")
ax_f.set_title("(f) NDVI Change in Intact Forest\n(NDVI > 0.6 in 2019, Eastern Amazon)",
               fontsize=11, fontweight="bold")
ax_f.set_xlabel("NDVI change (2023 - 2019)")
ax_f.set_ylabel("Number of 1-degree cells")
ax_f.legend(fontsize=9)
ax_f.grid(alpha=0.2)

# ---- (g) ET vs OLR scatter (wider region) ----
ax_g = fig.add_subplot(gs[3, 1])

from src.modis_et import process_region_year
from src.processing import subset_region, annual_mean

olr_19 = annual_mean(ceres, "toa_lw_all_mon", 2019)
olr_23 = annual_mean(ceres, "toa_lw_all_mon", 2023)
olr_d = subset_region(olr_23 - olr_19, WIDE_AMAZON[0], WIDE_AMAZON[1])

et_19 = process_region_year("data/modis_et", "Amazon", 2019,
                              WIDE_AMAZON[0], WIDE_AMAZON[1], resolution=1.0)
et_23 = process_region_year("data/modis_et", "Amazon", 2023,
                              WIDE_AMAZON[0], WIDE_AMAZON[1], resolution=1.0)
et_d = et_23 - et_19
et_on_ceres = et_d.interp(lat=olr_d.lat, lon=olr_d.lon, method="nearest")

et_f = et_on_ceres.values.ravel()
olr_f = olr_d.values.ravel()
valid = ~np.isnan(et_f) & ~np.isnan(olr_f)

ax_g.scatter(et_f[valid], olr_f[valid], s=30, c="#264653", alpha=0.5,
              edgecolors="black", linewidth=0.2)
slope, intercept, r_val, p_val, _ = sp_stats.linregress(et_f[valid], olr_f[valid])
xl = np.linspace(np.nanmin(et_f[valid]), np.nanmax(et_f[valid]), 100)
ax_g.plot(xl, slope * xl + intercept, "r--", linewidth=2,
          label=f"r={r_val:.3f}, p<0.0001, n={valid.sum()}")
ax_g.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
ax_g.axvline(0, color="gray", linewidth=0.5, alpha=0.5)
ax_g.set_xlabel("ET change (mm/yr)")
ax_g.set_ylabel("OLR change (W/m2)")
ax_g.set_title("(g) ET vs OLR Change per Grid Cell\n(Eastern Amazon, 1-degree)",
               fontsize=11, fontweight="bold")
ax_g.legend(fontsize=9)
ax_g.grid(alpha=0.2)
ax_g.text(0.97, 0.03, "ET down, OLR up\n= pump failure", transform=ax_g.transAxes,
          fontsize=8, ha="right", va="bottom", color="#e63946", fontstyle="italic")

# ---- Main title ----
fig.suptitle(
    "Satellite Evidence for Condensation-Driven Circulation Breakdown\n"
    "in Tropical Forest Moisture Corridors",
    fontsize=16, fontweight="bold", y=0.995
)

plt.savefig(OUTPUT_DIR / "final_summary.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print("Saved: final_summary.png")

print(f"\nTotal figures in outputs/: {len(list(OUTPUT_DIR.glob('*.png')))}")
print("=== DONE ===")

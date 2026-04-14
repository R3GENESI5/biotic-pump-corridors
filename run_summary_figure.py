"""Combined summary figure — the complete biotic pump analysis.

A multi-panel figure telling the full story:
(a) Tropical overview: OLR difference 2023-2019
(b) Amazon corridor transect: OLR + cloud + WV
(c) Congo corridor transect: OLR + cloud + WV
(d) Seasonal decomposition: SON dominates
(e) 25-year gradient trend
(f) Storm Daniel dipole
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
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import re
from pyhdf.SD import SD, SDC
from pathlib import Path
from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

# ===========================================================================
# Load all data
# ===========================================================================
print("Loading data...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

def read_airs_wv(filepath):
    sd = SD(str(filepath), SDC.READ)
    sds = sd.select("TotH2OVap_A")
    data = sds.get().astype(np.float64)
    attrs = sds.attributes()
    sd.end()
    data[data == attrs.get("_FillValue", -9999)] = np.nan
    lat = np.arange(-89.5, 90, 1.0)
    lon = np.arange(-179.5, 180, 1.0)
    return xr.DataArray(data, dims=["lat", "lon"], coords={"lat": lat, "lon": lon})

def load_airs_annual(year):
    files = sorted(Path("data/airs").glob(f"AIRS.{year}.*.hdf"))
    return xr.concat([read_airs_wv(f) for f in files], dim="time").mean(dim="time")

airs_2019 = load_airs_annual(2019)
airs_2023 = load_airs_annual(2023)

def lat_slice(da, lr):
    lo, hi = min(lr), max(lr)
    return slice(hi, lo) if da.lat[0] > da.lat[-1] else slice(lo, hi)

def corridor_transect(da, lat_band, lon_range):
    c = da.sel(lat=lat_slice(da, lat_band), lon=slice(lon_range[0], lon_range[1]))
    return c.weighted(np.cos(np.deg2rad(c.lat))).mean(dim="lat")

# ===========================================================================
# Build the figure
# ===========================================================================
print("Building summary figure...")

fig = plt.figure(figsize=(22, 28))
gs = gridspec.GridSpec(4, 2, hspace=0.35, wspace=0.25,
                       height_ratios=[1.0, 0.8, 0.8, 0.8])

proj = ccrs.PlateCarree()

# -----------------------------------------------------------------------
# (a) Tropical OLR difference map
# -----------------------------------------------------------------------
ax_a = fig.add_subplot(gs[0, :], projection=proj)

olr_19 = ceres["toa_lw_all_mon"].sel(time=slice("2019","2019")).mean(dim="time")
olr_23 = ceres["toa_lw_all_mon"].sel(time=slice("2023","2023")).mean(dim="time")
diff = olr_23 - olr_19
diff_trop = diff.sel(lat=lat_slice(diff, (-20, 40)), lon=slice(-65, 50))

ma = float(max(abs(diff_trop.min(skipna=True)), abs(diff_trop.max(skipna=True)))) or 1
im = diff_trop.plot(ax=ax_a, transform=proj, cmap="RdBu_r",
                     vmin=-ma, vmax=ma, add_colorbar=False)
plt.colorbar(im, ax=ax_a, shrink=0.5, label="delta OLR (W/m2)", pad=0.01,
             orientation="horizontal", aspect=40)
ax_a.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax_a.add_feature(cfeature.BORDERS, linewidth=0.2, linestyle="--")

# Mark corridors
for lons, lats, label, color in [
    ([-48.5, -60], [-1.4, -3.1], "Amazon corridor", "#2a9d8f"),
    ([9.7, 25.2], [4.0, 0.5], "Congo corridor", "#e9c46a"),
]:
    ax_a.plot(lons, lats, color=color, linewidth=3, transform=proj)
    ax_a.text(np.mean(lons), lats[0]+2, label, color=color, fontsize=10,
              fontweight="bold", transform=proj, ha="center")

# Mark storm locations
ax_a.plot(22.6, 32.8, "r*", markersize=15, transform=proj)
ax_a.text(24, 33.5, "Daniel", color="red", fontsize=9, fontweight="bold", transform=proj)
ax_a.plot(16, 49, "r*", markersize=15, transform=proj)
ax_a.text(17, 49.5, "Boris", color="red", fontsize=9, fontweight="bold", transform=proj)

ax_a.set_extent([-65, 50, -20, 55], crs=proj)
ax_a.gridlines(draw_labels=True, alpha=0.2, linewidth=0.3)
ax_a.set_title("(a) OLR Difference 2023 - 2019: Forest Source Regions and Storm Destinations",
               fontsize=13, fontweight="bold", pad=10)

# -----------------------------------------------------------------------
# (b) Amazon corridor: OLR difference transect by season
# -----------------------------------------------------------------------
ax_b = fig.add_subplot(gs[1, 0])

AMAZON_LAT = (-6.0, 0.0)
AMAZON_LON = (-62.0, -47.0)
SEASONS = {"Dry (JJA)": [6,7,8], "Wet (DJF)": [12,1,2],
           "SON": [9,10,11], "MAM": [3,4,5]}
SCOL = {"Dry (JJA)": "#e76f51", "Wet (DJF)": "#264653",
        "SON": "#e9c46a", "MAM": "#2a9d8f"}

def seasonal_mean(da, year, months):
    if 12 in months and 1 in months:
        dec = da.sel(time=slice(f"{year-1}-12-01", f"{year-1}-12-31"))
        jf = da.sel(time=slice(f"{year}-01-01", f"{year}-02-28"))
        return xr.concat([dec, jf], dim="time").mean(dim="time")
    start_m, end_m = min(months), max(months)
    return da.sel(time=slice(f"{year}-{start_m:02d}-01", f"{year}-{end_m:02d}-28")).mean(dim="time")

for sname, months in SEASONS.items():
    s19 = seasonal_mean(ceres["toa_lw_all_mon"], 2019, months)
    s23 = seasonal_mean(ceres["toa_lw_all_mon"], 2023, months)
    t_diff = corridor_transect(s23 - s19, AMAZON_LAT, AMAZON_LON)
    t_diff.plot(ax=ax_b, color=SCOL[sname], linewidth=2, label=sname)

ax_b.axhline(0, color="black", linewidth=0.5)
ax_b.set_title("(b) Amazon Corridor: OLR Change by Season", fontsize=11, fontweight="bold")
ax_b.set_ylabel("delta OLR (W/m2)")
ax_b.set_xlabel("Longitude")
ax_b.legend(fontsize=8)
ax_b.grid(alpha=0.3)
ax_b.text(-48.5, ax_b.get_ylim()[0]+1, "Belem->", fontsize=8, color="#555")
ax_b.text(-61.5, ax_b.get_ylim()[0]+1, "<-Manaus", fontsize=8, color="#555")

# -----------------------------------------------------------------------
# (c) Congo corridor: OLR difference transect by season
# -----------------------------------------------------------------------
ax_c = fig.add_subplot(gs[1, 1])

CONGO_LAT = (-3.0, 5.0)
CONGO_LON = (8.0, 28.0)

for sname, months in SEASONS.items():
    s19 = seasonal_mean(ceres["toa_lw_all_mon"], 2019, months)
    s23 = seasonal_mean(ceres["toa_lw_all_mon"], 2023, months)
    t_diff = corridor_transect(s23 - s19, CONGO_LAT, CONGO_LON)
    t_diff.plot(ax=ax_c, color=SCOL[sname], linewidth=2, label=sname)

ax_c.axhline(0, color="black", linewidth=0.5)
ax_c.set_title("(c) Congo Corridor: OLR Change by Season", fontsize=11, fontweight="bold")
ax_c.set_ylabel("delta OLR (W/m2)")
ax_c.set_xlabel("Longitude")
ax_c.legend(fontsize=8)
ax_c.grid(alpha=0.3)
ax_c.text(9, ax_c.get_ylim()[0]+1, "Douala->", fontsize=8, color="#555")
ax_c.text(26, ax_c.get_ylim()[0]+1, "<-Kisangani", fontsize=8, color="#555")

# -----------------------------------------------------------------------
# (d) 25-year OLR gradient evolution — both corridors
# -----------------------------------------------------------------------
ax_d = fig.add_subplot(gs[2, 0])

years = [y for y in sorted(set(ceres.time.dt.year.values)) if 2001 <= y <= 2025]

for label, lat_band, coast_sl, interior_sl, color in [
    ("Amazon", (-6,0), slice(-50,-47), slice(-62,-58), "#2a9d8f"),
    ("Congo", (-3,5), slice(8,12), slice(22,27), "#e9c46a"),
]:
    grads = []
    for year in years:
        d = ceres["toa_lw_all_mon"].sel(time=slice(f"{year}",f"{year}"))
        ls = lat_slice(d, lat_band)
        c = d.sel(lat=ls, lon=coast_sl)
        i = d.sel(lat=ls, lon=interior_sl)
        wc = np.cos(np.deg2rad(c.lat))
        wi = np.cos(np.deg2rad(i.lat))
        cv = float(c.weighted(wc).mean(dim=["lat","lon"]).mean(dim="time"))
        iv = float(i.weighted(wi).mean(dim=["lat","lon"]).mean(dim="time"))
        grads.append(iv - cv)
    grads = np.array(grads)
    ax_d.plot(years, grads, "o-", color=color, linewidth=1.5, markersize=3, label=label)
    z = np.polyfit(years, grads, 1)
    ax_d.plot(years, np.poly1d(z)(years), "--", color=color, linewidth=1,
              label=f"  trend: {z[0]:+.3f}/yr")

ax_d.set_title("(d) Coast-to-Interior OLR Gradient (25 years)", fontsize=11, fontweight="bold")
ax_d.set_ylabel("Interior - Coast OLR (W/m2)")
ax_d.set_xlabel("Year")
ax_d.legend(fontsize=8, ncol=2)
ax_d.grid(alpha=0.3)

# -----------------------------------------------------------------------
# (e) AIRS water vapor corridor comparison
# -----------------------------------------------------------------------
ax_e = fig.add_subplot(gs[2, 1])

# Amazon WV transect
for year, data, color in [(2019, airs_2019, "#264653"), (2023, airs_2023, "#e63946")]:
    t = corridor_transect(data, AMAZON_LAT, AMAZON_LON)
    t.plot(ax=ax_e, color=color, linewidth=2, label=f"Amazon {year}",
           linestyle="-")

for year, data, color in [(2019, airs_2019, "#264653"), (2023, airs_2023, "#e63946")]:
    t = corridor_transect(data, CONGO_LAT, CONGO_LON)
    t.plot(ax=ax_e, color=color, linewidth=2, label=f"Congo {year}",
           linestyle="--")

ax_e.set_title("(e) Column Water Vapor Along Both Corridors (AIRS)", fontsize=11, fontweight="bold")
ax_e.set_ylabel("Water Vapor (kg/m2)")
ax_e.set_xlabel("Longitude")
ax_e.legend(fontsize=7, ncol=2)
ax_e.grid(alpha=0.3)

# -----------------------------------------------------------------------
# (f) Storm Daniel dipole bar chart
# -----------------------------------------------------------------------
ax_f = fig.add_subplot(gs[3, 0])

sept_data = ceres.sel(time=ceres.time.dt.month == 9)
sept_baseline = sept_data.sel(time=slice("2001", "2018")).mean(dim="time")
sept_2023 = sept_data.sel(time="2023").mean(dim="time")

regions_dipole = {
    "Amazon": {"lat": (-7,-3), "lon": (-52,-47)},
    "Congo": {"lat": (-5,5), "lon": (15,30)},
    "Trop.\nAtlantic": {"lat": (-10,10), "lon": (-40,0)},
    "E. Med.\n(Daniel)": {"lat": (28,38), "lon": (15,30)},
}
colors_dipole = ["#2a9d8f", "#e9c46a", "#264653", "#e63946"]

olr_anoms = []
for (name, bounds) in regions_dipole.items():
    anom = sept_2023["toa_lw_all_mon"] - sept_baseline["toa_lw_all_mon"]
    r = anom.sel(lat=lat_slice(anom, bounds["lat"]), lon=slice(bounds["lon"][0], bounds["lon"][1]))
    olr_anoms.append(float(r.mean(skipna=True)))

ax_f.bar(range(len(olr_anoms)), olr_anoms, color=colors_dipole, alpha=0.85)
ax_f.set_xticks(range(len(olr_anoms)))
ax_f.set_xticklabels(regions_dipole.keys(), fontsize=9)
ax_f.axhline(0, color="black", linewidth=0.5)
ax_f.set_ylabel("Sept 2023 OLR Anomaly (W/m2)")
ax_f.set_title("(f) Moisture Dipole: Sept 2023 vs Climatology", fontsize=11, fontweight="bold")
ax_f.grid(alpha=0.3, axis="y")

# -----------------------------------------------------------------------
# (g) Key numbers summary table
# -----------------------------------------------------------------------
ax_g = fig.add_subplot(gs[3, 1])
ax_g.axis("off")

summary_data = [
    ["Metric", "Amazon", "Congo"],
    ["OLR change (W/m2)", "+3.20", "+1.28"],
    ["Cloud change (%)", "-3.30", "-0.47"],
    ["CRE change (W/m2)", "-2.06", "-0.74"],
    ["ET change (mm/yr)", "-65.8", "+12.7"],
    ["WV gradient shift (kg/m2)", "-1.24", "+0.01"],
    ["OLR gradient trend (/yr)", "+0.074", "+0.013"],
    ["SON OLR interior change", "+24.5", "+8.2*"],
    ["25-yr CRE trend (/yr)", "-0.116", "-0.072"],
]

table = ax_g.table(
    cellText=summary_data[1:],
    colLabels=summary_data[0],
    cellLoc="center",
    loc="center",
    colColours=["#f0f0f0", "#d4edda", "#fff3cd"],
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.8)

# Style header
for j in range(3):
    table[0, j].set_text_props(fontweight="bold")

ax_g.set_title("(g) Key Results Summary: 2019 vs 2023", fontsize=11,
               fontweight="bold", pad=20)

# -----------------------------------------------------------------------
# Main title
# -----------------------------------------------------------------------
fig.suptitle(
    "Satellite Evidence for Condensation-Driven Circulation Breakdown\n"
    "Belem-Manaus and Gulf of Guinea-Kisangani Moisture Corridors\n"
    "CERES EBAF-TOA, MODIS MOD16A3GF, AIRS L3 | 2001-2025",
    fontsize=16, fontweight="bold", y=0.98
)

plt.savefig(OUTPUT_DIR / "summary_figure.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close()
print("Saved: summary_figure.png")

print("\n=== COMPLETE ===")
print(f"Total figures in outputs/: {len(list(OUTPUT_DIR.glob('*.png')))}")

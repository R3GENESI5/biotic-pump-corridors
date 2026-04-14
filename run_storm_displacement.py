"""Storm displacement analysis.

Hypothesis: Moisture that would normally cycle through Amazon/Congo forests
was displaced when the biotic pump weakened, contributing to extreme
precipitation events elsewhere:
- Storm Daniel: Sept 2023, catastrophic flooding in Libya (Derna)
- Storm Boris: Sept 2024, extreme flooding in Central Europe

We test this by looking at water vapor and OLR anomalies during
the months of these events — is there a spatial dipole showing
moisture deficit over the forests and surplus over the storm regions?
"""
import sys
sys.path.insert(0, ".")

import os
os.add_dll_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   ".venv", "Lib", "site-packages", "pyhdf"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import re
from pyhdf.SD import SD, SDC
from pathlib import Path
from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

# --- Storm events ---
STORMS = {
    "Daniel": {
        "date": "September 2023",
        "location": "Libya (Derna)",
        "lat": 32.8, "lon": 22.6,
        "region": {"lat": (28, 38), "lon": (15, 30)},
        "year": 2023, "months": [9],
    },
    "Boris": {
        "date": "September 2024",
        "location": "Central Europe (Austria, Czech Republic, Poland)",
        "lat": 49.0, "lon": 16.0,
        "region": {"lat": (44, 54), "lon": (10, 25)},
        "year": 2024, "months": [9],
    },
}

# Forest source regions
SOURCES = {
    "Amazon (Maraba)": {"lat": (-7, -3), "lon": (-52, -47), "color": "#2a9d8f"},
    "Congo Basin": {"lat": (-5, 5), "lon": (15, 30), "color": "#e9c46a"},
}

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
    return xr.DataArray(data, dims=["lat", "lon"], coords={"lat": lat, "lon": lon})


def lat_slice(da, lat_range):
    lo, hi = min(lat_range), max(lat_range)
    if da.lat[0] > da.lat[-1]:
        return slice(hi, lo)
    return slice(lo, hi)


# ===========================================================================
# Load data
# ===========================================================================
print("Loading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

# Compute September climatology (2001-2018 baseline)
print("Computing September climatology (2001-2018)...")
sept_data = ceres.sel(time=ceres.time.dt.month == 9)
sept_baseline = sept_data.sel(time=slice("2001-01-01", "2018-12-31")).mean(dim="time")

# September 2023 and 2024
sept_2023 = sept_data.sel(time="2023").mean(dim="time") if len(sept_data.sel(time="2023").time) > 0 else None
sept_2024 = sept_data.sel(time="2024").mean(dim="time") if len(sept_data.sel(time="2024").time) > 0 else None

print(f"  Sept baseline: {len(sept_data.sel(time=slice('2001','2018')).time)} months")
print(f"  Sept 2023: {'available' if sept_2023 is not None else 'missing'}")
print(f"  Sept 2024: {'available' if sept_2024 is not None else 'missing'}")

# Load AIRS September data
print("Loading AIRS September files...")
airs_sept_files = sorted(Path("data/airs").glob("AIRS.*.09.*.hdf"))
print(f"  Found {len(airs_sept_files)} September files: {[f.name.split('.')[1] for f in airs_sept_files]}")

airs_septs = {}
for f in airs_sept_files:
    m = re.search(r"AIRS\.(\d{4})\.", f.name)
    year = int(m.group(1))
    airs_septs[year] = read_airs_wv(f)

# AIRS September baseline
if len([y for y in airs_septs if y < 2019]) > 0:
    airs_sept_baseline = xr.concat([airs_septs[y] for y in airs_septs if y < 2019], dim="time").mean(dim="time")
else:
    # Use 2019 as reference if no earlier data
    airs_sept_baseline = airs_septs.get(2019, None)


# ===========================================================================
# Figure 1: Wide-view OLR anomaly maps for September 2023 (Daniel)
# ===========================================================================
print("\n--- Storm Daniel: September 2023 OLR anomaly ---")

WIDE_VIEW = {"lat": (-15, 55), "lon": (-60, 50)}

for var, info, cmap in [
    ("toa_lw_all_mon", {"label": "OLR Anomaly", "units": "W/m2"}, "RdBu_r"),
    ("cldarea_total_daynight_mon", {"label": "Cloud Fraction Anomaly", "units": "%"}, "BrBG"),
    ("cre_lw", {"label": "CRE Anomaly", "units": "W/m2"}, "BrBG"),
]:
    if sept_2023 is None:
        continue

    anomaly = sept_2023[var] - sept_baseline[var]
    anom_region = anomaly.sel(lat=lat_slice(anomaly, WIDE_VIEW["lat"]),
                               lon=slice(WIDE_VIEW["lon"][0], WIDE_VIEW["lon"][1]))

    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(figsize=(16, 8), subplot_kw={"projection": proj})

    max_abs = float(max(abs(anom_region.min(skipna=True)),
                        abs(anom_region.max(skipna=True))))
    if max_abs == 0:
        max_abs = 1

    im = anom_region.plot(ax=ax, transform=proj, cmap=cmap,
                           vmin=-max_abs, vmax=max_abs, add_colorbar=False)
    plt.colorbar(im, ax=ax, shrink=0.6, label=f"delta {info['units']}", pad=0.02)

    ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")

    # Mark forest source regions
    for name, src in SOURCES.items():
        lat_r, lon_r = src["lat"], src["lon"]
        lons = [lon_r[0], lon_r[1], lon_r[1], lon_r[0], lon_r[0]]
        lats = [lat_r[0], lat_r[0], lat_r[1], lat_r[1], lat_r[0]]
        ax.plot(lons, lats, color=src["color"], linewidth=2.5, transform=proj)
        ax.text(np.mean(lon_r), lat_r[1] + 1, name, fontsize=9,
                color=src["color"], fontweight="bold", transform=proj, ha="center")

    # Mark storm location
    storm = STORMS["Daniel"]
    ax.plot(storm["lon"], storm["lat"], "r*", markersize=20, transform=proj,
            markeredgecolor="black", markeredgewidth=0.5)
    ax.text(storm["lon"] + 1, storm["lat"] + 1, f"Storm Daniel\n{storm['location']}",
            fontsize=10, color="red", fontweight="bold", transform=proj)

    # Draw conceptual moisture displacement arrow
    ax.annotate("", xy=(22, 33), xytext=(-5, 0),
                arrowprops=dict(arrowstyle="->", color="#e63946", lw=2.5),
                transform=proj)
    ax.text(8, 15, "Displaced\nmoisture?", fontsize=10, color="#e63946",
            transform=proj, ha="center", fontstyle="italic")

    ax.set_extent([WIDE_VIEW["lon"][0], WIDE_VIEW["lon"][1],
                   WIDE_VIEW["lat"][0], WIDE_VIEW["lat"][1]], crs=proj)
    ax.gridlines(draw_labels=True, alpha=0.3, linewidth=0.5)

    safe = var.replace("_mon", "").replace("_total_daynight", "")
    fig.suptitle(f"September 2023 {info['label']} (vs 2001-2018 climatology)\n"
                 f"Forest sources + Storm Daniel location",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    fname = f"storm_daniel_{safe}_anomaly.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")


# ===========================================================================
# Figure 2: Same for Storm Boris (Sept 2024) if data available
# ===========================================================================
if sept_2024 is not None:
    print("\n--- Storm Boris: September 2024 OLR anomaly ---")
    for var, info, cmap in [
        ("toa_lw_all_mon", {"label": "OLR Anomaly", "units": "W/m2"}, "RdBu_r"),
        ("cldarea_total_daynight_mon", {"label": "Cloud Fraction Anomaly", "units": "%"}, "BrBG"),
    ]:
        anomaly = sept_2024[var] - sept_baseline[var]
        anom_region = anomaly.sel(lat=lat_slice(anomaly, WIDE_VIEW["lat"]),
                                   lon=slice(WIDE_VIEW["lon"][0], WIDE_VIEW["lon"][1]))

        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(figsize=(16, 8), subplot_kw={"projection": proj})
        max_abs = float(max(abs(anom_region.min(skipna=True)),
                            abs(anom_region.max(skipna=True)))) or 1
        im = anom_region.plot(ax=ax, transform=proj, cmap=cmap,
                               vmin=-max_abs, vmax=max_abs, add_colorbar=False)
        plt.colorbar(im, ax=ax, shrink=0.6, label=f"delta {info['units']}", pad=0.02)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")

        for name, src in SOURCES.items():
            lat_r, lon_r = src["lat"], src["lon"]
            lons = [lon_r[0], lon_r[1], lon_r[1], lon_r[0], lon_r[0]]
            lats = [lat_r[0], lat_r[0], lat_r[1], lat_r[1], lat_r[0]]
            ax.plot(lons, lats, color=src["color"], linewidth=2.5, transform=proj)

        storm = STORMS["Boris"]
        ax.plot(storm["lon"], storm["lat"], "r*", markersize=20, transform=proj,
                markeredgecolor="black", markeredgewidth=0.5)
        ax.text(storm["lon"] + 1, storm["lat"] + 1, f"Storm Boris\n{storm['location']}",
                fontsize=10, color="red", fontweight="bold", transform=proj)

        ax.set_extent([WIDE_VIEW["lon"][0], WIDE_VIEW["lon"][1],
                       WIDE_VIEW["lat"][0], WIDE_VIEW["lat"][1]], crs=proj)
        ax.gridlines(draw_labels=True, alpha=0.3, linewidth=0.5)

        safe = var.replace("_mon", "").replace("_total_daynight", "")
        fig.suptitle(f"September 2024 {info['label']} (vs 2001-2018 climatology)\n"
                     f"Forest sources + Storm Boris location",
                     fontsize=14, fontweight="bold")
        plt.tight_layout()
        fname = f"storm_boris_{safe}_anomaly.png"
        fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Saved: {fname}")
else:
    print("\nSept 2024 not in CERES data range — Boris analysis skipped")


# ===========================================================================
# Figure 3: AIRS water vapor anomaly for September 2023
# ===========================================================================
if 2023 in airs_septs and airs_sept_baseline is not None:
    print("\n--- AIRS water vapor anomaly Sept 2023 ---")
    wv_anom = airs_septs[2023] - airs_sept_baseline
    wv_region = wv_anom.sel(lat=slice(WIDE_VIEW["lat"][0], WIDE_VIEW["lat"][1]),
                             lon=slice(WIDE_VIEW["lon"][0], WIDE_VIEW["lon"][1]))

    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(figsize=(16, 8), subplot_kw={"projection": proj})
    max_abs = float(max(abs(wv_region.min(skipna=True)),
                        abs(wv_region.max(skipna=True)))) or 1
    im = wv_region.plot(ax=ax, transform=proj, cmap="BrBG",
                         vmin=-max_abs, vmax=max_abs, add_colorbar=False)
    plt.colorbar(im, ax=ax, shrink=0.6, label="delta kg/m2", pad=0.02)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")

    for name, src in SOURCES.items():
        lat_r, lon_r = src["lat"], src["lon"]
        lons = [lon_r[0], lon_r[1], lon_r[1], lon_r[0], lon_r[0]]
        lats = [lat_r[0], lat_r[0], lat_r[1], lat_r[1], lat_r[0]]
        ax.plot(lons, lats, color=src["color"], linewidth=2.5, transform=proj)
        ax.text(np.mean(lon_r), lat_r[1] + 1, name, fontsize=9,
                color=src["color"], fontweight="bold", transform=proj, ha="center")

    storm = STORMS["Daniel"]
    ax.plot(storm["lon"], storm["lat"], "r*", markersize=20, transform=proj,
            markeredgecolor="black", markeredgewidth=0.5)
    ax.text(storm["lon"] + 1, storm["lat"] + 1, "Storm Daniel",
            fontsize=10, color="red", fontweight="bold", transform=proj)

    ax.set_extent([WIDE_VIEW["lon"][0], WIDE_VIEW["lon"][1],
                   WIDE_VIEW["lat"][0], WIDE_VIEW["lat"][1]], crs=proj)
    ax.gridlines(draw_labels=True, alpha=0.3, linewidth=0.5)

    fig.suptitle("September 2023: Water Vapor Anomaly (AIRS vs 2019 baseline)\n"
                 "Brown = drier than normal | Green = wetter than normal",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "storm_daniel_airs_wv_anomaly.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: storm_daniel_airs_wv_anomaly.png")


# ===========================================================================
# Figure 4: Dipole quantification — source vs sink
# ===========================================================================
print("\n--- Moisture dipole quantification ---")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel 1: September OLR anomaly at source vs storm region
if sept_2023 is not None:
    ax = axes[0]
    regions_compare = {
        "Amazon\n(source)": {"lat": (-7, -3), "lon": (-52, -47)},
        "Congo\n(source)": {"lat": (-5, 5), "lon": (15, 30)},
        "Tropical\nAtlantic": {"lat": (-10, 10), "lon": (-40, 0)},
        "E. Mediterranean\n(Daniel)": {"lat": (28, 38), "lon": (15, 30)},
    }
    colors_r = ["#2a9d8f", "#e9c46a", "#264653", "#e63946"]

    olr_anomalies = []
    for (name, bounds), color in zip(regions_compare.items(), colors_r):
        anom = (sept_2023["toa_lw_all_mon"] - sept_baseline["toa_lw_all_mon"])
        region = anom.sel(lat=lat_slice(anom, bounds["lat"]),
                          lon=slice(bounds["lon"][0], bounds["lon"][1]))
        val = float(region.mean(skipna=True))
        olr_anomalies.append(val)

    ax.bar(range(len(regions_compare)), olr_anomalies, color=colors_r, alpha=0.85,
           edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(len(regions_compare)))
    ax.set_xticklabels(regions_compare.keys(), fontsize=9)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("OLR Anomaly (W/m2)")
    ax.set_title("September 2023: OLR Anomaly by Region", fontsize=11)
    ax.grid(alpha=0.3, axis="y")

    # Panel 2: Cloud fraction anomaly
    ax = axes[1]
    cld_anomalies = []
    for (name, bounds), color in zip(regions_compare.items(), colors_r):
        anom = (sept_2023["cldarea_total_daynight_mon"] -
                sept_baseline["cldarea_total_daynight_mon"])
        region = anom.sel(lat=lat_slice(anom, bounds["lat"]),
                          lon=slice(bounds["lon"][0], bounds["lon"][1]))
        val = float(region.mean(skipna=True))
        cld_anomalies.append(val)

    ax.bar(range(len(regions_compare)), cld_anomalies, color=colors_r, alpha=0.85,
           edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(len(regions_compare)))
    ax.set_xticklabels(regions_compare.keys(), fontsize=9)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Cloud Fraction Anomaly (%)")
    ax.set_title("September 2023: Cloud Anomaly by Region", fontsize=11)
    ax.grid(alpha=0.3, axis="y")

fig.suptitle("Moisture Dipole: Forest Sources vs Storm Destination\n"
             "Do the tropical sources show deficit while the storm region shows surplus?",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "storm_moisture_dipole.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: storm_moisture_dipole.png")


# ===========================================================================
# Summary
# ===========================================================================
print("\n=== STORM DISPLACEMENT SUMMARY ===\n")
print("September 2023 anomalies vs 2001-2018 climatology:\n")

if sept_2023 is not None:
    regions_all = {
        "Amazon (Maraba)": {"lat": (-7, -3), "lon": (-52, -47)},
        "Congo Basin": {"lat": (-5, 5), "lon": (15, 30)},
        "Tropical Atlantic": {"lat": (-10, 10), "lon": (-40, 0)},
        "E. Mediterranean (Daniel)": {"lat": (28, 38), "lon": (15, 30)},
        "Central Europe (Boris path)": {"lat": (44, 54), "lon": (10, 25)},
    }

    print(f"{'Region':35s} {'OLR anom':>10s} {'Cloud anom':>10s} {'CRE anom':>10s}")
    print("-" * 70)
    for name, bounds in regions_all.items():
        for var_name, label in [("toa_lw_all_mon", "OLR"),
                                  ("cldarea_total_daynight_mon", "Cloud"),
                                  ("cre_lw", "CRE")]:
            anom = sept_2023[var_name] - sept_baseline[var_name]
            region = anom.sel(lat=lat_slice(anom, bounds["lat"]),
                              lon=slice(bounds["lon"][0], bounds["lon"][1]))
            val = float(region.mean(skipna=True))
            if label == "OLR":
                olr_v = val
            elif label == "Cloud":
                cld_v = val
            else:
                cre_v = val
        print(f"{name:35s} {olr_v:+10.2f} {cld_v:+10.2f} {cre_v:+10.2f}")

print("\n=== DONE ===")

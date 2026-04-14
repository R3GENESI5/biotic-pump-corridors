# %% [markdown]
# # Biotic Pump: Testing ET ↓ → OLR ↑ in 2019 vs 2023
#
# **Hypothesis**: Condensation-driven circulation stalled in key tropical regions,
# causing evapotranspiration (ET) to drop, cloud cover to thin, and outgoing
# longwave radiation (OLR) to increase — signatures of a weakened biotic pump.
#
# **Strongest signal first**: CERES EBAF OLR (reliable, global, monthly NetCDF),
# then MODIS ET, then AIRS water vapor and cloud analysis.
#
# **Focal regions**: Marabá (Amazon), Congo Basin, Tropical Atlantic.
#
# ---

# %% [markdown]
# ## 0. Setup
#
# Run this cell once to install dependencies (uncomment for Colab):
# ```
# !pip install earthaccess xarray netCDF4 matplotlib cartopy numpy pandas
# ```

# %%
import sys
from pathlib import Path

# Allow imports from project root
PROJECT_ROOT = Path("..").resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import earthaccess
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from src.config import REGIONS, FOCUS_YEARS, BASELINE_PERIOD, DATA_DIR, OUTPUT_DIR
from src.data_access import authenticate, discover_products, fetch_ceres
from src.processing import (
    load_ceres, subset_region, annual_mean, seasonal_mean,
    compute_anomaly, regional_timeseries, cloud_radiative_effect,
)
from src.visualization import (
    plot_region_map, plot_comparison_maps, plot_tropical_overview, plot_timeseries,
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print("Imports OK")

# %% [markdown]
# ## 1. Authenticate with NASA Earthdata
#
# First run will prompt for your Earthdata username and password.
# Credentials are stored in `~/.netrc` so you only do this once.

# %%
authenticate()

# %% [markdown]
# ## 2. Focal Regions
#
# Three regions selected based on Ali's analysis of EUMETSAT composites:
# - **Marabá**: Eastern Amazon, where ET drop and OLR increase were observed
# - **Congo Basin**: Record drought in 2023, paired deforestation pressure
# - **Tropical Atlantic**: Ocean corridor between the two forest regions,
#   where cloud cover anomalies were flagged
#
# > **Insight from Makarieva**: The biotic pump only needs to break along
# > a narrow coastal strip to interrupt inland moisture transport.
# > Watch for coast-to-interior gradients, not just interior averages.

# %%
fig, ax = plot_region_map(REGIONS)
fig.savefig(OUTPUT_DIR / "focal_regions.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 3. CERES OLR — Data Access
#
# CERES EBAF provides monthly top-of-atmosphere radiative fluxes at 1° resolution.
# We need two variables:
# - `toa_lw_all_mon`: All-sky OLR (total longwave leaving Earth)
# - `toa_lw_clr_t_mon`: Clear-sky OLR (what OLR would be without clouds)
#
# The difference (clear - all) is the **longwave cloud radiative effect (CRE)**.
# If CRE decreases → clouds are doing less to trap heat → fewer/thinner clouds.

# %%
# First, discover what CERES products are available
# (Run this if the fetch below returns 0 results)
discover_products("CERES EBAF")

# %%
# Download CERES EBAF data
ceres_files = fetch_ceres(FOCUS_YEARS, DATA_DIR)
print(f"\nDownloaded files: {[f.name for f in ceres_files]}")

# %%
# Load into xarray
ceres = load_ceres(ceres_files)
print(ceres)
print(f"\nAvailable variables: {list(ceres.data_vars)}")
print(f"Time range: {ceres.time.values[0]} to {ceres.time.values[-1]}")

# %% [markdown]
# ## 4. Sanity Check — Global OLR Map
#
# Quick visual check that the data loaded correctly.

# %%
# Plot global OLR for the first month in the dataset
sample = ceres["toa_lw_all_mon"].isel(time=0)
fig, ax = plt.subplots(figsize=(14, 6), subplot_kw={"projection": ccrs.PlateCarree()})
sample.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="inferno",
            cbar_kwargs={"label": "OLR (W/m²)", "shrink": 0.6})
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.set_title(f"Global OLR — {str(sample.time.values)[:7]}", fontsize=13)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 5. OLR Comparison Maps — 2019 vs 2023
#
# For each focal region, we compute the annual mean OLR and create:
# 1. Side-by-side maps (2019, 2023)
# 2. Difference map (2023 − 2019)
#
# **What to look for**: Positive difference (red) = OLR increased = less cloud
# shielding or hotter surface → consistent with weakened biotic pump.

# %%
# Compute annual mean OLR for both years
olr_2019 = annual_mean(ceres, "toa_lw_all_mon", 2019)
olr_2023 = annual_mean(ceres, "toa_lw_all_mon", 2023)

print(f"2019 global mean OLR: {float(olr_2019.mean()):.1f} W/m²")
print(f"2023 global mean OLR: {float(olr_2023.mean()):.1f} W/m²")
print(f"Global difference:    {float((olr_2023 - olr_2019).mean()):.2f} W/m²")

# %%
# Regional comparison maps
for key, region in REGIONS.items():
    lat, lon = region["bounds"]["lat"], region["bounds"]["lon"]
    r2019 = subset_region(olr_2019, lat, lon)
    r2023 = subset_region(olr_2023, lat, lon)

    fig = plot_comparison_maps(
        r2019, r2023,
        region_name=region["name"],
        variable_label="Outgoing Longwave Radiation",
        units="W/m²",
        cmap="inferno",
    )
    fig.savefig(OUTPUT_DIR / f"olr_comparison_{key}.png", dpi=150, bbox_inches="tight")
    plt.show()

    # Print regional statistics
    diff = float((r2023 - r2019).mean())
    print(f"  {region['name']}: mean OLR change = {diff:+.2f} W/m²")
    print()

# %% [markdown]
# ## 6. Tropical Overview — OLR Difference
#
# Wide view across the tropics (30°S–30°N) to see the full spatial pattern
# of OLR changes. This shows whether the signal is localized to our focal
# regions or part of a broader pattern.

# %%
# Subset to tropics
tropic_2019 = subset_region(olr_2019, (-30, 30), (-60, 50))
tropic_2023 = subset_region(olr_2023, (-30, 30), (-60, 50))

fig = plot_tropical_overview(
    tropic_2019, tropic_2023,
    variable_label="OLR", units="W/m²",
    cmap="inferno",
)
fig.savefig(OUTPUT_DIR / "olr_tropical_overview.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 7. Cloud Radiative Effect (CRE)
#
# The longwave CRE tells us directly how much clouds are reducing OLR.
#
# `CRE_LW = OLR_clear_sky - OLR_all_sky`
#
# - **High CRE** → clouds are trapping a lot of longwave → thick convective clouds
# - **Low CRE** → clouds doing less → thinner clouds or clear skies
#
# A **decrease** in CRE from 2019 to 2023 would mean fewer/thinner clouds,
# directly supporting the "reduced cloud cover" part of the hypothesis.

# %%
# Compute cloud radiative effect
# NOTE: adjust variable names if your CERES file uses different names
# Check: list(ceres.data_vars) to see available variables
try:
    cre = cloud_radiative_effect(ceres)
    cre_2019 = cre.sel(time=slice("2019-01-01", "2019-12-31")).mean(dim="time")
    cre_2023 = cre.sel(time=slice("2023-01-01", "2023-12-31")).mean(dim="time")

    for key, region in REGIONS.items():
        lat, lon = region["bounds"]["lat"], region["bounds"]["lon"]
        r2019 = subset_region(cre_2019, lat, lon)
        r2023 = subset_region(cre_2023, lat, lon)

        fig = plot_comparison_maps(
            r2019, r2023,
            region_name=region["name"],
            variable_label="LW Cloud Radiative Effect",
            units="W/m²",
            cmap="YlGnBu",
        )
        fig.savefig(OUTPUT_DIR / f"cre_comparison_{key}.png", dpi=150, bbox_inches="tight")
        plt.show()

        diff = float((r2023 - r2019).mean())
        print(f"  {region['name']}: mean CRE change = {diff:+.2f} W/m²")

except KeyError as e:
    print(f"Clear-sky OLR variable not found: {e}")
    print(f"Available variables: {list(ceres.data_vars)}")
    print("Check the variable names and update PRODUCTS config in src/config.py")

# %% [markdown]
# ## 8. OLR Time Series
#
# Monthly regional means over the full data period, with 2019 and 2023 highlighted.
# Look for: upward trend, seasonal changes, or abrupt shifts in the focus years.

# %%
ts_dict = {}
for key, region in REGIONS.items():
    lat, lon = region["bounds"]["lat"], region["bounds"]["lon"]
    ts = regional_timeseries(ceres, "toa_lw_all_mon", lat, lon)
    ts_dict[region["name"]] = ts

fig = plot_timeseries(ts_dict, "OLR", "W/m²", focus_years=FOCUS_YEARS)
fig.savefig(OUTPUT_DIR / "olr_timeseries.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 9. Coast-to-Interior OLR Gradient (Amazon)
#
# Makarieva argues the biotic pump pulls moisture inland from the coast.
# If the pump weakens, the coast-to-interior moisture gradient steepens.
# We can test this with OLR: if interior OLR rises more than coastal OLR,
# the pump is failing to distribute energy/moisture inland.

# %%
# Define coastal and interior strips for the Amazon
# Coastal: within ~200km of Atlantic coast
coastal_amazon = {"lat": (-7.0, 0.0), "lon": (-48.0, -44.0)}
interior_amazon = {"lat": (-7.0, 0.0), "lon": (-60.0, -56.0)}

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for label, bounds, ax in [
    ("Coastal Amazon", coastal_amazon, axes[0]),
    ("Interior Amazon", interior_amazon, axes[1]),
]:
    ts = regional_timeseries(
        ceres, "toa_lw_all_mon", bounds["lat"], bounds["lon"]
    )
    ts.plot(ax=ax, linewidth=0.6, alpha=0.7, color="#264653")

    if len(ts) > 12:
        rolling = ts.rolling(time=12, center=True).mean()
        rolling.plot(ax=ax, linewidth=2, color="#e63946")

    for year in FOCUS_YEARS:
        ax.axvspan(f"{year}-01-01", f"{year}-12-31", alpha=0.1, color="#e63946")

    ax.set_title(label, fontsize=12)
    ax.set_ylabel("OLR (W/m²)")
    ax.grid(alpha=0.3)

plt.suptitle("Coast vs Interior OLR — Amazon", fontsize=13)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "olr_coast_interior_amazon.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ---
# ## 10. Next Steps — MODIS ET and AIRS Water Vapor
#
# With the OLR baseline established, the next phases will:
#
# 1. **MODIS ET (MOD16A2GF)**: Download 8-day ET composites for focal regions,
#    aggregate to monthly/annual, and create the same comparison maps.
#    This directly tests the ET↓ side of the hypothesis.
#
# 2. **AIRS Water Vapor (AIRS3STM)**: Column water vapor maps show whether
#    moisture is being redistributed (less over forests, more elsewhere).
#
# 3. **Combined analysis**: Scatter plot ET vs OLR per grid cell to test
#    whether ET decline correlates spatially with OLR increase.
#
# 4. **Storm tracks**: Overlay the moisture displacement with the tracks
#    of Storm Daniel (2023) and Storm Boris (2024) to test whether
#    displaced biotic pump moisture fueled those events.

# %% [markdown]
# ### MODIS ET — Scaffold
#
# The MODIS pipeline is more complex because the data arrives as tiled HDF
# files in sinusoidal projection. Below is the search/download step; the
# processing code will be added in the next notebook.

# %%
# Search for MODIS ET data for the Marabá region (as a test)
# This will show how many granules exist — can be hundreds of tiles
from src.data_access import fetch_modis_et

# Uncomment to run (may download many files):
# maraba_et_files = fetch_modis_et(
#     years=[2019, 2023],
#     region_bounds=REGIONS["maraba"]["bounds"],
#     data_dir=DATA_DIR,
# )
# print(f"MODIS ET files: {len(maraba_et_files)}")

# %% [markdown]
# ### AIRS Water Vapor — Scaffold

# %%
# Uncomment to download AIRS monthly data:
# from src.data_access import fetch_airs_wv
# airs_files = fetch_airs_wv(years=[2019, 2023], data_dir=DATA_DIR)

# %% [markdown]
# ---
# *Biotic Pump Satellite Analysis — built for the investigation described
# by Ali, Rob, and the team. See Makarieva & Gorshkov for the theoretical
# framework behind condensation-driven atmospheric circulation.*

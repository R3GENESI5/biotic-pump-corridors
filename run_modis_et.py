"""Run MODIS ET comparison analysis for Maraba and Congo."""
import sys
sys.path.insert(0, ".")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path

from src.modis_et import process_region_year

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

regions = {
    "maraba": {"name": "Maraba, Amazon", "lat": (-7.0, -3.0), "lon": (-52.0, -47.0)},
    "congo":  {"name": "Congo Basin",    "lat": (-5.0, 5.0),   "lon": (15.0, 30.0)},
}

print("=== Processing MODIS ET ===\n")
results = {}
for key, r in regions.items():
    for year in [2019, 2023]:
        da = process_region_year(
            "data/modis_et", r["name"], year, r["lat"], r["lon"]
        )
        results[(key, year)] = da
        mean_val = float(da.mean(skipna=True))
        print(f"    Mean ET: {mean_val:.1f} mm/yr\n")


print("\n=== Generating ET Comparison Maps ===\n")
for key, r in regions.items():
    et_2019 = results[(key, 2019)]
    et_2023 = results[(key, 2023)]
    diff = et_2023 - et_2019

    proj = ccrs.PlateCarree()
    fig, axes = plt.subplots(1, 3, figsize=(20, 6), subplot_kw={"projection": proj})

    vmin = float(min(et_2019.min(skipna=True), et_2023.min(skipna=True)))
    vmax = float(max(et_2019.max(skipna=True), et_2023.max(skipna=True)))

    for ax in axes:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
        ax.add_feature(cfeature.RIVERS, linewidth=0.3, alpha=0.5)

    im1 = et_2019.plot(ax=axes[0], transform=proj, cmap="YlGn",
                        vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[0].set_title("2019", fontsize=12)
    plt.colorbar(im1, ax=axes[0], shrink=0.7, label="mm/yr", pad=0.02)

    im2 = et_2023.plot(ax=axes[1], transform=proj, cmap="YlGn",
                        vmin=vmin, vmax=vmax, add_colorbar=False)
    axes[1].set_title("2023", fontsize=12)
    plt.colorbar(im2, ax=axes[1], shrink=0.7, label="mm/yr", pad=0.02)

    max_abs = float(max(abs(np.nanmin(diff)), abs(np.nanmax(diff))))
    if max_abs == 0:
        max_abs = 1
    im3 = diff.plot(ax=axes[2], transform=proj, cmap="BrBG",
                     vmin=-max_abs, vmax=max_abs, add_colorbar=False)
    axes[2].set_title("2023 - 2019", fontsize=12)
    plt.colorbar(im3, ax=axes[2], shrink=0.7, label="mm/yr delta", pad=0.02)

    fig.suptitle(f"{r['name']}: Evapotranspiration (MODIS MOD16A3GF)",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    fname = f"et_comparison_{key}.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()

    mean_diff = float(diff.mean(skipna=True))
    print(f"  {r['name']:25s} delta_ET = {mean_diff:+.1f} mm/yr  -> saved {fname}")


print("\n=== SUMMARY ===\n")
print(f"{'Region':25s} {'ET 2019':>10s} {'ET 2023':>10s} {'delta':>10s} {'Change':>8s}")
print("-" * 68)
for key, r in regions.items():
    m19 = float(results[(key, 2019)].mean(skipna=True))
    m23 = float(results[(key, 2023)].mean(skipna=True))
    d = m23 - m19
    pct = 100 * d / m19 if m19 != 0 else 0
    print(f"{r['name']:25s} {m19:10.1f} {m23:10.1f} {d:+10.1f} {pct:+7.1f}%")

print("\nDone.")

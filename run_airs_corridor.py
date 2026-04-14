"""AIRS water vapor transects along the Belem-Manaus corridor.

Reads AIRS L3 monthly HDF4 files, extracts total column water vapor,
and creates corridor transect plots comparing 2019 vs 2023.
"""
import os
os.add_dll_directory(os.path.join(os.path.dirname(__file__), ".venv", "Lib", "site-packages", "pyhdf"))

import sys
sys.path.insert(0, ".")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pyhdf.SD import SD, SDC
from pathlib import Path
import re

OUTPUT_DIR = Path("outputs")

LANDMARKS = {
    "Belem": (-1.4, -48.5),
    "Maraba": (-5.4, -49.1),
    "Altamira": (-3.2, -52.2),
    "Itaituba": (-4.3, -55.9),
    "Manaus": (-3.1, -60.0),
}
LAT_BAND = (-6.0, 0.0)
LON_RANGE = (-62.0, -47.0)


def inspect_airs_file(filepath):
    """Print all datasets in an AIRS HDF4 file."""
    sd = SD(str(filepath), SDC.READ)
    print(f"\nFile: {filepath.name}")
    print(f"Global attrs: {list(sd.attributes().keys())[:10]}")
    print(f"\nDatasets ({len(sd.datasets())}):")
    for name, info in sorted(sd.datasets().items()):
        dims, shape, dtype, nattrs = info
        if "H2O" in name or "Vapor" in name or "humidity" in name.lower():
            print(f"  *** {name:40s} shape={shape}")
        elif shape == (180, 360) or shape == (360, 180):
            # Likely a gridded variable at 1-degree
            print(f"      {name:40s} shape={shape}")
    sd.end()


def read_airs_wv(filepath):
    """Read total column water vapor from AIRS monthly L3 file.

    Returns xarray DataArray with lat/lon coordinates.
    """
    sd = SD(str(filepath), SDC.READ)

    # Try common variable names for total column water vapor
    wv_names = ["TotH2OVap_A", "TotH2OVap_D", "H2O_MMR_TqJ_A",
                "totH2OStd_A", "totH2OStd", "TotH2OVap"]

    wv_data = None
    used_name = None
    for name in wv_names:
        try:
            sds = sd.select(name)
            wv_data = sds.get().astype(np.float64)
            attrs = sds.attributes()
            used_name = name
            break
        except Exception:
            continue

    if wv_data is None:
        # Fallback: look for anything with H2O in name
        for name in sd.datasets():
            if "H2O" in name or "Vapor" in name:
                sds = sd.select(name)
                shape = sds.get().shape
                if len(shape) == 2:
                    wv_data = sds.get().astype(np.float64)
                    attrs = sds.attributes()
                    used_name = name
                    break

    sd.end()

    if wv_data is None:
        raise ValueError(f"No water vapor variable found in {filepath.name}")

    # Apply fill value masking
    fill = attrs.get("_FillValue", -9999)
    wv_data[wv_data == fill] = np.nan

    # AIRS L3 monthly is on a 1x1 degree global grid
    # lat: -89.5 to 89.5, lon: -179.5 to 179.5
    if wv_data.shape == (180, 360):
        lat = np.arange(-89.5, 90, 1.0)
        lon = np.arange(-179.5, 180, 1.0)
    elif wv_data.shape == (360, 180):
        wv_data = wv_data.T
        lat = np.arange(-89.5, 90, 1.0)
        lon = np.arange(-179.5, 180, 1.0)
    else:
        raise ValueError(f"Unexpected shape {wv_data.shape} for {used_name}")

    # Extract year/month from filename
    m = re.search(r"AIRS\.(\d{4})\.(\d{2})\.", filepath.name)
    year, month = int(m.group(1)), int(m.group(2))

    units = attrs.get("units", attrs.get("Unit", "kg/m2"))

    da = xr.DataArray(
        wv_data,
        dims=["lat", "lon"],
        coords={"lat": lat, "lon": lon},
        name="TotH2OVap",
        attrs={"units": str(units), "long_name": f"Total Column Water Vapor",
               "source_var": used_name, "year": year, "month": month},
    )
    return da


def load_airs_annual(data_dir, year):
    """Load all AIRS monthly files for a year and compute annual mean."""
    pattern = f"AIRS.{year}.*.hdf"
    files = sorted(Path(data_dir).glob(pattern))
    print(f"  {year}: {len(files)} monthly files")

    monthly = []
    for f in files:
        try:
            da = read_airs_wv(f)
            monthly.append(da)
        except Exception as e:
            print(f"    Warning: {f.name}: {e}")

    if not monthly:
        raise ValueError(f"No valid AIRS data for {year}")

    stacked = xr.concat(monthly, dim="time")
    return stacked.mean(dim="time")


def main():
    data_dir = Path("data/airs")
    airs_files = sorted(data_dir.glob("*.hdf"))

    if not airs_files:
        print("No AIRS files found in data/airs/. Run download first.")
        return

    # Inspect first file
    inspect_airs_file(airs_files[0])

    # Load annual means
    print("\n=== Loading AIRS Water Vapor ===")
    wv_2019 = load_airs_annual(data_dir, 2019)
    wv_2023 = load_airs_annual(data_dir, 2023)
    print(f"\n  2019 global mean WV: {float(wv_2019.mean(skipna=True)):.1f} {wv_2019.attrs.get('units', '')}")
    print(f"  2023 global mean WV: {float(wv_2023.mean(skipna=True)):.1f} {wv_2023.attrs.get('units', '')}")

    units = wv_2019.attrs.get("units", "kg/m2")

    # ===================================================================
    # Figure 1: Corridor transect — water vapor 2019 vs 2023
    # ===================================================================
    print("\n--- Water vapor corridor transect ---")

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))

    # Top: absolute values
    ax = axes[0]
    for year_data, year, color in [(wv_2019, 2019, "#264653"), (wv_2023, 2023, "#e63946")]:
        corridor = year_data.sel(
            lat=slice(LAT_BAND[0], LAT_BAND[1]),
            lon=slice(LON_RANGE[0], LON_RANGE[1]),
        )
        weights = np.cos(np.deg2rad(corridor.lat))
        transect = corridor.weighted(weights).mean(dim="lat")
        transect.plot(ax=ax, color=color, linewidth=2.5, label=str(year))

    for name, (lat, lon) in LANDMARKS.items():
        ax.axvline(lon, color="gray", alpha=0.3, linewidth=0.8)
        ax.text(lon, ax.get_ylim()[1], f" {name}", rotation=45,
                fontsize=8, ha="left", va="bottom", color="#555")

    ax.set_title("Total Column Water Vapor Along Corridor", fontsize=12)
    ax.set_ylabel(f"Water Vapor ({units})")
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    ax.set_xlabel("")

    # Bottom: difference
    ax = axes[1]
    diff = wv_2023 - wv_2019
    corridor_diff = diff.sel(
        lat=slice(LAT_BAND[0], LAT_BAND[1]),
        lon=slice(LON_RANGE[0], LON_RANGE[1]),
    )
    weights = np.cos(np.deg2rad(corridor_diff.lat))
    transect_diff = corridor_diff.weighted(weights).mean(dim="lat")

    colors = ["#e63946" if float(transect_diff.sel(lon=lon, method="nearest")) < 0
              else "#457b9d" for lon in transect_diff.lon.values]
    ax.bar(transect_diff.lon.values, transect_diff.values,
           width=0.9, color=colors, alpha=0.8, edgecolor="white", linewidth=0.3)
    ax.axhline(0, color="black", linewidth=0.5)

    for name, (lat, lon) in LANDMARKS.items():
        ax.axvline(lon, color="gray", alpha=0.3, linewidth=0.8)

    ax.set_title("Change in Water Vapor (2023 - 2019)", fontsize=12)
    ax.set_ylabel(f"Delta {units}")
    ax.set_xlabel("Longitude")
    ax.grid(alpha=0.3, axis="y")

    fig.suptitle("AIRS Column Water Vapor: Belem-Manaus Corridor",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "airs_corridor_transect.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: airs_corridor_transect.png")

    # ===================================================================
    # Figure 2: Spatial map of water vapor over corridor
    # ===================================================================
    print("\n--- Water vapor corridor maps ---")
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    proj = ccrs.PlateCarree()
    fig, axes_map = plt.subplots(1, 3, figsize=(20, 5), subplot_kw={"projection": proj})

    d19 = wv_2019.sel(lat=slice(-8, 2), lon=slice(-63, -44))
    d23 = wv_2023.sel(lat=slice(-8, 2), lon=slice(-63, -44))
    dd = d23 - d19

    vmin = float(min(d19.min(skipna=True), d23.min(skipna=True)))
    vmax = float(max(d19.max(skipna=True), d23.max(skipna=True)))

    for ax in axes_map:
        ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
        ax.add_feature(cfeature.RIVERS, linewidth=0.4, alpha=0.6, color="#4a90d9")
        lons_path = [v[1] for v in LANDMARKS.values()]
        lats_path = [v[0] for v in LANDMARKS.values()]
        ax.plot(lons_path, lats_path, "k--", linewidth=1.5, alpha=0.6, transform=proj)
        for name, (lt, ln) in LANDMARKS.items():
            if name in ["Belem", "Maraba", "Manaus"]:
                ax.plot(ln, lt, "ko", markersize=5, transform=proj)
                ax.text(ln + 0.3, lt + 0.3, name, fontsize=8, transform=proj, fontweight="bold")

    im1 = d19.plot(ax=axes_map[0], transform=proj, cmap="YlGnBu",
                   vmin=vmin, vmax=vmax, add_colorbar=False)
    axes_map[0].set_title("2019", fontsize=12)
    plt.colorbar(im1, ax=axes_map[0], shrink=0.7, label=units, pad=0.02)

    im2 = d23.plot(ax=axes_map[1], transform=proj, cmap="YlGnBu",
                   vmin=vmin, vmax=vmax, add_colorbar=False)
    axes_map[1].set_title("2023", fontsize=12)
    plt.colorbar(im2, ax=axes_map[1], shrink=0.7, label=units, pad=0.02)

    max_abs = float(max(abs(dd.min(skipna=True)), abs(dd.max(skipna=True))))
    if max_abs == 0:
        max_abs = 1
    im3 = dd.plot(ax=axes_map[2], transform=proj, cmap="BrBG",
                  vmin=-max_abs, vmax=max_abs, add_colorbar=False)
    axes_map[2].set_title("2023 - 2019", fontsize=12)
    plt.colorbar(im3, ax=axes_map[2], shrink=0.7, label=f"delta {units}", pad=0.02)

    fig.suptitle("Belem-Manaus Corridor: Total Column Water Vapor (AIRS)",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "airs_corridor_map.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: airs_corridor_map.png")

    # ===================================================================
    # Summary numbers
    # ===================================================================
    print("\n=== AIRS CORRIDOR SUMMARY ===\n")

    for label, lon_slice in [("Coast (Belem)", slice(-50, -47)),
                              ("Mid (Maraba-Altamira)", slice(-53, -49)),
                              ("Interior (Manaus)", slice(-62, -58))]:
        v19 = float(wv_2019.sel(lat=slice(LAT_BAND[0], LAT_BAND[1]),
                                lon=lon_slice).mean(skipna=True))
        v23 = float(wv_2023.sel(lat=slice(LAT_BAND[0], LAT_BAND[1]),
                                lon=lon_slice).mean(skipna=True))
        print(f"  {label:25s}  2019={v19:.1f}  2023={v23:.1f}  delta={v23-v19:+.2f} {units}")

    # Gradient
    coast_19 = float(wv_2019.sel(lat=slice(LAT_BAND[0], LAT_BAND[1]), lon=slice(-50, -47)).mean(skipna=True))
    coast_23 = float(wv_2023.sel(lat=slice(LAT_BAND[0], LAT_BAND[1]), lon=slice(-50, -47)).mean(skipna=True))
    int_19 = float(wv_2019.sel(lat=slice(LAT_BAND[0], LAT_BAND[1]), lon=slice(-62, -58)).mean(skipna=True))
    int_23 = float(wv_2023.sel(lat=slice(LAT_BAND[0], LAT_BAND[1]), lon=slice(-62, -58)).mean(skipna=True))
    grad_19 = int_19 - coast_19
    grad_23 = int_23 - coast_23
    print(f"\n  Coast-to-interior gradient:")
    print(f"    2019: {grad_19:+.2f} {units}")
    print(f"    2023: {grad_23:+.2f} {units}")
    print(f"    Shift: {grad_23 - grad_19:+.2f} {units}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()

"""Visualization: comparison maps, time series, and diagnostic plots.

All map functions use cartopy for geographic projections.
"""
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np


REGION_COLORS = ["#e63946", "#457b9d", "#2a9d8f", "#e9c46a", "#264653"]


def _add_map_features(ax):
    """Add standard geographic features to a cartopy axis."""
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
    ax.add_feature(cfeature.RIVERS, linewidth=0.3, alpha=0.5)


def plot_region_map(regions):
    """Plot a world map highlighting all focal regions."""
    fig, ax = plt.subplots(
        figsize=(15, 8), subplot_kw={"projection": ccrs.PlateCarree()}
    )
    ax.add_feature(cfeature.LAND, alpha=0.2, color="#d4c5a9")
    ax.add_feature(cfeature.OCEAN, alpha=0.2, color="#b8d4e3")
    _add_map_features(ax)

    for i, (key, r) in enumerate(regions.items()):
        lat = r["bounds"]["lat"]
        lon = r["bounds"]["lon"]
        color = REGION_COLORS[i % len(REGION_COLORS)]

        # Draw rectangle
        lons = [lon[0], lon[1], lon[1], lon[0], lon[0]]
        lats = [lat[0], lat[0], lat[1], lat[1], lat[0]]
        ax.plot(lons, lats, transform=ccrs.PlateCarree(),
                linewidth=2.5, color=color, label=r["name"])
        ax.fill(lons, lats, transform=ccrs.PlateCarree(),
                alpha=0.15, color=color)

    ax.legend(loc="lower left", fontsize=11, framealpha=0.9)
    ax.set_global()
    ax.gridlines(draw_labels=True, alpha=0.3, linewidth=0.5)
    ax.set_title("Focal Regions for Biotic Pump Analysis", fontsize=14, pad=12)
    plt.tight_layout()
    return fig, ax


def plot_comparison_maps(
    data_2019, data_2023, region_name, variable_label, units,
    cmap="YlOrRd", diff_cmap="RdBu_r"
):
    """Create 3-panel comparison: Year A, Year B, and difference.

    Parameters
    ----------
    data_2019, data_2023 : xarray.DataArray
        Already subsetted to region, 2D (lat, lon)
    region_name : str
    variable_label : str
    units : str
    cmap : str
        Colormap for absolute values
    diff_cmap : str
        Colormap for difference (diverging)
    """
    diff = data_2023 - data_2019
    proj = ccrs.PlateCarree()

    fig, axes = plt.subplots(1, 3, figsize=(20, 6), subplot_kw={"projection": proj})

    # Shared scale for the two absolute panels
    vmin = float(min(data_2019.min(), data_2023.min()))
    vmax = float(max(data_2019.max(), data_2023.max()))

    for ax in axes:
        _add_map_features(ax)

    # 2019
    im1 = data_2019.plot(
        ax=axes[0], transform=proj, cmap=cmap, vmin=vmin, vmax=vmax,
        add_colorbar=False
    )
    axes[0].set_title("2019", fontsize=12)
    plt.colorbar(im1, ax=axes[0], shrink=0.7, label=units, pad=0.02)

    # 2023
    im2 = data_2023.plot(
        ax=axes[1], transform=proj, cmap=cmap, vmin=vmin, vmax=vmax,
        add_colorbar=False
    )
    axes[1].set_title("2023", fontsize=12)
    plt.colorbar(im2, ax=axes[1], shrink=0.7, label=units, pad=0.02)

    # Difference
    max_abs = float(max(abs(diff.min()), abs(diff.max())))
    if max_abs == 0:
        max_abs = 1
    im3 = diff.plot(
        ax=axes[2], transform=proj, cmap=diff_cmap,
        vmin=-max_abs, vmax=max_abs, add_colorbar=False
    )
    axes[2].set_title("2023 \u2212 2019", fontsize=12)
    plt.colorbar(im3, ax=axes[2], shrink=0.7, label=f"\u0394 {units}", pad=0.02)

    fig.suptitle(
        f"{region_name}: {variable_label}",
        fontsize=14, fontweight="bold", y=1.02
    )
    plt.tight_layout()
    return fig


def plot_tropical_overview(data_2019, data_2023, variable_label, units,
                           cmap="YlOrRd", diff_cmap="RdBu_r"):
    """Full-tropics comparison map (30S-30N) with all regions overlaid."""
    diff = data_2023 - data_2019
    proj = ccrs.PlateCarree()

    fig, axes = plt.subplots(
        3, 1, figsize=(16, 15), subplot_kw={"projection": proj}
    )

    vmin = float(min(data_2019.min(), data_2023.min()))
    vmax = float(max(data_2019.max(), data_2023.max()))
    max_abs = float(max(abs(diff.min()), abs(diff.max())))
    if max_abs == 0:
        max_abs = 1

    configs = [
        (data_2019, f"2019 {variable_label}", cmap, vmin, vmax, units),
        (data_2023, f"2023 {variable_label}", cmap, vmin, vmax, units),
        (diff, f"Difference (2023 \u2212 2019)", diff_cmap, -max_abs, max_abs, f"\u0394 {units}"),
    ]

    for ax, (data, title, cm, lo, hi, ulabel) in zip(axes, configs):
        _add_map_features(ax)
        im = data.plot(
            ax=ax, transform=proj, cmap=cm, vmin=lo, vmax=hi, add_colorbar=False
        )
        plt.colorbar(im, ax=ax, shrink=0.6, label=ulabel, pad=0.01)
        ax.set_title(title, fontsize=12)
        ax.set_extent([-60, 50, -30, 30], crs=proj)

    fig.suptitle(f"Tropical Overview: {variable_label}", fontsize=14,
                 fontweight="bold", y=0.92)
    plt.tight_layout()
    return fig


def plot_timeseries(timeseries_dict, variable_label, units, focus_years=None):
    """Plot regional mean time series for multiple regions.

    Parameters
    ----------
    timeseries_dict : dict
        {region_name: xarray.DataArray time series}
    focus_years : list of int, optional
        Years to highlight with shading
    """
    n = len(timeseries_dict)
    fig, axes = plt.subplots(n, 1, figsize=(14, 4 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for i, (name, ts) in enumerate(timeseries_dict.items()):
        ax = axes[i]
        ts.plot(ax=ax, linewidth=0.8, color="#264653")

        # 12-month rolling mean
        if len(ts) > 12:
            rolling = ts.rolling(time=12, center=True).mean()
            rolling.plot(ax=ax, linewidth=2, color="#e63946", label="12-month mean")

        if focus_years:
            for year in focus_years:
                ax.axvspan(f"{year}-01-01", f"{year}-12-31",
                           alpha=0.12, color="#e63946")

        ax.set_title(f"{name}", fontsize=12)
        ax.set_ylabel(units)
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig

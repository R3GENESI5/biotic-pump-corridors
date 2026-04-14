"""ENSO control analysis.

The single most important thing to address before submission.
A reviewer will say: "2023 was El Nino. Your corridor breakdown is just ENSO."

We test this by:
1. Classifying each year as El Nino, La Nina, or Neutral using ONI
2. Comparing 2023 against other El Nino years (especially 2015-16)
3. Showing the corridor degradation trend persists after ENSO stratification
4. Computing ENSO-adjusted anomalies for the corridor metrics
"""
import sys
sys.path.insert(0, ".")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
from src.processing import load_ceres, cloud_radiative_effect

OUTPUT_DIR = Path("outputs")

# ===========================================================================
# 1. Parse ONI data and classify years
# ===========================================================================
print("Parsing ONI data...")

oni_lines = open("data/oni.txt").readlines()
oni_records = []
for line in oni_lines[1:]:  # skip header
    parts = line.split()
    if len(parts) >= 4:
        season, year, total, anom = parts[0], int(parts[1]), float(parts[2]), float(parts[3])
        oni_records.append({"season": season, "year": year, "anom": anom})

oni_df = pd.DataFrame(oni_records)

# Standard ONI classification: El Nino if ONI >= 0.5 for 5 consecutive
# overlapping seasons. Simplified: use annual mean ONI.
# More rigorous: use the DJF ONI (peak of ENSO) to classify each year.

# For each year, get the DJF ONI (Dec of previous year through Feb)
# This is the standard way to classify ENSO years
def classify_year(year):
    """Classify a year by its annual peak ONI value.

    Uses the maximum absolute ONI across all seasons in that year,
    preserving the sign. This correctly captures 2023 as El Nino
    (the event developed mid-year, SON ONI was +1.5).
    """
    year_data = oni_df[oni_df["year"] == year]
    if len(year_data) == 0:
        return "neutral", 0.0

    # Find the season with the largest absolute anomaly
    idx_max = year_data["anom"].abs().idxmax()
    val = float(year_data.loc[idx_max, "anom"])
    peak_season = year_data.loc[idx_max, "season"]

    if val >= 0.5:
        return "el_nino", val
    elif val <= -0.5:
        return "la_nina", val
    else:
        return "neutral", val


def get_annual_oni(year):
    """Get the mean ONI across all seasons in a year (for regression)."""
    year_data = oni_df[oni_df["year"] == year]
    if len(year_data) == 0:
        return 0.0
    return float(year_data["anom"].mean())


years = list(range(2001, 2026))
enso_class = {}
for y in years:
    phase, oni_val = classify_year(y)
    enso_class[y] = {"phase": phase, "oni": oni_val, "oni_mean": get_annual_oni(y)}

print("\nENSO classification (peak ONI in year):")
for y in years:
    e = enso_class[y]
    marker = {"el_nino": "** EL NINO **", "la_nina": "   La Nina   ", "neutral": "   Neutral   "}
    print(f"  {y}: peak ONI={e['oni']:+.2f}  mean ONI={e['oni_mean']:+.2f}  {marker[e['phase']]}")

el_nino_years = [y for y in years if enso_class[y]["phase"] == "el_nino"]
la_nina_years = [y for y in years if enso_class[y]["phase"] == "la_nina"]
neutral_years = [y for y in years if enso_class[y]["phase"] == "neutral"]

print(f"\nEl Nino years: {el_nino_years}")
print(f"La Nina years: {la_nina_years}")
print(f"Neutral years: {neutral_years}")


# ===========================================================================
# 2. Load CERES and compute corridor metrics per year
# ===========================================================================
print("\nLoading CERES...")
ceres = load_ceres(list(Path("data/ceres").glob("*.nc")))
ceres["cre_lw"] = cloud_radiative_effect(ceres)

CORRIDORS = {
    "Amazon": {
        "lat_band": (-6.0, 0.0),
        "coast": slice(-50, -47),
        "interior": slice(-62, -58),
    },
    "Congo": {
        "lat_band": (-3.0, 5.0),
        "coast": slice(8, 12),
        "interior": slice(22, 27),
    },
}

VARS = {
    "toa_lw_all_mon": "OLR (W/m2)",
    "cldarea_total_daynight_mon": "Cloud Fraction (%)",
    "cre_lw": "CRE (W/m2)",
}


def lat_slice(da, lr):
    lo, hi = min(lr), max(lr)
    return slice(hi, lo) if da.lat[0] > da.lat[-1] else slice(lo, hi)


def compute_gradient(var, year, corridor):
    """Compute interior-minus-coast gradient for a variable and year."""
    data = ceres[var].sel(time=slice(f"{year}", f"{year}"))
    lb = corridor["lat_band"]
    ls = lat_slice(data, lb)

    coast = data.sel(lat=ls, lon=corridor["coast"])
    interior = data.sel(lat=ls, lon=corridor["interior"])

    wc = np.cos(np.deg2rad(coast.lat))
    wi = np.cos(np.deg2rad(interior.lat))

    c_val = float(coast.weighted(wc).mean(dim=["lat", "lon"]).mean(dim="time"))
    i_val = float(interior.weighted(wi).mean(dim=["lat", "lon"]).mean(dim="time"))
    return i_val - c_val


def compute_interior(var, year, corridor):
    """Compute interior mean for a variable and year."""
    data = ceres[var].sel(time=slice(f"{year}", f"{year}"))
    lb = corridor["lat_band"]
    ls = lat_slice(data, lb)
    interior = data.sel(lat=ls, lon=corridor["interior"])
    wi = np.cos(np.deg2rad(interior.lat))
    return float(interior.weighted(wi).mean(dim=["lat", "lon"]).mean(dim="time"))


# ===========================================================================
# Figure 1: 25-year time series colored by ENSO phase
# ===========================================================================
print("\n--- Time series colored by ENSO phase ---")

PHASE_COLORS = {"el_nino": "#e63946", "la_nina": "#457b9d", "neutral": "#999999"}
PHASE_LABELS = {"el_nino": "El Nino", "la_nina": "La Nina", "neutral": "Neutral"}

for corr_name, corridor in CORRIDORS.items():
    fig, axes = plt.subplots(len(VARS), 1, figsize=(16, 4 * len(VARS)), sharex=True)

    for i, (var, label) in enumerate(VARS.items()):
        ax = axes[i]

        grads = [compute_gradient(var, y, corridor) for y in years]
        colors = [PHASE_COLORS[enso_class[y]["phase"]] for y in years]

        ax.bar(years, grads, color=colors, alpha=0.8, edgecolor="white", linewidth=0.3)

        # Trend lines by ENSO phase
        for phase, phase_years in [("el_nino", el_nino_years),
                                     ("la_nina", la_nina_years),
                                     ("neutral", neutral_years)]:
            if len(phase_years) >= 3:
                py = [y for y in phase_years if y in years]
                pg = [grads[years.index(y)] for y in py]
                if len(py) >= 3:
                    z = np.polyfit(py, pg, 1)
                    ax.plot(py, np.poly1d(z)(py), "--",
                            color=PHASE_COLORS[phase], linewidth=1.5,
                            label=f"{PHASE_LABELS[phase]} trend: {z[0]:+.3f}/yr")

        # Overall trend
        z_all = np.polyfit(years, grads, 1)
        ax.plot(years, np.poly1d(z_all)(years), "k-", linewidth=2,
                label=f"Overall trend: {z_all[0]:+.3f}/yr")

        ax.set_title(f"{label}: Interior - Coast gradient", fontsize=11)
        ax.set_ylabel(f"Gradient ({label.split('(')[1]}" if "(" in label else "Gradient")
        ax.legend(fontsize=7, ncol=2, loc="best")
        ax.grid(alpha=0.3, axis="y")

        # Highlight 2023
        idx_2023 = years.index(2023)
        ax.annotate("2023", xy=(2023, grads[idx_2023]),
                     xytext=(2023, grads[idx_2023] + abs(grads[idx_2023]) * 0.15),
                     fontsize=9, ha="center", fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color="black", lw=0.8))

    axes[-1].set_xlabel("Year")

    # Custom legend for ENSO phases
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=PHASE_COLORS[p], label=PHASE_LABELS[p])
                       for p in ["el_nino", "la_nina", "neutral"]]
    axes[0].legend(handles=legend_elements + axes[0].get_legend_handles_labels()[0][-2:],
                   fontsize=7, ncol=3, loc="best")

    fig.suptitle(f"{corr_name} Corridor: Gradient Evolution by ENSO Phase\n"
                 f"Does the degradation trend persist within each ENSO phase?",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fname = f"enso_{corr_name.lower()}_gradient.png"
    fig.savefig(OUTPUT_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")


# ===========================================================================
# Figure 2: 2023 vs other El Nino years — is 2023 worse?
# ===========================================================================
print("\n--- 2023 vs other El Nino years ---")

fig, axes = plt.subplots(2, len(VARS), figsize=(18, 10))

for col, (var, label) in enumerate(VARS.items()):
    for row, (corr_name, corridor) in enumerate(CORRIDORS.items()):
        ax = axes[row, col]

        # Interior values for El Nino years
        en_years_sorted = sorted(el_nino_years)
        interior_vals = [compute_interior(var, y, corridor) for y in en_years_sorted]

        colors = ["#e63946" if y == 2023 else "#ffb3b3" for y in en_years_sorted]
        bars = ax.bar(range(len(en_years_sorted)), interior_vals, color=colors,
                       edgecolor="white", linewidth=0.5)

        ax.set_xticks(range(len(en_years_sorted)))
        ax.set_xticklabels(en_years_sorted, rotation=45, fontsize=8)
        ax.set_ylabel(label.split("(")[1].replace(")", "") if "(" in label else "")

        if row == 0:
            ax.set_title(label.split("(")[0].strip(), fontsize=11, fontweight="bold")
        if col == 0:
            ax.set_ylabel(f"{corr_name}\n{label}", fontsize=10)

        ax.grid(alpha=0.3, axis="y")

        # Add El Nino mean line (excluding 2023)
        other_en = [v for y, v in zip(en_years_sorted, interior_vals) if y != 2023]
        if other_en:
            mean_other = np.mean(other_en)
            ax.axhline(mean_other, color="#666", linewidth=1, linestyle="--",
                       label=f"Other El Nino mean: {mean_other:.1f}")
            val_2023 = interior_vals[en_years_sorted.index(2023)]
            diff = val_2023 - mean_other
            ax.text(0.98, 0.95, f"2023 vs mean: {diff:+.1f}",
                    transform=ax.transAxes, fontsize=8, ha="right", va="top",
                    fontweight="bold",
                    color="#e63946" if abs(diff) > abs(mean_other * 0.01) else "#666")
            ax.legend(fontsize=7)

fig.suptitle("Is 2023 Worse Than Other El Nino Years?\n"
             "Interior values for all El Nino years (dark red = 2023)",
             fontsize=14, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "enso_2023_vs_other_elnino.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: enso_2023_vs_other_elnino.png")


# ===========================================================================
# Figure 3: ENSO-adjusted corridor metrics (detrend by ONI)
# ===========================================================================
print("\n--- ENSO-adjusted trends ---")

fig, axes = plt.subplots(len(VARS), 2, figsize=(18, 4 * len(VARS)), sharex="col")

for i, (var, label) in enumerate(VARS.items()):
    for j, (corr_name, corridor) in enumerate(CORRIDORS.items()):
        ax = axes[i, j]

        grads = np.array([compute_gradient(var, y, corridor) for y in years])
        oni_vals = np.array([enso_class[y]["oni_mean"] for y in years])

        # Regress gradient on ONI to remove ENSO signal
        slope_oni, intercept_oni, r_oni, p_oni, _ = \
            __import__("scipy").stats.linregress(oni_vals, grads)

        # ENSO-adjusted residuals
        predicted_by_enso = slope_oni * oni_vals + intercept_oni
        residuals = grads - predicted_by_enso

        # Trend in residuals = ENSO-independent trend
        z_resid = np.polyfit(years, residuals, 1)
        _, _, r_resid, p_resid, _ = \
            __import__("scipy").stats.linregress(years, residuals)

        # Plot
        colors = [PHASE_COLORS[enso_class[y]["phase"]] for y in years]
        ax.bar(years, residuals, color=colors, alpha=0.8, edgecolor="white", linewidth=0.3)
        ax.plot(years, np.poly1d(z_resid)(years), "k-", linewidth=2,
                label=f"ENSO-adjusted trend: {z_resid[0]:+.4f}/yr\n"
                      f"p = {p_resid:.4f}")

        ax.axhline(0, color="gray", linewidth=0.5)
        ax.set_title(f"{corr_name}: {label.split('(')[0].strip()}", fontsize=10)
        ax.set_ylabel("ENSO-adjusted\ngradient anomaly")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3, axis="y")

axes[-1, 0].set_xlabel("Year")
axes[-1, 1].set_xlabel("Year")

fig.suptitle("ENSO-Adjusted Corridor Gradient Trends\n"
             "After removing the ENSO signal (regression on ONI), "
             "does the degradation trend persist?",
             fontsize=13, fontweight="bold")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "enso_adjusted_trends.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: enso_adjusted_trends.png")


# ===========================================================================
# Summary statistics
# ===========================================================================
print("\n=== ENSO CONTROL SUMMARY ===\n")

for corr_name, corridor in CORRIDORS.items():
    print(f"--- {corr_name} Corridor ---\n")
    for var, label in VARS.items():
        grads = np.array([compute_gradient(var, y, corridor) for y in years])
        oni_vals = np.array([enso_class[y]["oni_mean"] for y in years])

        # Raw trend
        z_raw = np.polyfit(years, grads, 1)

        # ENSO-ONI correlation
        from scipy.stats import linregress
        slope_oni, _, r_oni, p_oni, _ = linregress(oni_vals, grads)

        # ENSO-adjusted trend
        residuals = grads - (slope_oni * oni_vals + (np.mean(grads) - slope_oni * np.mean(oni_vals)))
        z_adj = np.polyfit(years, residuals, 1)
        _, _, r_adj, p_adj, _ = linregress(years, residuals)

        # 2023 vs other El Nino
        en_grads = {y: grads[years.index(y)] for y in el_nino_years}
        other_en_mean = np.mean([v for y, v in en_grads.items() if y != 2023])
        diff_2023 = en_grads.get(2023, 0) - other_en_mean

        print(f"  {label}:")
        print(f"    Raw trend:          {z_raw[0]:+.4f}/yr")
        print(f"    ONI correlation:    r={r_oni:.3f}, p={p_oni:.4f}")
        print(f"    ENSO-adjusted trend: {z_adj[0]:+.4f}/yr (p={p_adj:.4f})")
        print(f"    2023 vs other El Nino mean: {diff_2023:+.2f}")
        print()

print("=== DONE ===")

"""Build new figures: corridor map (Figure 1) and causal chain diagram."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("outputs")

# =========================================================================
# Figure 1: Study area with corridors
# =========================================================================
print("Building corridor study area map...")

fig, ax = plt.subplots(figsize=(16, 9), subplot_kw={"projection": ccrs.PlateCarree()})

ax.add_feature(cfeature.LAND, alpha=0.15, color="#c8b88a")
ax.add_feature(cfeature.OCEAN, alpha=0.15, color="#a8c8d8")
ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--", alpha=0.5)
ax.add_feature(cfeature.RIVERS, linewidth=0.4, alpha=0.4, color="#4a90d9")

proj = ccrs.PlateCarree()

# Amazon corridor
amazon_cities = [
    ("Belem", -1.4, -48.5),
    ("Maraba", -5.4, -49.1),
    ("Tucurui", -3.8, -49.7),
    ("Altamira", -3.2, -52.2),
    ("Itaituba", -4.3, -55.9),
    ("Manaus", -3.1, -60.0),
]
am_lons = [c[2] for c in amazon_cities]
am_lats = [c[1] for c in amazon_cities]
ax.plot(am_lons, am_lats, color="#2a9d8f", linewidth=3.5, transform=proj,
        zorder=5, path_effects=[pe.withStroke(linewidth=5, foreground="white")])
for name, lat, lon in amazon_cities:
    ax.plot(lon, lat, "o", color="#2a9d8f", markersize=7, transform=proj,
            markeredgecolor="white", markeredgewidth=1, zorder=6)
    offset_x, offset_y = 0.5, 0.5
    if name == "Belem":
        offset_x, offset_y = 0.5, 0.8
    elif name == "Manaus":
        offset_x, offset_y = -0.5, 0.8
    ax.text(lon + offset_x, lat + offset_y, name, fontsize=8, color="#2a9d8f",
            fontweight="bold", transform=proj, zorder=7,
            path_effects=[pe.withStroke(linewidth=2, foreground="white")])

# Amazon latitude band shading
ax.fill_between([-62, -47], -6, 0, alpha=0.06, color="#2a9d8f", transform=proj)

# Wider Amazon domain
for style in [{"color": "#2a9d8f", "linewidth": 1.5, "linestyle": ":", "alpha": 0.6}]:
    lons = [-65, -45, -45, -65, -65]
    lats = [-10, -10, 2, 2, -10]
    ax.plot(lons, lats, transform=proj, **style)
ax.text(-55, -9.5, "Wider Eastern Amazon\n(10S-2N, 65W-45W)", fontsize=7,
        color="#2a9d8f", ha="center", transform=proj, fontstyle="italic")

# Congo corridor
congo_cities = [
    ("Douala", 4.0, 9.7),
    ("Yaounde", 3.9, 11.5),
    ("Ouesso", 1.6, 16.0),
    ("Mbandaka", 0.0, 18.3),
    ("Kisangani", 0.5, 25.2),
]
co_lons = [c[2] for c in congo_cities]
co_lats = [c[1] for c in congo_cities]
ax.plot(co_lons, co_lats, color="#e9c46a", linewidth=3.5, transform=proj,
        zorder=5, path_effects=[pe.withStroke(linewidth=5, foreground="white")])
for name, lat, lon in congo_cities:
    ax.plot(lon, lat, "o", color="#e9c46a", markersize=7, transform=proj,
            markeredgecolor="white", markeredgewidth=1, zorder=6)
    offset_x, offset_y = 0.5, 0.5
    if name == "Kisangani":
        offset_x = 0.5
    ax.text(lon + offset_x, lat + offset_y, name, fontsize=8, color="#c48b00",
            fontweight="bold", transform=proj, zorder=7,
            path_effects=[pe.withStroke(linewidth=2, foreground="white")])

# Congo latitude band shading
ax.fill_between([8, 28], -3, 5, alpha=0.06, color="#e9c46a", transform=proj)

# Arrows showing moisture flow direction
ax.annotate("", xy=(-55, -3), xytext=(-48, -2),
            arrowprops=dict(arrowstyle="-|>", color="#2a9d8f", lw=2, mutation_scale=15),
            transform=proj)
ax.annotate("", xy=(20, 2), xytext=(11, 3.5),
            arrowprops=dict(arrowstyle="-|>", color="#c48b00", lw=2, mutation_scale=15),
            transform=proj)

# Ocean labels
ax.text(-35, 5, "ATLANTIC\nOCEAN", fontsize=11, color="#5a8aaa", ha="center",
        transform=proj, fontstyle="italic", alpha=0.7)
ax.text(-20, -12, "Moisture source", fontsize=8, color="#5a8aaa", ha="center",
        transform=proj, fontstyle="italic", alpha=0.6)

# Legend
legend_elements = [
    mpatches.Patch(facecolor="#2a9d8f", alpha=0.8, label="Amazon corridor (Belem-Manaus, ~1300 km)"),
    mpatches.Patch(facecolor="#e9c46a", alpha=0.8, label="Congo corridor (Douala-Kisangani, ~1700 km)"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=10, framealpha=0.9)

ax.set_extent([-68, 32, -15, 10], crs=proj)
gl = ax.gridlines(draw_labels=True, alpha=0.3, linewidth=0.3)
gl.top_labels = False
gl.right_labels = False

ax.set_title("Study Area: Tropical Forest Moisture Corridors", fontsize=14,
             fontweight="bold", pad=12)

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "fig1_corridor_map.png", dpi=200, bbox_inches="tight")
plt.close()
print("Saved: fig1_corridor_map.png")


# =========================================================================
# Causal chain diagram
# =========================================================================
print("\nBuilding causal chain diagram...")

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis("off")

# Define the chain steps
steps = [
    {
        "label": "Evapotranspiration\nDecline",
        "instrument": "MODIS ET, NDVI",
        "finding": "ET -16 mm/yr (Amazon)\n88% of intact forest browned",
        "y": 9.0, "color": "#2a9d8f",
    },
    {
        "label": "Condensation\nWeakens",
        "instrument": "Inferred from ET + WV",
        "finding": "Less moisture entering\nboundary layer",
        "y": 7.4, "color": "#457b9d",
    },
    {
        "label": "Cloud Cover\nDeclines",
        "instrument": "CERES cloud fraction",
        "finding": "Cloud -2.3% (Amazon)\n-3.6% at mid-corridor",
        "y": 5.8, "color": "#264653",
    },
    {
        "label": "OLR Increases\n(8-13 um window)",
        "instrument": "CERES EBAF-TOA",
        "finding": "OLR +2.9 W/m2 (Amazon)\n+4.3 at interior",
        "y": 4.2, "color": "#e76f51",
    },
    {
        "label": "Pressure Gradient\nFlattens",
        "instrument": "ERA5 (future work)",
        "finding": "CRE gradient -0.12 W/m2/yr\n(p=0.033, 25-year trend)",
        "y": 2.6, "color": "#999999",
    },
    {
        "label": "Inland Moisture\nTransport Fails",
        "instrument": "AIRS water vapour",
        "finding": "Coast +0.8 kg/m2,\ninterior -0.4 kg/m2\nGradient steepened -1.2 kg/m2",
        "y": 1.0, "color": "#e63946",
    },
]

# Box dimensions
box_w, box_h = 2.8, 1.0
center_x = 4.0
instr_x = 8.5
finding_x = 11.5

# Title
ax.text(7, 9.8, "Causal Chain: Biotic Pump Breakdown",
        fontsize=16, fontweight="bold", ha="center", va="center")
ax.text(7, 9.5, "Observable satellite signatures and key findings",
        fontsize=10, ha="center", va="center", color="#666", fontstyle="italic")

# Column headers
ax.text(center_x, 9.85, "Mechanism", fontsize=10, fontweight="bold",
        ha="center", va="center", color="#333")
ax.text(instr_x, 9.85, "Instrument", fontsize=10, fontweight="bold",
        ha="center", va="center", color="#333")
ax.text(finding_x, 9.85, "Key Finding", fontsize=10, fontweight="bold",
        ha="center", va="center", color="#333")

# Dashed line separating completed vs future work
ax.axhline(y=3.4, xmin=0.05, xmax=0.95, color="#999", linewidth=1, linestyle="--")
ax.text(0.5, 3.45, "Completed in this study", fontsize=8, color="#2a9d8f",
        fontweight="bold", va="bottom")
ax.text(0.5, 3.35, "Future work (ERA5)", fontsize=8, color="#999",
        fontweight="bold", va="top")

for i, step in enumerate(steps):
    y = step["y"]
    c = step["color"]

    # Main box
    rect = mpatches.FancyBboxPatch(
        (center_x - box_w/2, y - box_h/2), box_w, box_h,
        boxstyle="round,pad=0.1", facecolor=c, edgecolor="white",
        linewidth=2, alpha=0.85
    )
    ax.add_patch(rect)
    ax.text(center_x, y, step["label"], fontsize=10, fontweight="bold",
            ha="center", va="center", color="white")

    # Instrument tag
    ax.text(instr_x, y, step["instrument"], fontsize=9, ha="center", va="center",
            color="#333",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0f0f0",
                      edgecolor="#ccc", linewidth=0.5))

    # Finding text
    ax.text(finding_x, y, step["finding"], fontsize=8, ha="center", va="center",
            color="#333", fontstyle="italic")

    # Connecting line to instrument
    ax.plot([center_x + box_w/2 + 0.1, instr_x - 1.2], [y, y],
            color="#ccc", linewidth=1, linestyle="-")

    # Connecting line to finding
    ax.plot([instr_x + 1.2, finding_x - 1.5], [y, y],
            color="#ccc", linewidth=1, linestyle="-")

    # Arrow to next step
    if i < len(steps) - 1:
        next_y = steps[i + 1]["y"]
        ax.annotate("",
                     xy=(center_x, next_y + box_h/2 + 0.05),
                     xytext=(center_x, y - box_h/2 - 0.05),
                     arrowprops=dict(arrowstyle="-|>", color="#555",
                                      lw=2, mutation_scale=18))

# Feedback arrow (from bottom back to top)
ax.annotate("",
             xy=(center_x - box_w/2 - 0.3, steps[0]["y"]),
             xytext=(center_x - box_w/2 - 0.3, steps[-1]["y"]),
             arrowprops=dict(arrowstyle="-|>", color="#e63946",
                              lw=2, mutation_scale=18,
                              connectionstyle="arc3,rad=0.3"))
ax.text(center_x - box_w/2 - 0.8, 5.0, "Positive\nfeedback\nloop",
        fontsize=9, ha="center", va="center", color="#e63946",
        fontweight="bold", rotation=90)

# SON highlight
ax.text(13.5, 5.0,
        "Signal concentrates\nin SON (Sept-Nov)\nwhen forest should\ninitiate wet season",
        fontsize=8, ha="center", va="center", color="#e76f51",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff3e0",
                  edgecolor="#e76f51", linewidth=1.5))

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "fig_causal_chain.png", dpi=200, bbox_inches="tight")
plt.close()
print("Saved: fig_causal_chain.png")

print("\n=== DONE ===")

"""
Generate the Lobito Corridor map for the Two Bars Capital website.
Requires: pip install geopandas matplotlib
Usage: python generate_map.py
"""
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from shapely.geometry import LineString
from pathlib import Path

# Website colors
BG_COLOR = '#2d1410'
ACCENT = '#8B1A10'
ACCENT_LIGHT = '#a52a1a'
TEXT_MUTED = '#c0b0a0'
COUNTRY_FILL = '#3d2420'
CONTEXT_FILL = '#251510'
CONTEXT_EDGE = '#3a2018'

OUTPUT_DIR = Path(__file__).parent

# Load Natural Earth data
world = gpd.read_file("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")

# Find target countries
name_map = {
    'Angola': 'Angola',
    'DRC': 'Dem. Rep. Congo',
    'Zambia': 'Zambia',
    'Namibia': 'Namibia',
}

targets = []
for label, search in name_map.items():
    match = world[world['NAME'].str.contains(search, case=False, na=False)]
    if len(match) == 0:
        match = world[world['ADMIN'].str.contains(search, case=False, na=False)]
    if len(match) > 0:
        targets.append(match.iloc[0:1])
    else:
        print(f"Warning: could not find {label} ({search})")

target_gdf = gpd.GeoDataFrame(pd.concat(targets))
bounds = target_gdf.total_bounds  # minx, miny, maxx, maxy

# Context countries (neighbors)
pad = 2
context = world.cx[bounds[0]-pad:bounds[2]+pad, bounds[1]-pad:bounds[3]+pad]
context_other = context[~context.index.isin(target_gdf.index)]

# Lobito Corridor route (approximate coordinates from reference map)
# Lobito -> Benguela -> Huambo -> Munhango -> Luacano -> Dilolo -> Kolwezi -> Solwezi -> Chingola -> Kapiri Mposhi
corridor_coords = [
    (13.55, -12.35),   # Lobito
    (13.40, -12.58),   # Benguela
    (15.73, -12.78),   # Huambo
    (18.5, -13.5),     # Munhango
    (20.5, -12.5),     # Luacano
    (22.33, -10.68),   # Dilolo
    (25.47, -10.72),   # Kolwezi
    (26.40, -12.17),   # Solwezi
    (27.85, -12.53),   # Chingola
    (28.68, -14.97),   # Kapiri Mposhi
]

cities = [
    (13.55, -12.35, 'Lobito', 'right'),
    (13.40, -12.58, 'Benguela', 'right'),
    (15.73, -12.78, 'Huambo', 'left'),
    (25.47, -10.72, 'Kolwezi', 'left'),
    (26.40, -12.17, 'Solwezi', 'left'),
    (28.68, -14.97, 'Kapiri Mposhi', 'left'),
]

country_labels = {
    'Angola': (17.5, -12.5),
    'Dem. Rep. Congo': (24.0, -5.5),
    'Zambia': (27.5, -14.5),
    'Namibia': (17.5, -21.5),
}

# --- Plot ---
fig, ax = plt.subplots(1, 1, figsize=(12, 7))
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

# Context countries
context_other.plot(ax=ax, color=CONTEXT_FILL, edgecolor=CONTEXT_EDGE, linewidth=0.5)

# Target countries
target_gdf.plot(ax=ax, color=COUNTRY_FILL, edgecolor=ACCENT, linewidth=1.5)

# Country labels
for _, row in target_gdf.iterrows():
    name = row.get('NAME') or row.get('ADMIN') or row.get('name') or ''
    display_name = 'DRC' if 'Congo' in name else name.upper()
    for key, pos in country_labels.items():
        if key.lower() in name.lower():
            cx, cy = pos
            break
    else:
        cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
    ax.text(cx, cy, display_name, fontsize=14, fontweight='bold',
            color=TEXT_MUTED, ha='center', va='center',
            fontfamily='sans-serif', alpha=0.8)

# Corridor line
corridor_line = LineString(corridor_coords)
gpd.GeoDataFrame(geometry=[corridor_line]).plot(
    ax=ax, color=TEXT_MUTED, linewidth=3, linestyle='--',
    path_effects=[pe.Stroke(linewidth=5, foreground=ACCENT), pe.Normal()])

# City dots and labels
for lon, lat, name, ha in cities:
    ax.plot(lon, lat, 'o', color=TEXT_MUTED, markersize=5, zorder=5)
    ax.annotate(name, (lon, lat), xytext=(8 if ha == 'left' else -8, 5),
                textcoords='offset points', fontsize=7.5, color=TEXT_MUTED,
                ha=ha, fontfamily='sans-serif')

# Lobito port highlight
ax.plot(13.55, -12.35, 'o', color=ACCENT_LIGHT, markersize=10, zorder=6)
ax.plot(13.55, -12.35, 'o', color=TEXT_MUTED, markersize=5, zorder=7)

# Ocean label
ax.text(11.0, -16.0, 'ATLANTIC\nOCEAN', fontsize=8, color=ACCENT_LIGHT,
        ha='center', va='center', fontstyle='italic', alpha=0.6, fontfamily='sans-serif')

# Corridor label
ax.text(19.5, -11.2, 'LOBITO CORRIDOR', fontsize=9, fontweight='bold',
        color=ACCENT_LIGHT, ha='center', va='center', rotation=-5,
        fontfamily='sans-serif', alpha=0.9)

# Bounds
ax.set_xlim(bounds[0] - 2, bounds[2] + 2)
ax.set_ylim(bounds[1] - 1, bounds[3] + 1)
ax.axis('off')
plt.tight_layout(pad=0)

# Save
for fmt in ['svg', 'png']:
    plt.savefig(OUTPUT_DIR / f'lobito-corridor.{fmt}',
                format=fmt, bbox_inches='tight', facecolor=BG_COLOR,
                edgecolor='none', dpi=200, transparent=False)
    print(f"Saved lobito-corridor.{fmt}")

print("Done!")

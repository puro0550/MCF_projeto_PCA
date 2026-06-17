import os
import sys
import csv
csv.field_size_limit(10**8)
import re
import json
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MapPolygon
from matplotlib.collections import PatchCollection
import matplotlib.lines as mlines

# Ensure local imports work correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import original graph details and SSP algorithm
from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes
from ssp_algorithm import successive_shortest_path

# Balance adjustments (float precision correction)
no_balancos = orig_balancos.copy()
no_balancos["Ceilândia"] -= sum(no_balancos.values())
conexoes = orig_conexoes.copy()

# Solve optimal MCF flow via Successive Shortest Path (SSP)
x, pi, history = successive_shortest_path(no_balancos, conexoes)

# UTM Zone 23S -> Lat/Lon conversion
def utm_to_latlon(easting, northing, zone=23, northern=False):
    a = 6378137.0
    f = 1.0 / 298.257223563
    e_sq = f * (2 - f)
    e_prime_sq = e_sq / (1 - e_sq)
    k0 = 0.9996
    
    x = easting - 500000.0
    y = northing
    if not northern:
        y -= 10000000.0
        
    M = y / k0
    mu = M / (a * (1.0 - e_sq / 4.0 - 3.0 * e_sq**2 / 64.0 - 5.0 * e_sq**3 / 256.0))
    
    e1 = (1.0 - math.sqrt(1.0 - e_sq)) / (1.0 + math.sqrt(1.0 - e_sq))
    ca = 3.0 * e1 / 2.0 - 27.0 * e1**3 / 32.0
    cb = 21.0 * e1**2 / 16.0 - 55.0 * e1**4 / 32.0
    cc = 151.0 * e1**3 / 96.0
    cd = 1097.0 * e1**4 / 512.0
    
    phi1 = mu + ca * math.sin(2.0 * mu) + cb * math.sin(4.0 * mu) + cc * math.sin(6.0 * mu) + cd * math.sin(8.0 * mu)
    
    T1 = math.tan(phi1)**2
    C1 = e_prime_sq * math.cos(phi1)**2
    N1 = a / math.sqrt(1.0 - e_sq * math.sin(phi1)**2)
    R1 = a * (1.0 - e_sq) / (1.0 - e_sq * math.sin(phi1)**2)**1.5
    D = x / (N1 * k0)
    
    lat = phi1 - (N1 * math.tan(phi1) / R1) * (
        D**2 / 2.0 - (5.0 + 3.0 * T1 + 10.0 * C1 - 4.0 * C1**2 - 9.0 * e_prime_sq) * D**4 / 24.0 +
        (61.0 + 90.0 * T1 + 298.0 * C1 + 45.0 * T1**2 - 252.0 * e_prime_sq - 3.0 * C1**2) * D**6 / 720.0
    )
    
    lon = (
        D - (1.0 + 2.0 * T1 + C1) * D**3 / 6.0 +
        (5.0 - 2.0 * C1 + 28.0 * T1 - 3.0 * C1**2 + 8.0 * e_prime_sq + 24.0 * T1**2) * D**5 / 120.0
    ) / math.cos(phi1)
    
    lat_deg = math.degrees(lat)
    lon_deg = math.degrees(lon)
    
    lon0 = (zone * 6) - 183.0
    lon_deg += lon0
    
    return lat_deg, lon_deg

# Load Coordinates
etas_csv = os.path.join(script_dir, "dados_do_projeto", "estacoes_tratamento_agua.csv")
ras_csv = os.path.join(script_dir, "dados_do_projeto", "CONSUMO_AGUA_RA.csv")
water_json = os.path.join(script_dir, "dados_do_projeto", "CORPOS_DAGUA.json")

coords_nos = {}

# Parse supply nodes (ETAs) coordinates
with open(etas_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        nome = row["nome"].strip()
        if nome in no_balancos:
            geom = row["the_geom"]
            match = re.search(r'MULTIPOINT\s*\(\(\s*([-\d.]+)\s+([-\d.]+)\s*\)\)', geom)
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                # Note: csv geometry stores (lon, lat) or (lat, lon)?
                # Standard WKT is POINT(lon lat). Let's verify by plotting.
                # In Folium, it was mapping coords_nos[nome] = (lat, lon) where lat = match.group(1) and lon = match.group(2).
                # Actually, in Brazil DF, latitude is around -15.7 and longitude is around -47.8.
                # Let's ensure we assign lat/lon correctly:
                val1 = float(match.group(1))
                val2 = float(match.group(2))
                coords_nos[nome] = (val1, val2)  # (lat, lon)

# Parse demand nodes (RAs) coordinates (centroids)
with open(ras_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        nome = row["nome"].strip()
        if nome in no_balancos:
            geom = row["the_geom"]
            match = re.search(r'\(\(\((.*?)\)\)\)', geom)
            if not match:
                match = re.search(r'\(\((.*?)\)\)', geom)
            if match:
                ring_content = match.group(1)
                coords = ring_content.split(',')
                points = []
                for c in coords:
                    parts = c.strip().split()
                    if len(parts) == 2:
                        points.append((float(parts[0]), float(parts[1])))
                if points and points[0] == points[-1]:
                    vertices = points[:-1]
                else:
                    vertices = points
                avg_e = sum(p[0] for p in vertices) / len(vertices)
                avg_n = sum(p[1] for p in vertices) / len(vertices)
                lat, lon = utm_to_latlon(avg_e, avg_n, zone=23, northern=False)
                coords_nos[nome] = (lat, lon)

# Override RA coordinates to point to their actual urban centers (avoiding rural centroids)
ra_urban_coords = {
    "Plano Piloto": (-15.7801, -47.9292),
    "Taguatinga": (-15.8330, -48.0570),
    "Ceilândia": (-15.8200, -48.1150),
    "Samambaia": (-15.8750, -48.0850),
    "Guará": (-15.8180, -47.9750),
    "Sobradinho": (-15.6530, -47.7880),
    "Planaltina": (-15.6180, -47.6970)
}
for ra_name, coord in ra_urban_coords.items():
    if ra_name in coords_nos:
        coords_nos[ra_name] = coord

# Check that we have coords for all
for node in no_balancos:
    if node not in coords_nos:
        # Fallback if coordinates missing
        coords_nos[node] = (-15.7801, -47.9292)

def plot_water_bodies(ax):
    try:
        with open(water_json, "r", encoding="utf-8") as f:
            water_data = json.load(f)
            
        patches = []
        for feat in water_data.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Polygon":
                for ring in geom.get("coordinates", []):
                    # coords in json are [lon, lat] -> matplotlib expects [lon, lat] as X, Y
                    polygon_points = [(pt[0], pt[1]) for pt in ring]
                    patches.append(MapPolygon(polygon_points, closed=True))
            elif geom.get("type") == "MultiPolygon":
                for poly in geom.get("coordinates", []):
                    for ring in poly:
                        polygon_points = [(pt[0], pt[1]) for pt in ring]
                        patches.append(MapPolygon(polygon_points, closed=True))
        
        p_col = PatchCollection(patches, facecolor='#c0f2fe', edgecolor='#0891b2', alpha=0.6, linewidth=0.5, zorder=1)
        ax.add_collection(p_col)
    except Exception as e:
        print(f"Warning: Could not plot water bodies: {e}")

def generate_map(is_flow=False):
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')
    
    # Plot water bodies
    plot_water_bodies(ax)
    
    # Draw Edges (Adutoras)
    for (u, v), flow_val in x.items():
        # Get capacity and cost
        cap_val = next(c[2] for c in conexoes if c[0] == u and c[1] == v)
        lat1, lon1 = coords_nos[u]
        lat2, lon2 = coords_nos[v]
        
        # In matplotlib, x is longitude, y is latitude
        x1, y1 = lon1, lat1
        x2, y2 = lon2, lat2
        
        # Slight bend to avoid overlaps
        # We can draw it as a curved line using a path
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        dx = x2 - x1
        dy = y2 - y1
        # perp
        perp_x = -dy * 0.1
        perp_y = dx * 0.1
        ctrl_x = mid_x + perp_x
        ctrl_y = mid_y + perp_y
        
        # Draw curve
        curve_x = []
        curve_y = []
        for i in range(101):
            t = i / 100
            px = (1-t)**2 * x1 + 2*(1-t)*t * ctrl_x + t**2 * x2
            py = (1-t)**2 * y1 + 2*(1-t)*t * ctrl_y + t**2 * y2
            curve_x.append(px)
            curve_y.append(py)
            
        is_active = flow_val > 1e-2
        
        if is_flow:
            if is_active:
                width = 1.0 + 3.0 * (flow_val / cap_val)
                ax.plot(curve_x, curve_y, color='#059669', linewidth=width, alpha=0.9, zorder=2)
                # Draw arrowhead midway
                arrow_idx = 55
                ax.annotate('', xy=(curve_x[arrow_idx], curve_y[arrow_idx]), xytext=(curve_x[arrow_idx-1], curve_y[arrow_idx-1]),
                            arrowprops=dict(arrowstyle="->", color='#059669', lw=width, mutation_scale=15), zorder=2)
            else:
                ax.plot(curve_x, curve_y, color='#94a3b8', linewidth=0.6, linestyle='--', alpha=0.5, zorder=2)
        else:
            # Base topology: all connections in uniform gray-blue
            ax.plot(curve_x, curve_y, color='#1e3a8a', linewidth=1.2, alpha=0.7, zorder=2)
            # Arrow
            arrow_idx = 55
            ax.annotate('', xy=(curve_x[arrow_idx], curve_y[arrow_idx]), xytext=(curve_x[arrow_idx-1], curve_y[arrow_idx-1]),
                        arrowprops=dict(arrowstyle="->", color='#1e3a8a', lw=1.2, mutation_scale=10), zorder=2)
            
    # Draw Nodes
    eta_x, eta_y, eta_labels = [], [], []
    ra_x, ra_y, ra_labels = [], [], []
    
    for name, (lat, lon) in coords_nos.items():
        if "ETA" in name:
            eta_x.append(lon)
            eta_y.append(lat)
            eta_labels.append(name.replace("ETA ", ""))
        else:
            ra_x.append(lon)
            ra_y.append(lat)
            ra_labels.append(name)
            
    # Scatter plot
    ax.scatter(eta_x, eta_y, color='#1d4ed8', marker='^', s=120, label='ETA (Estação de Tratamento)', zorder=3, edgecolors='black', linewidths=0.8)
    ax.scatter(ra_x, ra_y, color='#10b981', marker='o', s=100, label='RA (Região Administrativa)', zorder=3, edgecolors='black', linewidths=0.8)
    
    # Label nodes
    for name, (lat, lon) in coords_nos.items():
        label_name = name.replace("ETA ", "")
        offset = (0.003, 0.003)
        if name == "Planaltina":
            offset = (-0.035, -0.012)
        elif name == "ETA Planaltina":
            offset = (0.005, 0.008)
        elif name == "ETA Brasília":
            offset = (-0.045, 0.005)
        elif name == "Plano Piloto":
            offset = (-0.045, -0.012)
            
        ax.annotate(label_name, xy=(lon, lat), xytext=(lon + offset[0], lat + offset[1]),
                    fontsize=7, fontweight='bold', color='#1e293b',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", lw=0.3, alpha=0.8), zorder=4)

    # Set map limits around DF coordinates
    ax.set_xlim(-48.3, -47.3)
    ax.set_ylim(-16.1, -15.45)
    
    # Titles & Legend
    if is_flow:
        ax.set_title("Resultados da Otimização SSP - Fluxos Ótimos de Água no DF", fontsize=12, fontweight='bold', color='#1e293b', pad=15)
        # Custom legends
        active_line = mlines.Line2D([], [], color='#059669', lw=2.5, label='Adutoras com Fluxo Ativo')
        inactive_line = mlines.Line2D([], [], color='#94a3b8', lw=0.6, ls='--', label='Capacidade Ociosa')
        ax.legend(handles=[
            mlines.Line2D([], [], color='#1d4ed8', marker='^', ls='', label='ETA (Fonte)'),
            mlines.Line2D([], [], color='#10b981', marker='o', ls='', label='RA (Déficit)'),
            active_line, inactive_line
        ], loc='upper right', framealpha=0.9, fontsize=8)
    else:
        ax.set_title("Topologia Física da Rede de Integração de Água do DF (Atlas)", fontsize=12, fontweight='bold', color='#1e293b', pad=15)
        ax.legend(handles=[
            mlines.Line2D([], [], color='#1d4ed8', marker='^', ls='', label='ETA (Fonte)'),
            mlines.Line2D([], [], color='#10b981', marker='o', ls='', label='RA (Déficit)'),
            mlines.Line2D([], [], color='#1e3a8a', lw=1.2, label='Adutora de Integração')
        ], loc='upper right', framealpha=0.9, fontsize=8)
        
    ax.set_xlabel("Longitude (deg)", fontsize=8, color='#475569')
    ax.set_ylabel("Latitude (deg)", fontsize=8, color='#475569')
    ax.grid(True, linestyle=':', alpha=0.6, color='#cbd5e1')
    
    # Output path
    out_name = "mapa_fluxos_otimos.png" if is_flow else "mapa_topologia.png"
    out_path = os.path.join(script_dir, "..", "apresentacao_slides", "figuras", out_name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    generate_map(is_flow=False)
    generate_map(is_flow=True)

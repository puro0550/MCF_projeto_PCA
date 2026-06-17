"""
Premium Curved Flow Map Visualization Generator
===============================================

This script solves the Minimum Cost Flow problem on the Distrito Federal (DF) water
network using the Successive Shortest Path (SSP) algorithm. It then maps the nodes to
their real geographical coordinates and renders an interactive, premium HTML visualization
featuring:
  - Custom SVG node markers (ETA vs RA)
  - Curved Bezier arcs as edges to avoid overlapping and improve visual flow
  - Animated marching ants (AntPath) in green for active flows
  - Dashed grey arcs for inactive capacities
  - Water bodies (Lago Paranoá, etc.) overlay
  - Premium dark HUD title card and glassmorphic legend overlays

Author: Antigravity Agent
Date: June 2026
"""

import os
import sys
import csv
import re
import json
import math
import folium
from folium.plugins import AntPath

# Ensure local imports work correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import original graph details and SSP algorithm
from grafo import no_balancos as orig_balancos, conexoes as orig_conexoes
from ssp_algorithm import successive_shortest_path

# Explicitly raise the CSV field size limit to handle large geometry fields
csv.field_size_limit(10**7)

# WGS84 Ellipsoid constants for UTM Zone 23S -> Lat/Lon conversion
def utm_to_latlon(easting, northing, zone=23, northern=False):
    a = 6378137.0
    f = 1.0 / 298.257223563
    e_sq = f * (2 - f)
    e_prime_sq = e_sq / (1 - e_sq)
    k0 = 0.9996
    
    # Adjust for false easting and false northing (Southern hemisphere)
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
    
    # Calculate the central meridian for Zone 23 (45 W)
    lon0 = (zone * 6) - 183.0
    lon_deg += lon0
    
    return lat_deg, lon_deg

def get_bezier_curve(p1, p2, curvature=0.15, num_points=30):
    """
    Computes a quadratic Bezier curve bending to the right of the path.
    p1, p2 are lists/tuples of [lat, lon]
    """
    lat1, lon1 = p1
    lat2, lon2 = p2
    
    # Midpoint
    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0
    
    # Direction vector from p1 to p2
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    
    # Clockwise perpendicular vector
    # rotate (d_lon, d_lat) 90 deg clockwise -> (d_lat, -d_lon)
    # perp_lat = -d_lon, perp_lon = d_lat
    perp_lat = -d_lon
    perp_lon = d_lat
    
    # Control point
    ctrl_lat = mid_lat + curvature * perp_lat
    ctrl_lon = mid_lon + curvature * perp_lon
    
    # Generate points along the quadratic Bezier curve
    curve_points = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = (1 - t)**2 * lat1 + 2 * (1 - t) * t * ctrl_lat + t**2 * lat2
        lon = (1 - t)**2 * lon1 + 2 * (1 - t) * t * ctrl_lon + t**2 * lon2
        curve_points.append([lat, lon])
        
    return curve_points

def main():
    # 1. Setup balanced graph (same logic as ssp_solucao.py)
    no_balancos = orig_balancos.copy()
    conexoes = orig_conexoes.copy()

    # Balance adjustments (float precision correction)
    no_balancos["Ceilândia"] -= sum(no_balancos.values())

    # Solve optimal MCF flow via Successive Shortest Path (SSP)
    x, pi, history = successive_shortest_path(no_balancos, conexoes)

    # 2. Parse geographical coordinates from project data
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
                    coords_nos[nome] = (lat, lon)

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

    # Confirm all nodes have coordinates
    for node in no_balancos:
        if node not in coords_nos:
            print(f"Error: Node '{node}' was not found in coordinates dataset.")
            sys.exit(1)

    # Calculate map center based on average coordinates
    all_lats = [coords[0] for coords in coords_nos.values()]
    all_lons = [coords[1] for coords in coords_nos.values()]
    map_center = [sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons)]

    # 3. Create Folium Map with Premium Layers
    m = folium.Map(location=map_center, zoom_start=11, tiles=None)

    # Base layer 1: Dark Minimalist (Glowing visual)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Mapa Escuro Minimalista (Recomendado)",
        overlay=False,
        control=True,
        show=True
    ).add_to(m)

    # Base layer 2: CartoDB Voyager (OSM-styled, does not block file:// requests)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Mapa Colorido (Voyager)",
        overlay=False,
        control=True,
        show=False
    ).add_to(m)

    # Base layer 3: Light Minimalist
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Mapa Claro Minimalista",
        overlay=False,
        control=True,
        show=False
    ).add_to(m)

    # Define Feature Groups
    active_group = folium.FeatureGroup(name="Fluxos Ativos (Verde Animado)", show=True)
    inactive_group = folium.FeatureGroup(name="Conexões Inativas (Tracejado)", show=True)
    physical_group = folium.FeatureGroup(name="Rede Física (Sem Solução)", show=False)
    water_group = folium.FeatureGroup(name="Corpos d'Água (Lago Paranoá, etc.)", show=True)

    # 4. Load and add water bodies
    try:
        with open(water_json, "r", encoding="utf-8") as f:
            water_data = json.load(f)
            
        for feat in water_data.get("features", []):
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            w_name = props.get("nome", "").strip()
            tooltip = w_name if w_name else "Corpo d'água"
            
            if geom.get("type") == "Polygon":
                for ring in geom.get("coordinates", []):
                    locations = [[pt[1], pt[0]] for pt in ring]
                    folium.Polygon(
                        locations=locations,
                        color="#1d4ed8",
                        fill=True,
                        fill_color="#3b82f6",
                        fill_opacity=0.25,
                        weight=1.0,
                        tooltip=tooltip
                    ).add_to(water_group)
            elif geom.get("type") == "MultiPolygon":
                for poly in geom.get("coordinates", []):
                    for ring in poly:
                        locations = [[pt[1], pt[0]] for pt in ring]
                        folium.Polygon(
                            locations=locations,
                            color="#1d4ed8",
                            fill=True,
                            fill_color="#3b82f6",
                            fill_opacity=0.25,
                            weight=1.0,
                            tooltip=tooltip
                        ).add_to(water_group)
    except Exception as e:
        print(f"Warning: Could not process water bodies JSON: {e}")

    water_group.add_to(m)

    # 5. Draw connections (Edges) as curved Bezier arcs
    # Let's map (u, v) connections to their physical details
    total_cost = 0.0
    total_flow = 0.0

    for (u, v), flow_val in x.items():
        # Get capacity and cost from conexoes list
        cap_val = next(c[2] for c in conexoes if c[0] == u and c[1] == v)
        cost_val = next(c[3] for c in conexoes if c[0] == u and c[1] == v)

        p1 = coords_nos[u]
        p2 = coords_nos[v]

        # Calculate Bezier curve points
        curve_points = get_bezier_curve(p1, p2, curvature=0.12, num_points=30)

        # Draw physical connection (without solution flows)
        physical_tooltip = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; line-height: 1.6; color: #1e293b; min-width: 200px; padding: 5px;">
            <strong style="color: #3b82f6; font-size: 14px; border-bottom: 1px solid #e2e8f0; display:block; padding-bottom:4px; margin-bottom:6px;">Tubulação de Integração (Rede Física)</strong>
            <strong>Origem (ETA):</strong> {u}<br/>
            <strong>Destino (RA):</strong> {v}<br/>
            <strong>Capacidade Máxima:</strong> {cap_val:.1f} l/s<br/>
            <strong>Custo de Transporte:</strong> {cost_val:.2f} km
        </div>
        """
        folium.PolyLine(
            locations=curve_points,
            color="#3b82f6",
            weight=3.0,
            opacity=0.8,
            tooltip=physical_tooltip
        ).add_to(physical_group)

        is_active = flow_val > 1e-2

        if is_active:
            flow_cost = flow_val * cost_val
            total_cost += flow_cost
            total_flow += flow_val
            
            # Width proportional to capacity usage: base width 2.5 + up to 6.5 extra
            width = 2.5 + 6.5 * (flow_val / cap_val)

            tooltip_html = f"""
            <div style="font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; line-height: 1.6; color: #1e293b; min-width: 200px; padding: 5px;">
                <strong style="color: #10b981; font-size: 14px; border-bottom: 1px solid #e2e8f0; display:block; padding-bottom:4px; margin-bottom:6px;">Adutora (Fluxo Ativo)</strong>
                <strong>Origem (ETA):</strong> {u}<br/>
                <strong>Destino (RA):</strong> {v}<br/>
                <strong>Fluxo Otimizado:</strong> <span style="color: #10b981; font-weight: bold;">{flow_val:.2f} l/s</span><br/>
                <strong>Capacidade Máxima:</strong> {cap_val:.1f} l/s<br/>
                <strong>Custo de Transporte:</strong> {cost_val:.2f} km
            </div>
            """

            # Active paths animated in green
            AntPath(
                locations=curve_points,
                color="#10b981",
                pulse_color="#34d399",
                weight=width,
                delay=1200 - int(800 * (flow_val / cap_val)), # Flow moves faster with higher volume
                dash_array=[15, 30],
                opacity=0.9,
                tooltip=tooltip_html
            ).add_to(active_group)
        else:
            tooltip_html = f"""
            <div style="font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; line-height: 1.6; color: #1e293b; min-width: 200px; padding: 5px;">
                <strong style="color: #64748b; font-size: 14px; border-bottom: 1px solid #e2e8f0; display:block; padding-bottom:4px; margin-bottom:6px;">Adutora (Sem Fluxo)</strong>
                <strong>Origem (ETA):</strong> {u}<br/>
                <strong>Destino (RA):</strong> {v}<br/>
                <strong>Fluxo Otimizado:</strong> <span style="color: #e2e8f0; font-weight: bold;">0.00 l/s</span><br/>
                <strong>Capacidade Máxima:</strong> {cap_val:.1f} l/s<br/>
                <strong>Custo de Transporte:</strong> {cost_val:.2f} km
            </div>
            """

            # Inactive paths dashed in grey
            folium.PolyLine(
                locations=curve_points,
                color="#64748b",
                weight=1.5,
                opacity=0.45,
                dash_array="5, 10",
                tooltip=tooltip_html
            ).add_to(inactive_group)

    active_group.add_to(m)
    inactive_group.add_to(m)
    physical_group.add_to(m)

    # 6. Render nodes with custom SVG icons (Premium Look)
    eta_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36" style="filter: drop-shadow(0px 3px 6px rgba(239,68,68,0.45));">
      <path fill="#ef4444" stroke="#ffffff" stroke-width="1.8" d="M12,2.69C12,2.69 4,10 4,14A8,8 0 0,0 12,22A8,8 0 0,0 20,14C20,10 12,2.69 12,2.69Z"/>
      <circle cx="12" cy="14" r="3.5" fill="#ffffff"/>
    </svg>
    """
    
    ra_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="36" height="36" style="filter: drop-shadow(0px 3px 6px rgba(59,130,246,0.45));">
      <rect x="2" y="2" width="20" height="20" rx="6" fill="#1e293b" opacity="0.3"/>
      <path fill="#3b82f6" stroke="#ffffff" stroke-width="1.8" d="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z"/>
    </svg>
    """

    for name, coords in coords_nos.items():
        bal = no_balancos[name]
        is_eta = "ETA" in name
        
        # Proportional size multiplier for node scale
        abs_bal = abs(bal)
        size_multiplier = 1.0 + 0.35 * math.log(1 + abs_bal / 100.0)

        if is_eta:
            node_type_label = "ETA (Estação de Tratamento)"
            type_color = "#ef4444"
            sign = "+"
            icon_markup = eta_svg
            # Find maximum capacity
            cap_sum = sum(c[2] for c in conexoes if c[0] == name)
            extra_details = f"<strong>Capacidade de Injeção:</strong> {cap_sum:.1f} l/s<br/>"
        else:
            node_type_label = "RA (Região Administrativa)"
            type_color = "#3b82f6"
            sign = ""
            icon_markup = ra_svg
            extra_details = ""

        tooltip_html = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13px; line-height: 1.6; color: #1e293b; min-width: 220px; padding: 5px;">
            <strong style="color: {type_color}; font-size: 14px; border-bottom: 1px solid #e2e8f0; display:block; padding-bottom:4px; margin-bottom:6px;">{node_type_label}</strong>
            <strong>Nome:</strong> {name}<br/>
            {extra_details}
            <strong>Balanço de Fluxo:</strong> <span style="color: {type_color}; font-weight: bold;">{sign}{bal:.2f} l/s</span>
        </div>
        """

        folium.Marker(
            location=coords,
            icon=folium.DivIcon(
                icon_size=(int(36 * size_multiplier), int(36 * size_multiplier)),
                icon_anchor=(int(18 * size_multiplier), int(36 * size_multiplier)),
                html=f'<div style="width:100%; height:100%; transform: scale({size_multiplier}); transform-origin: bottom center;">{icon_markup}</div>'
            ),
            tooltip=tooltip_html
        ).add_to(m)

    # 7. Append floating controls (Glassmorphism design system)
    # Glassmorphic Legend
    legend_html = """
    <div id="map-legend" style="
        position: fixed; 
        bottom: 30px; 
        left: 30px; 
        width: 280px; 
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(12px) saturate(180%);
        -webkit-backdrop-filter: blur(12px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 16px;
        padding: 20px; 
        font-size: 13px; 
        font-family: 'Outfit', 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #1e293b;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        z-index: 9999;
        transition: all 0.3s ease;
    ">
        <h4 style="margin: 0 0 8px 0; font-weight: 700; color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; font-size: 15px; letter-spacing: -0.02em;">Rede de Distribuição - DF</h4>
        <p style="margin: 0 0 12px 0; font-size: 11px; color: #64748b; line-height: 1.4;">Fluxos otimizados pelo algoritmo Successive Shortest Path (SSP).</p>
        
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" style="margin-right: 12px; filter: drop-shadow(0 2px 4px rgba(239, 68, 68, 0.2));">
              <path fill="#ef4444" stroke="#ffffff" stroke-width="1.5" d="M12,2.69C12,2.69 4,10 4,14A8,8 0 0,0 12,22A8,8 0 0,0 20,14C20,10 12,2.69 12,2.69Z"/>
            </svg>
            <span style="font-weight: 500;">ETA (Nó Fonte / Injeção)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" style="margin-right: 12px; filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.2));">
              <path fill="#3b82f6" stroke="#ffffff" stroke-width="1.5" d="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z"/>
            </svg>
            <span style="font-weight: 500;">RA (Nó Sumidouro / Consumo)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="width: 24px; height: 5px; background: linear-gradient(90deg, #10b981, #34d399); border-radius: 3px; margin-right: 12px; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);"></div>
            <span style="font-weight: 500;">Fluxo Ativo (Verde Animado)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <div style="width: 24px; height: 3px; background-color: #cbd5e1; border-radius: 1.5px; margin-right: 12px; border-top: 2px dashed #94a3b8;"></div>
            <span style="font-weight: 500; color: #64748b;">Capacidade Inativa (Tracejado)</span>
        </div>
        <div style="display: flex; align-items: center; border-top: 1px solid rgba(0, 0, 0, 0.05); padding-top: 10px;">
            <div style="width: 24px; height: 12px; background-color: rgba(59, 130, 246, 0.2); border: 1.5px solid #3b82f6; border-radius: 4px; margin-right: 12px;"></div>
            <span style="font-weight: 500;">Corpos d'Água / Reservatórios</span>
        </div>
    </div>
    """

    # HUD title panel with optimal details
    title_html = f"""
    <div style="
        position: fixed; 
        top: 20px; 
        left: 50%; 
        transform: translateX(-50%); 
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 14px 28px; 
        font-family: 'Outfit', 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #ffffff;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        z-index: 9999;
        text-align: center;
        min-width: 450px;
    ">
        <h2 style="margin: 0 0 4px 0; font-size: 18px; font-weight: 700; letter-spacing: -0.02em; color: #3b82f6;">Otimização da Rede de Distribuição de Água - DF</h2>
        <p style="margin: 0; font-size: 12px; color: #94a3b8; font-weight: 500;">
            Algoritmo SSP | Custo Total: <span style="color: #10b981; font-weight: 700;">{total_cost:.2f} km-l/s</span> | Vazão Otimizada: <span style="color: #3b82f6; font-weight: 700;">{total_flow:.2f} l/s</span>
        </p>
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))
    m.get_root().html.add_child(folium.Element(title_html))

    # Retrieve Javascript variable names for Leaflet FeatureGroups and map instance
    active_group_var = active_group.get_name()
    inactive_group_var = inactive_group.get_name()
    physical_group_var = physical_group.get_name()
    map_var = m.get_name()

    # Create and add the floating toggle switch
    toggle_html = f"""
    <div id="solution-toggle-container" style="
        position: fixed;
        top: 25px;
        right: 80px;
        z-index: 9999;
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 10px 18px;
        font-family: 'Outfit', 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #ffffff;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.3s ease;
    ">
        <span style="font-size: 13px; font-weight: 600; color: #94a3b8; letter-spacing: -0.01em;">Rede Física</span>
        <label class="switch" style="
            position: relative;
            display: inline-block;
            width: 46px;
            height: 24px;
            margin: 0;
        ">
            <input type="checkbox" id="solution-checkbox" checked style="opacity: 0; width: 0; height: 0;">
            <span class="slider" style="
                position: absolute;
                cursor: pointer;
                top: 0; left: 0; right: 0; bottom: 0;
                background-color: #475569;
                transition: .3s;
                border-radius: 24px;
            "></span>
        </label>
        <span style="font-size: 13px; font-weight: 600; color: #10b981; letter-spacing: -0.01em;">Solução Ótima</span>
    </div>

    <style>
    .switch input:checked + .slider {{
        background-color: #10b981;
    }}
    .slider:before {{
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .3s;
        border-radius: 50%;
    }}
    .switch input:checked + .slider:before {{
        transform: translateX(22px);
    }}
    </style>

    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        var mapInstance = {map_var};
        var activeGroup = {active_group_var};
        var inactiveGroup = {inactive_group_var};
        var physicalGroup = {physical_group_var};
        
        var checkbox = document.getElementById('solution-checkbox');
        
        function updateLayers() {{
            if (checkbox.checked) {{
                if (!mapInstance.hasLayer(activeGroup)) mapInstance.addLayer(activeGroup);
                if (!mapInstance.hasLayer(inactiveGroup)) mapInstance.addLayer(inactiveGroup);
                if (mapInstance.hasLayer(physicalGroup)) mapInstance.removeLayer(physicalGroup);
            }} else {{
                if (mapInstance.hasLayer(activeGroup)) mapInstance.removeLayer(activeGroup);
                if (mapInstance.hasLayer(inactiveGroup)) mapInstance.removeLayer(inactiveGroup);
                if (!mapInstance.hasLayer(physicalGroup)) mapInstance.addLayer(physicalGroup);
            }}
        }}
        
        checkbox.addEventListener('change', updateLayers);
        updateLayers();
    }});
    </script>
    """

    m.get_root().html.add_child(folium.Element(toggle_html))

    # Add Layer Control to allow toggling base layers and connections
    folium.LayerControl(position="topright").add_to(m)

    # Save final HTML map
    output_html = os.path.join(script_dir, "mapa_grafo_ssp.html")
    m.save(output_html)
    print(f"Success! Interactive flow map successfully generated and saved to '{output_html}'")

if __name__ == "__main__":
    main()

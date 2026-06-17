import csv
import re
import math
import json
import os
import sys

# Auto-bootstrap: if folium is missing, try to re-execute using the local virtual environment
try:
    import folium
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "venv", "bin", "python3")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Error: 'folium' is not installed, and the local virtual environment was not found.")
        print("Please run: python3 -m venv venv && ./venv/bin/pip install folium")
        sys.exit(1)

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

# Haversine formula to compute geodesic distance in km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

# ETA configurations (capacities and balances)
eta_configs = {
    "ETA Rio Descoberto": {"capacity": 6000, "balance": 4450},
    "ETA Brasília": {"capacity": 1200, "balance": 1200},
    "ETA Lago Norte": {"capacity": 700, "balance": 700},
    "ETA Gama": {"capacity": 320, "balance": 320},
    "ETA Planaltina": {"capacity": 60, "balance": 60},
    "ETA Sobradinho": {"capacity": 600, "balance": 570},
    "ETA Paranoá": {"capacity": 300, "balance": 300}
}

# RA configurations (consumption weights)
ra_weights = {
    "Ceilândia": 101,
    "Taguatinga": 127,
    "Plano Piloto": 213,
    "Samambaia": 103,
    "Guará": 129,
    "Sobradinho": 133,
    "Planaltina": 112
}

def main():
    etas_csv = "dados_do_projeto/estacoes_tratamento_agua.csv"
    ras_csv = "dados_do_projeto/CONSUMO_AGUA_RA.csv"
    water_json = "dados_do_projeto/CORPOS_DAGUA.json"
    
    # 1. Parse ETAs
    etas_parsed = {}
    with open(etas_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nome = row["nome"].strip()
            # If the plant is one of our target ETAs
            if nome in eta_configs:
                geom = row["the_geom"]
                # Parse coordinates: MULTIPOINT ((lat lon)) - first is Lat, second is Lon
                match = re.search(r'MULTIPOINT\s*\(\(\s*([-\d.]+)\s+([-\d.]+)\s*\)\)', geom)
                if match:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    etas_parsed[nome] = {
                        "lat": lat,
                        "lon": lon,
                        "capacity": eta_configs[nome]["capacity"],
                        "balance": eta_configs[nome]["balance"]
                    }
                else:
                    print(f"Warning: Could not parse geom for ETA {nome}")

    # 2. Parse RAs
    ras_parsed = {}
    with open(ras_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nome = row["nome"].strip()
            if nome in ra_weights:
                geom = row["the_geom"]
                # Parse MULTIPOLYGON outer ring
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
                    
                    # Remove last closed coordinate if identical to first
                    if points and points[0] == points[-1]:
                        vertices = points[:-1]
                    else:
                        vertices = points
                    
                    # Average of coordinates to calculate centroid
                    avg_e = sum(p[0] for p in vertices) / len(vertices)
                    avg_n = sum(p[1] for p in vertices) / len(vertices)
                    
                    # Convert to Lat/Lon
                    lat, lon = utm_to_latlon(avg_e, avg_n, zone=23, northern=False)
                    
                    ras_parsed[nome] = {
                        "lat": lat,
                        "lon": lon,
                        "weight": ra_weights[nome],
                        "utm_easting": avg_e,
                        "utm_northing": avg_n
                    }
                else:
                    print(f"Warning: Could not parse geom for RA {nome}")

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
        if ra_name in ras_parsed:
            ras_parsed[ra_name]["lat"] = coord[0]
            ras_parsed[ra_name]["lon"] = coord[1]

    # Verify we successfully parsed all nodes
    for name in eta_configs:
        if name not in etas_parsed:
            print(f"Error: Target ETA {name} was not parsed successfully.")
    for name in ra_weights:
        if name not in ras_parsed:
            print(f"Error: Target RA {name} was not parsed successfully.")

    # Calculate proportional balances for RAs (sinks)
    total_weight = sum(ra_weights.values())
    total_injection = sum(eta_configs[name]["balance"] for name in eta_configs)
    
    # We want sum of all balances to be exactly 0, so total RA balance = -total_injection = -7600 l/s
    for name, node in ras_parsed.items():
        node["balance"] = - (node["weight"] / total_weight) * total_injection

    # 3. Connect ETAs to 3 closest RAs (Edges)
    edges = []
    for eta_name, eta in etas_parsed.items():
        distances = []
        for ra_name, ra in ras_parsed.items():
            dist = haversine(eta["lat"], eta["lon"], ra["lat"], ra["lon"])
            distances.append((ra_name, dist))
        
        # Sort by distance and keep top 3
        distances.sort(key=lambda x: x[1])
        top_3 = distances[:3]
        
        for ra_name, dist in top_3:
            edges.append({
                "source": eta_name,
                "target": ra_name,
                "capacity": eta["capacity"],
                "cost": dist
            })

    # Adutoras de Integração adicionais baseadas nas interconexões do Atlas DF
    integracoes = [
        ("ETA Rio Descoberto", "Guará", 2000.0),
        ("ETA Rio Descoberto", "Plano Piloto", 2000.0),
        ("ETA Brasília", "Sobradinho", 1000.0),
        ("ETA Lago Norte", "Planaltina", 1000.0),
        ("ETA Sobradinho", "Planaltina", 1000.0)
    ]
    for src, tgt, cap in integracoes:
        if src in etas_parsed and tgt in ras_parsed:
            dist = haversine(etas_parsed[src]["lat"], etas_parsed[src]["lon"], ras_parsed[tgt]["lat"], ras_parsed[tgt]["lon"])
            # Evita duplicidade se já existir
            if not any(e["source"] == src and e["target"] == tgt for e in edges):
                edges.append({
                    "source": src,
                    "target": tgt,
                    "capacity": cap,
                    "cost": dist
                })

    # Ajuste de capacidade do arco local ETA Planaltina -> Planaltina para evitar gargalo artificial
    for edge in edges:
        if edge["source"] == "ETA Planaltina" and edge["target"] == "Planaltina":
            edge["capacity"] = 1000.0

    # 4. Generate Folium Map
    # Center map on average of all coordinates
    all_lats = [n["lat"] for n in etas_parsed.values()] + [n["lat"] for n in ras_parsed.values()]
    all_lons = [n["lon"] for n in etas_parsed.values()] + [n["lon"] for n in ras_parsed.values()]
    map_center = [sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons)]
    
    m = folium.Map(location=map_center, zoom_start=11, tiles=None)

    # 1. CartoDB Voyager base layer (OSM-styled, does not block file:// requests)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Mapa Base (Colorido Voyager)",
        overlay=False,
        control=True,
        show=True
    ).add_to(m)

    # 2. Solid White base layer (SVG data URI)
    folium.TileLayer(
        tiles='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" style="background:white"/>',
        attr='Fundo Branco',
        name="Sem Mapa (Fundo Branco)",
        overlay=False,
        control=True,
        show=False
    ).add_to(m)

    # 3. Solid Dark base layer (SVG data URI using #2c3e50 encoded as %232c3e50)
    folium.TileLayer(
        tiles='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" style="background:%232c3e50"/>',
        attr='Fundo Escuro',
        name="Sem Mapa (Fundo Escuro)",
        overlay=False,
        control=True,
        show=False
    ).add_to(m)

    # Add water bodies from JSON
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
                    # GeoJSON is [lon, lat], Folium is [lat, lon]
                    locations = [[pt[1], pt[0]] for pt in ring]
                    folium.Polygon(
                        locations=locations,
                        color="#2980b9",
                        fill=True,
                        fill_color="#3498db",
                        fill_opacity=0.35,
                        weight=1,
                        tooltip=tooltip
                    ).add_to(m)
            elif geom.get("type") == "MultiPolygon":
                for poly in geom.get("coordinates", []):
                    for ring in poly:
                        locations = [[pt[1], pt[0]] for pt in ring]
                        folium.Polygon(
                            locations=locations,
                            color="#2980b9",
                            fill=True,
                            fill_color="#3498db",
                            fill_opacity=0.35,
                            weight=1,
                            tooltip=tooltip
                        ).add_to(m)
    except Exception as e:
        print(f"Warning: Could not process water bodies JSON: {e}")

    # Add Edges (Pipelines)
    for edge in edges:
        eta = etas_parsed[edge["source"]]
        ra = ras_parsed[edge["target"]]
        
        # Scaling polyline width: 1 + sqrt(capacity) * 0.15
        width = 1.0 + math.sqrt(edge["capacity"]) * 0.15
        
        tooltip_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #2c3e50;">
            <strong style="color: #27ae60;">Tubulação de Distribuição</strong><br/>
            <strong>Origem (ETA):</strong> {edge["source"]}<br/>
            <strong>Destino (RA):</strong> {edge["target"]}<br/>
            <strong>Capacidade de Fluxo:</strong> {edge["capacity"]} l/s<br/>
            <strong>Custo (Haversine):</strong> {edge["cost"]:.2f} km
        </div>
        """
        
        folium.PolyLine(
            locations=[[eta["lat"], eta["lon"]], [ra["lat"], ra["lon"]]],
            color="#2ecc71",
            weight=width,
            opacity=0.8,
            tooltip=tooltip_html
        ).add_to(m)

    # SVG markup for ETAs
    eta_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%">
      <path fill="#e74c3c" stroke="#ffffff" stroke-width="1.5" d="M12,2.69C12,2.69 4,10 4,14A8,8 0 0,0 12,22A8,8 0 0,0 20,14C20,10 12,2.69 12,2.69Z"/>
      <circle cx="12" cy="14" r="3" fill="#ffffff" opacity="0.8"/>
    </svg>
    """
    
    # SVG markup for RAs
    ra_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%">
      <path fill="#2980b9" stroke="#ffffff" stroke-width="1.5" d="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z"/>
    </svg>
    """

    # Add ETA markers
    for name, eta in etas_parsed.items():
        tooltip_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #2c3e50; min-width: 150px;">
            <strong style="color: #e74c3c;">ETA (Estação de Tratamento)</strong><br/>
            <strong>Nome:</strong> {name}<br/>
            <strong>Capacidade:</strong> {eta["capacity"]} l/s<br/>
            <strong>Injeção (Balanço):</strong> +{eta["balance"]} l/s
        </div>
        """
        folium.Marker(
            location=[eta["lat"], eta["lon"]],
            icon=folium.DivIcon(
                icon_size=(32, 32),
                icon_anchor=(16, 16),
                class_name="",
                html=f'<div style="width:100%; height:100%;">{eta_svg}</div>'
            ),
            tooltip=tooltip_html
        ).add_to(m)

    # Add RA markers
    for name, ra in ras_parsed.items():
        tooltip_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #2c3e50; min-width: 150px;">
            <strong style="color: #2980b9;">RA (Região Administrativa)</strong><br/>
            <strong>Nome:</strong> {name}<br/>
            <strong>Peso Consumo:</strong> {ra["weight"]}<br/>
            <strong>Demanda (Balanço):</strong> {ra["balance"]:.2f} l/s
        </div>
        """
        folium.Marker(
            location=[ra["lat"], ra["lon"]],
            icon=folium.DivIcon(
                icon_size=(32, 32),
                icon_anchor=(16, 16),
                class_name="",
                html=f'<div style="width:100%; height:100%;">{ra_svg}</div>'
            ),
            tooltip=tooltip_html
        ).add_to(m)

    # Append glassmorphic legend
    legend_html = """
    <div id="map-legend" style="
        position: fixed; 
        bottom: 50px; 
        left: 50px; 
        width: 250px; 
        background-color: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 12px;
        padding: 16px; 
        font-size: 13px; 
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #2c3e50;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        z-index: 9999;
    ">
        <h4 style="margin: 0 0 12px 0; font-weight: bold; color: #1a252f; border-bottom: 2px solid #3498db; padding-bottom: 6px; font-size: 14px;">Rede de Distribuição - DF</h4>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" style="margin-right: 10px;">
              <path fill="#e74c3c" stroke="#ffffff" stroke-width="1" d="M12,2.69C12,2.69 4,10 4,14A8,8 0 0,0 12,22A8,8 0 0,0 20,14C20,10 12,2.69 12,2.69Z"/>
            </svg>
            <span>ETA (Nó Fonte)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" style="margin-right: 10px;">
              <path fill="#2980b9" stroke="#ffffff" stroke-width="1" d="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z"/>
            </svg>
            <span>RA (Nó Sumidouro)</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="width: 24px; height: 4px; background-color: #2ecc71; border-radius: 2px; margin-right: 10px;"></div>
            <span>Adutora (Arco de Ligação)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 24px; height: 12px; background-color: rgba(52, 152, 219, 0.4); border: 1px solid #3498db; border-radius: 3px; margin-right: 10px;"></div>
            <span>Corpos d'Água / Reservatórios</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add LayerControl to allow toggling base maps
    folium.LayerControl(position="topright").add_to(m)

    # Save map
    m.save("mapa_grafo_ssp_basico.html")
    print("Map successfully created and saved as mapa_grafo_ssp_basico.html")

    # 5. Print Tables to the Terminal
    print("\n" + "=" * 80)
    print("                                 TABELA DE NÓS")
    print("=" * 80)
    print(f"{'Tipo':<6} | {'Nome':<30} | {'Balanço (l/s)':<15}")
    print("-" * 80)
    for name, node in sorted(etas_parsed.items()):
        bal_str = f"+{node['balance']:.2f}"
        print(f"{'ETA':<6} | {name:<30} | {bal_str:>15}")
    for name, node in sorted(ras_parsed.items()):
        bal_str = f"{node['balance']:.2f}"
        print(f"{'RA':<6} | {name:<30} | {bal_str:>15}")
    
    # Print the sum of balances to verify it is exactly 0
    total_balance = sum(n["balance"] for n in etas_parsed.values()) + sum(n["balance"] for n in ras_parsed.values())
    print("-" * 80)
    print(f"{'TOTAL':<6} | {'Soma dos Balanços':<30} | {f'{total_balance:.2f}':>15}")
    print("=" * 80)
    
    print("\n" + "=" * 85)
    print("                                 TABELA DE ARCOS")
    print("=" * 85)
    print(f"{'Origem (ETA)':<22} | {'Destino (RA)':<22} | {'Capacidade (l/s)':<18} | {'Custo (km)':<12}")
    print("-" * 85)
    for edge in sorted(edges, key=lambda x: (x["source"], x["cost"])):
        print(f"{edge['source']:<22} | {edge['target']:<22} | {edge['capacity']:>18.2f} | {edge['cost']:>12.2f}")
    print("=" * 85)

if __name__ == "__main__":
    main()

"""
Dashboard Escuela de Padres — Generador automático
USO:
  pip install pandas requests
  python generar_dashboard.py
"""
import pandas as pd
import requests
import io
import json
import webbrowser
import os
from datetime import datetime

SHEETS = {
    "Corrigiendo con respeto":    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQlwttts0WlUcwFG7vkntfP4yNVJkl5OK7PcWEKnDay6rl16GW2F44oA0uZ6Lf1RG6tZ3O1FJErOw2K/pub?output=csv",
    "Educar emociones":           "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsy2rOjyvieHFywxMB6x1TWmLWMkeut0qzBAT3Vge5ALz-XO3tbzH-XZN1HJVZbEoU9_AkTEwcc6N1/pub?output=csv",
    "Conectando con mis hijos":   "https://docs.google.com/spreadsheets/d/e/2PACX-1vT5Hhpo4w1jSCrgoWB6KHnkwkV0h24wp1kqCDuocp89klSDbXT--l1CQH6fx025Er9RR0lQN-NtrRAD/pub?output=csv",
    "Hijos en la Era Digital":    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQB3_vcWhNtFeYZ_hxDd-afpcciBntjUGBzNe2wmGGRi0RSJmTwGpi6ZWDO-_MlTyrg-D5sbWjMkvu7/pub?output=csv",
    "Familias Saludables (30)":   "https://docs.google.com/spreadsheets/d/e/2PACX-1vSAnUQ53OtKxDvrAtXE39R15Mgp8jIhAjtESp-y7atwQMmPWMCV-ogr8xnTY-oLMy1ZGI2klT9YlS86/pub?output=csv",
    "Familias Saludables (70)":   "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6q4LcLvIGKGAFVMcDd7iMwv8aAsHdhsrSnxRPQixmOIPt7a65oM86-m29jLCvR_GdYghmLKaJedsR/pub?output=csv",
    "Criar con firmeza y carino": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7W1thpTXQ_CDvMT4pFmkxVwVOJUyxjphdy3GDBrR2wIbf1lZ3B5t4o9_V2yzEN3RFhos6IEl8VHlU/pub?output=csv",
    "Decisiones que protegen":    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8VpFW3VYcB4O7u7_UOTXRnlbMYVvdzaykAZE742S93ITvPoqCFaMwJKTwXMs_vPvhSicWNtYLJrnK/pub?output=csv",
}

TALLERES_INFO = {
    "Educar emociones":           {"cupo":25, "ponente":"Psic. Samy Manrique Enriquez",  "hora":"3:30-5:00 pm", "espacio":"2do sec.",  "rec":"Inicial y Primaria", "turno":"tarde1"},
    "Hijos en la Era Digital":    {"cupo":25, "ponente":"Psic. Delma Asuncion Quispe",   "hora":"3:30-5:00 pm", "espacio":"1ro sec.",  "rec":"Inicial y Primaria", "turno":"tarde1"},
    "Familias Saludables (70)":   {"cupo":70, "ponente":"Lic. Virginia Leon Gonzales",   "hora":"3:30-5:00 pm", "espacio":"Auditorio", "rec":"Inicial y Primaria", "turno":"tarde1"},
    "Corrigiendo con respeto":    {"cupo":70, "ponente":"Psic. Abel Alex Sumi Leon",     "hora":"3:30-5:00 pm", "espacio":"Auditorio", "rec":"Inicial y Primaria", "turno":"tarde1"},
    "Conectando con mis hijos":   {"cupo":25, "ponente":"Psic. Samy Manrique Enriquez",  "hora":"5:30-7:00 pm", "espacio":"2do sec.",  "rec":"Secundaria",         "turno":"tarde2"},
    "Criar con firmeza y carino": {"cupo":25, "ponente":"Psic. Abel Alex Sumi Leon",     "hora":"5:30-7:00 pm", "espacio":"1ro sec.",  "rec":"Secundaria",         "turno":"tarde2"},
    "Decisiones que protegen":    {"cupo":30, "ponente":"Psic. Delma Asuncion Quispe",   "hora":"5:30-7:00 pm", "espacio":"3ro sec.",  "rec":"Secundaria",         "turno":"tarde2"},
    "Familias Saludables (30)":   {"cupo":30, "ponente":"Lic. Virginia Leon Gonzales",   "hora":"5:30-7:00 pm", "espacio":"3ro sec.",  "rec":"Secundaria",         "turno":"tarde2"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
}

def normalizar(nombre):
    return str(nombre).strip().lower().replace("  ", " ")

def encontrar_col(df, palabras_clave):
    for col in df.columns:
        col_clean = col.strip().lower()
        if all(p in col_clean for p in palabras_clave):
            return col
    return None

def leer_sheet(nombre, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                df = pd.read_csv(io.StringIO(r.content.decode(enc)))
                break
            except Exception:
                continue
        print(f"  OK {nombre}: {len(df)} registros")
        return df
    except Exception as e:
        print(f"  ERROR {nombre}: {e}")
        return pd.DataFrame()

def detectar_duplicados(dfs):
    duplicados = {}
    for taller, df in dfs.items():
        if df.empty:
            continue
        col = encontrar_col(df, ["estudiante"])
        if not col:
            continue
        dup = df[df.duplicated(subset=[col], keep=False)]
        if not dup.empty:
            duplicados[taller] = dup[col].value_counts().to_dict()
    return duplicados

def procesar(dfs):
    talleres_data = []
    por_grado = {}
    # nombres[grado] = { norm_name: {asistente, estudiante, talleres:[...]} }
    nombres = {}

    for taller_nombre, df in dfs.items():
        info = TALLERES_INFO.get(taller_nombre, {})
        talleres_data.append({
            "name":    taller_nombre,
            "cupo":    info.get("cupo", 0),
            "asist":   len(df),
            "ponente": info.get("ponente", ""),
            "hora":    info.get("hora", ""),
            "espacio": info.get("espacio", ""),
            "rec":     info.get("rec", ""),
            "turno":   info.get("turno", "tarde1"),
        })

        col_grado     = encontrar_col(df, ["grado"])
        col_asistente = encontrar_col(df, ["asistente"])
        col_estudiante = encontrar_col(df, ["estudiante"])
        if not col_grado:
            continue

        for grado in df[col_grado].dropna().unique():
            grado = str(grado).strip()
            if not grado:
                continue
            if grado not in por_grado:
                por_grado[grado] = {"total": 0, "talleres": {}}
                nombres[grado] = {}

            subset = df[df[col_grado] == grado]
            por_grado[grado]["total"] += len(subset)
            por_grado[grado]["talleres"][taller_nombre] = len(subset)

            if col_asistente:
                for _, row in subset.iterrows():
                    asist = str(row[col_asistente]).strip()
                    estud = str(row[col_estudiante]).strip() if col_estudiante else ""
                    if not asist or asist == "nan":
                        continue
                    norm = normalizar(asist)
                    if norm not in nombres[grado]:
                        nombres[grado][norm] = {
                            "asistente": asist,
                            "estudiante": estud if estud != "nan" else "",
                            "talleres": []
                        }
                    # Add taller only if not already registered
                    if taller_nombre not in nombres[grado][norm]["talleres"]:
                        nombres[grado][norm]["talleres"].append(taller_nombre)

    # Convert nombres dict to list per grado for JSON
    nombres_list = {}
    for grado, personas in nombres.items():
        nombres_list[grado] = sorted(
            list(personas.values()),
            key=lambda x: x["asistente"].lower()
        )

    total      = sum(t["asist"] for t in talleres_data)
    cupo_total = sum(t["cupo"]  for t in talleres_data)

    # Personas unicas globales (por nombre normalizado, sin importar taller)
    personas_unicas_global = set()
    for grado, personas in nombres.items():
        for norm, info in personas.items():
            personas_unicas_global.add(norm)
    personas_unicas = len(personas_unicas_global)

    # Personas unicas por grado
    por_grado_unicas = {}
    for grado, personas in nombres.items():
        por_grado_unicas[grado] = len(personas)

    return talleres_data, por_grado, nombres_list, total, cupo_total, personas_unicas, por_grado_unicas

def generar_html(talleres_data, por_grado, nombres, total, cupo_total, personas_unicas, por_grado_unicas, duplicados, fecha):
    occ_global = round(total / cupo_total * 100) if cupo_total else 0
    max_taller = max((t["asist"] for t in talleres_data), default=0)
    n_grados   = len(por_grado)

    tj  = json.dumps(talleres_data,   ensure_ascii=False)
    gj  = json.dumps(por_grado,       ensure_ascii=False)
    nj  = json.dumps(nombres,         ensure_ascii=False)
    puj = json.dumps(por_grado_unicas, ensure_ascii=False)

    dup_section = ""
    if duplicados:
        rows = ""
        for taller, alumnos in duplicados.items():
            for alumno, veces in alumnos.items():
                rows += f"<tr><td>{taller}</td><td>{alumno}</td><td><span class='badge badge-red'>{veces}x inscrito</span></td></tr>"
        dup_section = f"""
<div class="g1">
  <div class="card">
    <p class="ct">Alerta</p>
    <p class="cs">Posibles inscripciones duplicadas</p>
    <div class="tw"><table>
      <thead><tr><th>Taller</th><th>Alumno</th><th>Estado</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </div>
</div>"""

    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard Escuela de Padres</title>
<script src="chartjs.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root{--bg:#0d0d14;--card:#1c1c2a;--border:#2a2a3d;--surf:#15151f;
  --a1:#7c3aed;--a2:#06b6d4;--a3:#f59e0b;--a4:#10b981;--a5:#f43f5e;
  --text:#e8e8f0;--muted:#7a7a9a}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif}
body::before{content:'';position:fixed;inset:0;
  background:radial-gradient(ellipse 80% 50% at 20% 10%,rgba(124,58,237,.12),transparent 60%),
             radial-gradient(ellipse 60% 40% at 80% 80%,rgba(6,182,212,.08),transparent 55%);
  pointer-events:none;z-index:0}
.wrap{position:relative;z-index:1;max-width:1280px;margin:0 auto;padding:48px 24px}
.lbl{font-family:'Syne',sans-serif;font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--a2);margin-bottom:12px}
h1{font-family:'Syne',sans-serif;font-size:clamp(26px,5vw,50px);font-weight:800}
h1 span{color:var(--a1)}
.sub{color:var(--muted);font-size:14px;margin-top:8px}
header{margin-bottom:44px}
.upd{display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,.1);
  border:1px solid rgba(16,185,129,.3);color:#10b981;padding:4px 12px;
  border-radius:999px;font-size:11px;margin-top:10px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px;margin-bottom:36px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:22px 18px;position:relative;overflow:hidden}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--kc,var(--a1))}
.kv{font-family:'Syne',sans-serif;font-size:38px;font-weight:800;color:var(--kc,var(--a1));line-height:1}
.kl{font-size:11px;color:var(--muted);margin-top:6px;text-transform:uppercase;letter-spacing:1px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:22px}
.g1{margin-bottom:22px}
@media(max-width:860px){.g2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:26px}
.ct{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.cs{font-size:18px;font-weight:500;margin-bottom:20px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.fb{background:var(--surf);border:1px solid var(--border);color:var(--muted);
  padding:5px 13px;border-radius:999px;font-size:12px;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:all .2s}
.fb:hover,.fb.active{background:var(--a1);border-color:var(--a1);color:#fff}
.tw{overflow-x:auto;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:var(--surf);color:var(--muted);text-transform:uppercase;
  letter-spacing:1px;font-size:10px;padding:11px 13px;text-align:left;
  border-bottom:1px solid var(--border)}
td{padding:10px 13px;border-bottom:1px solid var(--border);vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(124,58,237,.05)}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:11px;
  font-weight:600;background:rgba(124,58,237,.15);color:var(--a1)}
.badge-red{background:rgba(244,63,94,.15);color:var(--a5)}
.badge-green{background:rgba(16,185,129,.15);color:var(--a4)}
.badge-yellow{background:rgba(245,158,11,.15);color:var(--a3)}
.bi{display:flex;align-items:center;gap:8px}
.bb{flex:1;height:7px;background:var(--border);border-radius:99px;overflow:hidden}
.bf{height:100%;border-radius:99px}
.taller-tag{display:inline-block;margin:2px;padding:2px 8px;border-radius:999px;
  font-size:10px;font-weight:600;background:rgba(6,182,212,.12);color:#06b6d4}
.pg{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}
.pc{background:var(--surf);border:1px solid var(--border);border-radius:14px;
  padding:18px;position:relative;overflow:hidden}
.pc::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--pc,var(--a1))}
.pn{font-family:'Syne',sans-serif;font-weight:700;font-size:13px;margin-bottom:6px}
.pm{font-size:11px;color:var(--muted);display:flex;flex-direction:column;gap:3px}
.pt{display:inline-block;margin-top:8px;padding:2px 9px;border-radius:999px;
  font-size:10px;background:rgba(124,58,237,.15);color:var(--a1);font-weight:600}
footer{text-align:center;color:var(--muted);font-size:11px;margin-top:56px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <p class="lbl">Escuela de Padres · 27 de mayo · Reporte de Asistencia</p>
  <h1>Dashboard de <span>Participacion</span></h1>
  <p class="sub">Consolidado de 8 talleres · """ + str(n_grados) + """ grados y secciones</p>
  <div class="upd">Actualizado: """ + fecha + """</div>
</header>

<div class="kpis">
  <div class="kpi" style="--kc:#7c3aed"><div class="kv">""" + str(total) + """</div><div class="kl">Total inscripciones</div></div>
  <div class="kpi" style="--kc:#06b6d4"><div class="kv">""" + str(personas_unicas) + """</div><div class="kl">Personas unicas</div></div>
  <div class="kpi" style="--kc:#f59e0b"><div class="kv">8</div><div class="kl">Talleres</div></div>
  <div class="kpi" style="--kc:#10b981"><div class="kv">""" + str(n_grados) + """</div><div class="kl">Grados / Secciones</div></div>
  <div class="kpi" style="--kc:#f43f5e"><div class="kv">""" + str(cupo_total) + """</div><div class="kl">Cupos totales</div></div>
  <div class="kpi" style="--kc:#8b5cf6"><div class="kv">""" + str(occ_global) + """%</div><div class="kl">Ocupacion global</div></div>
</div>

<div class="g2">
  <div class="card"><p class="ct">Comparativa</p><p class="cs">Asistentes vs Cupo por taller</p>
    <div style="height:300px;position:relative"><canvas id="cOcc"></canvas></div></div>
  <div class="card"><p class="ct">Distribucion</p><p class="cs">Asistentes por taller</p>
    <div style="height:300px;position:relative"><canvas id="cDona"></canvas></div></div>
</div>
<div class="g2">
  <div class="card"><p class="ct">Participacion</p><p class="cs">Grados por asistencia</p>
    <div style="height:320px;position:relative"><canvas id="cGrados"></canvas></div></div>
  <div class="card"><p class="ct">Horario</p><p class="cs">Asistencia por turno</p>
    <div style="height:320px;position:relative"><canvas id="cTurno"></canvas></div></div>
</div>
<div class="g1">
  <div class="card"><p class="ct">Analisis cruzado</p><p class="cs">Participacion por grado en cada taller</p>
    <div class="filters" id="fNivel">
      <button class="fb active" data-n="todos">Todos</button>
      <button class="fb" data-n="inicial">Inicial</button>
      <button class="fb" data-n="primaria">Primaria</button>
      <button class="fb" data-n="secundaria">Secundaria</button>
    </div>
    <div style="height:340px;position:relative"><canvas id="cStack"></canvas></div>
  </div>
</div>
<div class="g1">
  <div class="card"><p class="ct">Detalle por taller</p><p class="cs">Cupos, asistentes y ocupacion</p>
  <div class="tw"><table>
    <thead><tr><th>#</th><th>Taller</th><th>Ponente</th><th>Hora</th><th>Espacio</th><th>Cupo</th><th>Asist.</th><th>Ocupacion</th><th>Nivel</th></tr></thead>
    <tbody id="tbT"></tbody>
  </table></div></div>
</div>
<div class="g1">
  <div class="card"><p class="ct">Detalle por grado</p><p class="cs">Participacion acumulada</p>
  <div class="tw"><table>
    <thead><tr><th>Grado / Seccion</th><th>Total</th><th>Talleres</th><th>Participacion</th></tr></thead>
    <tbody id="tbG"></tbody>
  </table></div></div>
</div>
""" + dup_section + """
<div class="g1">
  <div class="card"><p class="ct">Equipo</p><p class="cs">Ponentes y talleres</p>
    <div class="pg" id="pgDiv"></div>
  </div>
</div>

<div class="g1">
  <div class="card">
    <p class="ct">Directorio por salon</p>
    <p class="cs">Inscritos por grado y seccion</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:24px">
      <div style="position:relative;flex:1;min-width:220px">
        <span style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#7a7a9a;font-size:14px">&#127979;</span>
        <select id="selGrado" style="width:100%;background:#15151f;border:1px solid #2a2a3d;color:#e8e8f0;padding:10px 14px 10px 34px;border-radius:12px;font-size:13px;font-family:DM Sans,sans-serif;cursor:pointer;appearance:none">
          <option value="">Selecciona un grado / seccion</option>
        </select>
      </div>
      <div style="position:relative;min-width:200px">
        <span style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#7a7a9a;font-size:14px">&#128203;</span>
        <select id="selTaller" style="width:100%;background:#15151f;border:1px solid #2a2a3d;color:#e8e8f0;padding:10px 14px 10px 34px;border-radius:12px;font-size:13px;font-family:DM Sans,sans-serif;cursor:pointer;appearance:none">
          <option value="todos">Todos los talleres</option>
        </select>
      </div>
      <span id="countBadge" style="display:none;background:linear-gradient(135deg,#7c3aed,#06b6d4);color:#fff;padding:8px 16px;border-radius:999px;font-size:13px;font-weight:700;white-space:nowrap"></span>
    </div>
    <div id="placeholderDir" style="text-align:center;padding:60px 20px;color:#7a7a9a">
      <div style="font-size:40px;margin-bottom:12px">&#127979;</div>
      <div style="font-size:15px;font-weight:500">Selecciona un grado para ver los inscritos</div>
      <div style="font-size:12px;margin-top:6px">Puedes filtrar ademas por taller especifico</div>
    </div>
    <div id="listaInscritos" style="display:none">
      <div id="gridInscritos" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px"></div>
    </div>
  </div>
</div>

<footer>Escuela de Padres · 27 de mayo de 2026 · Datos desde Google Sheets</footer>
</div>

<script>
const TALLERES = """ + tj + """;
const NOMBRES  = """ + nj + """;
const POR_GRADO = """ + gj + """;
const POR_GRADO_UNICAS = """ + puj + """;
// Build unique-per-taller counts from NOMBRES
const POR_GRADO_UNICAS_TALLER = {};
Object.entries(NOMBRES).forEach(([grado, personas]) => {
  POR_GRADO_UNICAS_TALLER[grado] = {};
  personas.forEach(p => {
    p.talleres.forEach(t => {
      POR_GRADO_UNICAS_TALLER[grado][t] = (POR_GRADO_UNICAS_TALLER[grado][t]||0) + 1;
    });
  });
});
const TOTAL = """ + str(total) + """;
const COLORS = ['#7c3aed','#06b6d4','#f59e0b','#10b981','#f43f5e','#8b5cf6','#0ea5e9','#84cc16'];
const PCOLS  = ['#7c3aed','#06b6d4','#f59e0b','#10b981'];

Chart.defaults.color = '#7a7a9a';
Chart.defaults.font.family = 'DM Sans';

new Chart(document.getElementById('cOcc'), {
  type:'bar',
  data:{
    labels: TALLERES.map(t=>t.name.length>22?t.name.slice(0,20)+'...':t.name),
    datasets:[
      {label:'Cupo',data:TALLERES.map(t=>t.cupo),backgroundColor:'rgba(124,58,237,.25)',borderColor:'#7c3aed',borderWidth:1,borderRadius:4},
      {label:'Asistentes',data:TALLERES.map(t=>t.asist),
       backgroundColor:TALLERES.map(t=>t.asist>t.cupo?'rgba(244,63,94,.8)':'rgba(16,185,129,.8)'),
       borderColor:TALLERES.map(t=>t.asist>t.cupo?'#f43f5e':'#10b981'),borderWidth:1,borderRadius:4}
    ]
  },
  options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:'top',labels:{boxWidth:10,font:{size:11}}}},
    scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{grid:{color:'#2a2a3d'}}}}
});

new Chart(document.getElementById('cDona'), {
  type:'doughnut',
  data:{labels:TALLERES.map(t=>t.name),datasets:[{data:TALLERES.map(t=>t.asist),backgroundColor:COLORS,borderColor:'#1c1c2a',borderWidth:3,hoverOffset:8}]},
  options:{responsive:true,maintainAspectRatio:false,cutout:'62%',
    plugins:{legend:{position:'right',labels:{boxWidth:9,padding:10,font:{size:10}}},
      tooltip:{callbacks:{label:ctx=>ctx.label+': '+ctx.raw+' ('+Math.round(ctx.raw/TOTAL*100)+'%)'}}}}
});

const gSorted = Object.entries(POR_GRADO).sort((a,b)=>(POR_GRADO_UNICAS[b[0]]||0)-(POR_GRADO_UNICAS[a[0]]||0));
new Chart(document.getElementById('cGrados'), {
  type:'bar',
  data:{labels:gSorted.map(g=>g[0].replace(/['"]/g,'')),
    datasets:[{data:gSorted.map(g=>POR_GRADO_UNICAS[g[0]]||0),
      backgroundColor:gSorted.map((_,i)=>COLORS[i%COLORS.length]+'bb'),
      borderColor:gSorted.map((_,i)=>COLORS[i%COLORS.length]),borderWidth:1,borderRadius:4}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:false}},
    scales:{x:{grid:{color:'#2a2a3d'},ticks:{font:{size:11}}},y:{grid:{display:false},ticks:{font:{size:10}}}}}
});

const t1=TALLERES.filter(t=>t.turno==='tarde1').reduce((a,t)=>a+t.asist,0);
const t2=TALLERES.filter(t=>t.turno==='tarde2').reduce((a,t)=>a+t.asist,0);
new Chart(document.getElementById('cTurno'), {
  type:'pie',
  data:{labels:['3:30-5:00 pm (Inicial/Primaria)','5:30-7:00 pm (Secundaria)'],
    datasets:[{data:[t1,t2],backgroundColor:['rgba(6,182,212,.8)','rgba(124,58,237,.8)'],borderColor:['#06b6d4','#7c3aed'],borderWidth:2}]},
  options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:12,font:{size:12}}},
      tooltip:{callbacks:{label:ctx=>ctx.label+': '+ctx.raw+' asistentes'}}}}
});

let stackChart=null;
function buildStack(nivel){
  let grados=Object.entries(POR_GRADO);
  if(nivel==='inicial') grados=grados.filter(g=>g[0].startsWith('Inicial'));
  if(nivel==='primaria') grados=grados.filter(g=>g[0].includes('Primaria'));
  if(nivel==='secundaria') grados=grados.filter(g=>g[0].includes('Secundaria'));
  grados.sort((a,b)=>(POR_GRADO_UNICAS[b[0]]||0)-(POR_GRADO_UNICAS[a[0]]||0));
  const labels=grados.map(g=>g[0].replace(/['"]/g,''));
  const datasets=TALLERES.map((t,i)=>({
    label:t.name,data:grados.map(g=>(POR_GRADO_UNICAS_TALLER[g[0]]&&POR_GRADO_UNICAS_TALLER[g[0]][t.name])||0),
    backgroundColor:COLORS[i%COLORS.length]+'bb',borderColor:COLORS[i%COLORS.length],borderWidth:1,borderRadius:3
  }));
  if(stackChart) stackChart.destroy();
  stackChart=new Chart(document.getElementById('cStack'),{type:'bar',data:{labels,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:9,padding:8,font:{size:10}}}},
      scales:{x:{stacked:true,grid:{display:false},ticks:{font:{size:10}}},y:{stacked:true,grid:{color:'#2a2a3d'}}}}});
}
buildStack('todos');
document.querySelectorAll('#fNivel .fb').forEach(btn=>btn.addEventListener('click',function(){
  document.querySelectorAll('#fNivel .fb').forEach(b=>b.classList.remove('active'));
  this.classList.add('active'); buildStack(this.dataset.n);
}));

const tbT=document.getElementById('tbT');
TALLERES.forEach((t,i)=>{
  const pct=Math.round(t.asist/t.cupo*100);
  const over=t.asist>t.cupo;
  const bc=over?'#f43f5e':(pct>=60?'#f59e0b':'#10b981');
  const row=document.createElement('tr');
  row.innerHTML='<td style="color:#7a7a9a">'+(i+1)+'</td>'+
    '<td style="font-weight:500">'+t.name+'</td>'+
    '<td style="font-size:12px;color:#7a7a9a">'+t.ponente+'</td>'+
    '<td style="font-size:12px;color:#06b6d4">'+t.hora+'</td>'+
    '<td style="font-size:12px">'+t.espacio+'</td>'+
    '<td><span class="badge">'+t.cupo+'</span></td>'+
    '<td><span class="badge'+(over?' badge-red':'')+'">'+t.asist+'</span></td>'+
    '<td><div class="bi"><div class="bb"><div class="bf" style="width:'+Math.min(pct,100)+'%;background:'+bc+'"></div></div>'+
      '<span style="font-size:12px;color:'+bc+';min-width:36px">'+pct+'%</span>'+(over?'<span style="font-size:10px;color:#f43f5e;margin-left:4px">excede</span>':'')+'</div></td>'+
    '<td><span class="badge" style="background:rgba(6,182,212,.12);color:#06b6d4;font-size:10px">'+t.rec+'</span></td>';
  tbT.appendChild(row);
});

const tbG=document.getElementById('tbG');
gSorted.forEach(([grado,info])=>{
  const pct=Math.round(info.total/TOTAL*100);
  const row=document.createElement('tr');
  row.innerHTML='<td>'+grado.replace(/['"]/g,'')+'</td>'+
    '<td><span class="badge">'+(POR_GRADO_UNICAS[grado]||0)+'</span></td>'+
    '<td>'+Object.keys(info.talleres).length+' de 8</td>'+
    '<td><div class="bi"><div class="bb"><div class="bf" style="width:'+Math.min(pct*5,100)+'%;background:linear-gradient(90deg,#7c3aed,#06b6d4)"></div></div>'+
      '<span style="font-size:12px;color:#7a7a9a;min-width:32px">'+pct+'%</span></div></td>';
  tbG.appendChild(row);
});

const ponentes={};
TALLERES.forEach(t=>{
  if(!ponentes[t.ponente]) ponentes[t.ponente]={talleres:[],total:0};
  ponentes[t.ponente].talleres.push(t); ponentes[t.ponente].total+=t.asist;
});
const pgDiv=document.getElementById('pgDiv');
Object.entries(ponentes).forEach(([nombre,info],i)=>{
  const div=document.createElement('div');
  div.className='pc'; div.style.setProperty('--pc',PCOLS[i%PCOLS.length]);
  div.innerHTML='<div class="pn">'+nombre+'</div><div class="pm">'+
    info.talleres.map(t=>'<span>'+t.name+' <span style="color:#06b6d4">'+t.hora+'</span> - '+t.asist+'/'+t.cupo+' asist.</span>').join('')+
    '</div><span class="pt">Total: '+info.total+' participantes</span>';
  pgDiv.appendChild(div);
});

// ── Directorio por salon ─────────────────────────────────────────
const selGrado   = document.getElementById('selGrado');
const selTaller  = document.getElementById('selTaller');
const listaDiv   = document.getElementById('listaInscritos');
const placeholder= document.getElementById('placeholderDir');
const countBadge = document.getElementById('countBadge');

Object.keys(NOMBRES).sort().forEach(grado=>{
  const opt=document.createElement('option');
  opt.value=grado; opt.textContent=grado.replace(/['"]/g,'');
  selGrado.appendChild(opt);
});

const TALLER_COLORS = ['#7c3aed','#06b6d4','#f59e0b','#10b981','#f43f5e','#8b5cf6','#0ea5e9','#84cc16'];
const TALLER_COLOR_MAP = {};
TALLERES.forEach((t,i) => { TALLER_COLOR_MAP[t.name] = TALLER_COLORS[i%TALLER_COLORS.length]; });

function renderInscritos(){
  const grado   = selGrado.value;
  const taller  = selTaller.value;
  const gridDiv = document.getElementById('gridInscritos');

  if(!grado){
    listaDiv.style.display='none';
    placeholder.style.display='block';
    countBadge.style.display='none';
    return;
  }
  listaDiv.style.display='block';
  placeholder.style.display='none';
  gridDiv.innerHTML='';

  let personas = NOMBRES[grado] || [];
  if(taller !== 'todos'){
    personas = personas.filter(p => p.talleres.includes(taller));
  }

  personas.forEach((p, i) => {
    const initials = p.asistente.split(' ').slice(0,2).map(w=>w[0]||'').join('').toUpperCase();
    const color = TALLER_COLORS[i % TALLER_COLORS.length];
    const talleresHtml = p.talleres.map(t => {
      const c = TALLER_COLOR_MAP[t] || '#7c3aed';
      return '<span style="display:inline-block;margin:2px;padding:3px 9px;border-radius:999px;font-size:10px;font-weight:600;background:'+c+'22;color:'+c+';border:1px solid '+c+'44">'+t+'</span>';
    }).join('');

    const card = document.createElement('div');
    card.style.cssText = 'background:#15151f;border:1px solid #2a2a3d;border-radius:16px;padding:18px;position:relative;overflow:hidden;transition:transform .2s,border-color .2s;cursor:default';
    card.onmouseenter = function(){ this.style.transform='translateY(-2px)'; this.style.borderColor='#7c3aed55'; };
    card.onmouseleave = function(){ this.style.transform=''; this.style.borderColor='#2a2a3d'; };

    card.innerHTML =
      '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">' +
        '<div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,'+color+','+color+'88);display:flex;align-items:center;justify-content:center;font-family:Syne,sans-serif;font-weight:800;font-size:14px;color:#fff;flex-shrink:0">'+initials+'</div>' +
        '<div style="min-width:0">' +
          '<div style="font-weight:600;font-size:14px;color:#e8e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+p.asistente+'</div>' +
          (p.estudiante ? '<div style="font-size:11px;color:#7a7a9a;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">Hijo/a: '+p.estudiante+'</div>' : '') +
        '</div>' +
      '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:4px">'+talleresHtml+'</div>' +
      '<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,'+color+',transparent)"></div>';

    gridDiv.appendChild(card);
  });

  countBadge.textContent = personas.length + (personas.length===1?' persona':' personas');
  countBadge.style.display='inline-block';
}

selGrado.addEventListener('change',function(){
  selTaller.innerHTML='<option value="todos">Todos los talleres</option>';
  if(this.value && NOMBRES[this.value]){
    const tallsEnGrado=new Set();
    NOMBRES[this.value].forEach(p=>p.talleres.forEach(t=>tallsEnGrado.add(t)));
    Array.from(tallsEnGrado).sort().forEach(t=>{
      const opt=document.createElement('option');
      opt.value=t; opt.textContent=t; selTaller.appendChild(opt);
    });
  }
  renderInscritos();
});
selTaller.addEventListener('change',renderInscritos);
</script>
</body>
</html>"""
    return html

if __name__ == "__main__":
    print("\nLeyendo datos desde Google Sheets...\n")
    dfs = {}
    for nombre, url in SHEETS.items():
        dfs[nombre] = leer_sheet(nombre, url)

    print("\nBuscando duplicados...")
    duplicados = detectar_duplicados(dfs)
    if duplicados:
        print(f"  ALERTA: duplicados en {len(duplicados)} taller(es)")
    else:
        print("  Sin duplicados detectados")

    print("\nProcesando datos...")
    talleres_data, por_grado, nombres, total, cupo_total, personas_unicas, por_grado_unicas = procesar(dfs)

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    html  = generar_html(talleres_data, por_grado, nombres, total, cupo_total, personas_unicas, por_grado_unicas, duplicados, fecha)

    output = "dashboard_escuela_padres.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nDashboard generado: {output}")
    print(f"Total registros: {total} | Ocupacion global: {round(total/cupo_total*100)}%")
    print("\nAbriendo en el navegador...")
    webbrowser.open(f"file:///{os.path.abspath(output)}")

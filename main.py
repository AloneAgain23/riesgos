from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
from datetime import datetime, timedelta
import threading

app = FastAPI(title="CEPLAN Mapa de Riesgos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
SESSION_TTL_HOURS = 24

def keep_alive():
    import time, urllib.request
    while True:
        try:
            urllib.request.urlopen("https://riesgos-v6uu.onrender.com/")
        except:
            pass
        time.sleep(840)

threading.Thread(target=keep_alive, daemon=True).start()

def cleanup_sessions():
    now = datetime.utcnow()
    expired = [k for k, v in sessions.items() if v["expires"] < now]
    for k in expired:
        del sessions[k]

@app.get("/")
def root():
    return {"status": "ok", "service": "CEPLAN Mapa de Riesgos"}

@app.post("/generateRiesgos")
async def generate_riesgos(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body no es JSON valido")

    titulo = body.get("titulo", "Mapa de Riesgos Globales y Nacionales")
    periodo = body.get("periodo", "2026-2036")
    riesgos_json = body.get("riesgos_json")

    if not riesgos_json:
        raise HTTPException(status_code=400, detail="Falta riesgos_json")

    if isinstance(riesgos_json, str):
        try:
            riesgos_json = json.loads(riesgos_json)
        except Exception:
            raise HTTPException(status_code=400, detail="riesgos_json no es JSON valido")

    cleanup_sessions()
    session_id = str(uuid.uuid4()).replace("-", "")[:16]
    sessions[session_id] = {
        "titulo": titulo,
        "periodo": periodo,
        "data": riesgos_json,
        "created_at": datetime.utcnow().strftime("%d/%m/%Y"),
        "expires": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    }

    BASE_URL = "https://riesgos-v6uu.onrender.com"
    view_url = f"{BASE_URL}/view/{session_id}"
    return JSONResponse({"success": True, "view_url": view_url, "message": f"Mapa listo: {view_url}"})

@app.get("/view/{session_id}", response_class=HTMLResponse)
def view_riesgos(session_id: str):
    cleanup_sessions()
    if session_id not in sessions:
        return HTMLResponse("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>No encontrado</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5;}}
.box{{text-align:center;padding:3rem;background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.08);max-width:420px;}}
h1{{color:#C8102E;}}p{{color:#666;font-size:.9rem;}}</style></head>
<body><div class="box"><h1>Sesion expirada</h1><p>Genera un nuevo reporte desde ChatGPT.</p></div></body></html>""", status_code=404)

    s = sessions[session_id]
    data = s["data"]
    data_json = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{s['titulo']} — CEPLAN</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600;700&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
  <style>
    :root{{
      --rojo:#C8102E;--rojo-dark:#9B0B22;--gris:#F4F5F6;--gris2:#E8EAEC;
      --borde:#DDE1E6;--texto:#111827;--muted:#6B7280;--blanco:#FFFFFF;
      --social:#E84855;--ambiental:#3BB273;--economico:#F18F01;
      --politico:#A23B72;--tecnologico:#2E86AB;
    }}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:var(--gris);color:var(--texto);font-family:'Source Sans 3',sans-serif;font-size:15px;line-height:1.6;}}
    header{{background:var(--rojo);box-shadow:0 2px 16px rgba(200,16,46,.35);position:sticky;top:0;z-index:200;}}
    .hi{{max-width:1400px;margin:0 auto;padding:.85rem 2rem;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;}}
    .hb{{font-weight:700;font-size:.95rem;text-transform:uppercase;letter-spacing:.06em;color:#fff;}}
    .hb span{{display:block;font-size:.6rem;font-weight:400;opacity:.75;letter-spacing:.12em;}}
    .hbadge{{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);border-radius:4px;padding:.28rem .75rem;font-size:.7rem;font-weight:600;color:#fff;}}
    .hero{{background:var(--blanco);border-bottom:4px solid var(--rojo);padding:1.5rem 2rem;}}
    .hero-inner{{max-width:1400px;margin:0 auto;display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;flex-wrap:wrap;}}
    .eyebrow{{font-size:.68rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--rojo);margin-bottom:.3rem;}}
    .hero-title{{font-family:'Playfair Display',serif;font-size:clamp(1.4rem,3vw,2rem);font-weight:700;color:var(--texto);}}
    .hero-sub{{font-size:.82rem;color:var(--muted);margin-top:.3rem;}}
    .view-btns{{display:flex;gap:.5rem;flex-wrap:wrap;}}
    .vbtn{{font-size:.72rem;font-weight:700;padding:.4rem 1rem;border-radius:4px;border:1.5px solid var(--borde);background:var(--blanco);color:var(--muted);cursor:pointer;text-transform:uppercase;letter-spacing:.06em;transition:all .14s;}}
    .vbtn:hover{{background:var(--rojo);border-color:var(--rojo);color:#fff;}}
    .main{{max-width:1400px;margin:1.5rem auto;padding:0 2rem 3rem;}}
    .stats-bar{{display:flex;flex-wrap:wrap;gap:.8rem;margin-bottom:1.5rem;}}
    .stat{{background:var(--blanco);border:1px solid var(--borde);border-top:3px solid var(--rojo);border-radius:6px;padding:.8rem 1.2rem;flex:1;min-width:100px;}}
    .stat-num{{font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:700;color:var(--rojo);line-height:1;}}
    .stat-label{{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-top:.15rem;}}
    .filters{{background:var(--blanco);border:1px solid var(--borde);border-radius:8px;padding:1rem 1.2rem;margin-bottom:1.5rem;display:flex;flex-wrap:wrap;gap:.8rem;align-items:center;}}
    .filter-group{{display:flex;gap:.35rem;flex-wrap:wrap;align-items:center;}}
    .filter-label{{font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);}}
    .fbtn{{font-size:.68rem;font-weight:700;padding:.25rem .7rem;border-radius:4px;border:1.5px solid var(--borde);background:var(--blanco);color:var(--muted);cursor:pointer;transition:all .12s;}}
    .fbtn:hover{{border-color:var(--rojo);color:var(--rojo);}}
    .fbtn.active{{color:#fff;}}
    .fbtn.all.active{{background:var(--rojo);border-color:var(--rojo);}}
    .fbtn.social.active{{background:var(--social);border-color:var(--social);}}
    .fbtn.ambiental.active{{background:var(--ambiental);border-color:var(--ambiental);}}
    .fbtn.economico.active{{background:var(--economico);border-color:var(--economico);color:#111;}}
    .fbtn.politico.active{{background:var(--politico);border-color:var(--politico);}}
    .fbtn.tecnologico.active{{background:var(--tecnologico);border-color:var(--tecnologico);}}
    .chart-card{{background:var(--blanco);border:1px solid var(--borde);border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;}}
    .chart-title{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--texto);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem;}}
    .chart-title span{{color:var(--rojo);}}
    .q-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;}}
    .legend{{display:flex;flex-wrap:wrap;gap:.8rem;margin-top:1rem;padding-top:1rem;border-top:1px solid var(--gris2);}}
    .legend-item{{display:flex;align-items:center;gap:.4rem;font-size:.78rem;color:var(--texto);}}
    .legend-dot{{width:10px;height:10px;border-radius:50%;}}

    /* MODAL */
    .modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:300;align-items:flex-start;justify-content:center;padding:2rem 1rem;overflow-y:auto;}}
    .modal-overlay.open{{display:flex;}}
    .modal{{background:var(--blanco);border-radius:12px;width:100%;max-width:920px;box-shadow:0 24px 80px rgba(0,0,0,.3);animation:popIn .2s ease;margin:auto;}}
    @keyframes popIn{{from{{opacity:0;transform:translateY(-12px);}}to{{opacity:1;transform:translateY(0);}}}}
    .modal-header{{padding:1.2rem 1.5rem;border-bottom:1px solid var(--borde);display:flex;align-items:center;justify-content:space-between;background:var(--rojo);border-radius:12px 12px 0 0;}}
    .modal-header h2{{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#fff;}}
    .modal-close{{background:none;border:none;font-size:1.3rem;cursor:pointer;color:rgba(255,255,255,.8);line-height:1;}}
    .modal-close:hover{{color:#fff;}}
    .modal-body{{padding:1.5rem;max-height:75vh;overflow-y:auto;}}
    .rank-table{{width:100%;border-collapse:collapse;font-size:.85rem;}}
    .rank-table th{{background:var(--gris);padding:.6rem .8rem;text-align:left;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);border-bottom:2px solid var(--borde);}}
    .rank-table td{{padding:.55rem .8rem;border-bottom:1px solid var(--gris2);vertical-align:middle;}}
    .rank-table tr:hover td{{background:var(--gris);}}
    .rank-num{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--rojo);}}
    .intensity-bar{{height:6px;background:var(--borde);border-radius:3px;overflow:hidden;width:80px;display:inline-block;}}
    .intensity-fill{{height:100%;border-radius:3px;}}
    .cat-badge{{font-size:.6rem;font-weight:700;padding:.15rem .45rem;border-radius:3px;}}
    .timeline-row{{display:flex;align-items:center;gap:.8rem;padding:.6rem 0;border-bottom:1px solid var(--gris2);}}
    .timeline-row:last-child{{border-bottom:none;}}
    .tl-name{{font-size:.82rem;color:var(--texto);flex:0 0 240px;line-height:1.3;}}
    .tl-bar-wrap{{flex:1;position:relative;height:20px;background:var(--gris2);border-radius:4px;overflow:hidden;}}
    .tl-bar{{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:.5rem;font-size:.65rem;font-weight:700;color:#fff;white-space:nowrap;transition:width .4s ease;}}
    .tl-year{{font-size:.72rem;font-weight:700;color:var(--muted);flex:0 0 46px;text-align:right;}}

    /* RISK DETAIL MODAL */
    .detail-grid{{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin:1rem 0;}}
    .detail-metric{{background:var(--gris);border-radius:6px;padding:.7rem .9rem;}}
    .detail-metric-label{{font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.2rem;}}
    .detail-metric-value{{font-size:.95rem;font-weight:700;}}
    .detail-bar{{height:7px;background:var(--borde);border-radius:3px;margin-top:.35rem;overflow:hidden;}}
    .detail-bar-fill{{height:100%;border-radius:3px;}}
    .detail-desc{{font-size:.88rem;line-height:1.75;color:var(--texto);margin:.8rem 0;}}
    .detail-section-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:.8rem 0 .4rem;}}
    .interrel-chips{{display:flex;flex-wrap:wrap;gap:.35rem;}}
    .interrel-chip{{font-size:.7rem;font-weight:700;padding:.2rem .55rem;border-radius:3px;background:var(--gris2);color:var(--texto);border:1px solid var(--borde);cursor:pointer;}}
    .interrel-chip:hover{{background:var(--rojo);color:#fff;border-color:var(--rojo);}}
    .fuente-link{{font-size:.78rem;color:var(--rojo);text-decoration:none;word-break:break-all;}}
    .fuente-link:hover{{text-decoration:underline;}}
    .mitigation-box{{background:var(--gris);border-left:3px solid var(--rojo);border-radius:0 6px 6px 0;padding:.7rem .9rem;font-size:.83rem;color:var(--texto);line-height:1.6;}}

    #network-svg{{width:100%;}}
    footer{{background:#9B0B22;color:rgba(255,255,255,.7);padding:1.1rem 2rem;text-align:center;font-size:.68rem;letter-spacing:.06em;}}
    @media(max-width:640px){{.main{{padding:0 1rem 2rem;}}.hero{{padding:1rem;}}.hi{{padding:.8rem 1rem;}}.tl-name{{flex:0 0 140px;font-size:.75rem;}}.detail-grid{{grid-template-columns:1fr;}}}}
  </style>
</head>
<body>
<header>
  <div class="hi">
    <div class="hb">Mapa de Riesgos Globales y Nacionales<span>CEPLAN — Centro Nacional de Planeamiento Estrategico</span></div>
    <div class="hbadge">{s['periodo']}</div>
  </div>
</header>
<div class="hero">
  <div class="hero-inner">
    <div>
      <div class="eyebrow">▸ Identificacion y Priorizacion de Riesgos</div>
      <h1 class="hero-title">{s['titulo']}</h1>
      <p class="hero-sub">Generado el {s['created_at']} · Sesion valida 24h</p>
    </div>
    <div class="view-btns">
      <button class="vbtn" onclick="openModal('rankingModal')">📊 Ranking</button>
      <button class="vbtn" onclick="openModal('networkModal')">🔗 Interrelaciones</button>
      <button class="vbtn" onclick="openModal('timelineModal')">⏱ Aproximacion</button>
    </div>
  </div>
</div>

<div class="main">
  <div class="stats-bar" id="statsBar"></div>
  <div class="filters">
    <div class="filter-group">
      <span class="filter-label">Categoria:</span>
      <button class="fbtn all active" data-cat="all">Todas</button>
      <button class="fbtn social" data-cat="Social">Social</button>
      <button class="fbtn ambiental" data-cat="Ambiental">Ambiental</button>
      <button class="fbtn economico" data-cat="Economico">Economico</button>
      <button class="fbtn politico" data-cat="Politico">Politico</button>
      <button class="fbtn tecnologico" data-cat="Tecnologico">Tecnologico</button>
    </div>
    <div class="filter-group">
      <span class="filter-label">Cuadrante:</span>
      <button class="fbtn all active" data-quad="all">Todos</button>
      <button class="fbtn" data-quad="I" style="border-color:#C8102E;color:#C8102E;">I — Critico</button>
      <button class="fbtn" data-quad="II">II — Alto impacto</button>
      <button class="fbtn" data-quad="III">III — Bajo</button>
      <button class="fbtn" data-quad="IV">IV — Alta prob.</button>
    </div>
  </div>
  <div class="chart-card">
    <div class="chart-title"><span>◈</span> Mapa de Riesgos — Probabilidad vs Impacto <span style="font-size:.75rem;font-weight:400;color:var(--muted);margin-left:.5rem;">Haz click en cualquier punto para ver el detalle completo</span></div>
    <div id="scatter-container"></div>
    <div class="legend" id="legend"></div>
  </div>
</div>

<!-- DETAIL MODAL -->
<div class="modal-overlay" id="detailModal">
  <div class="modal" style="max-width:680px;">
    <div class="modal-header" id="detailHeader">
      <h2 id="detailTitle">Detalle del Riesgo</h2>
      <button class="modal-close" onclick="closeModal('detailModal')">✕</button>
    </div>
    <div class="modal-body" id="detailBody"></div>
  </div>
</div>

<!-- RANKING MODAL -->
<div class="modal-overlay" id="rankingModal">
  <div class="modal">
    <div class="modal-header"><h2>📊 Ranking de Riesgos por Intensidad</h2><button class="modal-close" onclick="closeModal('rankingModal')">✕</button></div>
    <div class="modal-body" id="rankingBody"></div>
  </div>
</div>

<!-- NETWORK MODAL -->
<div class="modal-overlay" id="networkModal">
  <div class="modal" style="max-width:1000px;">
    <div class="modal-header"><h2>🔗 Mapa de Interrelaciones</h2><button class="modal-close" onclick="closeModal('networkModal')">✕</button></div>
    <div class="modal-body">
      <p style="font-size:.82rem;color:var(--muted);margin-bottom:1rem;">Tamaño del nodo = centralidad. Haz click en cualquier nodo para ver el detalle.</p>
      <svg id="network-svg" style="min-height:520px;"></svg>
    </div>
  </div>
</div>

<!-- TIMELINE MODAL -->
<div class="modal-overlay" id="timelineModal">
  <div class="modal">
    <div class="modal-header"><h2>⏱ Nivel de Aproximacion — Riesgos Priorizados</h2><button class="modal-close" onclick="closeModal('timelineModal')">✕</button></div>
    <div class="modal-body" id="timelineBody"></div>
  </div>
</div>

<footer>CEPLAN — Centro Nacional de Planeamiento Estrategico &nbsp;|&nbsp; {s['periodo']} &nbsp;|&nbsp; {s['created_at']}</footer>

<script>
const RAW = {data_json};
const riesgos = RAW.riesgos || [];

const CAT_COLOR = {{
  'Social':'#E84855','Ambiental':'#3BB273','Economico':'#F18F01',
  'Politico':'#A23B72','Tecnologico':'#2E86AB'
}};

// STATS
(function(){{
  const bar = document.getElementById('statsBar');
  const cats = {{}};
  riesgos.forEach(r => {{ cats[r.categoria]=(cats[r.categoria]||0)+1; }});
  const criticos = riesgos.filter(r => {{
    const allP=riesgos.map(x=>x.probabilidad), allI=riesgos.map(x=>x.impacto);
    const midP=(Math.min(...allP)+Math.max(...allP))/2, midI=(Math.min(...allI)+Math.max(...allI))/2;
    return r.probabilidad>=midP && r.impacto>=midI;
  }}).length;
  [[riesgos.length,'Total Riesgos'],[criticos,'Criticos (Q-I)'],
   ...Object.entries(cats).map(([k,v])=>[v,k])].forEach(([n,l])=>{{
    const d=document.createElement('div'); d.className='stat';
    const color=CAT_COLOR[l]||'var(--rojo)';
    d.innerHTML=`<div class="stat-num" style="color:${{color}}">${{n}}</div><div class="stat-label">${{l}}</div>`;
    bar.appendChild(d);
  }});
}})();

// LEGEND
(function(){{
  const leg=document.getElementById('legend');
  Object.entries(CAT_COLOR).forEach(([cat,color])=>{{
    const item=document.createElement('div'); item.className='legend-item';
    item.innerHTML=`<div class="legend-dot" style="background:${{color}}"></div>${{cat}}`;
    leg.appendChild(item);
  }});
}})();

// DETAIL MODAL
function showDetail(d) {{
  const color = CAT_COLOR[d.categoria]||'#999';
  const intensity = ((d.probabilidad||0)*(d.impacto||0)).toFixed(2);
  document.getElementById('detailTitle').textContent = (d.codigo||'') + ' — ' + (d.nombre||'');
  document.getElementById('detailHeader').style.borderBottom = `4px solid ${{color}}`;

  const rels = (d.interrelaciones||[]).map(r=>
    `<span class="interrel-chip" onclick="showDetailByCode('${{r}}')">${{r}}</span>`).join('');

  const fuenteHtml = d.fuente_url
    ? `<a class="fuente-link" href="${{d.fuente_url}}" target="_blank" rel="noopener">🔗 ${{d.fuente_nombre||d.fuente_url}}</a>`
    : (d.fuente_nombre ? `<span style="font-size:.82rem;color:var(--muted)">${{d.fuente_nombre}}</span>` : '');

  document.getElementById('detailBody').innerHTML = `
    <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.5rem;">
      <span class="cat-badge" style="background:${{color}}22;color:${{color}};font-size:.72rem;padding:.25rem .7rem;">${{d.categoria||''}}</span>
      <span class="cat-badge" style="background:var(--gris2);color:var(--muted);font-size:.72rem;padding:.25rem .7rem;">${{d.codigo||''}}</span>
    </div>
    <p class="detail-desc">${{d.descripcion||'Sin descripcion disponible.'}}</p>
    <div class="detail-grid">
      <div class="detail-metric">
        <div class="detail-metric-label">Probabilidad de ocurrencia</div>
        <div class="detail-metric-value" style="color:${{color}}">${{(d.probabilidad||0).toFixed(2)}} / 5.0</div>
        <div class="detail-bar"><div class="detail-bar-fill" style="width:${{(d.probabilidad/5*100).toFixed(0)}}%;background:${{color}}"></div></div>
      </div>
      <div class="detail-metric">
        <div class="detail-metric-label">Magnitud de impacto</div>
        <div class="detail-metric-value" style="color:${{color}}">${{(d.impacto||0).toFixed(2)}} / 5.0</div>
        <div class="detail-bar"><div class="detail-bar-fill" style="width:${{(d.impacto/5*100).toFixed(0)}}%;background:${{color}}"></div></div>
      </div>
      <div class="detail-metric">
        <div class="detail-metric-label">Intensidad (prob × impacto)</div>
        <div class="detail-metric-value" style="color:${{color}}">${{intensity}}</div>
      </div>
      <div class="detail-metric">
        <div class="detail-metric-label">Año de aproximacion estimado</div>
        <div class="detail-metric-value" style="color:${{color}}">${{d.anio_aproximacion||'—'}}</div>
      </div>
    </div>
    ${{d.medidas_mitigacion ? `
    <div class="detail-section-label">▸ Medidas de mitigacion sugeridas</div>
    <div class="mitigation-box">${{d.medidas_mitigacion}}</div>` : ''}}
    ${{rels ? `<div class="detail-section-label">▸ Riesgos interrelacionados (click para ver)</div>
    <div class="interrel-chips">${{rels}}</div>` : ''}}
    ${{fuenteHtml ? `<div class="detail-section-label">▸ Fuente de referencia</div>${{fuenteHtml}}` : ''}}
  `;
  openModal('detailModal');
}}

function showDetailByCode(code) {{
  const r = riesgos.find(x => x.codigo === code);
  if (r) {{ closeModal('detailModal'); setTimeout(()=>showDetail(r), 200); }}
}}

// SCATTER PLOT
let activeCAT='all', activeQUAD='all';

function getQuadrant(prob, imp, midP, midI) {{
  if (prob>=midP && imp>=midI) return 'I';
  if (prob<midP && imp>=midI) return 'II';
  if (prob<midP && imp<midI) return 'III';
  return 'IV';
}}

function drawScatter(data) {{
  const container = document.getElementById('scatter-container');
  container.innerHTML = '';
  if (!data.length) {{ container.innerHTML='<p style="text-align:center;padding:2rem;color:var(--muted)">No hay riesgos para mostrar con los filtros actuales.</p>'; return; }}

  const margin = {{top:30, right:50, bottom:65, left:65}};
  const W = Math.max(600, container.clientWidth || 900);
  const H = Math.max(480, W * 0.58);
  const iW = W - margin.left - margin.right;
  const iH = H - margin.top - margin.bottom;

  const allP = riesgos.map(d=>d.probabilidad);
  const allI = riesgos.map(d=>d.impacto);
  const minP = Math.min(...allP)-0.2, maxP = Math.max(...allP)+0.2;
  const minI = Math.min(...allI)-0.2, maxI = Math.max(...allI)+0.2;
  const midP = (minP+maxP)/2, midI = (minI+maxI)/2;

  const xSc = d3.scaleLinear().domain([minP,maxP]).range([0,iW]);
  const ySc = d3.scaleLinear().domain([minI,maxI]).range([iH,0]);

  const svgEl = d3.select(container).append('svg').attr('width',W).attr('height',H);
  const g = svgEl.append('g').attr('transform',`translate(${{margin.left}},${{margin.top}})`);

  // Quadrant backgrounds
  [{{'x':xSc(midP),'y':0,'w':iW-xSc(midP),'h':ySc(midI),'label':'I — CRITICO','c':'rgba(200,16,46,0.07)'}},
   {{'x':0,'y':0,'w':xSc(midP),'h':ySc(midI),'label':'II — ALTO IMPACTO','c':'rgba(100,100,200,0.04)'}},
   {{'x':0,'y':ySc(midI),'w':xSc(midP),'h':iH-ySc(midI),'label':'III — BAJO','c':'rgba(150,150,150,0.04)'}},
   {{'x':xSc(midP),'y':ySc(midI),'w':iW-xSc(midP),'h':iH-ySc(midI),'label':'IV — ALTA PROB.','c':'rgba(241,143,1,0.06)'}}
  ].forEach(q=>{{
    g.append('rect').attr('x',q.x).attr('y',q.y).attr('width',q.w).attr('height',q.h).attr('fill',q.c);
    g.append('text').attr('x',q.x+q.w/2).attr('y',q.y+q.h/2)
      .attr('text-anchor','middle').attr('dominant-baseline','middle')
      .attr('class','q-label').attr('fill','#bbb').attr('font-size','11').attr('font-family','Source Sans 3,sans-serif')
      .attr('font-weight','700').attr('letter-spacing','0.08em').text(q.label);
  }});

  // Grid lines
  g.append('line').attr('x1',xSc(midP)).attr('x2',xSc(midP)).attr('y1',0).attr('y2',iH)
    .attr('stroke','rgba(200,16,46,0.3)').attr('stroke-width',1.5).attr('stroke-dasharray','6,4');
  g.append('line').attr('x1',0).attr('x2',iW).attr('y1',ySc(midI)).attr('y2',ySc(midI))
    .attr('stroke','rgba(200,16,46,0.3)').attr('stroke-width',1.5).attr('stroke-dasharray','6,4');

  // Axes
  const xAxis = g.append('g').attr('transform',`translate(0,${{iH}})`).call(d3.axisBottom(xSc).ticks(7).tickFormat(d=>d.toFixed(1)));
  xAxis.selectAll('text').style('font-size','11px').style('font-family','Source Sans 3,sans-serif');
  const yAxis = g.append('g').call(d3.axisLeft(ySc).ticks(7).tickFormat(d=>d.toFixed(1)));
  yAxis.selectAll('text').style('font-size','11px').style('font-family','Source Sans 3,sans-serif');

  g.append('text').attr('x',iW/2).attr('y',iH+50).attr('text-anchor','middle')
    .style('font-size','12px').style('font-weight','700').style('fill','var(--muted)').text('Probabilidad de Ocurrencia');
  g.append('text').attr('transform','rotate(-90)').attr('x',-iH/2).attr('y',-50)
    .attr('text-anchor','middle').style('font-size','12px').style('font-weight','700').style('fill','var(--muted)').text('Magnitud de Impacto');

  // Points
  const pts = g.selectAll('.pt').data(data).enter().append('g').attr('class','pt')
    .attr('transform',d=>`translate(${{xSc(d.probabilidad)}},${{ySc(d.impacto)}})`)
    .style('cursor','pointer');

  pts.append('circle').attr('r',8)
    .attr('fill',d=>CAT_COLOR[d.categoria]||'#999')
    .attr('stroke','#fff').attr('stroke-width',2).attr('opacity',0.85)
    .on('mouseover',function(){{ d3.select(this).attr('r',11).attr('opacity',1); }})
    .on('mouseout',function(){{ d3.select(this).attr('r',8).attr('opacity',0.85); }})
    .on('click',(event,d)=>{{ event.stopPropagation(); showDetail(d); }});

  pts.append('text').attr('dy',-13).attr('text-anchor','middle')
    .style('font-size','9px').style('font-weight','700').style('fill','#444')
    .style('pointer-events','none').text(d=>d.codigo||'');

  // Full name label on hover via title
  pts.append('title').text(d=>`${{d.codigo}} — ${{d.nombre}}\nProb: ${{d.probabilidad}} | Impacto: ${{d.impacto}}`);
}}

function filterAndDraw() {{
  let filtered = riesgos;
  if (activeCAT!=='all') filtered=filtered.filter(r=>r.categoria===activeCAT);
  if (activeQUAD!=='all') {{
    const allP=riesgos.map(x=>x.probabilidad), allI=riesgos.map(x=>x.impacto);
    const midP=(Math.min(...allP)+Math.max(...allP))/2, midI=(Math.min(...allI)+Math.max(...allI))/2;
    filtered=filtered.filter(r=>getQuadrant(r.probabilidad,r.impacto,midP,midI)===activeQUAD);
  }}
  drawScatter(filtered);
}}

document.querySelectorAll('[data-cat]').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('[data-cat]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active'); activeCAT=btn.dataset.cat; filterAndDraw();
  }});
}});
document.querySelectorAll('[data-quad]').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('[data-quad]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active'); activeQUAD=btn.dataset.quad; filterAndDraw();
  }});
}});

// MODALS
function openModal(id){{
  document.getElementById(id).classList.add('open');
  if(id==='rankingModal') buildRanking();
  if(id==='networkModal') setTimeout(buildNetwork,100);
  if(id==='timelineModal') buildTimeline();
}}
function closeModal(id){{ document.getElementById(id).classList.remove('open'); }}
document.querySelectorAll('.modal-overlay').forEach(el=>{{
  el.addEventListener('click',e=>{{ if(e.target===el) el.classList.remove('open'); }});
}});

// RANKING
function buildRanking(){{
  const sorted=[...riesgos].sort((a,b)=>(b.probabilidad*b.impacto)-(a.probabilidad*a.impacto));
  const maxInt=sorted[0].probabilidad*sorted[0].impacto;
  const rows=sorted.map((r,i)=>{{
    const int=(r.probabilidad*r.impacto).toFixed(2);
    const pct=((r.probabilidad*r.impacto)/maxInt*100).toFixed(0);
    const color=CAT_COLOR[r.categoria]||'#999';
    return `<tr style="cursor:pointer" onclick="closeModal('rankingModal');setTimeout(()=>showDetail(${{JSON.stringify(r).replace(/"/g,'&quot;')}}),200)">
      <td><span class="rank-num">${{i+1}}</span></td>
      <td><span class="cat-badge" style="background:${{color}}22;color:${{color}}">${{r.codigo||''}}</span></td>
      <td style="max-width:260px;font-size:.82rem">${{r.nombre}}</td>
      <td><span class="cat-badge" style="background:${{color}}22;color:${{color}}">${{r.categoria}}</span></td>
      <td>${{(r.probabilidad).toFixed(2)}}</td>
      <td>${{(r.impacto).toFixed(2)}}</td>
      <td>
        <div style="display:flex;align-items:center;gap:.4rem">
          <div class="intensity-bar"><div class="intensity-fill" style="width:${{pct}}%;background:${{color}}"></div></div>
          <span style="font-size:.75rem;font-weight:700;color:${{color}}">${{int}}</span>
        </div>
      </td>
    </tr>`;
  }}).join('');
  document.getElementById('rankingBody').innerHTML=`
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem;">Haz click en cualquier fila para ver el detalle completo del riesgo.</p>
    <table class="rank-table">
      <thead><tr><th>#</th><th>Cod.</th><th>Riesgo</th><th>Categoria</th><th>Prob.</th><th>Impacto</th><th>Intensidad</th></tr></thead>
      <tbody>${{rows}}</tbody>
    </table>`;
}}

// NETWORK
function buildNetwork(){{
  const svgEl=document.getElementById('network-svg');
  const W=svgEl.parentElement.clientWidth||800;
  const H=520;
  svgEl.setAttribute('width',W); svgEl.setAttribute('height',H);
  const svg=d3.select('#network-svg'); svg.selectAll('*').remove();

  const nodes=riesgos.map(r=>({...r,
    id:r.codigo, connections:(r.interrelaciones||[]).length,
    intensity:r.probabilidad*r.impacto
  }));
  const links=[];
  riesgos.forEach(r=>{{
    (r.interrelaciones||[]).forEach(rel=>{{
      if(riesgos.find(x=>x.codigo===rel))
        links.push({{source:r.codigo,target:rel}});
    }});
  }});

  const maxInt=Math.max(...nodes.map(n=>n.intensity));
  const rScale=d3.scaleSqrt().domain([0,maxInt]).range([7,24]);

  const sim=d3.forceSimulation(nodes)
    .force('link',d3.forceLink(links).id(d=>d.id).distance(90).strength(0.25))
    .force('charge',d3.forceManyBody().strength(-220))
    .force('center',d3.forceCenter(W/2,H/2))
    .force('collision',d3.forceCollide().radius(d=>rScale(d.intensity)+6));

  const link=svg.append('g').selectAll('line').data(links).enter().append('line')
    .attr('stroke','rgba(200,16,46,0.18)').attr('stroke-width',1.8);

  const nodeG=svg.append('g').selectAll('g').data(nodes).enter().append('g')
    .style('cursor','pointer')
    .call(d3.drag()
      .on('start',(e,d)=>{{if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;}})
      .on('drag',(e,d)=>{{d.fx=e.x;d.fy=e.y;}})
      .on('end',(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}}))
    .on('click',(event,d)=>{{event.stopPropagation();showDetail(d);}});

  nodeG.append('circle').attr('r',d=>rScale(d.intensity))
    .attr('fill',d=>CAT_COLOR[d.categoria]||'#999').attr('opacity',0.82)
    .attr('stroke','#fff').attr('stroke-width',2)
    .on('mouseover',function(){{d3.select(this).attr('opacity',1).attr('stroke-width',3);}})
    .on('mouseout',function(){{d3.select(this).attr('opacity',0.82).attr('stroke-width',2);}});

  nodeG.append('text').attr('dy','0.35em').attr('text-anchor','middle')
    .style('font-size','8px').style('font-weight','700').style('fill','#fff')
    .style('pointer-events','none').text(d=>d.id);

  nodeG.append('title').text(d=>`${{d.codigo}} — ${{d.nombre}}`);

  sim.on('tick',()=>{{
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y)
        .attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    nodeG.attr('transform',d=>`translate(${{Math.max(28,Math.min(W-28,d.x))}},${{Math.max(28,Math.min(H-28,d.y))}})`);
  }});
}}

// TIMELINE
function buildTimeline(){{
  const sorted=[...riesgos].filter(r=>r.anio_aproximacion)
    .sort((a,b)=>a.anio_aproximacion-b.anio_aproximacion);
  if(!sorted.length){{document.getElementById('timelineBody').innerHTML='<p style="color:var(--muted)">No hay datos de aproximacion disponibles.</p>';return;}}
  const minY=sorted[0].anio_aproximacion, maxY=sorted[sorted.length-1].anio_aproximacion;
  const rows=sorted.map(r=>{{
    const color=CAT_COLOR[r.categoria]||'#999';
    const pct=maxY===minY?50:Math.round((r.anio_aproximacion-minY)/(maxY-minY)*82+8);
    return `<div class="timeline-row" style="cursor:pointer" onclick="closeModal('timelineModal');setTimeout(()=>showDetail(${{JSON.stringify(r).replace(/"/g,'&quot;')}}),200)">
      <div class="tl-name"><span style="font-size:.6rem;font-weight:700;color:${{color}};margin-right:.3rem">${{r.codigo||''}}</span>${{r.nombre}}</div>
      <div class="tl-bar-wrap"><div class="tl-bar" style="width:${{pct}}%;background:${{color}}">${{r.anio_aproximacion}}</div></div>
      <div class="tl-year">${{r.anio_aproximacion}}</div>
    </div>`;
  }}).join('');
  document.getElementById('timelineBody').innerHTML=`
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem;">Ordenado por año estimado. Haz click en cualquier fila para ver el detalle.</p>
    <div>${{rows}}</div>`;
}}

// INIT
filterAndDraw();
</script>
</body>
</html>"""
    return HTMLResponse(html)

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
            urllib.request.urlopen("https://TU-RIESGOS-APP.onrender.com/")
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

    BASE_URL = "https://TU-RIESGOS-APP.onrender.com"
    view_url = f"{BASE_URL}/view/{session_id}"
    return JSONResponse({"success": True, "view_url": view_url, "message": f"Mapa listo: {view_url}"})

@app.get("/view/{session_id}", response_class=HTMLResponse)
def view_riesgos(session_id: str):
    cleanup_sessions()
    if session_id not in sessions:
        return HTMLResponse("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>No encontrado</title>
<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f5f5f5;}
.box{text-align:center;padding:3rem;background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.08);max-width:420px;}
h1{color:#C8102E;}p{color:#666;font-size:.9rem;}</style></head>
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
    .vbtn:hover,.vbtn.active{{background:var(--rojo);border-color:var(--rojo);color:#fff;}}

    .main{{max-width:1400px;margin:1.5rem auto;padding:0 2rem 3rem;}}

    /* STATS */
    .stats-bar{{display:flex;flex-wrap:wrap;gap:.8rem;margin-bottom:1.5rem;}}
    .stat{{background:var(--blanco);border:1px solid var(--borde);border-top:3px solid var(--rojo);border-radius:6px;padding:.8rem 1.2rem;flex:1;min-width:100px;}}
    .stat-num{{font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:700;color:var(--rojo);line-height:1;}}
    .stat-label{{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-top:.15rem;}}

    /* FILTERS */
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

    /* CHART CONTAINER */
    .chart-card{{background:var(--blanco);border:1px solid var(--borde);border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;}}
    .chart-title{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--texto);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem;}}
    .chart-title span{{color:var(--rojo);}}
    #scatter-svg{{width:100%;overflow:visible;}}

    /* QUADRANT LABELS */
    .q-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;opacity:.45;}}

    /* LEGEND */
    .legend{{display:flex;flex-wrap:wrap;gap:.8rem;margin-top:1rem;padding-top:1rem;border-top:1px solid var(--gris2);}}
    .legend-item{{display:flex;align-items:center;gap:.4rem;font-size:.78rem;color:var(--texto);}}
    .legend-dot{{width:10px;height:10px;border-radius:50%;}}

    /* MODALS */
    .modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:300;align-items:flex-start;justify-content:center;padding:2rem 1rem;overflow-y:auto;}}
    .modal-overlay.open{{display:flex;}}
    .modal{{background:var(--blanco);border-radius:12px;width:100%;max-width:900px;max-height:85vh;overflow-y:auto;box-shadow:0 24px 80px rgba(0,0,0,.3);animation:popIn .2s ease;margin:auto;}}
    @keyframes popIn{{from{{opacity:0;transform:translateY(-12px);}}to{{opacity:1;transform:translateY(0);}}}}
    .modal-header{{padding:1.2rem 1.5rem;border-bottom:1px solid var(--borde);display:flex;align-items:center;justify-content:space-between;background:var(--rojo);border-radius:12px 12px 0 0;}}
    .modal-header h2{{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#fff;}}
    .modal-close{{background:none;border:none;font-size:1.3rem;cursor:pointer;color:rgba(255,255,255,.8);line-height:1;}}
    .modal-close:hover{{color:#fff;}}
    .modal-body{{padding:1.5rem;}}

    /* RANKING */
    .rank-table{{width:100%;border-collapse:collapse;font-size:.85rem;}}
    .rank-table th{{background:var(--gris);padding:.6rem .8rem;text-align:left;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);border-bottom:2px solid var(--borde);}}
    .rank-table td{{padding:.55rem .8rem;border-bottom:1px solid var(--gris2);vertical-align:middle;}}
    .rank-table tr:hover td{{background:var(--gris);}}
    .rank-num{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--rojo);}}
    .intensity-bar{{height:6px;background:var(--borde);border-radius:3px;overflow:hidden;width:80px;}}
    .intensity-fill{{height:100%;background:var(--rojo);border-radius:3px;}}
    .cat-badge{{font-size:.6rem;font-weight:700;padding:.15rem .45rem;border-radius:3px;}}

    /* TIMELINE */
    .timeline-wrap{{overflow-x:auto;}}
    .timeline-row{{display:flex;align-items:center;gap:.8rem;padding:.5rem 0;border-bottom:1px solid var(--gris2);}}
    .timeline-row:last-child{{border-bottom:none;}}
    .tl-name{{font-size:.82rem;color:var(--texto);flex:0 0 260px;line-height:1.3;}}
    .tl-bar-wrap{{flex:1;position:relative;height:18px;background:var(--gris2);border-radius:4px;overflow:hidden;}}
    .tl-bar{{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:.4rem;font-size:.62rem;font-weight:700;color:#fff;white-space:nowrap;}}
    .tl-year{{font-size:.72rem;font-weight:700;color:var(--muted);flex:0 0 50px;text-align:right;}}

    /* RISK POPUP */
    .risk-popup{{display:none;position:fixed;z-index:400;background:var(--blanco);border:1px solid var(--borde);border-radius:10px;box-shadow:0 12px 40px rgba(0,0,0,.2);padding:1.2rem;max-width:320px;pointer-events:none;}}
    .risk-popup.visible{{display:block;}}
    .rp-code{{font-size:.62rem;font-weight:700;font-family:monospace;color:var(--muted);margin-bottom:.2rem;}}
    .rp-name{{font-family:'Playfair Display',serif;font-size:.95rem;font-weight:700;color:var(--texto);margin-bottom:.5rem;line-height:1.3;}}
    .rp-desc{{font-size:.8rem;color:var(--texto);line-height:1.6;margin-bottom:.7rem;}}
    .rp-grid{{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;}}
    .rp-metric{{background:var(--gris);border-radius:4px;padding:.5rem .7rem;}}
    .rp-metric-label{{font-size:.58rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);}}
    .rp-metric-value{{font-size:.85rem;font-weight:700;color:var(--rojo);}}
    .rp-close-btn{{position:absolute;top:.5rem;right:.6rem;background:none;border:none;cursor:pointer;font-size:1rem;color:var(--muted);pointer-events:auto;}}

    /* INTERRELATIONS */
    #network-svg{{width:100%;min-height:500px;}}

    @media(max-width:640px){{
      .main{{padding:0 1rem 2rem;}}
      .hero{{padding:1rem;}}
      .hi{{padding:.8rem 1rem;}}
      .tl-name{{flex:0 0 160px;font-size:.75rem;}}
    }}
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
    <div class="chart-title"><span>◈</span> Mapa de Riesgos — Probabilidad vs Impacto</div>
    <div id="scatter-container"></div>
    <div class="legend" id="legend"></div>
  </div>
</div>

<!-- RISK POPUP -->
<div class="risk-popup" id="riskPopup">
  <button class="rp-close-btn" id="riskPopupClose">✕</button>
  <div class="rp-code" id="rpCode"></div>
  <div class="rp-name" id="rpName"></div>
  <div class="rp-desc" id="rpDesc"></div>
  <div class="rp-grid" id="rpGrid"></div>
</div>

<!-- RANKING MODAL -->
<div class="modal-overlay" id="rankingModal">
  <div class="modal">
    <div class="modal-header">
      <h2>📊 Ranking de Riesgos por Intensidad</h2>
      <button class="modal-close" onclick="closeModal('rankingModal')">✕</button>
    </div>
    <div class="modal-body" id="rankingBody"></div>
  </div>
</div>

<!-- NETWORK MODAL -->
<div class="modal-overlay" id="networkModal">
  <div class="modal" style="max-width:1000px;">
    <div class="modal-header">
      <h2>🔗 Mapa de Interrelaciones</h2>
      <button class="modal-close" onclick="closeModal('networkModal')">✕</button>
    </div>
    <div class="modal-body">
      <p style="font-size:.82rem;color:var(--muted);margin-bottom:1rem;">El tamaño del nodo indica su centralidad (capacidad de arrastre). El grosor del vínculo refleja la intensidad de la relación.</p>
      <svg id="network-svg"></svg>
    </div>
  </div>
</div>

<!-- TIMELINE MODAL -->
<div class="modal-overlay" id="timelineModal">
  <div class="modal">
    <div class="modal-header">
      <h2>⏱ Nivel de Aproximacion — Riesgos Priorizados</h2>
      <button class="modal-close" onclick="closeModal('timelineModal')">✕</button>
    </div>
    <div class="modal-body" id="timelineBody"></div>
  </div>
</div>

<footer style="background:#9B0B22;color:rgba(255,255,255,.7);padding:1.1rem 2rem;text-align:center;font-size:.68rem;letter-spacing:.06em;">
  CEPLAN — Centro Nacional de Planeamiento Estrategico &nbsp;|&nbsp; {s['periodo']} &nbsp;|&nbsp; {s['created_at']}
</footer>

<script>
const RAW = {data_json};
const riesgos = RAW.riesgos || [];
const metadata = RAW.metadata || {{}};

const CAT_COLOR = {{
  'Social':'#E84855','Ambiental':'#3BB273','Economico':'#F18F01',
  'Politico':'#A23B72','Tecnologico':'#2E86AB'
}};

// STATS
(function(){{
  const bar = document.getElementById('statsBar');
  const cats = {{}};
  riesgos.forEach(r => {{ cats[r.categoria]=(cats[r.categoria]||0)+1; }});
  const criticos = riesgos.filter(r => r.probabilidad >= 3.6 && r.impacto >= 3.6).length;
  [
    [riesgos.length, 'Total Riesgos'],
    [criticos, 'Criticos (Q-I)'],
    ...Object.entries(cats).map(([k,v]) => [v, k])
  ].forEach(([n,l]) => {{
    const d = document.createElement('div');
    d.className = 'stat';
    const color = CAT_COLOR[l] || 'var(--rojo)';
    d.innerHTML = `<div class="stat-num" style="color:${{color}}">${{n}}</div><div class="stat-label">${{l}}</div>`;
    bar.appendChild(d);
  }});
}})();

// LEGEND
(function(){{
  const leg = document.getElementById('legend');
  Object.entries(CAT_COLOR).forEach(([cat, color]) => {{
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML = `<div class="legend-dot" style="background:${{color}}"></div>${{cat}}`;
    leg.appendChild(item);
  }});
}})();

// SCATTER PLOT with D3
let activeCAT = 'all', activeQUAD = 'all';

function getQuadrant(prob, imp, midP, midI) {{
  if (prob >= midP && imp >= midI) return 'I';
  if (prob < midP && imp >= midI) return 'II';
  if (prob < midP && imp < midI) return 'III';
  return 'IV';
}}

function drawScatter(data) {{
  const container = document.getElementById('scatter-container');
  container.innerHTML = '';

  const margin = {{top:30, right:40, bottom:60, left:60}};
  const width = container.clientWidth || 900;
  const height = Math.max(500, width * 0.6);
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const allProb = data.map(d=>d.probabilidad);
  const allImp = data.map(d=>d.impacto);
  const minP = Math.min(...allProb) - 0.15;
  const maxP = Math.max(...allProb) + 0.15;
  const minI = Math.min(...allImp) - 0.15;
  const maxI = Math.max(...allImp) + 0.15;
  const midP = (minP + maxP) / 2;
  const midI = (minI + maxI) / 2;

  const xScale = d3.scaleLinear().domain([minP, maxP]).range([0, innerW]);
  const yScale = d3.scaleLinear().domain([minI, maxI]).range([innerH, 0]);

  const svg = d3.select(container).append('svg')
    .attr('id','scatter-svg')
    .attr('width', width).attr('height', height);

  const g = svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);

  // Quadrant backgrounds
  const quads = [
    {{x:xScale(midP),y:0,w:innerW-xScale(midP),h:yScale(midI),label:'I — CRITICO',color:'rgba(200,16,46,0.06)'}},
    {{x:0,y:0,w:xScale(midP),h:yScale(midI),label:'II — ALTO IMPACTO',color:'rgba(161,163,178,0.06)'}},
    {{x:0,y:yScale(midI),w:xScale(midP),h:innerH-yScale(midI),label:'III — BAJO',color:'rgba(161,163,178,0.04)'}},
    {{x:xScale(midP),y:yScale(midI),w:innerW-xScale(midP),h:innerH-yScale(midI),label:'IV — ALTA PROB.',color:'rgba(241,143,1,0.05)'}},
  ];
  quads.forEach(q => {{
    g.append('rect').attr('x',q.x).attr('y',q.y).attr('width',q.w).attr('height',q.h).attr('fill',q.color);
    g.append('text').attr('x',q.x+q.w/2).attr('y',q.y+q.h/2)
      .attr('text-anchor','middle').attr('dominant-baseline','middle')
      .attr('class','q-label').attr('fill','#aaa').text(q.label);
  }});

  // Midlines
  g.append('line').attr('x1',xScale(midP)).attr('x2',xScale(midP)).attr('y1',0).attr('y2',innerH)
    .attr('stroke','rgba(200,16,46,0.3)').attr('stroke-width',1.5).attr('stroke-dasharray','5,4');
  g.append('line').attr('x1',0).attr('x2',innerW).attr('y1',yScale(midI)).attr('y2',yScale(midI))
    .attr('stroke','rgba(200,16,46,0.3)').attr('stroke-width',1.5).attr('stroke-dasharray','5,4');

  // Axes
  g.append('g').attr('transform',`translate(0,${{innerH}})`).call(d3.axisBottom(xScale).ticks(8).tickFormat(d=>d.toFixed(1)))
    .selectAll('text').style('font-size','11px').style('font-family','Source Sans 3,sans-serif');
  g.append('g').call(d3.axisLeft(yScale).ticks(8).tickFormat(d=>d.toFixed(1)))
    .selectAll('text').style('font-size','11px').style('font-family','Source Sans 3,sans-serif');

  // Axis labels
  g.append('text').attr('x',innerW/2).attr('y',innerH+45).attr('text-anchor','middle')
    .style('font-size','12px').style('font-weight','700').style('fill','var(--muted)').text('Probabilidad');
  g.append('text').attr('transform','rotate(-90)').attr('x',-innerH/2).attr('y',-45)
    .attr('text-anchor','middle').style('font-size','12px').style('font-weight','700').style('fill','var(--muted)').text('Impacto');

  // Points
  const points = g.selectAll('.point').data(data).enter().append('g').attr('class','point')
    .attr('transform', d=>`translate(${{xScale(d.probabilidad)}},${{yScale(d.impacto)}})`);

  points.append('circle').attr('r',7).attr('fill',d=>CAT_COLOR[d.categoria]||'#999')
    .attr('stroke','#fff').attr('stroke-width',1.5).attr('opacity',0.85)
    .style('cursor','pointer')
    .on('mouseover', function(event, d) {{ showPopup(event, d); d3.select(this).attr('r',10).attr('opacity',1); }})
    .on('mouseout', function() {{ hidePopup(); d3.select(this).attr('r',7).attr('opacity',0.85); }})
    .on('click', function(event, d) {{ showPopup(event, d, true); }});

  // Labels
  points.append('text').attr('dy',-11).attr('text-anchor','middle')
    .style('font-size','9px').style('font-weight','700').style('fill','var(--texto)')
    .style('pointer-events','none')
    .text(d => d.codigo || '');
}}

function filterAndDraw() {{
  let filtered = riesgos;
  if (activeCAT !== 'all') filtered = filtered.filter(r => r.categoria === activeCAT);
  if (activeQUAD !== 'all') {{
    const allProb = riesgos.map(d=>d.probabilidad);
    const allImp = riesgos.map(d=>d.impacto);
    const midP = (Math.min(...allProb) + Math.max(...allProb)) / 2;
    const midI = (Math.min(...allImp) + Math.max(...allImp)) / 2;
    filtered = filtered.filter(r => getQuadrant(r.probabilidad, r.impacto, midP, midI) === activeQUAD);
  }}
  drawScatter(filtered);
}}

// Filter buttons
document.querySelectorAll('[data-cat]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('[data-cat]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); activeCAT = btn.dataset.cat; filterAndDraw();
  }});
}});
document.querySelectorAll('[data-quad]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('[data-quad]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active'); activeQUAD = btn.dataset.quad; filterAndDraw();
  }});
}});

// POPUP
let popupPinned = false;
const popup = document.getElementById('riskPopup');

function showPopup(event, d, pinned=false) {{
  popupPinned = pinned;
  const color = CAT_COLOR[d.categoria]||'#999';
  document.getElementById('rpCode').textContent = d.codigo || '';
  document.getElementById('rpName').textContent = d.nombre || '';
  document.getElementById('rpDesc').textContent = d.descripcion || '';
  const intensity = ((d.probabilidad||0) * (d.impacto||0)).toFixed(2);
  document.getElementById('rpGrid').innerHTML = `
    <div class="rp-metric"><div class="rp-metric-label">Probabilidad</div><div class="rp-metric-value" style="color:${{color}}">${{(d.probabilidad||0).toFixed(2)}}</div></div>
    <div class="rp-metric"><div class="rp-metric-label">Impacto</div><div class="rp-metric-value" style="color:${{color}}">${{(d.impacto||0).toFixed(2)}}</div></div>
    <div class="rp-metric"><div class="rp-metric-label">Intensidad</div><div class="rp-metric-value" style="color:${{color}}">${{intensity}}</div></div>
    <div class="rp-metric"><div class="rp-metric-label">Categoria</div><div class="rp-metric-value" style="color:${{color}};font-size:.78rem">${{d.categoria||''}}</div></div>
    ${{d.aproximacion ? `<div class="rp-metric" style="grid-column:1/-1"><div class="rp-metric-label">Aproximacion</div><div class="rp-metric-value" style="font-size:.78rem;color:var(--texto)">${{d.aproximacion}}</div></div>` : ''}}
    ${{d.interrelaciones && d.interrelaciones.length ? `<div class="rp-metric" style="grid-column:1/-1"><div class="rp-metric-label">Se relaciona con</div><div style="font-size:.75rem;color:var(--texto);margin-top:.2rem">${{d.interrelaciones.slice(0,4).join(', ')}}</div></div>` : ''}}`;
  popup.style.pointerEvents = pinned ? 'auto' : 'none';
  popup.classList.add('visible');
  positionPopup(event);
}}

function positionPopup(event) {{
  const px = event.pageX + 15;
  const py = event.pageY - 10;
  const pw = popup.offsetWidth || 320;
  const ph = popup.offsetHeight || 200;
  popup.style.left = Math.min(px, window.innerWidth - pw - 20) + 'px';
  popup.style.top = Math.min(py, window.scrollY + window.innerHeight - ph - 20) + 'px';
}}

function hidePopup() {{
  if (!popupPinned) popup.classList.remove('visible');
}}

document.getElementById('riskPopupClose').addEventListener('click', () => {{
  popup.classList.remove('visible'); popupPinned = false;
}});

// MODALS
function openModal(id) {{
  document.getElementById(id).classList.add('open');
  if (id === 'rankingModal') buildRanking();
  if (id === 'networkModal') buildNetwork();
  if (id === 'timelineModal') buildTimeline();
}}
function closeModal(id) {{ document.getElementById(id).classList.remove('open'); }}
document.querySelectorAll('.modal-overlay').forEach(el => {{
  el.addEventListener('click', e => {{ if (e.target === el) el.classList.remove('open'); }});
}});

// RANKING
function buildRanking() {{
  const sorted = [...riesgos].sort((a,b) => (b.probabilidad*b.impacto)-(a.probabilidad*a.impacto));
  const maxInt = sorted[0].probabilidad * sorted[0].impacto;
  const rows = sorted.map((r,i) => {{
    const int = (r.probabilidad*r.impacto).toFixed(2);
    const pct = ((r.probabilidad*r.impacto)/maxInt*100).toFixed(0);
    const color = CAT_COLOR[r.categoria]||'#999';
    return `<tr>
      <td><span class="rank-num">${{i+1}}</span></td>
      <td><span class="cat-badge" style="background:${{color}}22;color:${{color}}">${{r.codigo||''}}</span></td>
      <td style="max-width:280px;font-size:.82rem">${{r.nombre}}</td>
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
  document.getElementById('rankingBody').innerHTML = `
    <table class="rank-table">
      <thead><tr><th>#</th><th>Cod.</th><th>Riesgo</th><th>Categoria</th><th>Prob.</th><th>Impacto</th><th>Intensidad</th></tr></thead>
      <tbody>${{rows}}</tbody>
    </table>`;
}}

// NETWORK
function buildNetwork() {{
  const svg = d3.select('#network-svg');
  svg.selectAll('*').remove();
  const W = document.getElementById('networkModal').querySelector('.modal-body').clientWidth || 800;
  const H = 520;
  svg.attr('width', W).attr('height', H);

  const nodes = riesgos.map(r => ({{
    id: r.codigo, name: r.nombre, cat: r.categoria,
    intensity: r.probabilidad * r.impacto,
    connections: (r.interrelaciones||[]).length
  }}));

  const links = [];
  riesgos.forEach(r => {{
    (r.interrelaciones||[]).forEach(rel => {{
      const target = riesgos.find(x => x.codigo===rel || x.nombre===rel);
      if (target) links.push({{source: r.codigo, target: target.codigo, strength: 1}});
    }});
  }});

  const maxInt = Math.max(...nodes.map(n=>n.intensity));
  const rScale = d3.scaleSqrt().domain([0,maxInt]).range([6,22]);

  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d=>d.id).distance(80).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d=>rScale(d.intensity)+5));

  const link = svg.append('g').selectAll('line').data(links).enter().append('line')
    .attr('stroke','rgba(200,16,46,0.2)').attr('stroke-width',1.5);

  const node = svg.append('g').selectAll('g').data(nodes).enter().append('g')
    .style('cursor','pointer')
    .call(d3.drag()
      .on('start', (e,d) => {{ if(!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
      .on('drag', (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
      .on('end', (e,d) => {{ if(!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }}));

  node.append('circle').attr('r', d=>rScale(d.intensity))
    .attr('fill', d=>CAT_COLOR[d.cat]||'#999').attr('opacity',0.8)
    .attr('stroke','#fff').attr('stroke-width',1.5);

  node.append('text').attr('dy','0.35em').attr('text-anchor','middle')
    .style('font-size','8px').style('font-weight','700').style('fill','#fff')
    .style('pointer-events','none').text(d=>d.id);

  simulation.on('tick', () => {{
    link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y)
        .attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
    node.attr('transform',d=>`translate(${{Math.max(25,Math.min(W-25,d.x))}},${{Math.max(25,Math.min(H-25,d.y))}})`);
  }});
}}

// TIMELINE
function buildTimeline() {{
  const sorted = [...riesgos]
    .filter(r => r.anio_aproximacion)
    .sort((a,b) => a.anio_aproximacion - b.anio_aproximacion);

  const minY = Math.min(...sorted.map(r=>r.anio_aproximacion));
  const maxY = Math.max(...sorted.map(r=>r.anio_aproximacion));

  const rows = sorted.map(r => {{
    const color = CAT_COLOR[r.categoria]||'#999';
    const pct = maxY===minY ? 50 : ((r.anio_aproximacion-minY)/(maxY-minY)*85+5);
    return `<div class="timeline-row">
      <div class="tl-name"><span style="font-size:.62rem;font-weight:700;color:${{color}};margin-right:.3rem">${{r.codigo||''}}</span>${{r.nombre}}</div>
      <div class="tl-bar-wrap">
        <div class="tl-bar" style="width:${{pct}}%;background:${{color}}">${{r.anio_aproximacion}}</div>
      </div>
      <div class="tl-year">${{r.anio_aproximacion}}</div>
    </div>`;
  }}).join('');

  document.getElementById('timelineBody').innerHTML = `
    <p style="font-size:.8rem;color:var(--muted);margin-bottom:1rem;">Ordenado por año estimado de concretizacion. Los riesgos mas a la derecha son menos proximos.</p>
    <div class="timeline-wrap">${{rows}}</div>`;
}}

// INIT
filterAndDraw();
</script>
</body>
</html>"""
    return HTMLResponse(html)

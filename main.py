from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
from datetime import datetime, timedelta
import threading
import os

app = FastAPI(title="CEPLAN Mapa de Riesgos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (dashboard.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/data/{session_id}")
def get_data(session_id: str):
    cleanup_sessions()
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesion no encontrada o expirada")
    s = sessions[session_id]
    return JSONResponse({
        "titulo": s["titulo"],
        "periodo": s["periodo"],
        "created_at": s["created_at"],
        **s["data"]
    })

@app.get("/view/{session_id}", response_class=HTMLResponse)
def view_riesgos(session_id: str):
    cleanup_sessions()
    if session_id not in sessions:
        return HTMLResponse("""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>No encontrado</title>
<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
min-height:100vh;background:#f5f5f5;}
.box{text-align:center;padding:3rem;background:#fff;border-radius:12px;
box-shadow:0 4px 24px rgba(0,0,0,.08);max-width:420px;}
h1{color:#C8102E;}p{color:#666;font-size:.9rem;}</style></head>
<body><div class="box"><h1>Sesion expirada</h1>
<p>Genera un nuevo reporte desde ChatGPT.</p></div></body></html>""", status_code=404)

    # Read dashboard template and inject session_id
    with open("static/dashboard.html", "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("__SESSION_ID__", session_id)
    return HTMLResponse(html)

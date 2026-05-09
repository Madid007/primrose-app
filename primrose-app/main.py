"""
PRIM'ROSE RH - API Backend
FastAPI + Python — Hébergement Render.com
"""
import os, json, hashlib, secrets
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn

from processor import process_files, load_data

# ── CONFIG ──────────────────────────────────────────────────────────────────
ADMIN_USER     = os.getenv("ADMIN_USER", "anass")
ADMIN_PASS     = os.getenv("ADMIN_PASS", "primrose2025")
VIEWER_PASS    = os.getenv("VIEWER_PASS", "direction2025")
DATA_DIR       = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE      = DATA_DIR / "dashboard_data.json"
UPLOAD_LOG     = DATA_DIR / "upload_log.json"

# ── APP ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="PRIM'ROSE RH API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
security = HTTPBasic()

# ── AUTH ─────────────────────────────────────────────────────────────────────
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    ok_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Accès refusé", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

def verify_viewer(credentials: HTTPBasicCredentials = Depends(security)):
    # Admin ou viewer peuvent voir le dashboard
    is_admin = (secrets.compare_digest(credentials.username, ADMIN_USER) and
                secrets.compare_digest(credentials.password, ADMIN_PASS))
    is_viewer = secrets.compare_digest(credentials.password, VIEWER_PASS)
    if not (is_admin or is_viewer):
        raise HTTPException(status_code=401, detail="Accès refusé", headers={"WWW-Authenticate": "Basic"})
    return credentials.username

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    """Page d'accueil publique"""
    return HTMLResponse(content=get_landing_page())

@app.get("/health")
async def health():
    data_exists = DATA_FILE.exists()
    last_update = None
    if UPLOAD_LOG.exists():
        log = json.loads(UPLOAD_LOG.read_text())
        last_update = log.get("last_upload")
    return {
        "status": "ok",
        "data_ready": data_exists,
        "last_update": last_update,
        "version": "1.0.0"
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(user: str = Depends(verify_viewer)):
    """Dashboard principal — accès équipe de direction"""
    if not DATA_FILE.exists():
        return HTMLResponse(content=no_data_page())
    data = json.loads(DATA_FILE.read_text())
    return HTMLResponse(content=build_dashboard_html(data))

@app.get("/admin", response_class=HTMLResponse)
async def get_admin(user: str = Depends(verify_admin)):
    """Page d'administration pour Anass"""
    log = {}
    if UPLOAD_LOG.exists():
        log = json.loads(UPLOAD_LOG.read_text())
    return HTMLResponse(content=get_admin_page(log))

@app.post("/upload")
async def upload_files(
    user: str = Depends(verify_admin),
    paie_file: UploadFile = File(..., description="Fichier Excel état de paie BeeOne"),
    prod_file: UploadFile  = File(..., description="Fichier Excel production"),
    quinzaine: str = Form(..., description="Ex: Q1, Q2... ou Campagne complète"),
    campagne:  str = Form(..., description="C2425 ou C2526")
):
    """Upload des fichiers Excel et mise à jour du dashboard"""
    try:
        # Sauvegarder les fichiers temporairement
        paie_path = DATA_DIR / f"paie_{campagne}.xlsx"
        prod_path  = DATA_DIR / f"prod_{campagne}.xlsx"

        paie_path.write_bytes(await paie_file.read())
        prod_path.write_bytes(await prod_file.read())

        # Traitement
        dashboard_data = process_files(str(paie_path), str(prod_path))

        # Sauvegarder
        DATA_FILE.write_text(json.dumps(dashboard_data, ensure_ascii=True))

        # Log
        log = {
            "last_upload": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "campagne": campagne,
            "quinzaine": quinzaine,
            "uploaded_by": user,
            "paie_file": paie_file.filename,
            "prod_file": prod_file.filename,
        }
        UPLOAD_LOG.write_text(json.dumps(log, ensure_ascii=False))

        return JSONResponse({
            "success": True,
            "message": f"Dashboard mis à jour — {campagne} {quinzaine}",
            "timestamp": log["last_upload"]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur traitement: {str(e)}")

@app.get("/api/data")
async def get_data(user: str = Depends(verify_viewer)):
    """Données JSON brutes pour intégrations futures"""
    if not DATA_FILE.exists():
        raise HTTPException(status_code=404, detail="Pas encore de données")
    return JSONResponse(json.loads(DATA_FILE.read_text()))

# ── HTML PAGES ────────────────────────────────────────────────────────────────
def get_landing_page():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PRIM'ROSE RH</title>
<style>
  body{margin:0;font-family:Arial,sans-serif;background:#2a4e26;min-height:100vh;
       display:flex;align-items:center;justify-content:center;flex-direction:column}
  .card{background:#fff;border-radius:20px;padding:40px;text-align:center;max-width:380px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.3)}
  h1{color:#2a4e26;font-size:28px;margin:10px 0 5px}
  .sub{color:#6b7f69;font-size:14px;margin-bottom:30px}
  .btn{display:block;padding:14px 20px;border-radius:12px;text-decoration:none;font-weight:700;font-size:15px;margin:10px 0;transition:all .2s}
  .btn-green{background:#3a6b35;color:#fff}
  .btn-gold{background:#e8a020;color:#fff}
  .btn:hover{opacity:.85;transform:translateY(-1px)}
  .rose{font-size:60px;margin-bottom:10px}
</style>
</head>
<body>
<div class="card">
  <div class="rose">🌹</div>
  <h1>PRIM'ROSE RH</h1>
  <div class="sub">Tableau de Bord RH — Azemmour</div>
  <a href="/dashboard" class="btn btn-green">📊 Voir le Dashboard</a>
  <a href="/admin" class="btn btn-gold">⚙️ Admin (Anass)</a>
</div>
</body>
</html>"""

def no_data_page():
    return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>PRIM'ROSE RH</title>
<style>body{font-family:Arial;background:#f0f5ef;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.box{background:#fff;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.1)}
h2{color:#3a6b35}p{color:#6b7f69}</style></head>
<body><div class="box"><div style="font-size:50px">📋</div>
<h2>Pas encore de données</h2>
<p>Anass doit uploader les fichiers Excel BeeOne<br>via la page d'administration.</p>
<a href="/admin" style="background:#e8a020;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700">
Aller à l'administration</a></div></body></html>"""

def get_admin_page(log: dict):
    last = log.get("last_upload", "Jamais")
    camp = log.get("campagne", "-")
    qu   = log.get("quinzaine", "-")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Admin — PRIM'ROSE RH</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Arial,sans-serif;background:#f0f5ef;min-height:100vh;padding:20px}}
  .hdr{{background:#2a4e26;color:#fff;padding:16px 20px;border-radius:12px;margin-bottom:20px;display:flex;align-items:center;gap:12px}}
  .hdr h1{{font-size:18px}}
  .card{{background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
  .card h2{{color:#2a4e26;font-size:15px;margin-bottom:12px;display:flex;align-items:center;gap:8px}}
  .status{{background:#e8f5e9;border:1px solid #c8e6c9;border-radius:8px;padding:12px;margin-bottom:16px;font-size:13px}}
  .field{{margin-bottom:14px}}
  label{{display:block;font-size:12px;font-weight:700;color:#6b7f69;margin-bottom:5px;text-transform:uppercase}}
  input,select{{width:100%;padding:10px 12px;border:1.5px solid #d4e4d2;border-radius:8px;font-size:14px;font-family:Arial}}
  input:focus,select:focus{{outline:none;border-color:#3a6b35}}
  .upload-zone{{border:2px dashed #d4e4d2;border-radius:10px;padding:20px;text-align:center;cursor:pointer;transition:all .2s;position:relative}}
  .upload-zone:hover,.upload-zone.over{{border-color:#3a6b35;background:#f0f5ef}}
  .upload-zone input[type=file]{{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}}
  .upload-zone .icon{{font-size:30px;margin-bottom:5px}}
  .upload-zone .label{{font-size:13px;color:#6b7f69}}
  .upload-zone .fname{{font-size:12px;color:#3a6b35;font-weight:700;margin-top:6px}}
  .btn-submit{{width:100%;padding:14px;background:#3a6b35;color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;transition:all .2s}}
  .btn-submit:hover{{background:#2a4e26}}
  .btn-submit:disabled{{background:#95a5a6;cursor:not-allowed}}
  .msg{{border-radius:8px;padding:12px;font-size:13px;margin-top:12px;display:none}}
  .msg.ok{{background:#e8f5e9;color:#1a6b45;border:1px solid #c8e6c9}}
  .msg.err{{background:#fdecea;color:#c0392b;border:1px solid #fadbd8}}
  .progress{{height:6px;background:#e0e0e0;border-radius:3px;margin-top:10px;display:none}}
  .progress-bar{{height:100%;background:#3a6b35;border-radius:3px;width:0;transition:width .3s}}
  .info-row{{display:flex;gap:8px;margin-bottom:8px}}
  .info-badge{{background:#f0f5ef;border-radius:6px;padding:6px 10px;font-size:12px;flex:1;text-align:center}}
  .info-badge strong{{display:block;color:#2a4e26;font-size:14px}}
  a.back{{display:inline-flex;align-items:center;gap:6px;color:#3a6b35;text-decoration:none;font-size:13px;font-weight:700;margin-bottom:16px}}
</style>
</head>
<body>
<a href="/dashboard" class="back">← Dashboard</a>
<div class="hdr">
  <span style="font-size:24px">🌹</span>
  <div>
    <h1>Administration — PRIM'ROSE RH</h1>
    <div style="font-size:12px;opacity:.8">Upload des fichiers BeeOne chaque quinzaine</div>
  </div>
</div>

<div class="card">
  <h2>📊 Dernière mise à jour</h2>
  <div class="info-row">
    <div class="info-badge"><label>Date</label><strong>{last}</strong></div>
    <div class="info-badge"><label>Campagne</label><strong>{camp}</strong></div>
    <div class="info-badge"><label>Quinzaine</label><strong>{qu}</strong></div>
  </div>
</div>

<div class="card">
  <h2>⬆️ Mettre à jour le Dashboard</h2>
  
  <form id="uploadForm">
    <div class="field">
      <label>Campagne</label>
      <select name="campagne" required>
        <option value="C2526">C2526 (2025-2026)</option>
        <option value="C2425">C2425 (2024-2025)</option>
      </select>
    </div>
    
    <div class="field">
      <label>Quinzaine</label>
      <select name="quinzaine" required>
        {''.join(f'<option value="Q{i}">Q{i}</option>' for i in range(1,25))}
      </select>
    </div>
    
    <div class="field">
      <label>📋 Fichier Paie (BeeOne)</label>
      <div class="upload-zone" id="zone-paie">
        <input type="file" name="paie_file" accept=".xlsx,.xls" required onchange="showFile(this,'zone-paie')">
        <div class="icon">📄</div>
        <div class="label">Etat de paie — Excel BeeOne</div>
        <div class="fname" id="fname-paie"></div>
      </div>
    </div>
    
    <div class="field">
      <label>🌱 Fichier Production</label>
      <div class="upload-zone" id="zone-prod">
        <input type="file" name="prod_file" accept=".xlsx,.xls" required onchange="showFile(this,'zone-prod')">
        <div class="icon">📊</div>
        <div class="label">Tableau de bord production</div>
        <div class="fname" id="fname-prod"></div>
      </div>
    </div>
    
    <button type="submit" class="btn-submit" id="submitBtn">
      🔄 Mettre à jour le Dashboard
    </button>
    
    <div class="progress" id="progress">
      <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <div class="msg" id="msg"></div>
  </form>
</div>

<div class="card" style="background:#fff8e6;border:1px solid #ffe082">
  <h2>📱 Partager le Dashboard</h2>
  <p style="font-size:13px;color:#6b7f69;margin-bottom:10px">
    Envoyez ce lien à l'équipe de direction. Sur iPhone: Safari → Partager → Sur l'écran d'accueil.
  </p>
  <div style="background:#f0f5ef;border-radius:8px;padding:10px;font-family:monospace;font-size:12px;word-break:break-all" id="dashUrl"></div>
  <button onclick="copyUrl()" style="margin-top:10px;width:100%;padding:10px;background:#e8a020;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:13px">
    📋 Copier le lien
  </button>
</div>

<script>
function showFile(input, zoneId) {{
  var fname = input.files[0] ? input.files[0].name : '';
  var suffix = zoneId === 'zone-paie' ? 'paie' : 'prod';
  document.getElementById('fname-' + suffix).textContent = fname;
  document.getElementById(zoneId).style.borderColor = '#3a6b35';
}}

document.getElementById('uploadForm').addEventListener('submit', async function(e) {{
  e.preventDefault();
  var btn = document.getElementById('submitBtn');
  var prog = document.getElementById('progress');
  var bar  = document.getElementById('progressBar');
  var msg  = document.getElementById('msg');
  
  btn.disabled = true;
  btn.textContent = '⏳ Traitement en cours...';
  prog.style.display = 'block';
  msg.style.display = 'none';
  
  // Animation progress
  var pct = 0;
  var interval = setInterval(function() {{
    pct = Math.min(pct + Math.random()*15, 85);
    bar.style.width = pct + '%';
  }}, 300);
  
  try {{
    var fd = new FormData(this);
    var resp = await fetch('/upload', {{method:'POST', body:fd}});
    var data = await resp.json();
    
    clearInterval(interval);
    bar.style.width = '100%';
    
    if (resp.ok) {{
      msg.className = 'msg ok';
      msg.textContent = '✅ ' + data.message + ' — ' + data.timestamp;
      msg.style.display = 'block';
      btn.textContent = '✅ Dashboard mis à jour !';
      setTimeout(function(){{ window.location.href = '/dashboard'; }}, 2000);
    }} else {{
      throw new Error(data.detail || 'Erreur serveur');
    }}
  }} catch(err) {{
    clearInterval(interval);
    msg.className = 'msg err';
    msg.textContent = '❌ ' + err.message;
    msg.style.display = 'block';
    btn.disabled = false;
    btn.textContent = '🔄 Réessayer';
  }}
}});

// Afficher l'URL du dashboard
var url = window.location.origin + '/dashboard';
document.getElementById('dashUrl').textContent = url;
function copyUrl() {{
  navigator.clipboard.writeText(url).then(function() {{
    alert('Lien copié ! Partagez-le avec l\\'équipe.');
  }});
}}
</script>
</body>
</html>"""

def build_dashboard_html(data: dict) -> str:
    """Injecter les données dans le template dashboard"""
    template = open("dashboard_template.html", encoding="utf-8").read()
    data_js  = json.dumps(data.get("data", {}), ensure_ascii=True)
    prod_js  = json.dumps(data.get("prod", {}), ensure_ascii=True)
    ct_js    = json.dumps(data.get("ct",   {}), ensure_ascii=True)
    import re
    result = re.sub(r'var DATA=\{.*?\};', f'var DATA={data_js};', template, flags=re.DOTALL)
    result = re.sub(r'var PROD=\{.*?\};', f'var PROD={prod_js};', result, flags=re.DOTALL)
    result = re.sub(r'var CT=\{.*?\};',   f'var CT={ct_js};',   result, flags=re.DOTALL)
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)

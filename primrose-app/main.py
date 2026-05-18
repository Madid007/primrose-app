"""
PRIM'ROSE RH - API Backend v2
FastAPI + Python — Authentification par formulaire (cookie)
"""
import os, json, secrets
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from processor import process_files, load_data
 
# ── CONFIG ───────────────────────────────────────────────────────────────────
ADMIN_USER  = os.getenv("ADMIN_USER",  "madid")
ADMIN_PASS  = os.getenv("ADMIN_PASS",  "primrose2526")
VIEWER_PASS = os.getenv("VIEWER_PASS", "direction2526")
DATA_DIR    = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE   = DATA_DIR / "dashboard_data.json"
UPLOAD_LOG  = DATA_DIR / "upload_log.json"
SESSIONS: dict = {}
 
app = FastAPI(title="PRIM'ROSE RH", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
 
# ── AUTH ──────────────────────────────────────────────────────────────────────
def create_session(role: str) -> str:
    token = secrets.token_hex(32)
    SESSIONS[token] = role
    return token
 
def get_role(request: Request) -> str:
    token = request.cookies.get("session", "")
    return SESSIONS.get(token, "")
 
# ── PAGE LOGIN ─────────────────────────────────────────────────────────────────
def login_page(error="", redirect="/dashboard"):
    err_html = f'<div class="error">⚠️ {error}</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PRIM'ROSE RH — Connexion</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#1a3a18,#3a6b35);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#fff;border-radius:24px;padding:40px 36px;width:100%;max-width:390px;box-shadow:0 25px 60px rgba(0,0,0,.4)}}
.logo{{text-align:center;margin-bottom:28px}}
.rose{{font-size:60px;display:block;margin-bottom:8px}}
h1{{color:#2a4e26;font-size:24px;font-weight:800}}
.sub{{color:#6b7f69;font-size:13px;margin-top:4px}}
.field{{margin-bottom:16px}}
label{{display:block;font-size:11px;font-weight:700;color:#3a6b35;margin-bottom:7px;text-transform:uppercase;letter-spacing:.5px}}
input{{width:100%;padding:13px 16px;border:2px solid #d4e4d2;border-radius:12px;font-size:15px;font-family:inherit;background:#f9fbf9;transition:border .2s}}
input:focus{{outline:none;border-color:#3a6b35;background:#fff}}
.btn{{width:100%;padding:15px;background:#3a6b35;color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px;font-family:inherit;transition:all .2s}}
.btn:hover{{background:#2a4e26;box-shadow:0 4px 15px rgba(42,78,38,.35)}}
.error{{background:#fdecea;border:1px solid #fadbd8;color:#c0392b;padding:12px 14px;border-radius:10px;font-size:13px;margin-bottom:16px}}
.hint{{background:#f0f5ef;border-radius:10px;padding:11px 14px;font-size:12px;color:#6b7f69;text-align:center;margin-top:18px;line-height:1.5}}
.hint strong{{color:#3a6b35}}
</style></head>
<body>
<div class="card">
  <div class="logo">
    <span class="rose">🌹</span>
    <h1>PRIM'ROSE RH</h1>
    <div class="sub">Tableau de Bord — Azemmour</div>
  </div>
  {err_html}
  <form method="POST" action="/login">
    <input type="hidden" name="redirect" value="{redirect}">
    <div class="field">
      <label>Identifiant</label>
      <input type="text" name="username" placeholder="Votre identifiant" autofocus autocomplete="username">
    </div>
    <div class="field">
      <label>Mot de passe</label>
      <input type="password" name="password" placeholder="Votre mot de passe" autocomplete="current-password">
    </div>
    <button type="submit" class="btn">🔐 Se connecter</button>
  </form>
  <div class="hint">
    Contactez <strong>Madid</strong> pour obtenir<br>vos identifiants de connexion
  </div>
</div>
</body></html>"""
 
# ── ROUTES ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    role = get_role(request)
    if role in ("admin","viewer"):
        return RedirectResponse("/dashboard")
    return HTMLResponse(login_page())
 
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, redirect: str = "/dashboard"):
    if get_role(request) in ("admin","viewer"):
        return RedirectResponse(redirect)
    return HTMLResponse(login_page(redirect=redirect))
 
@app.post("/login")
async def login_post(
    username: str = Form(default=""),
    password: str = Form(default=""),
    redirect: str = Form(default="/dashboard")
):
    u = username.strip()
    p = password.strip()
    # Admin
    if secrets.compare_digest(u, ADMIN_USER) and secrets.compare_digest(p, ADMIN_PASS):
        token = create_session("admin")
        resp = RedirectResponse(redirect, status_code=303)
        resp.set_cookie("session", token, httponly=True, samesite="lax", max_age=86400*30)
        return resp
    # Viewer (n'importe quel nom + bon mot de passe)
    if p == VIEWER_PASS:
        token = create_session("viewer")
        resp = RedirectResponse("/dashboard", status_code=303)
        resp.set_cookie("session", token, httponly=True, samesite="lax", max_age=86400*30)
        return resp
    return HTMLResponse(login_page(error="Identifiant ou mot de passe incorrect", redirect=redirect))
 
@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login")
    resp.delete_cookie("session")
    return resp
 
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    role = get_role(request)
    if role not in ("admin","viewer"):
        return RedirectResponse("/login?redirect=/dashboard")
    if not DATA_FILE.exists():
        return HTMLResponse(no_data_page(role))
    data = json.loads(DATA_FILE.read_text())
    return HTMLResponse(build_dashboard_html(data, role))
 
@app.get("/admin", response_class=HTMLResponse)
async def get_admin(request: Request):
    if get_role(request) != "admin":
        return RedirectResponse("/login?redirect=/admin")
    log = json.loads(UPLOAD_LOG.read_text()) if UPLOAD_LOG.exists() else {}
    return HTMLResponse(get_admin_page(log))
 
@app.post("/upload")
async def upload_files(
    request: Request,
    paie_file: UploadFile = File(...),
    prod_file: UploadFile = File(...),
    quinzaine: str = Form(...),
    campagne:  str = Form(...)
):
    if get_role(request) != "admin":
        return JSONResponse({"error":"Non autorisé"}, status_code=401)
    try:
        paie_path = DATA_DIR / f"paie_{campagne}.xlsx"
        prod_path = DATA_DIR / f"prod_{campagne}.xlsx"
        paie_path.write_bytes(await paie_file.read())
        prod_path.write_bytes(await prod_file.read())
        dashboard_data = process_files(str(paie_path), str(prod_path))
        DATA_FILE.write_text(json.dumps(dashboard_data, ensure_ascii=True))
        log = {"last_upload": datetime.now().strftime("%d/%m/%Y %H:%M"),
               "campagne": campagne, "quinzaine": quinzaine,
               "paie_file": paie_file.filename, "prod_file": prod_file.filename}
        UPLOAD_LOG.write_text(json.dumps(log, ensure_ascii=False))
        return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta http-equiv="refresh" content="2;url=/dashboard">
<title>Mise à jour...</title>
<style>body{{font-family:Arial;background:#f0f5ef;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.box{{background:#fff;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.1);max-width:380px;width:90%}}
h2{{color:#3a6b35;margin:10px 0}}p{{color:#6b7f69}}</style></head>
<body><div class="box">
<div style="font-size:50px">✅</div>
<h2>Dashboard mis à jour !</h2>
<p>{campagne} — {quinzaine}</p>
<p style="font-size:12px;margin-top:10px">Redirection automatique dans 2 secondes...</p>
<a href="/dashboard" style="display:inline-block;margin-top:16px;background:#3a6b35;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700">
Voir le Dashboard →</a>
</div></body></html>""")
    except Exception as e:
        return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Erreur</title>
<style>body{{font-family:Arial;background:#fdecea;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.box{{background:#fff;border-radius:16px;padding:40px;text-align:center;max-width:380px;width:90%}}
h2{{color:#c0392b}}</style></head>
<body><div class="box"><div style="font-size:50px">❌</div>
<h2>Erreur de traitement</h2>
<p style="color:#666;font-size:13px">{str(e)}</p>
<a href="/admin" style="display:inline-block;margin-top:16px;background:#e8a020;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700">
← Réessayer</a></div></body></html>""", status_code=500)
 
@app.get("/health")
async def health():
    lu = None
    if UPLOAD_LOG.exists():
        lu = json.loads(UPLOAD_LOG.read_text()).get("last_update")
    return {"status":"ok","data_ready":DATA_FILE.exists(),"last_update":lu,"version":"2.0.0"}
 
# ── HTML HELPERS ───────────────────────────────────────────────────────────────
def no_data_page(role="viewer"):
    admin_btn = '<a href="/admin" style="background:#e8a020;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:700;display:inline-block;margin:5px">⚙️ Administration</a>' if role=="admin" else ""
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PRIM'ROSE RH</title><style>body{{font-family:Arial;background:#f0f5ef;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.box{{background:#fff;border-radius:16px;padding:40px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.1);max-width:380px;width:90%}}
h2{{color:#3a6b35;margin:12px 0 8px}}p{{color:#6b7f69;margin-bottom:20px}}</style></head>
<body><div class="box"><div style="font-size:50px">📋</div>
<h2>Pas encore de données</h2><p>Uploadez les fichiers Excel BeeOne<br>via la page d'administration.</p>
{admin_btn}
<a href="/logout" style="display:block;margin-top:20px;color:#95a5a6;font-size:12px">Se déconnecter</a>
</div></body></html>"""
 
def get_admin_page(log: dict):
    last = log.get("last_upload","Jamais")
    camp = log.get("campagne","-")
    qu   = log.get("quinzaine","-")
    opts = "".join(f'<option value="Q{i}">Q{i}</option>' for i in range(1,25))
    return f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Admin — PRIM'ROSE RH</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f5ef;min-height:100vh;padding:14px}}
.hdr{{background:#2a4e26;color:#fff;padding:13px 16px;border-radius:14px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between}}
.hdr h1{{font-size:16px;font-weight:700}}.hdr p{{font-size:11px;opacity:.75;margin-top:2px}}
.logout{{color:rgba(255,255,255,.7);font-size:12px;text-decoration:none;padding:5px 12px;border:1px solid rgba(255,255,255,.3);border-radius:20px}}
.card{{background:#fff;border-radius:13px;padding:16px;margin-bottom:13px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.card h2{{color:#2a4e26;font-size:13px;font-weight:700;margin-bottom:11px}}
.info-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}}
.badge{{background:#f0f5ef;border-radius:8px;padding:8px;text-align:center}}
.badge label{{display:block;font-size:9px;color:#6b7f69;text-transform:uppercase;margin-bottom:2px}}
.badge strong{{font-size:13px;color:#2a4e26}}
.field{{margin-bottom:13px}}
.field label{{display:block;font-size:10px;font-weight:700;color:#3a6b35;margin-bottom:5px;text-transform:uppercase}}
select{{width:100%;padding:10px 12px;border:1.5px solid #d4e4d2;border-radius:10px;font-size:14px;font-family:inherit;background:#f9fbf9}}
.zone{{border:2px dashed #d4e4d2;border-radius:11px;padding:16px;text-align:center;position:relative;cursor:pointer;transition:all .2s}}
.zone:hover{{border-color:#3a6b35;background:#f0f5ef}}
.zone input[type=file]{{position:absolute;inset:0;opacity:0;width:100%;height:100%;cursor:pointer}}
.zone .ico{{font-size:26px;margin-bottom:5px}}.zone .lbl{{font-size:12px;color:#6b7f69}}
.zone .fn{{font-size:11px;color:#3a6b35;font-weight:700;margin-top:4px;min-height:14px}}
.btn{{width:100%;padding:14px;background:#3a6b35;color:#fff;border:none;border-radius:11px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;transition:all .2s}}
.btn:hover{{background:#2a4e26}}.btn:disabled{{background:#95a5a6;cursor:not-allowed}}
.prog{{height:5px;background:#e0e0e0;border-radius:3px;margin-top:11px;display:none}}
.bar{{height:100%;background:#3a6b35;border-radius:3px;width:0%;transition:width .3s}}
.msg{{border-radius:9px;padding:11px;font-size:13px;margin-top:11px;display:none}}
.ok{{background:#e8f5e9;color:#1a6b45;border:1px solid #c8e6c9}}
.er{{background:#fdecea;color:#c0392b;border:1px solid #fadbd8}}
.url-box{{background:#f0f5ef;border-radius:8px;padding:9px;font-family:monospace;font-size:11px;word-break:break-all;margin:8px 0}}
.btn-gold{{width:100%;padding:10px;background:#e8a020;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:13px;font-family:inherit}}
</style></head>
<body>
<div class="hdr">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:22px">🌹</span>
    <div><h1>Administration</h1><p>PRIM'ROSE RH</p></div>
  </div>
  <a href="/logout" class="logout">Déconnexion</a>
</div>
 
<div class="card">
  <h2>📊 Dernière mise à jour</h2>
  <div class="info-row">
    <div class="badge"><label>Date</label><strong>{last}</strong></div>
    <div class="badge"><label>Campagne</label><strong>{camp}</strong></div>
    <div class="badge"><label>Quinzaine</label><strong>{qu}</strong></div>
  </div>
</div>
 
<div class="card">
  <h2>⬆️ Mettre à jour</h2>
  <form method="POST" action="/upload" enctype="multipart/form-data">
    <div class="field"><label>Campagne</label>
      <select name="campagne" style="width:100%;padding:10px;border:2px solid #d4e4d2;border-radius:10px;font-size:14px;font-family:inherit;background:#f9fbf9">
        <option value="C2526">C2526 (2025-2026)</option>
        <option value="C2425">C2425 (2024-2025)</option>
      </select>
    </div>
    <div class="field"><label>Quinzaine</label>
      <select name="quinzaine" style="width:100%;padding:10px;border:2px solid #d4e4d2;border-radius:10px;font-size:14px;font-family:inherit;background:#f9fbf9">
        {opts}
      </select>
    </div>
    <div class="field">
      <label>📋 Fichier Paie (BeeOne)</label>
      <input type="file" name="paie_file" required
        style="width:100%;padding:12px;border:2px solid #d4e4d2;border-radius:10px;font-size:13px;background:#fff;font-family:inherit;display:block">
      <div style="font-size:11px;color:#6b7f69;margin-top:4px">Sélectionnez le fichier Excel état de paie</div>
    </div>
    <div class="field">
      <label>🌱 Fichier Production</label>
      <input type="file" name="prod_file" required
        style="width:100%;padding:12px;border:2px solid #d4e4d2;border-radius:10px;font-size:13px;background:#fff;font-family:inherit;display:block">
      <div style="font-size:11px;color:#6b7f69;margin-top:4px">Sélectionnez le fichier Excel production</div>
    </div>
    <button type="submit" class="btn" style="margin-top:8px">🔄 Mettre à jour le Dashboard</button>
  </form>
</div>
 
<div class="card">
  <h2>📱 Lien Dashboard</h2>
  <div class="url-box" id="du"></div>
  <button class="btn-gold" onclick="cp()">📋 Copier et partager</button>
</div>
<p style="text-align:center;margin:14px 0 20px;font-size:11px">
  <a href="/dashboard" style="color:#3a6b35;font-weight:700">← Voir le Dashboard</a>
</p>
 
<script>
function sf(inp,id){{document.getElementById('f'+id).textContent=inp.files[0]?inp.files[0].name:'';inp.closest('.zone').style.borderColor='#3a6b35';}}
document.getElementById('frm').addEventListener('submit',async function(e){{
  e.preventDefault();
  var sb=document.getElementById('sb'),prog=document.getElementById('prog'),bar=document.getElementById('bar'),msg=document.getElementById('msg');
  sb.disabled=true;sb.textContent='⏳ Traitement...';prog.style.display='block';msg.style.display='none';
  var p=0,iv=setInterval(function(){{p=Math.min(p+Math.random()*12,85);bar.style.width=p+'%';}},400);
  try{{
    var r=await fetch('/upload',{{method:'POST',body:new FormData(this)}});
    var d=await r.json();clearInterval(iv);bar.style.width='100%';
    if(r.ok){{msg.className='msg ok';msg.textContent='✅ '+d.message+' — '+d.timestamp;sb.textContent='✅ Mis à jour !';setTimeout(function(){{location.href='/dashboard';}},2000);}}
    else throw new Error(d.error||'Erreur');
  }}catch(err){{clearInterval(iv);msg.className='msg er';msg.textContent='❌ '+err.message;sb.disabled=false;sb.textContent='🔄 Réessayer';}}
  msg.style.display='block';
}});
document.getElementById('du').textContent=location.origin+'/dashboard';
function cp(){{navigator.clipboard.writeText(location.origin+'/dashboard').then(function(){{alert('Lien copié ! Partagez-le avec l\'équipe.');}});}}
</script>
</body></html>"""
 
def build_dashboard_html(data: dict, role: str = "viewer") -> str:
    try:
        template = open("dashboard_template.html", encoding="utf-8").read()
    except:
        return "<h1>Template non trouvé</h1>"
    import re
    data_js = json.dumps(data.get("data", {}), ensure_ascii=True)
    prod_js = json.dumps(data.get("prod", {}), ensure_ascii=True)
    ct_js   = json.dumps(data.get("ct",   {}), ensure_ascii=True)
    result  = re.sub(r'var DATA=\{.*?\};', f'var DATA={data_js};', template, flags=re.DOTALL)
    result  = re.sub(r'var PROD=\{.*?\};', f'var PROD={prod_js};', result,   flags=re.DOTALL)
    result  = re.sub(r'var CT=\{.*?\};',   f'var CT={ct_js};',     result,   flags=re.DOTALL)
    admin_btn = '<a href="/admin" style="background:#e8a020;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;text-decoration:none;font-weight:700">⚙️ Admin</a>' if role=="admin" else ""
    nav = f'<div style="display:flex;align-items:center;gap:8px">{admin_btn}<a href="/logout" style="color:rgba(255,255,255,.7);font-size:11px;text-decoration:none">Déconnexion</a></div>'
    result = result.replace('<span class="hbg" id="hbg">...</span>', f'<span class="hbg" id="hbg">...</span>{nav}', 1)
    return result
 
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)

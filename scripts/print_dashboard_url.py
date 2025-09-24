#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.parse

"""
Lee:
- GRAFANA_URL (p.ej. https://ricardops2211.grafana.net)
- GC_GRAFANA_API_TOKEN (token de Service Account con rol Editor/Admin)
- DASHBOARD_UID (opcional; si se define, se usa directamente)
- DASHBOARD_TITLE (opcional; si no hay UID, se busca por título)
- DASHBOARD_JSON (opcional; si no existe el dashboard, intenta importarlo desde este JSON)
Escribe:
- URL al dashboard en stdout
- (si existe) al resumen del job vía $GITHUB_STEP_SUMMARY
Salida con código !=0 si hay error “real”; si no encuentra, sale 0 pero avisa.
"""

def api_get(path, token):
    req = urllib.request.Request(
        url=base(path),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def api_post(path, token, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=base(path),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def base(path):
    return f"{GRAFANA_URL.rstrip('/')}{path}"

def find_uid_by_title(title, token):
    q = urllib.parse.quote(title)
    items = api_get(f"/api/search?query={q}", token)
    if not items:
        return None
    # Prefer dashboards with exact title and type "dash-db"
    candidates = [i for i in items if i.get("type") in ("dash-db","dash-folder")]
    if not candidates:
        candidates = items
    # Exact match first
    for it in candidates:
        if it.get("title") == title and it.get("uid"):
            return it["uid"]
    # Fallback: take first with uid
    for it in candidates:
        if it.get("uid"):
            return it["uid"]
    return None

def import_dashboard(json_path, token):
    with open(json_path, "r", encoding="utf-8") as f:
        dash = json.load(f)
    # ensure dashboard JSON conforms to API
    payload = {"dashboard": dash, "overwrite": True, "folderId": 0, "message": "CI import"}
    resp = api_post("/api/dashboards/db", token, payload)
    # Grafana API returns object with "uid" inside "slug"/"status" or inside "dashboard"
    uid = None
    if isinstance(resp, dict):
        if "uid" in resp:
            uid = resp["uid"]
        elif "dashboard" in resp and isinstance(resp["dashboard"], dict):
            uid = resp["dashboard"].get("uid")
    return uid

def write_summary(lines):
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    with open(summary, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    GRAFANA_URL = os.environ.get("GRAFANA_URL", "").strip()
    TOKEN = os.environ.get("GC_GRAFANA_API_TOKEN", "").strip()
    DASHBOARD_UID = os.environ.get("DASHBOARD_UID", "").strip()
    DASHBOARD_TITLE = os.environ.get("DASHBOARD_TITLE", "").strip()
    DASHBOARD_JSON = os.environ.get("DASHBOARD_JSON", "").strip()

    if not GRAFANA_URL or not TOKEN:
        print("ERROR: GRAFANA_URL o GC_GRAFANA_API_TOKEN vacíos.", file=sys.stderr)
        sys.exit(1)

    uid = None

    # 1) si hay UID fijo, úsalo
    if DASHBOARD_UID:
        uid = DASHBOARD_UID

    # 2) si no hay UID, busca por título
    if not uid and DASHBOARD_TITLE:
        try:
            uid = find_uid_by_title(DASHBOARD_TITLE, TOKEN)
        except Exception as e:
            print(f"WARNING: fallo buscando por título: {e}", file=sys.stderr)

    # 3) si no hay y hay JSON, intenta importarlo
    if not uid and DASHBOARD_JSON:
        if not os.path.isfile(DASHBOARD_JSON):
            print(f"WARNING: no existe DASHBOARD_JSON en ruta: {DASHBOARD_JSON}", file=sys.stderr)
        else:
            try:
                uid = import_dashboard(DASHBOARD_JSON, TOKEN)
                if not uid:
                    print("WARNING: import realizado pero no retornó UID.", file=sys.stderr)
            except Exception as e:
                print(f"WARNING: fallo importando dashboard: {e}", file=sys.stderr)

    if not uid:
        msg = "No se encontró/importó el dashboard (sin UID). Revisa título/JSON."
        print(msg)
        write_summary([f"### Dashboard", msg])
        sys.exit(0)  # no fallamos el pipeline, solo avisamos

    url = f"{GRAFANA_URL.rstrip('/')}/d/{uid}"
    print(url)
    write_summary([
        "## Dashboard",
        f"- URL: {url}",
        f"- Explore: {GRAFANA_URL.rstrip('/')}/explore",
    ])

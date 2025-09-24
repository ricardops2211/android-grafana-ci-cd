#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.parse

GRAFANA_URL = os.environ.get("GRAFANA_URL","").rstrip("/")
TOKEN = os.environ.get("GC_GRAFANA_API_TOKEN","").strip()
UID = os.environ.get("DASHBOARD_UID","").strip()          # ej: sre-mttr-lab
TITLE = os.environ.get("DASHBOARD_TITLE","").strip()      # ej: SRE MTTR Lab
JSON_PATH = os.environ.get("DASHBOARD_JSON","").strip()   # ej: dashboards/mttr_grafana.json

def req(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    r = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        data=data, method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(r) as resp:
        txt = resp.read().decode()
        return json.loads(txt) if txt else {}

def find_uid():
    # Si ya tienes UID fijo, intenta primero leerlo
    if UID:
        try:
            _ = req("GET", f"/api/dashboards/uid/{UID}")
            return UID
        except Exception:
            pass
    # Busca por título
    if TITLE:
        q = urllib.parse.quote(TITLE)
        try:
            items = req("GET", f"/api/search?query={q}")
            for it in items or []:
                if it.get("uid") and it.get("title") == TITLE:
                    return it["uid"]
            # fallback: primero con uid
            for it in items or []:
                if it.get("uid"):
                    return it["uid"]
        except Exception:
            pass
    return None

def import_from_json():
    if not JSON_PATH or not os.path.isfile(JSON_PATH):
        return None
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        dash = json.load(f)
    payload = {"dashboard": dash, "overwrite": True, "folderId": 0, "message": "CI import"}
    resp = req("POST", "/api/dashboards/db", payload)
    # El UID puede venir en resp["uid"] o en resp["dashboard"]["uid"]
    if isinstance(resp, dict):
        if "uid" in resp: return resp["uid"]
        if isinstance(resp.get("dashboard"), dict) and resp["dashboard"].get("uid"):
            return resp["dashboard"]["uid"]
    return dash.get("uid")

def main():
    if not GRAFANA_URL or not TOKEN:
        print("ERROR: Define GRAFANA_URL y GC_GRAFANA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    uid = find_uid()
    if not uid:
        uid = import_from_json()
        if uid:
            # confirmar que existe
            try:
                _ = req("GET", f"/api/dashboards/uid/{uid}")
            except Exception:
                pass
    if not uid:
        print("Dashboard no encontrado ni importado. Revisa TITLE/UID/JSON.", file=sys.stderr)
        print("TIP: usa un UID fijo en tu JSON (ej: 'uid': 'sre-mttr-lab').")
        sys.exit(0)

    url = f"{GRAFANA_URL}/d/{uid}"
    print(url)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as s:
            s.write("## Dashboard\n")
            s.write(f"- URL: {url}\n")
            s.write(f"- Explore: {GRAFANA_URL}/explore\n")

if __name__ == "__main__":
    main()

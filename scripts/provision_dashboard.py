#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.parse

GRAFANA_URL = os.environ.get("GRAFANA_URL","").rstrip("/")
TOKEN = os.environ.get("GC_GRAFANA_API_TOKEN","").strip()
JSON_PATH = os.environ.get("DASHBOARD_JSON","dashboards/mttr_grafana.json")
DASHBOARD_UID = os.environ.get("DASHBOARD_UID","sre-mttr-lab").strip()
DASHBOARD_TITLE = os.environ.get("DASHBOARD_TITLE","SRE MTTR Lab").strip()
LOKI_DS_NAME = os.environ.get("LOKI_DS_NAME","").strip()  # opcional: nombre del datasource Loki (ej. "grafanacloud-<stack>-logs")
LOKI_DS_UID  = os.environ.get("LOKI_DS_UID","").strip()   # opcional: UID del datasource Loki (si ya lo sabes)

def _req(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    r = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        data=data, method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(r) as resp:
        txt = resp.read().decode()
        return json.loads(txt) if txt else {}

def _find_dashboard_uid_by_uid(uid: str):
    try:
        _ = _req("GET", f"/api/dashboards/uid/{uid}")
        return uid
    except Exception:
        return None

def _find_dashboard_uid_by_title(title: str):
    q = urllib.parse.quote(title)
    try:
        items = _req("GET", f"/api/search?query={q}")
    except Exception:
        return None
    for it in items or []:
        if it.get("title")==title and it.get("uid"):
            return it["uid"]
    for it in items or []:
        if it.get("uid"):
            return it["uid"]
    return None

def _get_loki_uid_by_name(name: str):
    # Busca datasources y devuelve el UID del Loki que tenga ese "name"
    try:
        ds = _req("GET", "/api/datasources")
    except Exception:
        return None
    for d in ds or []:
        if d.get("type")=="loki" and d.get("name")==name and d.get("uid"):
            return d["uid"]
    return None

def _get_first_loki_uid():
    try:
        ds = _req("GET", "/api/datasources")
    except Exception:
        return None
    for d in ds or []:
        if d.get("type")=="loki" and d.get("uid"):
            return d["uid"]
    return None

def _patch_dashboard_datasources(dash: dict, loki_uid: str):
    # Recorre targets y pone {"type":"loki","uid":<loki_uid>}
    def patch_targets(p):
        if "targets" in p and isinstance(p["targets"], list):
            for t in p["targets"]:
                ds = t.get("datasource")
                if isinstance(ds, dict):
                    if ds.get("type")=="loki":
                        ds["uid"]=loki_uid
                elif ds is None:
                    t["datasource"] = {"type":"loki", "uid": loki_uid}
        return p

    # Panels
    for p in dash.get("panels", []):
        patch_targets(p)
        # nested panels (rows)
        if "panels" in p and isinstance(p["panels"], list):
            for sp in p["panels"]:
                patch_targets(sp)

    # Templating (si existiera)
    templ = dash.get("templating", {}).get("list", [])
    for v in templ:
        ds = v.get("datasource")
        if isinstance(ds, dict) and ds.get("type")=="loki":
            ds["uid"] = loki_uid

    return dash

def _import_dashboard(dash: dict):
    payload = {"dashboard": dash, "overwrite": True, "folderId": 0, "message": "CI import"}
    resp = _req("POST", "/api/dashboards/db", payload)
    # UID puede venir en distintos campos
    if isinstance(resp, dict):
        if resp.get("uid"):
            return resp["uid"]
        db = resp.get("dashboard")
        if isinstance(db, dict) and db.get("uid"):
            return db["uid"]
    return dash.get("uid")

def main():
    if not GRAFANA_URL or not TOKEN:
        print("ERROR: Define GRAFANA_URL y GC_GRAFANA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    # 1) si ya existe el dashboard por UID/título, úsalo
    uid = _find_dashboard_uid_by_uid(DASHBOARD_UID) or _find_dashboard_uid_by_title(DASHBOARD_TITLE)

    # 2) si no existe, importa desde JSON (opcionalmente mapeando datasource)
    if not uid:
        if not os.path.isfile(JSON_PATH):
            print(f"WARNING: no existe {JSON_PATH}. No se puede importar.", file=sys.stderr)
        else:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                dash = json.load(f)

            # asegura un UID fijo
            dash["uid"] = dash.get("uid") or DASHBOARD_UID
            dash["title"] = dash.get("title") or DASHBOARD_TITLE

            # resolver UID de Loki
            loki_uid = LOKI_DS_UID
            if not loki_uid and LOKI_DS_NAME:
                loki_uid = _get_loki_uid_by_name(LOKI_DS_NAME)
            if not loki_uid:
                loki_uid = _get_first_loki_uid()

            if loki_uid:
                dash = _patch_dashboard_datasources(dash, loki_uid)

            # importar
            uid = _import_dashboard(dash)

    if not uid:
        print("Dashboard no encontrado ni importado. Revisa JSON/título/UID.", file=sys.stderr)
        sys.exit(0)

    url = f"{GRAFANA_URL}/d/{uid}"
    print(url)
    # summary del job
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as s:
            s.write("## Dashboard\n")
            s.write(f"- URL: {url}\n")
            s.write(f"- Explore: {GRAFANA_URL}/explore\n")

if __name__ == "__main__":
    main()

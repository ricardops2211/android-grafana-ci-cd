#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.parse

# ======== ENV ========
GRAFANA_URL = os.environ.get("GRAFANA_URL", "").rstrip("/")
TOKEN       = os.environ.get("GC_GRAFANA_API_TOKEN", "").strip()

DASH_UID    = os.environ.get("DASHBOARD_UID", "").strip()       # ej: "sre-mttr-lab"
DASH_TITLE  = os.environ.get("DASHBOARD_TITLE", "").strip()     # ej: "SRE MTTR Lab"

LOKI_DS_NAME= os.environ.get("LOKI_DS_NAME", "").strip()        # ej: "grafanacloud-ricardops2211-logs"
LOKI_DS_UID = os.environ.get("LOKI_DS_UID", "").strip()         # si ya lo sabes

# Filtros opcionales para tus labels (para alinear con lo que empujas)
LABEL_APP   = os.environ.get("LABEL_APP", "").strip()           # ej: "podinfo" (o vacío)
LABEL_ENV   = os.environ.get("LABEL_ENV", "").strip()           # ej: "ci" (o vacío)

# Rango por defecto del dashboard
DEFAULT_FROM= os.environ.get("DEFAULT_FROM", "now-24h")
DEFAULT_TO  = os.environ.get("DEFAULT_TO", "now")

# ======== HTTP helpers ========
def _req(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    r = urllib.request.Request(
        f"{GRAFANA_URL}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(r) as resp:
        txt = resp.read().decode() or ""
        return json.loads(txt) if txt else {}

def _get_json(path):
    return _req("GET", path)

def _post_json(path, payload):
    return _req("POST", path, payload)

# ======== Grafana helpers ========
def find_dashboard():
    # try by UID
    if DASH_UID:
        try:
            resp = _get_json(f"/api/dashboards/uid/{DASH_UID}")
            return resp.get("dashboard"), resp
        except Exception:
            pass
    # try by title
    if DASH_TITLE:
        q = urllib.parse.quote(DASH_TITLE)
        try:
            items = _get_json(f"/api/search?query={q}")
            for it in items or []:
                if it.get("uid") and it.get("title") == DASH_TITLE:
                    resp = _get_json(f"/api/dashboards/uid/{it['uid']}")
                    return resp.get("dashboard"), resp
            # fallback
            for it in items or []:
                if it.get("uid"):
                    resp = _get_json(f"/api/dashboards/uid/{it['uid']}")
                    return resp.get("dashboard"), resp
        except Exception:
            pass
    return None, None

def get_loki_uid():
    # If provided explicitly
    if LOKI_DS_UID:
        return LOKI_DS_UID
    # Search by name
    try:
        dses = _get_json("/api/datasources")
        if LOKI_DS_NAME:
            for d in dses or []:
                if d.get("type") == "loki" and d.get("name") == LOKI_DS_NAME and d.get("uid"):
                    return d["uid"]
        # fallback: first loki
        for d in dses or []:
            if d.get("type") == "loki" and d.get("uid"):
                return d["uid"]
    except Exception:
        pass
    return None

# ======== Patching dashboard ========
def selector_for_mttr():
    # Always include metric="mttr"; optionally app/env labels
    parts = ['metric="mttr"']
    if LABEL_APP:
        parts.append(f'app="{LABEL_APP}"')
    if LABEL_ENV:
        parts.append(f'env="{LABEL_ENV}"')
    return "{" + ", ".join(parts) + "}"

# Queries robustas
def q_stat_last_min():
    return f'max_over_time(( {selector_for_mttr()} | json | unwrap mttr_seconds )[1h]) / 60'

def q_timeseries_min():
    return f'( {selector_for_mttr()} | json | unwrap mttr_seconds ) / 60'

def q_pie_env():
    # si no hay env, esto seguirá funcionando pero habrá una sola serie
    return f'sum by (env) ( count_over_time({selector_for_mttr()}[24h]) )'

def q_logs():
    return selector_for_mttr()

def patch_datasource_uid(target, loki_uid):
    ds = target.get("datasource")
    if ds is None:
        target["datasource"] = {"type": "loki", "uid": loki_uid}
    elif isinstance(ds, dict):
        if ds.get("type") == "loki":
            target["datasource"]["uid"] = loki_uid
        else:
            # fuerza a loki si es un placeholder
            target["datasource"] = {"type": "loki", "uid": loki_uid}
    else:
        # string legacy -> reemplaza por dict
        target["datasource"] = {"type": "loki", "uid": loki_uid}

def normalize_expr(panel):
    """Si el panel parece ser de MTTR, ajusta a las expresiones robustas."""
    t = (panel.get("type") or "").lower()
    title = (panel.get("title") or "").lower()
    # Define destino según tipo/título
    if "stat" in t and "mttr" in title:
        return q_stat_last_min()
    if ("timeseries" in t or "graph" in t) and "mttr" in title:
        return q_timeseries_min()
    if "pie" in t and ("incidente" in title or "env" in title or "pie" in title):
        return q_pie_env()
    if "logs" in t:
        return q_logs()
    # Si no reconoce, no toca
    return None

def patch_panels(dash, loki_uid):
    def patch_panel(p):
        # targets
        if isinstance(p.get("targets"), list) and p["targets"]:
            # si reconocemos el panel, reescribimos expr
            new_expr = normalize_expr(p)
            for tgt in p["targets"]:
                patch_datasource_uid(tgt, loki_uid)
                if new_expr:
                    tgt["expr"] = new_expr
        # nested
        if isinstance(p.get("panels"), list):
            for child in p["panels"]:
                patch_panel(child)

    for p in dash.get("panels", []):
        patch_panel(p)

    # templating (si lo hay)
    templ = dash.get("templating", {}).get("list", [])
    for v in templ:
        ds = v.get("datasource")
        if isinstance(ds, dict) and ds.get("type") == "loki":
            ds["uid"] = loki_uid

    # rango por defecto
    dash["time"] = {"from": DEFAULT_FROM, "to": DEFAULT_TO}
    return dash

def save_dashboard(dash):
    payload = {"dashboard": dash, "overwrite": True, "folderId": 0, "message": "CI auto-adjust"}
    return _post_json("/api/dashboards/db", payload)

# ======== Main ========
def main():
    if not GRAFANA_URL or not TOKEN:
        print("ERROR: Define GRAFANA_URL y GC_GRAFANA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    dash, raw = find_dashboard()
    if not dash:
        print("WARNING: Dashboard no encontrado por UID/Título. ¿Ya lo importaste?", file=sys.stderr)
        sys.exit(0)

    loki_uid = get_loki_uid()
    if not loki_uid:
        print("WARNING: No encontré datasource Loki en la instancia. Crea uno primero.", file=sys.stderr)
        sys.exit(0)

    # Asegura UID/título presentes
    if not dash.get("uid") and DASH_UID:
        dash["uid"] = DASH_UID
    if not dash.get("title") and DASH_TITLE:
        dash["title"] = DASH_TITLE

    dash = patch_panels(dash, loki_uid)
    resp = save_dashboard(dash)

    # URL final
    uid = (dash.get("uid")
           or (resp.get("dashboard") or {}).get("uid")
           or resp.get("uid")
           or DASH_UID)
    url = f"{GRAFANA_URL}/d/{uid}?from={urllib.parse.quote(DEFAULT_FROM)}&to={urllib.parse.quote(DEFAULT_TO)}"
    print(url)

    # Summary
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as s:
            s.write("## Dashboard ajustado\n")
            s.write(f"- URL: {url}\n")

if __name__ == "__main__":
    main()

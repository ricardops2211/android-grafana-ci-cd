#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.parse

GRAFANA_URL = os.environ.get("GRAFANA_URL","").rstrip("/")
TOKEN       = os.environ.get("GC_GRAFANA_API_TOKEN","").strip()
DASH_UID    = os.environ.get("DASHBOARD_UID","sre-mttr-lab").strip()
DASH_TITLE  = os.environ.get("DASHBOARD_TITLE","SRE MTTR Lab").strip()
LOKI_DS_NAME= os.environ.get("LOKI_DS_NAME","").strip()  # ej: grafanacloud-ricardops2211-logs

LABEL_APP   = os.environ.get("LABEL_APP","").strip()     # ej: podinfo
LABEL_ENV   = os.environ.get("LABEL_ENV","").strip()     # ej: ci

DEFAULT_FROM= os.environ.get("DEFAULT_FROM","now-24h")
DEFAULT_TO  = os.environ.get("DEFAULT_TO","now")

def req(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    r = urllib.request.Request(
        f"{GRAFANA_URL}{path}", data=data, method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    with urllib.request.urlopen(r) as resp:
        txt = resp.read().decode() or ""
        return json.loads(txt) if txt else {}

def get(path): return req("GET", path)
def post(path,p): return req("POST", path, p)

def find_dash():
    # por UID
    if DASH_UID:
        try: return get(f"/api/dashboards/uid/{DASH_UID}")["dashboard"]
        except Exception: pass
    # por título
    if DASH_TITLE:
        q = urllib.parse.quote(DASH_TITLE)
        try:
            items = get(f"/api/search?query={q}")
            for it in items or []:
                if it.get("title")==DASH_TITLE and it.get("uid"):
                    return get(f"/api/dashboards/uid/{it['uid']}")["dashboard"]
            for it in items or []:
                if it.get("uid"):
                    return get(f"/api/dashboards/uid/{it['uid']}")["dashboard"]
        except Exception:
            pass
    return None

def loki_uid():
    ds = get("/api/datasources")
    if LOKI_DS_NAME:
        for d in ds:
            if d.get("type")=="loki" and d.get("name")==LOKI_DS_NAME and d.get("uid"):
                return d["uid"]
    for d in ds:
        if d.get("type")=="loki" and d.get("uid"):
            return d["uid"]
    return None

def mttr_selector():
    parts = ['metric="mttr"']
    if LABEL_APP: parts.append(f'app="{LABEL_APP}"')
    if LABEL_ENV: parts.append(f'env="{LABEL_ENV}"')
    return "{"+", ".join(parts)+"}"

def q_stat():       return f'max_over_time(( {mttr_selector()} | json | unwrap mttr_seconds )[1h]) / 60'
def q_timeseries(): return f'( {mttr_selector()} | json | unwrap mttr_seconds ) / 60'
def q_pie():        return f'sum by (env) ( count_over_time({mttr_selector()}[24h]) )'
def q_logs():       return mttr_selector()

def patch_ds(target, uid):
    ds = target.get("datasource")
    if ds is None or not isinstance(ds, dict) or ds.get("type")!="loki":
        target["datasource"] = {"type":"loki","uid":uid}
    else:
        target["datasource"]["uid"] = uid

def normalize_expr(panel):
    t = (panel.get("type") or "").lower()
    title = (panel.get("title") or "").lower()
    if "stat" in t and "mttr" in title: return q_stat()
    if ("timeseries" in t or "graph" in t) and "mttr" in title: return q_timeseries()
    if "pie" in t and ("env" in title or "incidente" in title or "pie" in title): return q_pie()
    if "logs" in t: return q_logs()
    return None

def patch_panels(dash, loki):
    changed = False
    def walk(p):
        nonlocal changed
        if isinstance(p.get("targets"), list) and p["targets"]:
            new_expr = normalize_expr(p)
            for tgt in p["targets"]:
                before = json.dumps(tgt.get("datasource",{}), sort_keys=True)
                patch_ds(tgt, loki)
                if new_expr: tgt["expr"] = new_expr
                after = json.dumps(tgt.get("datasource",{}), sort_keys=True)
                if before != after or new_expr: changed = True
        for child in p.get("panels",[]) or []: walk(child)
    for pnl in dash.get("panels",[]) or []: walk(pnl)
    dash["time"] = {"from": DEFAULT_FROM, "to": DEFAULT_TO}
    return changed, dash

def save_dash(dash):
    payload = {"dashboard": dash, "overwrite": True, "folderId": 0, "message":"CI auto-fix"}
    return post("/api/dashboards/db", payload)

def main():
    if not GRAFANA_URL or not TOKEN:
        print("ERROR: GRAFANA_URL o GC_GRAFANA_API_TOKEN vacíos.", file=sys.stderr); sys.exit(1)

    dash = find_dash()
    if not dash:
        print("WARNING: Dashboard no encontrado (UID/Título). ¿Lo importaste?", file=sys.stderr); sys.exit(0)

    loki = loki_uid()
    if not loki:
        print("WARNING: No hay datasource Loki en la instancia.", file=sys.stderr); sys.exit(0)

    # Log de diagnóstico
    print("🧭 Paneles y queries actuales:")
    for p in dash.get("panels",[]) or []:
        t = p.get("type"); title = p.get("title"); tgts = p.get("targets") or []
        if tgts:
            for i,tg in enumerate(tgts):
                print(f"- {t} :: {title} :: ds={tg.get('datasource')} :: expr={tg.get('expr')}")

    changed, patched = patch_panels(dash, loki)
    if not changed:
        print("ℹ️ Dashboard ya tenía datasource Loki y queries compatibles.")
    resp = save_dash(patched)

    uid = patched.get("uid") or resp.get("uid") or (resp.get("dashboard") or {}).get("uid") or DASH_UID
    url = f"{GRAFANA_URL}/d/{uid}?from={urllib.parse.quote(DEFAULT_FROM)}&to={urllib.parse.quote(DEFAULT_TO)}"
    print(url)

    # summary
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ,"a",encoding="utf-8") as f:
            f.write("## Dashboard (diagnosticado y ajustado)\n")
            f.write(f"- URL: {url}\n")

if __name__=="__main__":
    main()

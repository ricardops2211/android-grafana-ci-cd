#!/usr/bin/env bash
# Simula un incidente MTTR en K8s (escala a 0 y reescala), mide MTTR y publica en Loki (Grafana Cloud)
# Requisitos env:
#   KUBECONFIG (opcional si ya está en contexto)
#   GC_LOKI_URL, GC_LOKI_USERNAME, GC_LOKI_PASSWORD

set -euo pipefail

: "${GC_LOKI_URL:?Falta GC_LOKI_URL}"
: "${GC_LOKI_USERNAME:?Falta GC_LOKI_USERNAME}"
: "${GC_LOKI_PASSWORD:?Falta GC_LOKI_PASSWORD}"

NS="${NS:-demo-app}"
DEPLOY="${DEPLOY:-podinfo}"
SLEEP_DOWN="${SLEEP_DOWN:-90}"        # tiempo que dejamos "caída" la app
ENV_LABEL="${ENV_LABEL:-ci}"
APP_LABEL="${APP_LABEL:-podinfo}"
SEVERITY="${SEVERITY:-sev2}"
SERVICE="${SERVICE:-checkout}"        # un nombre de servicio arbitrario para el ejemplo
REGION="${REGION:-us-west-2}"
CLUSTER="${CLUSTER:-kind-sre-mttr}"

echo "📌 Inicio incidente en $NS/$DEPLOY (app=$APP_LABEL env=$ENV_LABEL sev=$SEVERITY)"

START_S=$(date +%s)
INC_ID="inc-${START_S}"
START_MS=$((START_S*1000))

kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=0
sleep "$SLEEP_DOWN"
kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=2
kubectl -n "$NS" rollout status deploy/"$DEPLOY" --timeout=5m

END_S=$(date +%s)
END_MS=$((END_S*1000))
MTTR_SEC=$((END_S-START_S)); (( MTTR_SEC<0 )) && MTTR_SEC=0

echo "✅ Restaurado. MTTR=${MTTR_SEC}s (id=$INC_ID)"

# ---------- Publicar 3 eventos en Loki: start, restore y resumen ----------
TS_NS_NOW="$(date +%s%N)"

# 1) Evento de "start"
LINE_START=$(jq -c -n \
  --arg id "$INC_ID" --arg app "$APP_LABEL" --arg env "$ENV_LABEL" \
  --arg sev "$SEVERITY" --arg svc "$SERVICE" --arg reg "$REGION" --arg clu "$CLUSTER" \
  --arg msg "incident_start" \
  --argjson start_ms "$START_MS" \
  '{kind:"mttr", phase:$msg, incident_id:$id, app:$app, env:$env, severity:$sev,
    service:$svc, region:$reg, cluster:$clu, start_ms:$start_ms}')

# 2) Evento de "restore"
LINE_RESTORE=$(jq -c -n \
  --arg id "$INC_ID" --arg app "$APP_LABEL" --arg env "$ENV_LABEL" \
  --arg sev "$SEVERITY" --arg svc "$SERVICE" --arg reg "$REGION" --arg clu "$CLUSTER" \
  --arg msg "incident_restored" \
  --argjson end_ms "$END_MS" \
  '{kind:"mttr", phase:$msg, incident_id:$id, app:$app, env:$env, severity:$sev,
    service:$svc, region:$reg, cluster:$clu, end_ms:$end_ms, restored:true}')

# 3) Evento "summary" con todo junto
LINE_SUMMARY=$(jq -c -n \
  --arg id "$INC_ID" --arg app "$APP_LABEL" --arg env "$ENV_LABEL" \
  --arg sev "$SEVERITY" --arg svc "$SERVICE" --arg reg "$REGION" --arg clu "$CLUSTER" \
  --arg msg "incident_summary" \
  --argjson start_ms "$START_MS" --argjson end_ms "$END_MS" --argjson mttr "$MTTR_SEC" \
  --arg sla "99.9" \
  --arg owner "sre" \
  '{kind:"mttr", phase:$msg, incident_id:$id, app:$app, env:$env, severity:$sev,
    service:$svc, region:$reg, cluster:$clu,
    start_ms:$start_ms, end_ms:$end_ms, mttr_seconds:$mttr,
    sla_target_percent:$sla, owner_team:$owner,
    message:"MTTR (Kind→Grafana Cloud)"
  }')

# Labels del stream (para filtros rápidos en LogQL)
STREAM_LABELS=$(jq -n -c --arg app "$APP_LABEL" --arg env "$ENV_LABEL" \
  --arg sev "$SEVERITY" --arg reg "$REGION" --arg clu "$CLUSTER" \
  '{metric:"mttr", app:$app, env:$env, severity:$sev, region:$reg, cluster:$clu}')

PAYLOAD=$(jq -nc --arg ts "$TS_NS_NOW" \
  --arg l1 "$LINE_START" --arg l2 "$LINE_RESTORE" --arg l3 "$LINE_SUMMARY" \
  --argjson lbl "$STREAM_LABELS" '
  { streams: [
      { stream: $lbl, values: [ [$ts, $l1] ] },
      { stream: $lbl, values: [ [$ts, $l2] ] },
      { stream: $lbl, values: [ [$ts, $l3] ] }
    ]
  }')

RESP=$(curl -sS -w "\n%{http_code}" \
  -u "${GC_LOKI_USERNAME}:${GC_LOKI_PASSWORD}" \
  -H "Content-Type: application/json" \
  -X POST "${GC_LOKI_URL}" \
  --data-raw "$PAYLOAD")

BODY=$(echo "$RESP" | head -n-1); CODE=$(echo "$RESP" | tail -n1)
echo "HTTP_CODE=$CODE"; [[ -n "$BODY" ]] && echo "RESP_BODY=$BODY"
test "$CODE" = "204" -o "$CODE" = "200" || { echo "::error::Push a Loki falló"; exit 1; }

echo "✅ Publicados eventos MTTR en Loki:"
echo "   • incident_start  • incident_restored  • incident_summary"
echo "   -> labels: $(echo "$STREAM_LABELS" | jq -c '.')"
echo "   -> id: $INC_ID  mttr_seconds: $MTTR_SEC"

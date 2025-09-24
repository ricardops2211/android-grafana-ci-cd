#!/usr/bin/env bash
set -euo pipefail

START_FILE="/tmp/incident_start"
[[ -f "$START_FILE" ]] || date +%s > "$START_FILE"
START=$(cat "$START_FILE")

# el incidente se resuelve al terminar incident_inject.sh (rollout OK):
END=$(date +%s)
MTTR_SEC=$((END - START)); (( MTTR_SEC < 0 )) && MTTR_SEC=0

echo "📏 MTTR medido: ${MTTR_SEC}s"

TS_NS=$(($(date +%s%N)))
LOG_LINE=$(jq -nc --argjson mttr "$MTTR_SEC" \
  '{"mttr_seconds":$mttr, "message":"MTTR (runner→Grafana Cloud)", "incidents_resolved":1}')

# Push a Loki Cloud (Basic Auth con tenant y token)
curl -sS -u "${GC_LOKI_USERNAME}:${GC_LOKI_PASSWORD}" \
  -H "Content-Type: application/json" \
  -X POST "${GC_LOKI_URL}" \
  --data "{\"streams\":[{\"stream\":{\"app\":\"podinfo\",\"metric\":\"mttr\"},\"values\":[[\"${TS_NS}\",\"${LOG_LINE}\"]]}]}" \
  >/dev/null || true

echo "✅ MTTR enviado a Grafana Cloud Loki."

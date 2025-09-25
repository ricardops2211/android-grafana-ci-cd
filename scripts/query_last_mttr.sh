#!/usr/bin/env bash
# Lee el último evento MTTR desde Grafana Cloud Loki y lo imprime (JSON del log).
# Requisitos env:
#   GC_LOKI_URL, GC_LOKI_USERNAME, GC_LOKI_PASSWORD
# Opcionales (para filtrar):
#   Q_LABELS   -> default: {metric="mttr",app="podinfo",env="ci"}
#   WINDOW_H   -> rango de búsqueda en horas (default: 2)

set -euo pipefail

: "${GC_LOKI_URL:?Falta GC_LOKI_URL}"
: "${GC_LOKI_USERNAME:?Falta GC_LOKI_USERNAME}"
: "${GC_LOKI_PASSWORD:?Falta GC_LOKI_PASSWORD}"

Q_LABELS="${Q_LABELS:-{metric=\"mttr\",app=\"podinfo\",env=\"ci\"}}"
WINDOW_H="${WINDOW_H:-2}"

NOW_MS=$(($(date +%s%N)/1000000))
FROM_MS=$((NOW_MS - WINDOW_H*60*60*1000))

# Construir consulta Loki (range) y URL-encode con jq
QUERY="${Q_LABELS} | json"
Q_ENC=$(printf '%s' "$QUERY" | jq -sRr @uri)

BASE="${GC_LOKI_URL%/loki/api/v1/push}"
URL="${BASE}/loki/api/v1/query_range?query=${Q_ENC}&start=${FROM_MS}000000&end=${NOW_MS}000000&limit=1&direction=backward"

echo "🔎 GET $URL" >&2
curl -sS -u "${GC_LOKI_USERNAME}:${GC_LOKI_PASSWORD}" "$URL" \
| jq -r 'if (.data.result | length)==0 then "NO_ROWS" else .data.result[0].values[0][1] end'

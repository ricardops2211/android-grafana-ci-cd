#!/usr/bin/env bash
set -euo pipefail

NS="demo-app"
DEPLOY="podinfo"

echo "🔧 Inyectando incidente: reduciendo replicas a 0..."
kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=0

echo "⏳ Esperando a que Prometheus dispare la alerta (PodinfoDown)..."
# Simple espera; para labs es suficiente (la alerta tiene for: 1m)
sleep 90

echo "🩹 Restaurando servicio: subiendo replicas a 2..."
kubectl -n "$NS" scale deploy "$DEPLOY" --replicas=2

echo "⏳ Esperando a que las réplicas estén listas..."
kubectl -n "$NS" rollout status deploy/"$DEPLOY" --timeout=5m

echo "✅ Incidente inyectado y resuelto."

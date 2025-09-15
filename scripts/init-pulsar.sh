# #!/bin/bash

# # Script para inicializar Pulsar con los topics necesarios para Campaign Management

# echo "Esperando a que Pulsar esté disponible..."
# sleep 30

# # Crear tenant y namespace
# pulsar-admin tenants create campaign-management || echo "Tenant ya existe"
# pulsar-admin namespaces create campaign-management/events || echo "Namespace ya existe"

# # Crear topics para eventos de campañas
# pulsar-admin topics create persistent://campaign-management/events/campaign-events || echo "Topic campaign-events ya existe"

# echo "Inicialización de Pulsar completada para Campaign Management"



#!/usr/bin/env sh
set -euo pipefail

ADMIN_BIN="/pulsar/bin/pulsar-admin"
ADMIN_URL="${PULSAR_ADMIN_URL:-http://pulsar:8080}"

echo "[init-pulsar] Esperando broker en ${ADMIN_URL}..."
# Espera activa al health del broker (mucho más fiable que sleep fijo)
until curl -sf "${ADMIN_URL}/admin/v2/brokers/health" >/dev/null; do
  sleep 2
done
echo "[init-pulsar] Broker OK"

TENANT="campaign-management"
NAMESPACE="${TENANT}/events"
TOPIC_FQN="persistent://${NAMESPACE}/campaign-events"

# 1) Tenant (con allowed-clusters=standalone)
if ! ${ADMIN_BIN} --admin-url "${ADMIN_URL}" tenants list | grep -qx "${TENANT}"; then
  echo "[init-pulsar] Creando tenant ${TENANT}"
  ${ADMIN_BIN} --admin-url "${ADMIN_URL}" tenants create "${TENANT}" --allowed-clusters standalone
else
  echo "[init-pulsar] Tenant ${TENANT} ya existe"
fi

# 2) Namespace
if ! ${ADMIN_BIN} --admin-url "${ADMIN_URL}" namespaces list "${TENANT}" | grep -qx "${NAMESPACE}"; then
  echo "[init-pulsar] Creando namespace ${NAMESPACE}"
  ${ADMIN_BIN} --admin-url "${ADMIN_URL}" namespaces create "${NAMESPACE}"
else
  echo "[init-pulsar] Namespace ${NAMESPACE} ya existe"
fi

# (Opcional) retención razonable para dev
${ADMIN_BIN} --admin-url "${ADMIN_URL}" namespaces set-retention "${NAMESPACE}" --size 1G --time 3d || true

# 3) Topic (no particionado). Pulsar los crea “perezosamente”, pero lo forzamos para verificar.
if ! ${ADMIN_BIN} --admin-url "${ADMIN_URL}" topics list "${NAMESPACE}" | grep -qx "${TOPIC_FQN}"; then
  echo "[init-pulsar] Creando topic ${TOPIC_FQN}"
  ${ADMIN_BIN} --admin-url "${ADMIN_URL}" topics create "${TOPIC_FQN}"
else
  echo "[init-pulsar] Topic ${TOPIC_FQN} ya existe"
fi

echo "[init-pulsar] OK: ${TOPIC_FQN} listo"

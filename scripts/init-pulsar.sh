#!/bin/bash

# Script para inicializar Pulsar con los topics necesarios para Campaign Management

echo "Esperando a que Pulsar esté disponible..."
sleep 30

# Crear tenant y namespace
pulsar-admin tenants create campaign-management || echo "Tenant ya existe"
pulsar-admin namespaces create campaign-management/events || echo "Namespace ya existe"

# Crear topics para eventos de campañas
pulsar-admin topics create persistent://campaign-management/events/campaign-events || echo "Topic campaign-events ya existe"

echo "Inicialización de Pulsar completada para Campaign Management"

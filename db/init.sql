-- Script de inicialización de la base de datos para Campaign Management
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS campaign_management;

-- Crear tabla de campañas
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_marca UUID NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo_campana VARCHAR(50) NOT NULL,
    objetivo VARCHAR(50) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'borrador',
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    presupuesto_total FLOAT NOT NULL DEFAULT 0.0,
    presupuesto_utilizado FLOAT NOT NULL DEFAULT 0.0,
    meta_ventas INTEGER NOT NULL DEFAULT 0,
    ventas_actuales INTEGER NOT NULL DEFAULT 0,
    meta_engagement INTEGER NOT NULL DEFAULT 0,
    engagement_actual INTEGER NOT NULL DEFAULT 0,
    target_audiencia TEXT,
    canales_distribucion TEXT,
    terminos_condiciones TEXT,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_actividad TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla Outbox
CREATE TABLE IF NOT EXISTS outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL DEFAULT 'Campaign',
    event_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    occurred_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING|PUBLISHED|FAILED
    attempts INT NOT NULL DEFAULT 0
);

-- Proyección de lectura 
CREATE TABLE IF NOT EXISTS campaigns_read (
    id UUID PRIMARY KEY,
    id_marca UUID NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo_campana VARCHAR(50) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'borrador',
    fecha_inicio TIMESTAMP NULL,
    fecha_fin TIMESTAMP NULL,
    presupuesto_total FLOAT NOT NULL DEFAULT 0.0,
    presupuesto_utilizado FLOAT NOT NULL DEFAULT 0.0,
    meta_ventas INT NOT NULL DEFAULT 0,
    ventas_actuales INT NOT NULL DEFAULT 0,
    meta_engagement INT NOT NULL DEFAULT 0,
    engagement_actual INT NOT NULL DEFAULT 0,
    last_version INT NOT NULL DEFAULT 0,
    fecha_ultima_actividad TIMESTAMP NULL
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_campaigns_id_marca ON campaigns(id_marca);
CREATE INDEX IF NOT EXISTS idx_campaigns_estado ON campaigns(estado);
CREATE INDEX IF NOT EXISTS idx_campaigns_tipo_campana ON campaigns(tipo_campana);
CREATE INDEX IF NOT EXISTS idx_campaigns_fecha_creacion ON campaigns(fecha_creacion);

CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox_events(status, occurred_at);
CREATE INDEX IF NOT EXISTS idx_outbox_agg_time ON outbox_events(aggregate_id, occurred_at);

-- Insertar datos de ejemplo
INSERT INTO campaigns (id, id_marca, nombre, descripcion, tipo_campana, objetivo, estado, presupuesto_total, meta_ventas, meta_engagement, target_audiencia, canales_distribucion) VALUES
    (gen_random_uuid(), gen_random_uuid(), 'Campaña de Verano 2024', 'Campaña promocional para el verano', 'afiliacion', 'ventas', 'borrador', 10000.0, 100, 5000, 'Jóvenes 18-35 años', 'Redes sociales, email marketing'),
    (gen_random_uuid(), gen_random_uuid(), 'Black Friday 2024', 'Campaña especial para Black Friday', 'influencer', 'conversion', 'programada', 25000.0, 500, 10000, 'Adultos 25-50 años', 'Influencers, redes sociales, web');

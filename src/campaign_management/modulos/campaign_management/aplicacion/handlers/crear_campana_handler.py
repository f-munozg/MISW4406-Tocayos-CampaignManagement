import json
import logging
from datetime import datetime

from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import CrearCampana
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.config.db import db
from campaign_management.infraestructura.outbox.model import OutboxEvent

logger = logging.getLogger(__name__)

def _parse_iso(dt: str):
    if not dt:
        return None
    try:
        if dt.endswith('Z'):
            dt = dt.replace('Z', '+00:00')
        from datetime import datetime
        return datetime.fromisoformat(dt)
    except Exception:
        return None

def manejar_crear_campana(cmd: CrearCampana):
    try:

        fi = _parse_iso(cmd.fecha_inicio)
        ff = _parse_iso(cmd.fecha_fin)

        camp = CampanaDBModel(
            id_marca          = cmd.id_marca,
            saga_id           = cmd.saga_id,
            nombre            = cmd.nombre,
            descripcion       = cmd.descripcion,
            tipo_campana      = cmd.tipo_campana,
            objetivo          = cmd.objetivo,
            estado            = "borrador",
            fecha_inicio      = fi,
            fecha_fin         = ff,
            presupuesto_total = cmd.presupuesto_total or 0.0,
            presupuesto_utilizado = 0.0,
            meta_ventas       = cmd.meta_ventas or 0,
            ventas_actuales   = 0,
            meta_engagement   = cmd.meta_engagement or 0,
            engagement_actual = 0,
            target_audiencia  = cmd.target_audiencia,
            canales_distribucion = cmd.canales_distribucion,
        )
        db.session.add(camp)
        db.session.flush()

        evento = {
            "event_type": "CampaignCreated",
            "aggregate_id": str(camp.id),
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": str(camp.id),
                "id_marca": str(camp.id_marca),
                "nombre": camp.nombre,
                "tipo_campana": camp.tipo_campana,
                "fecha_inicio": camp.fecha_inicio.isoformat() if camp.fecha_inicio else None,
                "fecha_fin": camp.fecha_fin.isoformat() if camp.fecha_fin else None
            },
            "metadata": {}
        }

        out = OutboxEvent(
            saga_id=cmd.saga_id,
            aggregate_id=camp.id,
            aggregate_type="Campaign",
            event_type="CampaignCreated",
            payload=json.dumps(evento)
        )
        db.session.add(out)
        db.session.commit()
        logger.info("Campaña creada %s y evento almacenado en outbox %s", camp.id, out.id)
        return str(camp.id)

    except Exception as e:
        db.session.rollback()
        logger.exception("Error creando campaña: %s", e)
        raise

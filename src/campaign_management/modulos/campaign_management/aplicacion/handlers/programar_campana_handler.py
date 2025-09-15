"""Handler para programar campaña

En este archivo se define el handler para programar campañas
"""

import json
import logging
from datetime import datetime

from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import ProgramarCampana
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

def manejar_programar_campana(cmd: ProgramarCampana):
    try:
        # Buscar la campaña
        campana = CampanaDBModel.query.filter_by(id=cmd.id_campana).first()
        if not campana:
            raise ValueError(f"Campaña con id {cmd.id_campana} no encontrada")
        
        # Verificar que esté en estado borrador
        if campana.estado != "borrador":
            raise ValueError(f"La campaña debe estar en estado 'borrador' para ser programada. Estado actual: {campana.estado}")
        
        # Actualizar la campaña
        campana.estado = "programada"

        campana.fecha_inicio = _parse_iso(cmd.fecha_inicio)
        campana.fecha_fin = _parse_iso(cmd.fecha_fin)

        # campana.fecha_inicio = datetime.fromisoformat(cmd.fecha_inicio) if cmd.fecha_inicio else None
        # campana.fecha_fin = datetime.fromisoformat(cmd.fecha_fin) if cmd.fecha_fin else None
        campana.fecha_actualizacion = datetime.utcnow()
        
        db.session.flush()

        # Crear evento
        evento = {
            "event_type": "CampaignScheduled",
            "aggregate_id": str(campana.id),
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": str(campana.id),
                "id_marca": str(campana.id_marca),
                "nombre": campana.nombre,
                "fecha_inicio": campana.fecha_inicio.isoformat() if campana.fecha_inicio else None,
                "fecha_fin": campana.fecha_fin.isoformat() if campana.fecha_fin else None,
                "fecha_programacion": datetime.utcnow().isoformat()
            },
            "metadata": {}
        }

        out = OutboxEvent(
            aggregate_id=campana.id,
            aggregate_type="Campaign",
            event_type="CampaignScheduled",
            payload=json.dumps(evento)
        )
        db.session.add(out)
        db.session.commit()
        logger.info("Campaña programada %s y evento almacenado en outbox %s", campana.id, out.id)
        return str(campana.id)

    except Exception as e:
        db.session.rollback()
        logger.exception("Error programando campaña: %s", e)
        raise

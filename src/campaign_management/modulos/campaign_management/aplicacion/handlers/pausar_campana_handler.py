"""Handler para pausar campaña

En este archivo se define el handler para pausar campañas
"""

import json
import logging
from datetime import datetime

from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import PausarCampana
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.config.db import db
from campaign_management.infraestructura.outbox.model import OutboxEvent

logger = logging.getLogger(__name__)

def manejar_pausar_campana(cmd: PausarCampana):
    try:
        # Buscar la campaña
        campana = CampanaDBModel.query.filter_by(id=cmd.id_campana).first()
        if not campana:
            raise ValueError(f"Campaña con id {cmd.id_campana} no encontrada")
        
        # Verificar que esté en estado activa
        if campana.estado != "activa":
            raise ValueError(f"La campaña debe estar en estado 'activa' para ser pausada. Estado actual: {campana.estado}")
        
        # Actualizar la campaña
        campana.estado = "pausada"
        campana.fecha_actualizacion = datetime.utcnow()
        
        db.session.flush()

        # Crear evento
        evento = {
            "event_type": "CampaignPaused",
            "aggregate_id": str(campana.id),
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": str(campana.id),
                "id_marca": str(campana.id_marca),
                "nombre": campana.nombre,
                "motivo": cmd.motivo,
                "fecha_pausa": datetime.utcnow().isoformat()
            },
            "metadata": {}
        }

        out = OutboxEvent(
            aggregate_id=campana.id,
            aggregate_type="Campaign",
            event_type="CampaignPaused",
            payload=json.dumps(evento)
        )
        db.session.add(out)
        db.session.commit()
        logger.info("Campaña pausada %s y evento almacenado en outbox %s", campana.id, out.id)
        return str(campana.id)

    except Exception as e:
        db.session.rollback()
        logger.exception("Error pausando campaña: %s", e)
        raise
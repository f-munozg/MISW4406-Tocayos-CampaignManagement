"""Handler para activar campaña

En este archivo se define el handler para activar campañas
"""

import json
import logging
from datetime import datetime

from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import ActivarCampana
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.config.db import db
from campaign_management.infraestructura.outbox.model import OutboxEvent

logger = logging.getLogger(__name__)

def manejar_activar_campana(cmd: ActivarCampana):
    try:
        # Buscar la campaña
        campana = CampanaDBModel.query.filter_by(id=cmd.id_campana).first()
        if not campana:
            raise ValueError(f"Campaña con id {cmd.id_campana} no encontrada")
        
        # Verificar que esté en estado programada
        if campana.estado != "programada":
            raise ValueError(f"La campaña debe estar en estado 'programada' para ser activada. Estado actual: {campana.estado}")
        
        # Actualizar la campaña
        campana.estado = "activa"
        campana.fecha_actualizacion = datetime.utcnow()
        
        db.session.flush()

        # Crear evento
        evento = {
            "event_type": "CampaignActivated",
            "aggregate_id": str(campana.id),
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": str(campana.id),
                "id_marca": str(campana.id_marca),
                "nombre": campana.nombre,
                "fecha_activacion": datetime.utcnow().isoformat()
            },
            "metadata": {}
        }

        out = OutboxEvent(
            aggregate_id=campana.id,
            aggregate_type="Campaign",
            event_type="CampaignActivated",
            payload=json.dumps(evento)
        )
        db.session.add(out)
        db.session.commit()
        logger.info("Campaña activada %s y evento almacenado en outbox %s", campana.id, out.id)
        return str(campana.id)

    except Exception as e:
        db.session.rollback()
        logger.exception("Error activando campaña: %s", e)
        raise
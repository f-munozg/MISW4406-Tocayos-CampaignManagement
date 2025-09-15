"""Handler para finalizar campaña

En este archivo se define el handler para finalizar campañas
"""

import json
import logging
from datetime import datetime

from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import FinalizarCampana
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.config.db import db
from campaign_management.infraestructura.outbox.model import OutboxEvent

logger = logging.getLogger(__name__)

def manejar_finalizar_campana(cmd: FinalizarCampana):
    try:
        # Buscar la campaña
        campana = CampanaDBModel.query.filter_by(id=cmd.id_campana).first()
        if not campana:
            raise ValueError(f"Campaña con id {cmd.id_campana} no encontrada")
        
        # Verificar que esté en estado activa o pausada
        if campana.estado not in ["activa", "pausada"]:
            raise ValueError(f"La campaña debe estar en estado 'activa' o 'pausada' para ser finalizada. Estado actual: {campana.estado}")
        
        # Actualizar la campaña
        campana.estado = "finalizada"
        campana.fecha_actualizacion = datetime.utcnow()
        
        db.session.flush()

        # Crear evento
        evento = {
            "event_type": "CampaignFinished",
            "aggregate_id": str(campana.id),
            "version": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "id": str(campana.id),
                "id_marca": str(campana.id_marca),
                "nombre": campana.nombre,
                "motivo": cmd.motivo,
                "fecha_finalizacion": datetime.utcnow().isoformat()
            },
            "metadata": {}
        }

        out = OutboxEvent(
            aggregate_id=campana.id,
            aggregate_type="Campaign",
            event_type="CampaignFinished",
            payload=json.dumps(evento)
        )
        db.session.add(out)
        db.session.commit()
        logger.info("Campaña finalizada %s y evento almacenado en outbox %s", campana.id, out.id)
        return str(campana.id)

    except Exception as e:
        db.session.rollback()
        logger.exception("Error finalizando campaña: %s", e)
        raise
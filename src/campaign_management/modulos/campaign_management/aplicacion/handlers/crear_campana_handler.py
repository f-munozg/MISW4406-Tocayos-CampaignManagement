"""Handler para el comando CrearCampana

En este archivo se define el handler para crear campañas

"""

from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import CrearCampana
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.seedwork.aplicacion.comandos import ejecutar_commando
from campaign_management.infraestructura.pulsar import pulsar_publisher
from campaign_management.config.db import db
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

@ejecutar_commando.register
def _(comando: CrearCampana):
    """Handler para crear una nueva campaña"""
    logger.info(f"Ejecutando comando CrearCampana: {comando}")
    try:
        # Crear modelo de base de datos directamente
        campana_model = CampanaDBModel()
        campana_model.id = uuid.UUID(comando.id)
        campana_model.id_marca = uuid.UUID(comando.id_marca)
        campana_model.nombre = comando.nombre
        campana_model.descripcion = comando.descripcion
        campana_model.tipo_campana = comando.tipo_campana
        campana_model.objetivo = comando.objetivo
        campana_model.estado = 'borrador'
        campana_model.presupuesto_total = comando.presupuesto_total
        campana_model.meta_ventas = comando.meta_ventas
        campana_model.meta_engagement = comando.meta_engagement
        campana_model.target_audiencia = comando.target_audiencia
        campana_model.canales_distribucion = comando.canales_distribucion
        campana_model.terminos_condiciones = comando.terminos_condiciones
        
        if comando.fecha_creacion:
            campana_model.fecha_creacion = datetime.fromisoformat(comando.fecha_creacion)
        if comando.fecha_actualizacion:
            campana_model.fecha_actualizacion = datetime.fromisoformat(comando.fecha_actualizacion)
        
        # Guardar en base de datos
        db.session.add(campana_model)
        db.session.commit()
        
        # Crear y publicar evento de dominio
        from campaign_management.modulos.campaign_management.dominio.entidades import CampanaCreada
        evento = CampanaCreada(
            id_campana=campana_model.id,
            id_marca=campana_model.id_marca,
            nombre=campana_model.nombre,
            tipo_campana=campana_model.tipo_campana,
            objetivo=campana_model.objetivo,
            fecha_creacion=campana_model.fecha_creacion
        )
        
        # Publicar evento en Pulsar (opcional)
        try:
            pulsar_publisher.publish_event(evento, 'campaign-events')
            logger.info(f"Evento publicado en Pulsar para campaña: {campana_model.id}")
        except Exception as pulsar_error:
            logger.warning(f"Error publicando evento en Pulsar: {pulsar_error}")
        
        logger.info(f"Campaña creada exitosamente: {campana_model.id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creando campaña: {e}")
        raise

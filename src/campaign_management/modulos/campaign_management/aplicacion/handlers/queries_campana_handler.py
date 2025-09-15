"""Handlers para queries de campaña

En este archivo se definen los handlers para queries de campañas
"""

import logging
from typing import List, Optional
from campaign_management.modulos.campaign_management.aplicacion.queries.queries_campana import (
    ObtenerCampana, ObtenerCampanasPorMarca, ObtenerCampanasPorTipo,
    ObtenerCampanasPorEstado, ObtenerCampanasActivas
)
from campaign_management.modulos.campaign_management.infraestructura.modelos import CampanaDBModel
from campaign_management.modulos.campaign_management.aplicacion.mapeadores import MapeadorCampanaDTOJson
from campaign_management.config.db import db

logger = logging.getLogger(__name__)

def manejar_obtener_campana(query: ObtenerCampana) -> Optional[dict]:
    """Obtiene una campaña por su ID"""
    try:
        campana = CampanaDBModel.query.filter_by(id=query.id_campana).first()
        if not campana:
            return None
        
        return _convertir_campana_a_dto(campana)
    except Exception as e:
        logger.exception("Error obteniendo campaña: %s", e)
        raise

def _convertir_campana_a_dto(campana: CampanaDBModel) -> dict:
    """Convierte un modelo de BD a DTO"""
    return {
        'id': str(campana.id),
        'id_marca': str(campana.id_marca),
        'nombre': campana.nombre,
        'descripcion': campana.descripcion or '',
        'tipo_campana': campana.tipo_campana,
        'objetivo': campana.objetivo,
        'estado': campana.estado,
        'fecha_inicio': campana.fecha_inicio.isoformat() if campana.fecha_inicio else '',
        'fecha_fin': campana.fecha_fin.isoformat() if campana.fecha_fin else '',
        'presupuesto_total': campana.presupuesto_total,
        'presupuesto_utilizado': campana.presupuesto_utilizado,
        'meta_ventas': campana.meta_ventas,
        'ventas_actuales': campana.ventas_actuales,
        'meta_engagement': campana.meta_engagement,
        'engagement_actual': campana.engagement_actual,
        'target_audiencia': campana.target_audiencia or '',
        'canales_distribucion': campana.canales_distribucion or '',
        'terminos_condiciones': campana.terminos_condiciones or '',
        'fecha_creacion': campana.fecha_creacion.isoformat() if campana.fecha_creacion else '',
        'fecha_ultima_actividad': campana.fecha_ultima_actividad.isoformat() if campana.fecha_ultima_actividad else '',
        'fecha_actualizacion': campana.fecha_actualizacion.isoformat() if campana.fecha_actualizacion else ''
    }

def manejar_obtener_campanas_por_marca(query: ObtenerCampanasPorMarca) -> List[dict]:
    """Obtiene campañas por ID de marca"""
    try:
        campanas = CampanaDBModel.query.filter_by(id_marca=query.id_marca).all()
        return [_convertir_campana_a_dto(campana) for campana in campanas]
    except Exception as e:
        logger.exception("Error obteniendo campañas por marca: %s", e)
        raise

def manejar_obtener_campanas_por_tipo(query: ObtenerCampanasPorTipo) -> List[dict]:
    """Obtiene campañas por tipo"""
    try:
        campanas = CampanaDBModel.query.filter_by(tipo_campana=query.tipo_campana).all()
        return [_convertir_campana_a_dto(campana) for campana in campanas]
    except Exception as e:
        logger.exception("Error obteniendo campañas por tipo: %s", e)
        raise

def manejar_obtener_campanas_por_estado(query: ObtenerCampanasPorEstado) -> List[dict]:
    """Obtiene campañas por estado"""
    try:
        campanas = CampanaDBModel.query.filter_by(estado=query.estado).all()
        return [_convertir_campana_a_dto(campana) for campana in campanas]
    except Exception as e:
        logger.exception("Error obteniendo campañas por estado: %s", e)
        raise

def manejar_obtener_campanas_activas(query: ObtenerCampanasActivas) -> List[dict]:
    """Obtiene todas las campañas activas"""
    try:
        campanas = CampanaDBModel.query.filter_by(estado="activa").all()
        return [_convertir_campana_a_dto(campana) for campana in campanas]
    except Exception as e:
        logger.exception("Error obteniendo campañas activas: %s", e)
        raise

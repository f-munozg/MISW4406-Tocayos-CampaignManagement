"""API para la gestión de campañas

En este archivo se define la API REST para la gestión de campañas

"""

from flask import Blueprint, request, jsonify, Response
from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import (
    CrearCampana, ProgramarCampana, ActivarCampana, PausarCampana, 
    FinalizarCampana, CancelarCampana, ActualizarMetricasCampana
)
from campaign_management.modulos.campaign_management.aplicacion.queries.queries_campana import (
    ObtenerCampana, ObtenerCampanasPorMarca, ObtenerCampanasPorTipo,
    ObtenerCampanasPorEstado, ObtenerCampanasActivas
)
from campaign_management.modulos.campaign_management.aplicacion.mapeadores import MapeadorCampanaDTOJson
from campaign_management.seedwork.aplicacion.comandos import ejecutar_commando
from campaign_management.seedwork.aplicacion.queries import ejecutar_query
from campaign_management.seedwork.dominio.excepciones import ExcepcionDominio
from datetime import datetime
import json
from uuid import UUID
import logging

def _is_uuid(v: str) -> bool:
    try:
        UUID(v)
        return True
    except Exception:
        return False


logger = logging.getLogger(__name__)

bp = Blueprint('campaign_management', __name__, url_prefix='/campaign-management')

@bp.route('/campaign', methods=['POST'])
def crear_campana():
    try:
        campana_dict = request.json
        logger.info(f"Request data: {campana_dict}")
                
        map_campana = MapeadorCampanaDTOJson()
        campana_dto = map_campana.externo_a_dto(campana_dict)
        
        bid = campana_dto.id_marca
        if not bid or not _is_uuid(bid):
            return jsonify({"error": "id_marca debe ser UUID válido"}), 400
        
        comando = CrearCampana(
            id=campana_dto.id,
            id_marca=campana_dto.id_marca,
            nombre=campana_dto.nombre,
            descripcion=campana_dto.descripcion,
            tipo_campana=campana_dto.tipo_campana,
            objetivo=campana_dto.objetivo,
            presupuesto_total=campana_dto.presupuesto_total,
            meta_ventas=campana_dto.meta_ventas,
            meta_engagement=campana_dto.meta_engagement,
            target_audiencia=campana_dto.target_audiencia,
            canales_distribucion=campana_dto.canales_distribucion,
            terminos_condiciones=campana_dto.terminos_condiciones,
            fecha_creacion=datetime.now().isoformat(),
            fecha_actualizacion=datetime.now().isoformat()
        )
        
        new_id = ejecutar_commando(comando)
        return jsonify({"id": new_id}), 202
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')

@bp.route('/campaign/<id>/programar', methods=['PUT'])
def programar_campana(id):
    try:
        data = request.json
        fecha_inicio = data.get('fecha_inicio', '') if data else ''
        fecha_fin = data.get('fecha_fin', '') if data else ''
        
        comando = ProgramarCampana(
            id_campana=id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_actualizacion=datetime.now().isoformat()
        )
        
        ejecutar_commando(comando)
        
        return Response('{}', status=202, mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')

@bp.route('/campaign/<id>/activar', methods=['PUT'])
def activar_campana(id):
    # Aceptar body vacío sin reventar el mapeo
    _ = request.get_json(silent=True) or {}

    if not _is_uuid(id):
        return jsonify({"error": "id inválido, debe ser UUID"}), 400

    try:
        # Construye y ejecuta comando de dominio (sin publicar a Pulsar aquí)
        cmd = ActivarCampana(id_campana=id)
        ejecutar_commando(cmd)
        return jsonify({"id": id, "status": "accepted"}), 202

    except ExcepcionDominio as e:
        # define/usa tu excepción de “no encontrada”
        logger.info("Campaña no encontrada: %s", id)
        return jsonify({"error": "campaña no encontrada", "id": id}), 404

    except ExcepcionDominio as e:
        # define/usa tu excepción de dominio para transiciones inválidas
        return jsonify({"error": "transición inválida", "detail": str(e)}), 409

    except Exception as e:
        logger.exception("Error activando campaña %s", id)
        return jsonify({"error": "internal", "detail": str(e)}), 500

@bp.route('/campaign/<id>/pausar', methods=['PUT'])
def pausar_campana(id):
    try:
        data = request.json
        motivo = data.get('motivo', '') if data else ''
        
        comando = PausarCampana(
            id_campana=id,
            motivo=motivo,
            fecha_actualizacion=datetime.now().isoformat()
        )
        
        ejecutar_commando(comando)
        
        return Response('{}', status=202, mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')

@bp.route('/campaign/<id>/finalizar', methods=['PUT'])
def finalizar_campana(id):
    try:
        data = request.json
        motivo = data.get('motivo', '') if data else ''
        
        comando = FinalizarCampana(
            id_campana=id,
            motivo=motivo,
            fecha_actualizacion=datetime.now().isoformat()
        )
        
        ejecutar_commando(comando)
        
        return Response('{}', status=202, mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')

@bp.route('/campaign/<id>/cancelar', methods=['PUT'])
def cancelar_campana(id):
    try:
        data = request.json
        motivo = data.get('motivo', '') if data else ''
        
        comando = CancelarCampana(
            id_campana=id,
            motivo=motivo,
            fecha_actualizacion=datetime.now().isoformat()
        )
        
        ejecutar_commando(comando)
        
        return Response('{}', status=202, mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')

@bp.route('/campaign/<id>/actualizar-metricas', methods=['PUT'])
def actualizar_metricas_campana(id):
    try:
        data = request.json
        ventas = data.get('ventas', 0) if data else 0
        engagement = data.get('engagement', 0) if data else 0
        presupuesto_utilizado = data.get('presupuesto_utilizado', 0.0) if data else 0.0
        
        comando = ActualizarMetricasCampana(
            id_campana=id,
            ventas=ventas,
            engagement=engagement,
            presupuesto_utilizado=presupuesto_utilizado,
            fecha_actualizacion=datetime.now().isoformat()
        )
        
        ejecutar_commando(comando)
        
        return Response('{}', status=202, mimetype='application/json')
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')

@bp.route('/campaign/<id>', methods=['GET'])
def obtener_campana(id):
    try:
        query = ObtenerCampana(id_campana=id)
        resultado = ejecutar_query(query)
        if resultado is None:
            return Response(json.dumps(dict(error='Campaña no encontrada')), status=404, mimetype='application/json')
        return jsonify(resultado)
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception("Error obteniendo campaña: %s", e)
        return Response(json.dumps(dict(error='Error interno del servidor')), status=500, mimetype='application/json')

@bp.route('/campaigns/marca/<id_marca>', methods=['GET'])
def obtener_campanas_por_marca(id_marca):
    try:
        query = ObtenerCampanasPorMarca(id_marca=id_marca)
        resultado = ejecutar_query(query)
        return jsonify(resultado)
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception("Error obteniendo campañas por marca: %s", e)
        return Response(json.dumps(dict(error='Error interno del servidor')), status=500, mimetype='application/json')

@bp.route('/campaigns/tipo/<tipo_campana>', methods=['GET'])
def obtener_campanas_por_tipo(tipo_campana):
    try:
        query = ObtenerCampanasPorTipo(tipo_campana=tipo_campana)
        resultado = ejecutar_query(query)
        return jsonify(resultado)
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception("Error obteniendo campañas por tipo: %s", e)
        return Response(json.dumps(dict(error='Error interno del servidor')), status=500, mimetype='application/json')

@bp.route('/campaigns/estado/<estado>', methods=['GET'])
def obtener_campanas_por_estado(estado):
    try:
        query = ObtenerCampanasPorEstado(estado=estado)
        resultado = ejecutar_query(query)
        return jsonify(resultado)
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception("Error obteniendo campañas por estado: %s", e)
        return Response(json.dumps(dict(error='Error interno del servidor')), status=500, mimetype='application/json')

@bp.route('/campaigns/activas', methods=['GET'])
def obtener_campanas_activas():
    try:
        query = ObtenerCampanasActivas()
        resultado = ejecutar_query(query)
        return jsonify(resultado)
    except ExcepcionDominio as e:
        return Response(json.dumps(dict(error=str(e))), status=400, mimetype='application/json')
    except Exception as e:
        logger.exception("Error obteniendo campañas activas: %s", e)
        return Response(json.dumps(dict(error='Error interno del servidor')), status=500, mimetype='application/json')

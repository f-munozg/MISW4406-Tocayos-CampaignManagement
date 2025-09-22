"""Mapeadores para la gestión de campañas

En este archivo se definen los mapeadores para la gestión de campañas

"""

from campaign_management.modulos.campaign_management.dominio.entidades import Campana, TipoCampana, EstadoCampana, ObjetivoCampana
from campaign_management.modulos.campaign_management.aplicacion.dto import CampanaDTO
from datetime import datetime
import uuid

class MapeadorCampana:
    
    def dto_a_entidad(self, dto: CampanaDTO) -> Campana:
        campana = Campana()
        campana.id = uuid.UUID(dto.id)
        campana.saga_id = uuid.UUID(dto.saga_id)
        campana.id_marca = uuid.UUID(dto.id_marca)
        campana.nombre = dto.nombre
        campana.descripcion = dto.descripcion
        campana.tipo_campana = TipoCampana(dto.tipo_campana)
        campana.objetivo = ObjetivoCampana(dto.objetivo)
        campana.estado = EstadoCampana(dto.estado)
        campana.presupuesto_total = dto.presupuesto_total
        campana.presupuesto_utilizado = dto.presupuesto_utilizado
        campana.meta_ventas = dto.meta_ventas
        campana.ventas_actuales = dto.ventas_actuales
        campana.meta_engagement = dto.meta_engagement
        campana.engagement_actual = dto.engagement_actual
        campana.target_audiencia = dto.target_audiencia
        campana.canales_distribucion = dto.canales_distribucion
        campana.terminos_condiciones = dto.terminos_condiciones
        
        if dto.fecha_inicio:
            campana.fecha_inicio = datetime.fromisoformat(dto.fecha_inicio)
        if dto.fecha_fin:
            campana.fecha_fin = datetime.fromisoformat(dto.fecha_fin)
        
        return campana
    
    def entidad_a_dto(self, entidad: Campana) -> CampanaDTO:
        return CampanaDTO(
            id=str(entidad.id),
            saga_id=str(entidad.saga_id),
            id_marca=str(entidad.id_marca),
            nombre=entidad.nombre,
            descripcion=entidad.descripcion,
            tipo_campana=entidad.tipo_campana.value,
            objetivo=entidad.objetivo.value,
            estado=entidad.estado.value,
            fecha_inicio=entidad.fecha_inicio.isoformat() if entidad.fecha_inicio else "",
            fecha_fin=entidad.fecha_fin.isoformat() if entidad.fecha_fin else "",
            presupuesto_total=entidad.presupuesto_total,
            presupuesto_utilizado=entidad.presupuesto_utilizado,
            meta_ventas=entidad.meta_ventas,
            ventas_actuales=entidad.ventas_actuales,
            meta_engagement=entidad.meta_engagement,
            engagement_actual=entidad.engagement_actual,
            target_audiencia=entidad.target_audiencia,
            canales_distribucion=entidad.canales_distribucion,
            terminos_condiciones=entidad.terminos_condiciones,
            fecha_creacion=entidad.fecha_creacion.isoformat(),
            fecha_ultima_actividad=entidad.fecha_ultima_actividad.isoformat(),
            fecha_actualizacion=entidad.fecha_actualizacion.isoformat()
        )

class MapeadorCampanaDTOJson:
    
    def externo_a_dto(self, externo: dict) -> CampanaDTO:
        return CampanaDTO(
            id=externo.get('id', str(uuid.uuid4())),
            saga_id=externo.get('saga_id', ''),
            id_marca=externo.get('id_marca', ''),
            nombre=externo.get('nombre', ''),
            descripcion=externo.get('descripcion', ''),
            tipo_campana=externo.get('tipo_campana', 'afiliacion'),
            objetivo=externo.get('objetivo', 'ventas'),
            estado=externo.get('estado', 'borrador'),
            fecha_inicio=externo.get('fecha_inicio', ''),
            fecha_fin=externo.get('fecha_fin', ''),
            presupuesto_total=externo.get('presupuesto_total', 0.0),
            presupuesto_utilizado=externo.get('presupuesto_utilizado', 0.0),
            meta_ventas=externo.get('meta_ventas', 0),
            ventas_actuales=externo.get('ventas_actuales', 0),
            meta_engagement=externo.get('meta_engagement', 0),
            engagement_actual=externo.get('engagement_actual', 0),
            target_audiencia=externo.get('target_audiencia', ''),
            canales_distribucion=externo.get('canales_distribucion', ''),
            terminos_condiciones=externo.get('terminos_condiciones', ''),
            fecha_creacion=externo.get('fecha_creacion', ''),
            fecha_ultima_actividad=externo.get('fecha_ultima_actividad', ''),
            fecha_actualizacion=externo.get('fecha_actualizacion', '')
        )
    
    def dto_a_externo(self, dto: CampanaDTO) -> dict:
        return {
            'id': dto.id,
            'saga_id': dto.saga_id,
            'id_marca': dto.id_marca,
            'nombre': dto.nombre,
            'descripcion': dto.descripcion,
            'tipo_campana': dto.tipo_campana,
            'objetivo': dto.objetivo,
            'estado': dto.estado,
            'fecha_inicio': dto.fecha_inicio,
            'fecha_fin': dto.fecha_fin,
            'presupuesto_total': dto.presupuesto_total,
            'presupuesto_utilizado': dto.presupuesto_utilizado,
            'meta_ventas': dto.meta_ventas,
            'ventas_actuales': dto.ventas_actuales,
            'meta_engagement': dto.meta_engagement,
            'engagement_actual': dto.engagement_actual,
            'target_audiencia': dto.target_audiencia,
            'canales_distribucion': dto.canales_distribucion,
            'terminos_condiciones': dto.terminos_condiciones,
            'fecha_creacion': dto.fecha_creacion,
            'fecha_ultima_actividad': dto.fecha_ultima_actividad,
            'fecha_actualizacion': dto.fecha_actualizacion
        }

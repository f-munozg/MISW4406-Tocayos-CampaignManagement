"""Aplicación principal del microservicio Campaign Management

En este archivo se define la aplicación principal del microservicio
"""

from flask import Flask
from campaign_management.api.health import bp as health_bp
from campaign_management.config.db import init_db
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuración de la base de datos
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/campaign_management')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar base de datos
    init_db(app)    
    app.register_blueprint(health_bp)

    # Importar y registrar handlers de comandos
    try:
        from campaign_management.modulos.campaign_management.aplicacion.handlers.crear_campana_handler import manejar_crear_campana
        from campaign_management.modulos.campaign_management.aplicacion.handlers.programar_campana_handler import manejar_programar_campana
        from campaign_management.modulos.campaign_management.aplicacion.handlers.activar_campana_handler import manejar_activar_campana
        from campaign_management.modulos.campaign_management.aplicacion.handlers.pausar_campana_handler import manejar_pausar_campana
        from campaign_management.modulos.campaign_management.aplicacion.handlers.finalizar_campana_handler import manejar_finalizar_campana
        from campaign_management.modulos.campaign_management.aplicacion.handlers.cancelar_campana_handler import manejar_cancelar_campana
        from campaign_management.modulos.campaign_management.aplicacion.handlers.actualizar_metricas_campana_handler import manejar_actualizar_metricas_campana
        
        from campaign_management.modulos.campaign_management.aplicacion.comandos.comandos_campana import (
            CrearCampana, ProgramarCampana, ActivarCampana, PausarCampana, 
            FinalizarCampana, CancelarCampana, ActualizarMetricasCampana
        )
        
        from campaign_management.seedwork.aplicacion.comandos import ejecutar_commando
        
        # Registrar handlers de comandos
        ejecutar_commando.register(CrearCampana, manejar_crear_campana)
        ejecutar_commando.register(ProgramarCampana, manejar_programar_campana)
        ejecutar_commando.register(ActivarCampana, manejar_activar_campana)
        ejecutar_commando.register(PausarCampana, manejar_pausar_campana)
        ejecutar_commando.register(FinalizarCampana, manejar_finalizar_campana)
        ejecutar_commando.register(CancelarCampana, manejar_cancelar_campana)
        ejecutar_commando.register(ActualizarMetricasCampana, manejar_actualizar_metricas_campana)
        
        logger.info("Handlers de comandos de campaign management registrados")
    except Exception as e:
        logger.error(f"Error registrando handlers de comandos de campaign management: {e}")
    
    # Importar y registrar handlers de queries
    try:
        from campaign_management.modulos.campaign_management.aplicacion.handlers.queries_campana_handler import (
            manejar_obtener_campana, manejar_obtener_campanas_por_marca,
            manejar_obtener_campanas_por_tipo, manejar_obtener_campanas_por_estado,
            manejar_obtener_campanas_activas
        )
        
        from campaign_management.modulos.campaign_management.aplicacion.queries.queries_campana import (
            ObtenerCampana, ObtenerCampanasPorMarca, ObtenerCampanasPorTipo,
            ObtenerCampanasPorEstado, ObtenerCampanasActivas
        )
        
        from campaign_management.seedwork.aplicacion.queries import ejecutar_query
        
        # Registrar handlers de queries
        ejecutar_query.register(ObtenerCampana, manejar_obtener_campana)
        ejecutar_query.register(ObtenerCampanasPorMarca, manejar_obtener_campanas_por_marca)
        ejecutar_query.register(ObtenerCampanasPorTipo, manejar_obtener_campanas_por_tipo)
        ejecutar_query.register(ObtenerCampanasPorEstado, manejar_obtener_campanas_por_estado)
        ejecutar_query.register(ObtenerCampanasActivas, manejar_obtener_campanas_activas)
        
        logger.info("Handlers de queries de campaign management registrados")
    except Exception as e:
        logger.error(f"Error registrando handlers de queries de campaign management: {e}")
    
    try:
        from campaign_management.api.campaign_management import bp as campaign_management_bp
        app.register_blueprint(campaign_management_bp)
        logger.info("Blueprint de campaign management registrado")
    except Exception as e:
        logger.error(f"Error registrando blueprint de campaign management: {e}")
    
    # Inicializar servicios de Pulsar (opcional)
    try:
        from campaign_management.infraestructura.event_consumer_service import event_consumer_service
        from campaign_management.infraestructura.pulsar import pulsar_publisher
        import atexit
        
        # Iniciar el servicio de consumo de eventos
        event_consumer_service.start_consuming()
        logger.info("Servicio de consumo de eventos iniciado")
        
        # Registrar función de limpieza al cerrar la aplicación
        atexit.register(cleanup_pulsar_connections)
        
    except Exception as e:
        logger.warning(f"Pulsar no disponible, continuando sin eventos: {e}")
    
    return app

def cleanup_pulsar_connections():
    """Limpia las conexiones de Pulsar al cerrar la aplicación"""
    try:
        from campaign_management.infraestructura.event_consumer_service import event_consumer_service
        from campaign_management.infraestructura.pulsar import pulsar_publisher
        # Note: The event_consumer_service instance is local to create_app()
        # The Pulsar consumer will be cleaned up when the process exits
        event_consumer_service.stop_consuming()
        pulsar_publisher.close()
        logger.info("Conexiones de Pulsar cerradas correctamente")
    except Exception as e:
        logger.error(f"Error cerrando conexiones de Pulsar: {e}")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

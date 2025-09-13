# Campaign Management Microservice

Este microservicio se encarga de la gestión de campañas de marketing, incluyendo su creación, programación, activación, pausa, finalización y cancelación.

## Características

- **Gestión de Campañas**: Crear, programar, activar, pausar, finalizar y cancelar campañas
- **Tipos de Campaña**: Afiliación, Influencer, Lealtad, B2B, Mixta
- **Objetivos**: Ventas, Brand Awareness, Engagement, Lead Generation, Conversión
- **Estados**: Borrador, Programada, Activa, Pausada, Finalizada, Cancelada
- **Métricas**: Seguimiento de ventas, engagement y presupuesto utilizado
- **Eventos**: Arquitectura orientada a eventos con Pulsar
- **Base de Datos**: PostgreSQL con SQLAlchemy

## Arquitectura

El microservicio sigue los principios de Domain-Driven Design (DDD) con:

- **Dominio**: Entidades, eventos de dominio y reglas de negocio
- **Aplicación**: Comandos, queries, handlers y DTOs
- **Infraestructura**: Modelos de base de datos, Pulsar, configuración
- **API**: Endpoints REST para operaciones CRUD

## Tecnologías

- **Backend**: Python 3.11, Flask
- **Base de Datos**: PostgreSQL 15
- **Eventos**: Apache Pulsar 3.1.0
- **ORM**: SQLAlchemy
- **Contenedores**: Docker, Docker Compose

## Instalación y Ejecución

### Con Docker Compose (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd campaign-management

# Ejecutar con Docker Compose
docker-compose up -d

# El microservicio estará disponible en http://localhost:5000
```

### Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql://user:password@localhost:5432/campaign_management"
export PULSAR_SERVICE_URL="pulsar://localhost:6650"
export PULSAR_ADMIN_URL="http://localhost:8080"

# Ejecutar la aplicación
python src/campaign_management/main.py
```

## API Endpoints

### Campañas

- `POST /campaign-management/campaign` - Crear campaña
- `PUT /campaign-management/campaign/{id}/programar` - Programar campaña
- `PUT /campaign-management/campaign/{id}/activar` - Activar campaña
- `PUT /campaign-management/campaign/{id}/pausar` - Pausar campaña
- `PUT /campaign-management/campaign/{id}/finalizar` - Finalizar campaña
- `PUT /campaign-management/campaign/{id}/cancelar` - Cancelar campaña
- `PUT /campaign-management/campaign/{id}/actualizar-metricas` - Actualizar métricas
- `GET /campaign-management/campaign/{id}` - Obtener campaña
- `GET /campaign-management/campaigns/marca/{id_marca}` - Obtener campañas por marca
- `GET /campaign-management/campaigns/tipo/{tipo}` - Obtener campañas por tipo
- `GET /campaign-management/campaigns/estado/{estado}` - Obtener campañas por estado
- `GET /campaign-management/campaigns/activas` - Obtener campañas activas

## Eventos

El microservicio publica los siguientes eventos en Pulsar:

- `CampanaCreada` - Cuando se crea una nueva campaña
- `CampanaProgramada` - Cuando se programa una campaña
- `CampanaActivada` - Cuando se activa una campaña
- `CampanaPausada` - Cuando se pausa una campaña
- `CampanaFinalizada` - Cuando se finaliza una campaña
- `CampanaCancelada` - Cuando se cancela una campaña
- `MetricasCampanaActualizadas` - Cuando se actualizan las métricas

## Configuración

### Variables de Entorno

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `PULSAR_SERVICE_URL`: URL del servicio Pulsar
- `PULSAR_ADMIN_URL`: URL del admin de Pulsar
- `FLASK_ENV`: Entorno de Flask (development/production)

### Base de Datos

El microservicio utiliza PostgreSQL con la siguiente estructura:

- **Tabla**: `campaigns`
- **Esquema**: `campaign_management`
- **Índices**: Optimizados para consultas por marca, estado y tipo

## Monitoreo

- **Pulsar Manager**: http://localhost:9527
- **Logs**: Disponibles en los contenedores Docker
- **Métricas**: A través de los eventos publicados en Pulsar

## Desarrollo

### Estructura del Proyecto

```
src/campaign_management/
├── api/                    # Endpoints REST
├── config/                 # Configuración
├── infraestructura/        # Pulsar, base de datos
├── modulos/
│   └── campaign_management/
│       ├── aplicacion/     # Comandos, queries, handlers
│       ├── dominio/        # Entidades, eventos
│       └── infraestructura/ # Modelos de BD
└── seedwork/              # Código reutilizable
```

### Agregar Nuevas Funcionalidades

1. **Dominio**: Definir entidades y eventos en `dominio/`
2. **Aplicación**: Crear comandos/queries en `aplicacion/`
3. **Infraestructura**: Implementar persistencia en `infraestructura/`
4. **API**: Exponer endpoints en `api/`

## Contribución

1. Fork el repositorio
2. Crear una rama para la funcionalidad
3. Hacer commit de los cambios
4. Crear un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT.

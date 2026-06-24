# Incendios API — Backend

API REST FastAPI para el sistema de gestión táctica de incendios. Sirve como BFF (Backend for Frontend) y expone endpoints públicos, autenticación, reportes, alertas y panel admin.

## Tecnologías

- Python 3.11+ / FastAPI
- DynamoDB (AWS) + SQLite
- S3 (AWS) para imágenes
- JWT + bcrypt para autenticación
- SNS para notificaciones
- Docker + docker-compose
- pytest + pytest-cov (tests)

## Requisitos

- Python 3.11+
- Docker (opcional, para deploy)
- Credenciales AWS (DynamoDB, S3)

## Instalación local

```bash
cd ec2/api
pip install -r requirements.txt
```

## Ejecución local

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Variables de entorno requeridas:

| Variable | Descripción |
|----------|-------------|
| `JWT_SECRET` | Secreto para firmar tokens JWT |
| `SYNC_TOKEN` | Token para sync desde Lambda |
| `AWS_ACCESS_KEY_ID` | Credencial AWS |
| `AWS_SECRET_ACCESS_KEY` | Credencial AWS |
| `AWS_DEFAULT_REGION` | Región AWS (ej: us-east-1) |

## Tests

```bash
cd ec2/api

# Todos los tests
python -m pytest

# Con reporte de cobertura HTML
python -m pytest --cov --cov-report=html
```

El reporte se genera en `ec2/api/htmlcov/`.

## Docker

```bash
docker build -t incendios-api -f ec2/api/Dockerfile .
docker run -p 8000:8000 incendios-api
```

## Endpoints principales

| Ruta | Descripción |
|------|-------------|
| `POST /login` | Inicio de sesión |
| `POST /register` | Registro de usuario |
| `POST /reports` | Crear reporte |
| `GET /public/dashboard-stats` | Estadísticas públicas |
| `GET /public/map-coordinates` | Coordenadas para mapa |
| `GET /admin/reports` | Reportes (admin) |
| `PUT /admin/reports/{id}/status` | Cambiar estado (admin) |
| `GET /health` | Health check |

Ver `docs/api-spec/openapi.json` para la especificación completa.

## Estructura

```
ec2/api/
├── main.py              # App FastAPI + routers
├── routers/             # auth, reports, public, admin, alerts, bff, password_reset, bootstrap
├── repositories/        # UserRepository, ReportRepository
├── services.py          # S3, Lambda
├── dependencies.py      # Dependencias (auth, DB)
├── factories.py         # Factory Method pattern
├── circuit_breaker.py   # Circuit Breaker pattern
├── tests/               # Tests unitarios (167)
└── requirements.txt
```

# Guía de Ejecución — Incendios Valle del Sol

## Requisitos del sistema

- Python 3.11+
- Node.js 22+
- npm
- Docker + docker-compose (opcional, para deploy)

---

## Backend (API FastAPI)

### Instalación

```bash
cd ec2/api
pip install -r requirements.txt
```

### Ejecución local

```bash
export JWT_SECRET=tu-secreto
export SYNC_TOKEN=tu-sync-token
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1

uvicorn main:app --host 0.0.0.0 --port 8000
```

### Tests

```bash
cd ec2/api
python -m pytest                                    # Todos los tests
python -m pytest -v                                 # Modo verbose
python -m pytest tests/test_auth.py                 # Tests específicos
python -m pytest --cov --cov-report=html            # Con cobertura HTML
```

El reporte de cobertura se genera en `ec2/api/htmlcov/index.html`.

---

## Frontend (React PWA)

### Instalación

```bash
cd frontend
npm install
```

### Ejecución (desarrollo)

```bash
npm run dev
```

Abre en `http://localhost:5173`.

### Build producción

```bash
npm run build
```

### Tests

```bash
cd frontend
npm test                                           # Todos los tests
npm run test:watch                                 # Modo watch
npm run test:coverage                              # Con cobertura HTML
```

El reporte de cobertura se genera en `frontend/coverage/index.html`.

---

## Lambdas (Microservicios)

Cada Lambda sigue el mismo patrón:

```bash
cd lambda/<nombre>/
pip install -r requirements.txt -t .
zip -r <nombre>.zip .
```

| Lambda | Directorio | Tests |
|--------|-----------|-------|
| upload-proxy | `lambda/upload_proxy/` | `python -m pytest lambda/upload_proxy/` |
| ms-usuarios | `lambda/usuarios/` | `python -m pytest lambda/usuarios/` |
| ms-incidencias | `lambda/ms-incidencias/` | `python -m pytest lambda/ms-incidencias/` |
| ms-notificaciones | `lambda/ms-notificaciones/` | `python -m pytest lambda/ms-notificaciones/` |
| sns-to-grafana | `lambda/sns-to-grafana/` | `python -m pytest lambda/sns-to-grafana/` |

Para ejecutar todos los tests Lambda:

```bash
python -m pytest lambda/
```

---

## Tests completos (todo el proyecto)

```bash
# Backend (API)
cd ec2/api && python -m pytest --cov --cov-report=html

# Lambdas
cd <raíz-proyecto> && python -m pytest lambda/

# Frontend
cd frontend && npm test -- --run
```

---

## Generar reportes de cobertura

```bash
# Backend
cd ec2/api && python -m pytest --cov --cov-report=html
# → ec2/api/htmlcov/index.html

# Frontend
cd frontend && npm run test:coverage
# → frontend/coverage/index.html
```

---

## Docker (deploy)

```bash
docker build -t incendios-api -f ec2/api/Dockerfile .
docker run -p 8000:8000 -e JWT_SECRET=... incendios-api
```

## Ver documentación de la API

La especificación OpenAPI está en `docs/api-spec/openapi.json`. Se puede visualizar en:

- https://editor.swagger.io/ (cargar el JSON)
- O localmente: `python -c "import sys; sys.path.insert(0, 'ec2/api'); from main import app; print('Swagger en /docs')"`

## Estructura del proyecto

```
incendios-valle/
├── ec2/api/              # Backend FastAPI (BFF + microservicio)
│   ├── routers/          # auth, reports, public, admin, alerts, bff, ...
│   ├── tests/            # 167 tests unitarios
│   └── main.py           # Entry point
├── frontend/             # PWA React + TypeScript
│   ├── src/              # Código fuente
│   ├── __tests__/        # 172 tests unitarios
│   └── package.json
├── lambda/               # 5 Lambdas (microservicios serverless)
│   ├── upload_proxy/     # Subida de imágenes a S3
│   ├── usuarios/         # Autenticación sobre DynamoDB
│   ├── ms-incidencias/   # CRUD reportes sobre DynamoDB
│   ├── ms-notificaciones/# Publicación SNS
│   └── sns-to-grafana/   # Anotaciones Grafana
└── docs/                 # Documentación y specs
    ├── api-spec/         # OpenAPI + ejemplos
    ├── GOAL.md
    ├── ARQUITECTURA.md
    └── ...
```

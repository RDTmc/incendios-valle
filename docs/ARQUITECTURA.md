# ARQUITECTURA — Incendios Valle del Sol

## Vista general

```
Cliente PWA ──► API Gateway (api.keogh.lat, DNS-only en Cloudflare)
                   ├── /auth         → λ ms-usuarios (bcrypt + JWT)
                   ├── /reports      → λ ms-incidencias (DynamoDB)
                   ├── /alerts       → λ ms-notificaciones (SNS)
                   ├── /upload       → λ upload-proxy (S3)
                   └── /api/{proxy+} → HTTP_PROXY → EC2 nginx → FastAPI + Grafana
```

## Backend (`ec2/api/`)

- **FastAPI** monolítico con 8 routers: auth, reports, public, alerts, bff, admin, password_reset, bootstrap
- **Patrones**: Repository (DynamoDB), Factory Method (tipos de reporte), Circuit Breaker
- **Auth**: JWT HS256 con bcrypt. Token centralizado en `dependencies.py`
- **Base de datos relacional**: RDS PostgreSQL 15 (reemplaza SQLite desde Jul 2026). Datos de lectura para endpoints públicos, admin, dashboard, y Grafana vía API REST (Infinity datasource)
- **DynamoDB**: Almacén primario para usuarios y reportes (escritura desde API + Lambdas). PostgreSQL recibe réplica vía `sync_to_postgres()`
- **Modelos**: Pydantic en `models.py` (LoginRequest, RegisterRequest, ReportRequest, SyncRequest, ExternalReportRequest)

## Frontend (`frontend/`)

- React + TypeScript + Vite + PWA (service worker)
- Mapbox GL JS primario, Leaflet fallback
- Patrones: Observer (Toast), Strategy (MapboxStrategy), Composite (ui/Button, Input, Card)
- BFF: `/bff/dashboard` endpoint

## Lambdas (`lambda/`)

- `ms-usuarios`: login/register contra DynamoDB, bcrypt compilado con Docker Lambda image (Amazon Linux 2)
- `ms-incidencias`: CRUD reports DynamoDB (key: reports_id HASH + created_at RANGE)
- `ms-notificaciones`: SNS publish
- `upload-proxy`: S3 direct upload (base64)
- `sns-to-grafana`: SNS subscriber → anotaciones Grafana

## CI/CD (`.github/workflows/deploy.yml`)

- Disparo: push a main con cambios en frontend/**, ec2/api/**, lambda/**, scripts/**, sonar-project.properties, *.github/workflows/deploy.yml
- Pasos: build → test (pytest desde raíz con PYTHONPATH) → SonarCloud scan → push Docker Hub → SCP archivos → SSH pull & recreate
- SonarCloud: Docker container, workspace montado en /github/workspace

## EC2 (t3.micro)

- 5 contenedores: Nginx (proxy reverso), API (FastAPI), Grafana 10.4.8, Prometheus, node-exporter
- Docker Compose con volúmenes para dashboards provisioning y datos persistentes
- Conexión a RDS PostgreSQL 15 externo (db.t3.micro, mismo VPC)
- No hot-patching permitido. Solo pipeline deploy.

## Decisiones clave

1. API Gateway como entry point único, no Cloudflare Tunnel
2. SonarCloud > SonarQube local (t3.micro no corre SQ)
3. bcrypt compilado con Docker Lambda image (GLIBC correcto)
4. Coverage path: relative_files=True + pytest desde raíz del repo
5. JWT_SECRET sin default en dependencies.py
6. Sin credenciales AWS en env vars — solo LabRole vía IMDS

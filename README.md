# 🔥 Plataforma de Gestión de Incendios — Valle del Sol

[![CI/CD](https://github.com/RDTmc/incendios-valle/actions/workflows/deploy.yml/badge.svg)](https://github.com/RDTmc/incendios-valle/actions/workflows/deploy.yml)
[![SonarCloud](https://img.shields.io/badge/SonarCloud-A%20(1.0)-brightgreen)](https://sonarcloud.io/project/overview?id=incendios-valle)
[![GitHub language count](https://img.shields.io/github/languages/count/RDTmc/incendios-valle)](https://github.com/RDTmc/incendios-valle)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Sistema de gestión táctica de incendios forestales y urbanos para la **Municipalidad de Valle del Sol** — 5 microservicios Lambda serverless, PWA ciudadana con soporte offline, dashboard táctico Grafana y CI/CD automatizado.

---

## Arquitectura

```
Ciudadano / Admin → Cloudflare Pages (PWA React)
                        ↓
                  Cloudflare Worker (CORS + rate limit)
                        ↓
              Cloudflare DNS-only → API Gateway
                        ↓
     ┌──────────────────┼──────────────────┐
     ▼                  ▼                   ▼
λ usuarios    λ ms-incidencias      λ ms-notificaciones
     ↓                  ↓                   ↓
     ▼                                    ▼
λ upload-proxy (S3)           λ sns-to-grafana (SNS→Grafana)
     ↓
──────────────────── EC2 t3.micro ────────────────────
  ┌────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐
  │ nginx  │→ │ FastAPI  │  │ Grafana │  │Prometheus│
  │ proxy  │  │ (BFF)    │  │ 10.4.8  │  │ + node_ex│
  └────────┘  └────┬─────┘  └────┬────┘  └──────────┘
                   ▼              ▼
              ┌────────┐   ┌──────────┐
              │ SQLite │   │ DynamoDB │
              └────────┘   └──────────┘
```

---

## Estructura del proyecto

```
incendios-valle/
├── ec2/api/                # FastAPI BFF (45 endpoints)
│   ├── routers/            # auth, reports, public, admin, alerts, bff, ...
│   ├── tests/              # 168 tests (88% cobertura)
│   └── main.py
├── frontend/               # PWA React + TypeScript + Tailwind
│   ├── src/pages/          # 10 páginas (9 ciudadanas + 1 admin)
│   ├── src/__tests__/      # 177 tests (82% cobertura)
│   └── package.json
├── lambda/                 # 5 microservicios serverless (10 tests)
│   ├── usuarios/           # Auth contra DynamoDB
│   ├── ms-incidencias/     # CRUD reportes DynamoDB
│   ├── ms-notificaciones/  # Publicación SNS
│   ├── upload_proxy/       # Subida imágenes a S3
│   └── sns-to-grafana/     # Anotaciones Grafana desde SNS
├── ec2/                    # Infraestructura EC2
│   ├── docker-compose.yml  # 5 contenedores (nginx, api, grafana, prometheus, node-exporter)
│   ├── grafana-provisioning/  # Dashboards táctico + DevOps
│   ├── nginx/              # Configuración proxy reverso
│   └── prometheus/         # Monitoreo de infraestructura
├── cloudflare/             # Cloudflare Worker (CORS + rate limit)
├── docs/                   # Documentación, diagramas, API spec
└── .github/workflows/      # 4 workflows CI/CD (deploy, audit, restart-grafana, fix-permissions)
```

---

## Tech Stack

| Capa                | Tecnología                                      |
|---------------------|-------------------------------------------------|
| Frontend            | React 18 + TypeScript + Vite + Tailwind CSS     |
| Backend             | Python 3.11 + FastAPI + Uvicorn                 |
| Mapas               | Mapbox GL JS (Strategy Pattern) + Leaflet       |
| Base datos primaria | DynamoDB (AWS)                                  |
| Base datos local    | SQLite (WAL mode, datasource nativo Grafana)    |
| Imágenes            | S3 (AWS)                                        |
| Serverless          | 5 AWS Lambda (Python 3.11)                      |
| Mensajería          | SNS (AWS)                                       |
| Dashboards          | Grafana 10.4.8 (SQLite + Prometheus)            |
| Monitoreo           | Prometheus + Node Exporter                      |
| Contenedores        | Docker + docker-compose                         |
| CI/CD               | GitHub Actions (4 workflows)                    |
| Edge/DNS            | Cloudflare Pages + DNS-only                     |
| Correo              | Mailtrap SMTP (OTP 2FA + password reset)        |
| Testing backend     | pytest 8.3 + pytest-cov (168 tests, 88%)        |
| Testing frontend    | Vitest 1.6 + Testing Library (177 tests, 82%)   |
| Calidad código      | SonarCloud — A en 4 dimensiones, 0 Code Smells  |

---

## Patrones de Diseño

| Patrón           | Tipo           | Ubicación                             | Tests |
|------------------|----------------|---------------------------------------|:-----:|
| **BFF**          | Arquitectónico | `routers/bff.py`                      | 5     |
| **Circuit Breaker** | Comportamiento | `circuit_breaker.py`                | 6     |
| **Factory Method**  | Creacional     | `factories/report_factory.py`       | 5     |
| **Strategy**     | Comportamiento | `util/map/MapStrategy.ts`             | 19    |
| **Observer**     | Comportamiento | `components/Toast.tsx`                | 5     |
| **Composite**    | Estructural    | `components/ui/` (Button, Input, Card)| 3     |

---

## Seguridad

- **JWT** (HS256, RFC 7519) + bcrypt + 2FA con OTP server-side
- **Password reset** 3 pasos: email → OTP 6 dígitos → nueva contraseña
- **CORS** restrictivo a dominios conocidos
- **Sin leak de errores**: `str(e)` eliminado de todos los endpoints
- **Grafana**: token y password vía GitHub Secrets (sin hardcodeos)
- **SonarCloud**: Security A, Reliability A, Maintainability A, Security Review A

---

## Tests Totales

| Componente    | Tests | Cobertura |
|---------------|:-----:|:---------:|
| Backend       | 168   | 88%       |
| Frontend      | 177   | 82%       |
| Lambdas (5)   | 10    | ≥85%      |
| **TOTAL**     | **355** | **≥82%** |

---

## Setup local

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd ec2/api && pip install -r requirements.txt
export JWT_SECRET=... && uvicorn main:app --host 0.0.0.0 --port 8000

# Docker (todo el stack)
docker compose -f ec2/docker-compose.yml up -d
```

---

## Ejecutar tests

```bash
# Backend + cobertura HTML
cd ec2/api && python -m pytest --cov --cov-report=html

# Frontend + cobertura HTML
cd frontend && npm run test:coverage

# Lambdas
python -m pytest lambda/ -v
```

---

## Enlaces

| Recurso          | URL                                          |
|------------------|----------------------------------------------|
| PWA              | https://incendios-valle.pages.dev            |
| API              | https://api.keogh.lat/api                    |
| Swagger          | https://api.keogh.lat/api/docs               |
| Dashboard táctico| https://dashboard.keogh.lat/dashboard/dashboards |
| Dashboard DevOps | https://dashboard.keogh.lat/dashboard/dashboards |
| GitHub           | https://github.com/RDTmc/incendios-valle     |

---

## Licencia

MIT

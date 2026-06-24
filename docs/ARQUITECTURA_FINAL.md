# Arquitectura Final - Plataforma Incendios Valle del Sol

## Diagrama de Arquitectura

```
[Usuario] → [React PWA (Cloudflare Pages)]
              incendios-valle.pages.dev
                    ↕ HTTPS
              [Cloudflare DNS]
              api.keogh.lat / dashboard.keogh.lat
                    ↕ HTTPS
              ┌─────────────────────────────────┐
              │       API GATEWAY (REST)        │
              │  Rate limit: 1000 req/min       │
              │  CloudWatch: logs + metrics     │
              ├─────────────────────────────────┤
              │                                 │
    ┌─────────┤  /auth/*    → Lambda Usuarios   │
    │         │  /reports/* → Lambda Incidencias │
    │         │  /api/*     → EC2 Nginx · FastAPI│
    │         │  /upload/*  → Lambda upload-proxy│
    │         │  /alerts/*  → Lambda Notificacio │
    │         └─────────────────────────────────┘
    │
    │  ┌───────── EC2 t3.micro (1GB RAM, 2vCPU) ─────────┐
    │  │                                                  │
    │  │  ┌──────────────┐   ┌──────────────┐            │
    │  │  │   Nginx:80   │──▶│  FastAPI:8000 │            │
    │  │  │  (revers.    │   │  (1 MS princ.)│            │
    │  │  │   proxy)     │   │  25 endpoints │            │
    │  │  └──────────────┘   │  +background  │            │
    │  │                     │  tasks (CIREN,│            │
    │  │  ┌──────────────┐   │   FIRMS, OWM) │            │
    │  │  │  Grafana:3000│   └──────┬────────┘            │
    │  │  │  10.4.8      │          │                     │
    │  │  │  SQLite DS   │          ▼                     │
    │  │  └──────┬───────┘   ┌──────────────┐            │
    │  │         │           │   SQLite DB   │            │
    │  │         └──────────▶│ incendios.db  │            │
    │  │                     │  (6 tablas)   │            │
    │  │                     └──────┬────────┘            │
    │  └────────────────────────────┼─────────────────────┘
    │                               │
    │                               ▼
    │  ┌────────────────────────────────────────┐
    │  │           AWS Lambda (Serverless)       │
    │  │  ┌──────────────────┐                  │
    │  │  │  upload-proxy    │──▶ S3 imágenes   │
    │  │  └──────────────────┘                  │
    │  │  ┌──────────────────┐                  │
    │  │  │  ms-usuarios     │──▶ DynamoDB:users│
    │  │  └──────────────────┘                  │
    │  │  ┌──────────────────┐                  │
    │  │  │  ms-incidencias   │──▶ DynDB:reports│
    │  │  └──────────────────┘                  │
    │  │  ┌──────────────────┐                  │
    │  │  │  ms-notificaciones│──▶ SNS topic    │
    │  │  └──────────────────┘                  │
    │  └────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────┐
│           AWS DynamoDB (Fuente de Verdad)      │
│  Table: users (PK: user_id, GSI: email-index) │
│  Table: reports (PK: report_id, GSI: user-ind)│
│          ↕ DynamoDB Streams                    │
│  Lambda: sync → SQLite (caché Grafana)        │
└──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│           S3 Bucket: incendios-valle-sol      │
│  /reportes/{uuid}.jpg  (imágenes subidas)     │
│  /backups/*.db         (backups SQLite)       │
└──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│           SNS Topic: incendios-alerts         │
│  Publica alertas → Suscriptores (email, SMS)  │
└──────────────────────────────────────────────┘
```

## Microservicios

| Servicio | Tipo | Lenguaje | DB | Responsabilidad |
|----------|------|----------|----|-----------------|
| **FastAPI (EC2)** | Microservicio principal | Python 3.11 | DynamoDB + SQLite | 25 endpoints, background tasks (CIREN, FIRMS, OWM), dashboard stats, admin |
| **Lambda ms-usuarios** | Serverless | Python 3.11 | DynamoDB | Login, register, getUser, JWT |
| **Lambda ms-incidencias** | Serverless | Python 3.11 | DynamoDB | CRUD reportes ciudadanos |
| **Lambda upload-proxy** | Serverless | Python 3.11 | S3 | Subida de imágenes con presigned URL |
| **Lambda ms-notificaciones** | Serverless | Python 3.11 | SNS | Envío de alertas a la comunidad |
| **Lambda sync** | Serverless | Python 3.11 | DynamoDB → SQLite | Réplica de datos para Grafana |

## Patrones de Diseño Implementados

### Backend (Python/FastAPI)

| Patrón | Uso | Archivo |
|--------|-----|---------|
| **Repository Pattern** | Abstracción de persistencia: `UserRepository`, `ReportRepository`, interfaz común para DynamoDB + SQLite | `ec2/api/repositories/` |
| **Factory Method** | Creación de tipos de reporte: `FORESTAL`, `URBANO`. Cada tipo con lógica de validación distinta | `ec2/api/factories/` |
| **Circuit Breaker** | Protección en llamadas externas: CIREN, NASA FIRMS, OpenWeatherMap. 3 fallos → degraded mode 30s | `ec2/api/circuit_breaker.py` |
| **BFF Pattern** | Capa de agregación `/bff/` que consolida datos de múltiples fuentes para el frontend | `ec2/api/routers/bff.py` |
| **Singleton** | Conexiones a DynamoDB, SQLite (pool reutilizable) | `ec2/api/database.py` |
| **Observer** | Sistema de eventos: nuevo reporte → notificar + actualizar dashboard | `ec2/api/events.py` |
| **Strategy** | Integraciones externas intercambiables (CIREN, FIRMS, OWM) | `ec2/api/integrations/` |

### Frontend (React/TypeScript)

| Patrón | Uso | Archivo |
|--------|-----|---------|
| **Observer Pattern** | Sistema global de toasts/notificaciones: `ToastContext` + `useToast()` | `frontend/src/components/Toast.tsx` |
| **Factory Pattern** | Creación de tipos de alerta: `success()`, `error()`, `warning()`, `info()` | `frontend/src/util/toast.ts` |
| **Strategy Pattern** | Renderizado de mapas: Leaflet (reportes) vs Mapbox (focos activos) | `frontend/src/pages/MapaFocos.tsx` |
| **Composite Pattern** | Componentes UI reutilizables: `Button`, `Input`, `Card`, `Modal` | `frontend/src/components/ui/` |
| **Context Pattern** | Estado global: `AuthContext`, `ToastContext` | `frontend/src/App.tsx` |
| **Hook Pattern** | Custom hooks: `useAuth()`, `useToast()`, `useGeolocation()` | `frontend/src/hooks/` |

## Flujo de Datos

### Registro de Reporte Ciudadano
```
Usuario → PWA → API Gateway → Lambda Incidencias → DynamoDB
                                                    ↓ Stream
                                              Lambda sync → SQLite → Grafana
                                                    ↓ Evento
                                              Lambda Notificaciones → SNS
```

### Detección Satelital (Background)
```
EC2 (cada 30min) → NASA FIRMS API
                 → OpenWeatherMap API
EC2 (cada 1h)    → CIREN/CONAF API
                 ↓
               SQLite → Grafana Dashboard
```

## API Gateway: Rutas

| Ruta | Método | Target | Auth |
|------|--------|--------|------|
| `/auth/login` | POST | Lambda usuarios | None |
| `/auth/register` | POST | Lambda usuarios | None |
| `/auth/profile` | GET | Lambda usuarios | JWT |
| `/reports` | GET, POST | Lambda incidencias | JWT (opcional) |
| `/reports/{id}` | GET, PUT | Lambda incidencias | JWT |
| `/api/*` | ANY | EC2 FastAPI (proxy) | None / JWT |
| `/upload` | POST | Lambda upload-proxy | None |
| `/alerts` | GET | Lambda notificaciones | JWT |
| `/alerts/subscribe` | POST | Lambda notificaciones | None |

## Estrategia de Branching (GitHub Flow)

```
main (producción)
  ├── feature/testing-foundation
  ├── feature/ux-core
  ├── feature/design-patterns
  ├── feature/api-gateway
  ├── feature/alertas
  └── feature/monitoreo
```

- `main` → depliegue automático a producción
- `feature/*` → branches por cada fase
- Pull Request obligatorio con tests pasando
- Merge a main → GitHub Actions: build + test + deploy

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|------------|---------|
| Frontend | React + TypeScript + Vite | 18 / 5.3 / 5.1 |
| PWA | vite-plugin-pwa + Workbox | 0.19 |
| Mapas | Mapbox GL + Leaflet | 3.24 / 1.9 |
| Estilos | Tailwind CSS | 3.4 |
| Backend | Python + FastAPI | 3.11 / 0.109 |
| ASGI | Uvicorn | standard |
| Auth | JWT propio (PyJWT + bcrypt) | — |
| DB primaria | DynamoDB (AWS) | — |
| DB caché | SQLite (local EC2) | — |
| Dashboard | Grafana + frser-sqlite-datasource | 10.4.8 |
| Proxy | Nginx (Docker) | alpine |
| API Gateway | AWS API Gateway (REST) | — |
| Serverless | AWS Lambda (Python) | 3.11 |
| Mensajería | AWS SNS | — |
| Imágenes | AWS S3 | — |
| Infra | AWS CloudWatch | — |
| Túneles | Cloudflare Tunnel | — |
| CI/CD | GitHub Actions | — |
| Calidad | SonarCloud | SaaS |

## Costos Estimados

| Servicio | Estimado | Cobertura |
|----------|----------|-----------|
| EC2 t3.micro | $0 | Free Tier |
| Lambda (1M req/mes) | $0 | Free Tier |
| DynamoDB (25GB) | $0 | Free Tier |
| S3 (5GB) | $0 | Free Tier |
| API Gateway (1M req/mes) | $0 | Free Tier |
| SNS (1M pub/mes) | $0 | Free Tier |
| CloudWatch (5GB logs) | $0 | Free Tier |
| SonarCloud | $0 | Free para repos públicos |
| **Total** | **$0/mes** | Free Tier |

## Limitaciones AWS Academy

| Restricción | Impacto | Mitigación |
|-------------|---------|------------|
| Lab resets cada 4h | API Gateway + Lambdas dejan de funcionar | Cloudflare Tunnel para URLs estables. Pipeline CI/CD recrea en minutos |
| LabRole no permite `iam:GetPolicy` | No podemos leer política exacta | Validación práctica: todos los servicios necesarios funcionan |
| SES bloqueado | No podemos enviar emails | Solo usamos SNS (notificaciones push) |
| Elastic IP cambia en reset | URLs de integración cambian | Usar API Gateway como fachada estática. El backend proxy apunta a API Gateway, no a IP directa |

## Documentos Relacionados

- `API_GATEWAY_GUIDE.md` → Pasos detallados para crear API Gateway manual
- `TEST_PLAN.md` → Estrategia de pruebas unitarias y de integración
- `ROADMAP_10_DAYS.md` → Plan de implementación en 10 días

---

*Documento actualizado: 6 Junio 2026*
*Arquitectura Final v2.0 - Incendios Valle del Sol*

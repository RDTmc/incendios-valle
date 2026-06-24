# Diagrama de Arquitectura — Incendios Valle del Sol

```mermaid
graph TB
    subgraph "Usuarios"
        CIUDADANO[Ciudadano]
        ADMIN[Admin Municipal]
        VECINO[Vecino]
    end

    subgraph "Frontend"
        PWA["PWA React + TypeScript<br/>incendios-valle.pages.dev"]
        SW[Service Worker]
    end

    subgraph "CDN / Edge"
        CF["Cloudflare Worker<br/>api-proxy.abyssiagencia.workers.dev"]
        DNS["Cloudflare DNS-only<br/>api.keogh.lat"]
    end

    subgraph "API Gateway"
        AG["API Gateway<br/>HTTP_PROXY"]
    end

    subgraph "EC2 (t3.micro)"
        nginx["nginx reverse proxy"]
        API["FastAPI (BFF)<br/>8 routers"]
        GRAFANA["Grafana 10.4.8<br/>Dashboard táctico"]
        PROM["Prometheus<br/>Scrape node_exporter"]
        NODE["Node Exporter<br/>Métricas sistema"]
        SQLITE[(SQLite<br/>incendios.db)]
    end

    subgraph "Microservicios Lambda"
        UP["upload-proxy<br/>Imágenes S3"]
        USR["ms-usuarios<br/>Login/Registro"]
        INC["ms-incidencias<br/>CRUD Reportes"]
        NOT["ms-notificaciones<br/>SNS Alerts"]
        SNS2G["sns-to-grafana<br/>Anotaciones"]
    end

    subgraph "AWS Persistencia"
        DDB[(DynamoDB<br/>users + reports)]
        S3[(S3<br/>imágenes)]
        SNS["SNS Topic<br/>incendios-alerts"]
    end

    subgraph "APIs Externas"
        FIRMS["NASA FIRMS<br/>Satélites"]
        OWM["OpenWeatherMap<br/>Clima"]
        CONAF["CONAF / CIREN<br/>Datos incendios"]
        MAILTRAP["Mailtrap SMTP<br/>Correos OTP"]
        MAPBOX["Mapbox GL JS<br/>Mapas"]
    end

    %% Conexiones Frontend
    CIUDADANO --> PWA
    ADMIN --> PWA
    VECINO --> PWA
    PWA --> SW

    %% Flujo principal
    PWA --> CF
    CF --> AG
    AG --> nginx
    nginx --> API

    %% API interna
    API --> SQLITE
    API --> GRAFANA
    GRAFANA --> SQLITE
    NODE --> PROM

    %% API a AWS
    API --> DDB
    API --> S3
    API --> SNS

    %% Lambdas
    UP --> S3
    USR --> DDB
    INC --> DDB
    NOT --> SNS
    SNS2G --> GRAFANA

    %% APIs externas
    API --> FIRMS
    API --> OWM
    API --> CONAF
    API --> MAILTRAP
    PWA --> MAPBOX

    %% Sync Lambda → API
    USR -.->|/sync endpoint| API
    INC -.->|/sync endpoint| API

    %% Labels
    classDef frontend fill:#e1f5fe,stroke:#0288d1
    classDef infra fill:#fff3e0,stroke:#f57c00
    classDef compute fill:#e8f5e9,stroke:#388e3c
    classDef aws fill:#f3e5f5,stroke:#7b1fa2
    classDef external fill:#fce4ec,stroke:#c62828
    classDef db fill:#fff8e1,stroke:#f9a825

    class PWA,SW frontend
    class CF,DNS,AG infra
    class nginx,API,GRAFANA,PROM,NODE compute
    class UP,USR,INC,NOT,SNS2G aws
    class FIRMS,OWM,CONAF,MAILTRAP,MAPBOX external
    class DDB,S3,SNS,SQLITE db
```

## Descripción del flujo

1. **Usuario** accede a la PWA en `incendios-valle.pages.dev`
2. La PWA se comunica via **Cloudflare Worker** (proxy CORS) → **API Gateway** → **nginx** → **FastAPI** (EC2)
3. **FastAPI** (BFF) orquesta datos desde:
   - **SQLite**: reportes, alertas, auditoría (para Grafana + admin)
   - **DynamoDB**: usuarios, reportes (para Lambdas)
   - **S3**: imágenes de reportes
   - **APIs externas**: NASA FIRMS, OpenWeatherMap, CONAF/CIREN
4. **Grafana** se conecta directamente a SQLite para dashboards tácticos
5. **5 Lambdas** manejan operaciones específicas sin servidor
6. **Mailtrap** envía OTPs por correo para 2FA y password reset
7. **CI/CD**: GitHub Actions → Docker build/push → SCP + SSH deploy a EC2

## Tecnologías

| Componente | Tecnología |
|------------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Mapbox GL JS |
| API | Python 3.11+, FastAPI, uvicorn |
| Lambdas | Python 3.11+, boto3 |
| Base de datos primaria | DynamoDB (AWS) |
| Base de datos secundaria | SQLite (WAL mode) |
| Almacenamiento imágenes | S3 (AWS) |
| Mensajería | SNS (AWS) |
| Dashboard | Grafana 10.4.8 |
| Contenedores | Docker, docker-compose |
| CI/CD | GitHub Actions |
| Edge/DNS | Cloudflare (DNS-only) |
| Correo | Mailtrap SMTP |
| Mapas | Mapbox GL JS |

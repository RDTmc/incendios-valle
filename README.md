# 🔥 Plataforma de Gestión de Incendios - Valle del Sol

Sistema de microservicios para gestión de emergencias de incendios con soporte offline, notificaciones en tiempo real y dashboard de monitoreo.

## 🏗️ Arquitectura

```
Frontend (PWA)     → Cloudflare Pages
Backend (Lambda)  → AWS Lambda (3 funciones)
API Gateway       → AWS API Gateway
EC2 (FastAPI)     → Docker + Grafana
Database          → DynamoDB + SQLite Bridge
```

## 📂 Estructura del Proyecto

```
incendios-valle/
├── backend/
│   ├── lambda-usuarios/      # Funciones Lambda para usuarios
│   ├── lambda-incidencias/  # Funciones Lambda para reportes
│   └── lambda-notificaciones/ # Funciones Lambda para alertas
├── ec2/
│   └── fastapi/             # FastAPI ms-monitoreo + Grafana
├── frontend/                 # PWA React
├── docs/                    # Documentación
└── README.md
```

## 🚀 Tech Stack

| Capa | Tecnología |
|------|------------|
| Frontend | React + Vite + TypeScript + Tailwind |
| Backend | FastAPI + Python 3.11 |
| Database | DynamoDB + SQLite |
| AWS | Lambda, EC2, S3, API Gateway |
| Maps | Google Maps API |
| Dashboard | Grafana |

## 📋 Semanas de Desarrollo

| Semana | Entregable |
|--------|------------|
| 1 | AWS Setup completo |
| 2 | PWA + Cloudflare |
| 3 | Lambda + FastAPI |
| 4 | Notificaciones + Grafana |
| 5 | Testing + Demo |

## 💰 Costos Estimados

- **Total**: $0-3.50 / 10 semanas
- **Presupuesto**: $50 (AWS Academy)

## 🛠️ Setup Local

```bash
# Clonar repo
git clone git@github.com:RDTmc/incendios-valle.git

# Frontend
cd frontend
npm install
npm run dev

# Backend (EC2)
cd ec2/fastapi
docker compose up -d
```

## 📝 Licencia

MIT
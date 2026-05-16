# Arquitectura del Proyecto - Valle del Sol

## Estructura del Repositorio

```
incendios-valle/
├── frontend/                    → Cloudflare Pages (deploy automático)
├── lambda/
│   ├── usuarios/                → AWS Lambda (login/register)
│   └── ms-incidencias/          → AWS Lambda (reportes)
├── ec2/
│   ├── api/                     → FastAPI (Docker)
│   ├── nginx/                   → Configuración Nginx
│   ├── grafana-provisioning/    → Datasources Grafana
│   └── docker-compose.yml
├── ARQUITECTURA.md              → Este archivo
└── README.md
```

## Servicios AWS - Estado Actual

| Servicio | Uso | Estado | Notas |
|----------|-----|--------|-------|
| S3 | Almacenamiento fotos | ✅ Listo | Bucket: incendios-valle-sol |
| DynamoDB | Tablas users, reports | ✅ Activo | Fuente de verdad en la nube |
| Lambda | Funciones serverless | ⏳ Pendiente | ms-usuarios, ms-incidencias |
| EC2 t3.micro | FastAPI + Grafana | ✅ Desplegado | Elastic IP: 3.227.186.158 |
| Elastic IP | IP fija EC2 | ✅ Asociada | 3.227.186.158 |

## Servicios Desplegados en EC2

| Servicio | Puerto | Estado | URL Acceso |
|----------|--------|--------|------------|
| **Nginx** | 80 | ✅ Corriendo | http://3.227.186.158/ |
| **FastAPI** | 8000 | ✅ Healthy | http://3.227.186.158/api/docs |
| **Grafana** | 3000 | ✅ Corriendo | http://3.227.186.158/dashboard/ |

### Credenciales

- **Grafana**: usuario `admin`, contraseña configurable
- **API**: Endpoints públicos en `/api/`

## Flujo de Datos (Arquitectura)

```
App (PWA - Cloudflare)
    ↓
Nginx (Puerto 80)
    ↓
FastAPI (Puerto 8000)
    ↓
DynamoDB (Fuente de verdad - AWS)
    ↓
DynamoDB Streams (pendiente)
    ↓
Lambda Réplica (pendiente)
    ↓
SQLite (caché local)
    ↓
Grafana (dashboards)
```

## Configuración de Volúmenes en EC2

| Carpeta | Contenido | Permisos |
|---------|-----------|----------|
| `/home/ec2-user/incendios-data/api/` | Datos persistentes API | ec2-user:ec2-user |
| `/home/ec2-user/incendios-data/grafana/` | Datos Grafana, dashboards | 472:472 (Grafana user) |

## nginx.conf - Configuración Activa

```nginx
upstream api { server incendios-api:8000; }
upstream grafana { server incendios-grafana:3000; }

location /api/ { proxy_pass http://api/; ... }
location /dashboard/ { proxy_pass http://grafana; ... }
location = / { return 301 /dashboard/; }
```

## docker-compose.yml - Servicios Activos

```yaml
services:
  nginx:
    image: nginx:alpine
    depends_on:
      api:
        condition: service_healthy
    ports:
      - "80:80"

  api:
    image: incendios-api:latest
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs', timeout=2)"]
    volumes:
      - /home/ec2-user/incendios-data/api:/app/data

  grafana:
    image: grafana/grafana:10.4.2
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "admin123"
      GF_SERVER_SERVE_FROM_SUB_PATH: "true"
      GF_SERVER_ROOT_URL: "http://3.227.186.158/dashboard/"
    volumes:
      - /home/ec2-user/incendios-data/grafana:/var/lib/grafana
```

## Seguridad

- ✅ NO credenciales .env en EC2 (usa LabRole)
- ✅ NO git clone en EC2 (imágenes pre-compiladas)
- ✅ Elastic IP fija asociada
- ✅ Healthcheck nativo (Python)
- ❌ NO SonarQube en EC2 (ejecutar local)

## Roadmap de Desarrollo

| Week | Componente | Estado | Notas |
|------|------------|--------|-------|
| 1 | AWS Setup (S3, DynamoDB, EC2) | ✅ | VPC, SG, EC2, Elastic IP |
| 2 | PWA Frontend + Cloudflare | ✅ | Deploy automático |
| 3 | FastAPI + Docker EC2 | ✅ | Nginx, API, Grafana corriendo |
| 3 | Lambda ms-usuarios, ms-incidencias | ⏳ | Código listo, pend. deployment |
| 4 | Lambda ms-notifications | ⏳ | Pendiente desarrollo |
| 4 | DynamoDB Streams + SQLite sync | ⏳ | Pendiente |
| 5 | Grafana dashboards | ⏳ | Pendiente |
| 5 | PWA → URL API actualizada | 🔄 | Pendiente actualizar en Cloudflare |

## Comandos de Despliegue (EC2)

```bash
# En EC2 - Crear carpetas de datos
sudo mkdir -p ~/incendios-data/api ~/incendios-data/grafana
sudo chown -R 472:472 ~/incendios-data/grafana

# Levantar servicios
docker-compose up -d --force-recreate
```

## Notas Importantes

1. EC2: t3.micro (cuenta académica)
2. Security Group: SSH (22) desde IP admin, HTTP (80) público, HTTPS (443) pendiente
3. VPC personalizada con subnet pública
4. Grafana versión fija: 10.4.2 (no latest)
5. API healthcheck: Python nativo (sin curl/wget)

## Próximos Pasos

1. Actualizar PWA en Cloudflare con URL API correcta
2. Desplegar Lambdas (ms-usuarios, ms-incidencias)
3. Configurar DynamoDB Streams
4. Desarrollar Lambda de réplica (sync a SQLite)
5. Crear dashboards en Grafana

---

*Documento actualizado: 16 Mayo 2026*
*Proyecto: Valle del Sol - Gestión de Incendios*
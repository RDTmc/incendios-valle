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
│   └── docker-compose.yml
└── ARQUITECTURA.md              → Este archivo
```

## Servicios AWS

| Servicio | Uso | Notas |
|----------|-----|-------|
| S3 | Almacenamiento fotos | Bucket: incendios-valle-sol |
| DynamoDB | Tablas users, reports | Fuente de verdad |
| Lambda | Funciones serverless | ms-usuarios, ms-incidencias |
| EC2 | FastAPI + Grafana | t3.micro (LabRole) |
| Elastic IP | IP fija para EC2 | ~$1.20 USD/mes |

## Flujo de Datos (Arquitectura)

```
App (PWA)
    ↓
DynamoDB (Fuente de verdad)
    ↓
DynamoDB Streams
    ↓
Lambda Réplica (pendiente)
    ↓
FastAPI (EC2)
    ↓
SQLite (caché solo lectura)
    ↓
Grafana (dashboards)
```

## Flujo de Despliegue

### 1. Frontend → Cloudflare Pages
- Rama: main
- Carpeta: frontend/
- URL: https://incendios-valle.pages.dev

### 2. Lambdas → AWS Lambda
- Carpeta: lambda/
- Despliegue manual (zip + upload AWS Console)

### 3. API + Grafana → EC2 (BUILD MODE)
- Compilar en PC local → docker build
- Guardar imagen → docker save
- Transferir a EC2 → scp
- Cargar imagen → docker load
- Ejecutar con volúmenes

## Seguridad

- ❌ NO credenciales .env en EC2 (usa LabRole)
- ❌ NO git clone en EC2
- ✅ Elastic IP fija (asociada a cuenta)
- ❌ NO SonarQube en EC2 (ejecutar local)

## Notas Importantes

1. EC2 debe ser t3.micro (cuenta académica)
2. Security Group: SSH solo desde tu IP
3. VPC personalizada con subnet pública
4. SQLite: volumen compartido entre FastAPI y Grafana

## Roadmap de Desarrollo

| Week | Componente | Estado |
|------|------------|--------|
| 1 | AWS Setup (S3, DynamoDB, EC2) | ✅ |
| 2 | PWA Frontend + Cloudflare | ✅ |
| 3 | FastAPI + Docker EC2 | 🔄 BUILD |
| 3 | Lambda ms-usuarios, ms-incidencias | ⏳ |
| 4 | Lambda ms-notifications | ⏳ |
| 4 | DynamoDB Streams + SQLite | ⏳ |
| 5 | Grafana dashboards | ⏳ |

---

## Comandos BUILD (PC Local → EC2)

```powershell
# 1. Compilar imagen
cd incendios-valle/ec2
docker build -t incendios-api:latest ./api

# 2. Guardar imagen
docker save -o incendios-api.tar incendios-api:latest

# 3. Transferir a EC2 (con Elastic IP)
scp -i incendios-key.pem incendios-api.tar ec2-user@<ELASTIC-IP>:~/

# 4. En EC2: cargar imagen
docker load -i incendios-api.tar

# 5. Ejecutar (con volúmenes)
docker run -d -p 8000:8000 -v ./data:/app/data incendios-api:latest
```
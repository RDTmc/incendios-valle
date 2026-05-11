# Arquitectura del Proyecto

## Estructura del Repositorio

```
incendios-valle/
├── frontend/               → Cloudflare Pages (deploy automático)
├── lambda/
│   ├── usuarios/           → AWS Lambda (login/register)
│   └── ms-incidencias/     → AWS Lambda (reportes)
├── ec2/
│   ├── api/                → FastAPI (EC2 Docker)
│   └── docker-compose.yml
```

## Servicios AWS

| Servicio | Uso | Límites AWS Academy |
|----------|-----|---------------------|
| S3 |存储 fotos de reportes | ✅ Ilimitado |
| DynamoDB | Tablas users, reports | ✅ On-demand |
| Lambda | Funciones serverless | ✅ 1M invocaciones/mes |
| EC2 | FastAPI + Grafana | ⚠️ t3.micro solo |
| API Gateway | HTTP endpoints | ✅ 1M llamadas/mes |

## Flujo de Despliegue

### 1. Frontend → Cloudflare Pages
- Rama: main
- Carpeta: frontend/
- URL: https://incendios-valle.pages.dev

### 2. Backend Lambda → AWS Lambda
- Carpeta: lambda/
- Despliegue manual (zip + upload)

### 3. API + Grafana → EC2
- Carpeta: ec2/
- Docker compose
- Puerto 8000 (API)
- Puerto 3000 (Grafana)

## Notas Importantes

1. NO usar Elastic IP (costo extra)
2. EC2 debe ser t3.micro (cuenta académica)
3. Security Group: solo SSH desde tu IP
4. VPC personalizada con subnet pública
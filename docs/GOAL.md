# GOAL — Incendios Valle del Sol

## Meta

Plataforma PWA de gestión táctica de incendios forestales/urbanos para la Municipalidad de Valle del Sol. Permite reportar incidentes, visualizar focos activos en mapa, coordinar recursos, monitorear clima y datos satelitales (NASA FIRMS), todo con autenticación JWT, dashboard Grafana nativo SQLite, y despliegue CI/CD automatizado.

## Stack

- Backend: FastAPI + Lambdas Python (boto3, bcrypt, PyJWT)
- Frontend: React + TypeScript + Mapbox GL JS / Leaflet
- Dashboard: Grafana 10.4.8 con datasource SQLite nativo
- Infra: AWS Academy (EC2 t3.micro + DynamoDB + API Gateway + S3), Cloudflare DNS-only
- CI/CD: GitHub Actions → Docker Hub → deploy EC2 + SonarCloud SaaS
- Monitoreo: Prometheus + node_exporter + healthcheck.sh + dashboard devops

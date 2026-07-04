# Conclusión — Incendios Valle del Sol

## 1. Cumplimiento de Criterios Técnicos

### 1.1 Arquitectura Cloud-Native

El sistema implementa una arquitectura híbrida de microservicios: backend FastAPI [1] en EC2 como BFF, 5 funciones serverless AWS Lambda [2] orquestadas por API Gateway, y frontend PWA [3] desplegado en Cloudflare Pages. El pipeline CI/CD en GitHub Actions [4] automatiza tests, SonarCloud scan, Docker build y deploy a EC2.

La persistencia es dual: DynamoDB como primaria (Lambdas) y SQLite como datasource nativo para Grafana [5], con migración activa a RDS PostgreSQL y datasource Infinity JSON API (Jul 2026). Imágenes almacenadas en S3.

### 1.2 Seguridad Integral

- **Autenticación**: JWT (RFC 7519) + bcrypt + 2FA con OTP en `_otp_store` server-side (no viaja en JWT — corregido post-auditoría).
- **CORS restrictivo**: dominios permitidos configurados explícitamente.
- **Sin leak de errores**: `str(e)` eliminado de 27 endpoints.
- **Grafana sin hardcodeos**: token y password inyectados vía GitHub Secrets.

### 1.3 Calidad y Pruebas

| Métrica | Valor |
|---------|:-----:|
| Security / Reliability / Maintainability | A (1.0) — SonarCloud |
| Code Smells | 0 |
| Tests | 353 (171 backend + 172 frontend + 10 lambdas) |
| Cobertura | 88% backend / 82% frontend |

Patrones implementados: BFF, Circuit Breaker, Factory Method, Strategy (mapas), Observer (notificaciones), Composite (UI).

### 1.4 Desafío Técnico Superado

La restricción de AWS Academy LabRole (sin escritura DynamoDB desde EC2) se resolvió con persistencia dual DynamoDB + SQLite. La corrupción de imágenes JPEG por Cloudflare se mitigó con DNS-only para `api.keogh.lat`.

---

## 2. Aporte a la Comunidad

### 2.1 Canal Ciudadano

La PWA permite reportar incendios en <30 segundos con foto, GPS automático y visualización en mapa interactivo, sin necesidad de registro. Antes del proyecto, el único canal era llamada telefónica.

### 2.2 Dashboard Táctico (Grafana)

El equipo de emergencia visualiza en tiempo real: focos activos con estados coloreados, condiciones climáticas 30-30-30, focos satelitales NASA FIRMS, datos CONAF [6], y cross-filtering entre tabla de reportes y mapas.

### 2.3 Panel Admin (PWA)

Gestión municipal completa: CRUD de usuarios con roles VECINO/ADMIN, cambio de estados de reportes (PENDIENTE→ACTIVO→CONTROLADO→EXTINGUIDO), 2FA con backup codes, notificaciones y alertas en vivo con polling cada 30s.

### 2.4 Monitoreo DevOps

Métricas de servidor EC2 vía Prometheus + Grafana: CPU, memoria, disco, red, más healthcheck y alertas del sistema.

### 2.5 Stack 100% Open Source

React + TypeScript + Vite + Tailwind (frontend), Python + FastAPI + PostgreSQL/RDS (backend), Grafana + Prometheus (observabilidad), AWS Free Tier (infraestructura). Replicable por otros municipios.

---

## 3. Impacto Real

El sistema está desplegado en infraestructura cloud real: `app.keogh.lat` (PWA), `dashboard.keogh.lat` (Grafana), API Gateway + 5 Lambdas en AWS Academy, y CI/CD funcional con Docker Hub + GitHub Actions. El equipo de emergencia de Valle del Sol puede hoy:

1. Recibir reportes ciudadanos georreferenciados con fotografía.
2. Visualizar focos activos en mapa y dashboard táctico.
3. Coordinar recursos según tipo de incendio y criticidad climática.
4. Monitorear datos satelitales NASA FIRMS y alertas del sistema.
5. Gestionar usuarios, roles, estados y autenticación 2FA.

---

## 4. Referencias

[1] FastAPI. https://fastapi.tiangolo.com
[2] AWS Lambda Developer Guide. https://docs.aws.amazon.com/lambda/latest/dg/
[3] MDN Web Docs / Progressive Web Apps. https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps
[4] GitHub Actions Documentation. https://docs.github.com/en/actions
[5] Grafana SQLite Datasource. https://grafana.com/plugins/frser-sqlite-datasource/
[6] CONAF. *Estadísticas Históricas de Incendios Forestales*. https://www.conaf.cl/incendios-forestales/
[7] OWASP Authentication Cheat Sheet. https://cheatsheetseries.owasp.org/
[8] NASA FIRMS. https://firms.modaps.eosdis.nasa.gov
[9] Amazon DynamoDB Developer Guide. https://docs.aws.amazon.com/dynamodb/
[10] Prometheus Documentation. https://prometheus.io/docs/

---

*Documento generado a partir de la documentación y código fuente del proyecto. Junio 2026.*

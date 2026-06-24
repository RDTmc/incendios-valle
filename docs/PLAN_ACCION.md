# PLAN DE ACCIÓN — Auditoría 23 Jun 2026

## Propósito

Este archivo documenta los hallazgos de la auditoría completa del sistema realizada el 23 de junio de 2026, incluyendo deuda técnica detectada, riesgos asociados a cada cambio propuesto, y un plan de acción priorizado. Sirve como referencia post-compactación para retomar el trabajo sin perder contexto.

---

## 1. ESTADO ACTUAL DEL SISTEMA

### ¿Qué funciona hoy en producción?

| Componente | Estado | ¿Desde dónde? |
|-----------|:------:|---------------|
| Frontend PWA | ✅ | Cloudflare Pages (auto-deploy desde GitHub) |
| API FastAPI | ✅ | Docker container en EC2 (imagen `rdtmc/incendios-api` en Docker Hub) |
| Grafana (12 paneles SQLite) | ✅ | Docker container en EC2 |
| Prometheus + node-exporter | ✅ | Docker containers en EC2 |
| Login/Registro JWT | ✅ | FastAPI → DynamoDB con fallback SQLite |
| 2FA Email OTP | ✅ | FastAPI → Mailtrap SMTP |
| Password reset | ✅ | FastAPI → Mailtrap SMTP |
| Lambdas (5) | ✅ | AWS Lambda (versión desplegada, NO la del repo) |
| CI/CD pipeline | ✅ | GitHub Actions → Docker Hub → EC2 |

### Git: estado local vs remoto

```
GitHub (origin/main): 1c2b20b — fix: eliminar sync login
  ↓ idéntico
Local (HEAD):         1c2b20b
  ↓ cambios sin commit
Local (working dir):  test_*.py (2FA, admin status, lambda tests)
                      lambda/usuarios/app.py (bugfix null safety)
                      conftest.py (admin_2fa table)
                      Login.test.tsx (2FA frontend tests)
                      5 lambda test_*.py + 5 README.md (untracked)
                      docs/ completo (untracked)
                      frontend/coverage/ (untracked, debería estar en .gitignore)
```

### Secrets en GitHub Actions (14 actuales)

| Secret | Última actualización |
|--------|:-------------------:|
| AWS_ACCESS_KEY_ID | 29 may 2026 |
| AWS_REGION | 27 may 2026 |
| AWS_SECRET_ACCESS_KEY | 29 may 2026 |
| AWS_SESSION_TOKEN | 29 may 2026 |
| AWS_SG_ID | 27 may 2026 |
| DOCKERHUB_TOKEN | 20 may 2026 |
| DOCKERHUB_USERNAME | 20 may 2026 |
| EC2_HOST | 20 may 2026 |
| EC2_SSH_KEY | 20 may 2026 |
| EC2_USER | 20 may 2026 |
| EC2_USERNAME | 27 may 2026 |
| FIRMS_API_KEY | 6 jun 2026 |
| OWM_API_KEY | 6 jun 2026 |
| SONAR_TOKEN | 8 jun 2026 |

### Secrets FALTANTES en GitHub (solo existen en EC2 .env)

| Secret | ¿Dónde está? | ¿Riesgo? |
|--------|-------------|:--------:|
| JWT_SECRET | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| SYNC_TOKEN | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| GRAFANA_ADMIN_PASSWORD | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| GRAFANA_TOKEN | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| MAILTRAP_TOKEN | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| MAILTRAP_SENDER | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| MAILTRAP_SENDER_NAME | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |
| AWS_S3_BUCKET | Solo en EC2 `.env` | Si EC2 se destruye, se pierde |

---

## 2. ARQUITECTURA REAL DEL SISTEMA

```
Cliente PWA (Cloudflare Pages, auto-deploy desde GitHub)
    │
    ▼ api.keogh.lat (DNS-only, sin proxy Cloudflare)
    │
    ▼ API Gateway (REST, binaryMediaTypes para multipart)
    │
    ├── POST /auth           → Lambda ms-usuarios (DynamoDB users) [manual]
    ├── POST/GET/PUT /reports → Lambda ms-incidencias (DynamoDB) [manual]
    ├── POST /upload          → Lambda upload-proxy (S3) [manual]
    ├── POST /alerts          → Lambda ms-notificaciones (SNS) [manual]
    │
    └── ANY /api/{proxy+}    → HTTP_PROXY [CI/CD]
            │
            ▼ EC2 t3.micro (5 servicios Docker)
            │
            ├── nginx:80 → proxy inverso
            │   ├── /api/     → FastAPI (45 endpoints, SQLite)
            │   └── /dashboard/ → Grafana 10.4.8 (12 paneles SQLite)
            ├── Grafana  (datasource SQLite + Prometheus)
            ├── Prometheus (scrape node-exporter:9100)
            └── node-exporter (host metrics)

Servicios externos:
  - Mailtrap SMTP (OTP 2FA + password reset)
  - NASA FIRMS (focos activos satelitales)
  - OpenWeatherMap (clima)
  - CONAF/CIREN (datos incendios Chile)
  - Mapbox GL JS (mapas frontend)
  - S3 → imágenes de reportes
  - SNS Topic → sns-to-grafana Lambda → Grafana annotations
```

### Componentes CI/CD vs manuales

| Componente | ¿Cómo se deploya? | Estado |
|-----------|-------------------|:------:|
| API FastAPI | CI/CD: Docker build/push → pull + recreate | ✅ Automático |
| Frontend PWA | Cloudflare Pages (integración GitHub) | ✅ Automático |
| Grafana dashboards | CI/CD: SCP + restart condicional por hash | ✅ Automático |
| nginx config | CI/CD: SCP | ✅ Automático |
| Prometheus config | CI/CD: SCP | ✅ Automático |
| Lambdas (5) | `package_lambdas.sh` en EC2 o AWS Console | ❌ Manual |
| Cloudflare Worker | Wrangler CLI o dashboard Cloudflare | ❌ Manual |

---

## 3. DEUDA TÉCNICA DETECTADA

### 🔴 NIVEL 1 — Afecta rúbrica/presentación

| # | Deuda | ¿Qué hay que hacer? | ¿Riesgo? |
|---|-------|--------------------|:--------:|
| 1 | **Documentación desactualizada**: INFORME-GLOBAL.md dice multi-stage, /sync, CloudWatch, 3 contenedores | Corregir docs | 🟢 Nulo |
| 2 | **Lambdas desincronizadas**: repo tiene login/register separado, AWS tiene `handle_auth()` unificado. sns-to-grafana usa `urllib.request` vs `http.client` en AWS | Sincronizar repo con AWS | 🟢 Bajo |
| 3 | **Secrets críticos fuera de GitHub**: 8 secrets solo en EC2 `.env` | Agregar a GitHub Secrets | 🟢 Nulo |

### 🟡 NIVEL 2 — Seguridad/estabilidad

| # | Deuda | ¿Qué hay que hacer? | ¿Riesgo? |
|---|-------|--------------------|:--------:|
| 4 | **Grafana token hardcodeado** en `notification_service.py:13` y `package_lambdas.sh:85` | Mover a env var + GitHub Secret | 🟡 Medio |
| 5 | **Grafana password hardcodeada** en `export_dashboards.sh:14` | Mover a env var | 🟢 Bajo |
| 6 | **Bootstrap `/auth/bootstrap-admin` sin auth** | Agregar validación | 🟢 Bajo |
| 7 | **`str(e)` leaks** en admin.py:75, admin.py:213, bootstrap.py:49 | Mensaje genérico | 🟢 Nulo |

### ⚪ NIVEL 3 — Limpieza/mantención

| # | Deuda | ¿Qué hay que hacer? | ¿Riesgo? |
|---|-------|--------------------|:--------:|
| 8 | `ec2/grafana-dashboards/` (duplicado obsoleto, 3 paneles vs 12) | Eliminar | 🟢 Nulo |
| 9 | `ec2/monitoring/` (CloudWatch config inservible + dash obsoleto) | Eliminar | 🟢 Nulo |
| 10 | `.dockerignore` faltante | Crear | 🟢 Bajo |
| 11 | 3 dependencias frontend sin uso (zustand, idb, @aws-amplify/core) | Eliminar | 🟡 Medio |
| 12 | Dockerfile healthcheck `/health` vs docker-compose `/api/health` | Unificar | 🟢 Bajo |
| 13 | Trigger `lambda/**` en CI/CD que no deploya lambdas | Eliminar del trigger | 🟢 Nulo |
| 14 | `incendios-key.pem` + `incendios-api.tar` en disco local | Mover fuera del repo | 🟢 Nulo |

---

## 4. MAPA DE DEPENDENCIAS Y RIESGOS

### ¿Qué se rompe si tocamos X?

| Cambio | Se rompe | Explicación |
|--------|----------|-------------|
| `lambda/usuarios/app.py` (repo) | Nada | AWS corre la versión unificada, no la del repo |
| `lambda/usuarios/app.py` (AWS) | Login/Registro | La Lambda ms-usuarios deja de funcionar |
| API Gateway | Todo el backend serverless | Auth, reports, upload, alerts dejan de responder |
| SQLite schema | 12 paneles Grafana | Las queries SQL dependen de columnas específicas |
| `notification_service.py` hardcode | Anotaciones Grafana | Si se elimina hardcode sin configurar env var |
| `Dockerfile` FROM | Build CI/CD | Si cambia imagen base drásticamente |
| `.env` en EC2 (JWT_SECRET) | Login | Tokens JWT existentes se invalidan |
| `.env` en EC2 (GRAFANA_TOKEN) | Anotaciones Grafana | Notificaciones dejan de funcionar |
| `ec2/api/main.py` (routes) | Frontend + Grafana | Cambios en paths rompen llamadas API |

---

## 5. TESTS REALES DEL SISTEMA

| Componente | Tests | Cobertura | Archivos |
|-----------|:-----:|:---------:|----------|
| Backend | 167 | 88% | 15 test_*.py en `ec2/api/tests/` |
| Frontend | 172 | 82% | 21 test_*.tsx en `frontend/src/__tests__/` |
| Lambda upload-proxy | 2 | ~85% | `lambda/upload_proxy/test_upload_proxy.py` |
| Lambda ms-usuarios | 2 | ~85% | `lambda/usuarios/test_usuarios.py` |
| Lambda ms-incidencias | 2 | ~85% | `lambda/ms-incidencias/test_incidencias.py` |
| Lambda ms-notificaciones | 2 | ~85% | `lambda/ms-notificaciones/test_notificaciones.py` |
| Lambda sns-to-grafana | 2 | ~85% | `lambda/sns-to-grafana/test_sns_to_grafana.py` |
| **TOTAL** | **349** | — | — |

---

## 6. PLAN DE ACCIÓN PRIORIZADO

### FASE 1 — ANTES DE LA PRESENTACIÓN (urgencia máxima, riesgo nulo)

| Paso | Acción | Archivos a tocar |
|:----:|--------|-----------------|
| 1.1 | Corregir INFORME-GLOBAL.md: multi-stage → single-stage, /sync → no existe, CloudWatch → Prometheus, 3→5 contenedores, 11→12 paneles | `docs/INFORME-GLOBAL.md` |
| 1.2 | Corregir CONCLUSION.md: eliminar referencias a CloudWatch, multi-stage | `docs/CONCLUSION.md` |
| 1.3 | Corregir ARQUITECTURA.md: 3 contenedores → 5 servicios | `docs/ARQUITECTURA.md` |
| 1.4 | Corregir GOAL.md: CloudWatch → Prometheus | `docs/GOAL.md` |
| 1.5 | Commit + push de tests pendientes (lambda tests, 2FA, admin) | ~15 archivos |
| 1.6 | Agregar 8 secrets faltantes a GitHub Secrets | GitHub UI |
| 1.7 | Agregar `docs/` a `.gitignore` o commit inicial de docs | `.gitignore` |

### FASE 2 — POST-ENTREGA (mejora calidad, riesgo bajo-medio)

| Paso | Acción | Archivos a tocar | Riesgo |
|:----:|--------|-----------------|:------:|
| 2.1 | Sincronizar `lambda/usuarios/app.py` con versión unificada handle_auth | `lambda/usuarios/app.py` | 🟢 Bajo |
| 2.2 | Sincronizar `lambda/sns-to-grafana/app.py` con versión AWS (http.client) | `lambda/sns-to-grafana/app.py` | 🟢 Bajo |
| 2.3 | Agregar `.dockerignore` | `ec2/.dockerignore` | 🟢 Bajo |
| 2.4 | Eliminar `ec2/grafana-dashboards/` | `git rm -r ec2/grafana-dashboards/` | 🟢 Nulo |
| 2.5 | Eliminar `ec2/monitoring/` | `git rm -r ec2/monitoring/` | 🟢 Nulo |
| 2.6 | Corregir hardcode Grafana token en `notification_service.py` | `ec2/api/notification_service.py:13` | 🟡 Medio |
| 2.7 | Corregir hardcode Grafana token en `package_lambdas.sh` | `lambda/package_lambdas.sh:85` | 🟡 Medio |
| 2.8 | Corregir hardcode Grafana password en `export_dashboards.sh` | `ec2/export_dashboards.sh:14` | 🟢 Bajo |
| 2.9 | Unificar healthcheck (Dockerfile `/health` vs compose `/api/health`) | `ec2/api/Dockerfile`, `ec2/docker-compose.yml` | 🟢 Bajo |
| 2.10 | Eliminar trigger `lambda/**` de deploy.yml | `.github/workflows/deploy.yml:12` | 🟢 Nulo |

### FASE 3 — ARQUITECTURA (para después de la entrega)

| Paso | Acción | Riesgo |
|:----:|--------|:------:|
| 3.1 | Agregar lambdas al CI/CD (package + deploy) | 🔴 Alto |
| 3.2 | Agregar Cloudflare Worker al CI/CD (wrangler.toml) | 🟡 Medio |
| 3.3 | Eliminar dependencias frontend sin uso (zustand, idb, @aws-amplify/core) | 🟡 Medio |
| 3.4 | Corregir Bootstrap `/auth/bootstrap-admin` con auth | 🟢 Bajo |
| 3.5 | Corregir `str(e)` leaks en admin.py, bootstrap.py | 🟢 Nulo |

---

## 7. LAMBDAS: REPO vs AWS (desincronización)

### ms-usuarios — VERSIÓN DIFERENTE

| Aspecto | Repo | AWS (real) |
|---------|------|------------|
| Router | `login()`, `register()`, `get_user()` separados | `handle_auth()` unificado |
| Soporta `/auth` | ❌ No | ✅ Sí |
| Bugfix null safety | ❌ `[None]` fallback | ✅ `items[0] if items else None` |

**Archivo de origen AWS**: `lambda/update_usuarios.sh` (línea 15-122) sobrescribe `app.py` con versión unificada + compila bcrypt con Docker Lambda.

### sns-to-grafana — IMPLEMENTACIÓN DIFERENTE

| Aspecto | Repo | AWS (real) |
|---------|------|------------|
| HTTP client | `urllib.request` | `http.client.HTTPSConnection` |
| URL | `f"{GRAFANA_URL}/api/annotations"` | `dashboard.keogh.lat/api/annotations` |
| SSL verify | ✅ Sí | ❌ `ssl._create_unverified_context()` |

### ms-incidencias — CODE DEAD EN AWS

```python
# AWS (tu versión) tiene código muerto después del return:
    return {  # ← esto funciona
        'statusCode': 200,
        'body': json.dumps(items[0])
    }

    return {  # ← NUNCA se ejecuta (dead code, item no definido)
        'statusCode': 200,
        'body': json.dumps(item)
    }
```

El repo NO tiene este bug.

### ms-notificaciones — IDÉNTICO
60 líneas, misma implementación.

### upload-proxy — CONFIRMADO
- `create_api_gateway.sh:115` lo referencia
- `package_lambdas.sh` NO lo empaqueta (quedó fuera)
- Existe en `ec2/lambda/upload_proxy/` (duplicado) y `lambda/upload_proxy/` (oficial)

---

## 8. RIESGOS POR ACCIÓN (resumen ejecutivo)

| Riesgo | Significado | Acciones en esta categoría |
|:------:|-------------|---------------------------|
| 🟢 Nulo | No afecta producción, solo docs/código fuente | 1.1–1.4, 2.4–2.5, 2.10 |
| 🟢 Bajo | Cambio seguro, impacto mínimo si falla | 2.1–2.3, 2.8–2.9, 3.4–3.5 |
| 🟡 Medio | Puede romper funcionalidad si no se configura correctamente | 2.6–2.7, 3.2–3.3 |
| 🔴 Alto | Puede dejar el sistema inoperativo | 3.1 |

---

## 9. VULNERABILIDADES DE SEGURIDAD

| # | Vulnerabilidad | Archivo | Línea | Severidad |
|---|---------------|---------|:-----:|:---------:|
| 1 | Grafana token hardcodeado | `notification_service.py` | 13 | 🔴 Crítica |
| 2 | Grafana token hardcodeado | `package_lambdas.sh` | 85 | 🔴 Crítica |
| 3 | Grafana password hardcodeada | `export_dashboards.sh` | 14 | 🔴 Crítica |
| 4 | Bootstrap `/auth/bootstrap-admin` sin auth | `routers/bootstrap.py` | 19-55 | 🔴 Crítica |
| 5 | `str(e)` leaks | `admin.py` | 75, 213 | 🟡 Alta |
| 6 | `str(e)` leak | `bootstrap.py` | 49 | 🟡 Alta |
| 7 | OTP viaja en JWT (base64 decodificable) | `auth.py` | 159-164 | 🟡 Alta |
| 8 | JWT_SECRET default débil en Lambda | `lambda/usuarios/app.py` | 12 | 🟡 Media |
| 9 | SNS_TOPIC_ARN hardcodeado | `notification_service.py` | 10 | 🟡 Media |
| 10 | SSL verification deshabilitado (sns-to-grafana AWS) | `lambda/sns-to-grafana/app.py` | — | 🟡 Media |
| 11 | chmod 666/777 en scripts deploy | `restart-grafana.yml`, `refresh_api.sh` | múltiples | 🟡 Media |

---

## 10. CAMBIOS LOCALES PENDIENTES DE COMMIT

### Modificados (no commiteados)

| Archivo | Cambio |
|---------|--------|
| `ec2/api/tests/conftest.py` | Agregada tabla `admin_2fa` en fixture DB |
| `ec2/api/tests/test_auth.py` | Tests B1: login 2FA + verify OTP |
| `ec2/api/tests/test_reports.py` | Tests B6: admin update report status |
| `frontend/src/__tests__/Login.test.tsx` | Tests F1: 2FA OTP input + submit |
| `lambda/usuarios/app.py` | Bugfix: `[None]` → `items[0] if items else None` |

### Nuevos (untracked)

| Archivos | Descripción |
|----------|-------------|
| `docs/` | Toda la documentación del proyecto |
| `lambda/*/test_*.py` (5 archivos) | Tests para cada lambda (2 c/u) |
| `lambda/*/README.md` (5 archivos) | READMEs para cada lambda |
| `frontend/src/__tests__/AdminPage.test.tsx` | Tests AdminPage |
| `frontend/src/__tests__/ForgotPassword.test.tsx` | Tests ForgotPassword |
| `ec2/api/tests/test_password_reset.py` | Tests password reset |
| `ec2/api/README.md` | README backend |
| `frontend/README.md` | README frontend |
| `incendios-valle-entrega.zip` | ZIP de entrega |
| `frontend/coverage/` | Reportes de cobertura HTML |

---

## 11. WORKFLOWS CI/CD (4 activos)

| Workflow | Disparo | Steps | Propósito |
|----------|---------|:-----:|-----------|
| `deploy.yml` | Push a `main` (paths específicos) + `workflow_dispatch` | 12 | Tests → SonarCloud → Docker build/push → SCP → SSH deploy |
| `restart-grafana.yml` | `workflow_dispatch` | 3 | SCP provisioning → restart Grafana |
| `audit.yml` | `workflow_dispatch` | 1 | Read-only: docker ps, configs, logs |
| `fix-permissions.yml` | `workflow_dispatch` | 1 | chown 472:472 + chmod 664 en SQLite |

### deploy.yml — Detalle de 12 steps

1. Checkout code (fetch-depth: 0)
2. Set up Python 3.11
3. Install backend test deps (requirements-dev.txt + pytest-cov)
4. Run backend tests (pytest, 167 tests, coverage.xml)
5. Set up Node 20 (con cache npm)
6. Install frontend deps (npm ci)
7. Run frontend tests (vitest, 172 tests)
8. SonarCloud Scan
9. Set up Docker Buildx
10. Login to Docker Hub
11. Extract metadata (sha + latest tags)
12. Build and push Docker image (`ec2/api/Dockerfile`, context=`.`)
13. SCP configs a EC2 (refresh_api.sh, docker-compose.yml, export_dashboards.sh, prometheus, nginx)
14. SCP grafana provisioning a EC2
15. SSH deploy: sanitiza .env, inyecta FIRMS/OWM, refresh_api.sh, restore SQLite, permisos, restart Grafana condicional

### deploy.yml — Secrets inyectados (solo 2 de 10 necesarios)

| Secret | ¿En GitHub? | ¿Se inyecta? |
|--------|:-----------:|:------------:|
| DOCKERHUB_USERNAME | ✅ | ✅ |
| DOCKERHUB_TOKEN | ✅ | ✅ |
| SONAR_TOKEN | ✅ | ✅ |
| FIRMS_API_KEY | ✅ | ✅ |
| OWM_API_KEY | ✅ | ✅ |
| **JWT_SECRET** | ❌ | ❌ |
| **SYNC_TOKEN** | ❌ | ❌ |
| **GRAFANA_ADMIN_PASSWORD** | ❌ | ❌ |
| **GRAFANA_TOKEN** | ❌ | ❌ |
| **MAILTRAP_TOKEN** | ❌ | ❌ |
| **MAILTRAP_SENDER** | ❌ | ❌ |
| **MAILTRAP_SENDER_NAME** | ❌ | ❌ |
| **AWS_S3_BUCKET** | ❌ | ❌ |
| EC2_HOST | ✅ | ✅ |
| EC2_USERNAME | ✅ | ✅ |
| EC2_SSH_KEY | ✅ | ✅ |
| AWS_SG_ID | ✅ | ❌ (no se usa en ningún step) |

---

## 12. BRANCHES EN GITHUB

| Branch | Protegida | Estado |
|--------|:---------:|--------|
| `main` | ✅ Sí | Rama principal, CI/CD activo |
| `develop` | ❌ No | Desarrollo |
| `developer` | ❌ No | Desarrollo alternativo |
| `feature/flujo-hibrido-auth` | ❌ No | Feature: auth híbrido |
| `feature/pipeline-ssh-deploy` | ❌ No | Feature: SSH deploy |
| `feature/pwa-icons-installable` | ❌ No | Feature: PWA icons |
| `feature/pwa-instalacion-forzada` | ❌ No | Feature: instalación forzada PWA |
| `feature/sg-elastic-deploy` | ❌ No | Feature: security group elástico |

---

## 13. ARCHIVOS MUERTOS / BASURA TÉCNICA

| Ruta | Problema | Tamaño aprox |
|------|----------|:-----------:|
| `ec2/grafana-dashboards/` | Duplicado obsoleto (3 paneles vs 12 en provisioning) | ~50 KB |
| `ec2/monitoring/` | CloudWatch config inservible + dashboard obsoleto + healthcheck | ~15 KB |
| `ec2/lambda/upload_proxy/` | Duplicado de `lambda/upload_proxy/` | ~3 KB |
| `ec2/incendios-key.pem` | Clave privada SSH en disco (¡no tracked!) | ~2 KB |
| `ec2/incendios-api.tar` | Tarball imagen Docker (~200MB) | ~200 MB |
| `ec2/seed_admin.py` | Parchea módulos internos, expone servidor | ~10 KB |
| `ec2/*.py` (18 scripts sueltos en raíz) | Scripts one-time, debug, parches | ~50 KB |
| `s3_service.py` | Código completo nunca llamado desde endpoints | ~3 KB |
| `ec2/api/debug/` (28 archivos) | Scripts debug/parche, no deberían estar | ~100 KB |

---

## 14. REGLAS PARA PRÓXIMAS SESIONES

1. **Antes de editar el repo**, leer este archivo para entender el estado actual y los riesgos
2. **No tocar lambdas en AWS directo** — sincronizar primero el repo, luego deployar
3. **No agregar lambdas al CI/CD** sin antes sincronizar repo con AWS
4. **Priorizar FASE 1** para la presentación (documentación + secrets + tests)
5. **Dejar FASE 3 para después** (no arriesgar estabilidad antes de la entrega)
6. **Verificar secrets** después de agregarlos: el CI/CD debe poder leerlos
7. **No confiar en docs antiguos** — verificar contra código antes de escribir
8. **Si hay duda entre repo y AWS**, AWS es la fuente de verdad para lo que funciona

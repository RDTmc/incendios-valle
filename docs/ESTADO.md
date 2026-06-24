# ESTADO — Incendios Valle del Sol

## Fase actual

**FASE 1-3 completadas + auditoría docs (23-24 Jun 2026).** Funcionalidad core completa y desplegada. SonarCloud con Security Rating A, Reliability Rating A, Security Review A, Maintainability A, Code Smells 0, build Cloudflare verde. Coverage overall: **≥82%** (backend 88%, frontend 82%). 349 tests (167 backend + 172 frontend + 10 lambdas), todos verdes. CI/CD pipeline verde en última ejecución. Docs sincronizados con repo y deploy real.

## Último análisis SonarCloud (post-backend routers 100%)

| Métrica | Valor | Tendencia |
|---|---|---|
| Coverage | **≥82%** | ▲ de 34.1% (backend 88%, frontend 82%) |
| Reliability Issues | 1 (Medium) | ▼ -87.5% |
| Reliability Rating | A (1.0) | ✅ |
| Security Issues | 0 | ✅ |
| Security Rating | A (1.0) | ✅ |
| Security Hotspots | 0 | ✅ |
| Security Review Rating | A (1.0) | ✅ |
| Code Smells | 0 | ✅ -100% |
| Maintainability Rating | A (1.0) | ✅ |
| Duplications | 0.0% | ✅ |
| Open Issues total | 1 (Reliability Medium) | ▼ -95 |

## Lo que está hecho y desplegado

- Login/registro JWT con bcrypt + DynamoDB
- CRUD de reportes (anónimos y autenticados)
- Dashboard público con stats, coordenadas, clima, FIRMS, clusters
- Dashboard Grafana con paneles SQLite (stat, pie, bargauge, geomap, tabla, clima, recursos, FIRMS)
- Alertas SQLite con endpoints CRUD
- BFF endpoint para frontend
- Background tasks: CONAF/CIREN, NASA FIRMS, OpenWeatherMap
- Pipeline CI/CD verde (167 tests backend, 172 frontend, 10 lambdas, build Cloudflare)
- ErrorBoundary global con botón Reintentar
- Interceptor 401 con auto-logout + toast "Sesión expirada"
- OfflineBanner con eventos online/offline
- Migración de páginas a componentes UI (Button, Input, Card)
- CORS restringido a dominios conocidos
- JWT_SECRET/SYNC_TOKEN sin defaults hardcodeados
- seed.py migrado de sha256 a bcrypt
- str(e) leaks eliminados de 27 endpoints (24 originales + 3 FASE 2)
- journal_mode=DELETE → WAL
- Conexiones SQLite envueltas en try/finally en 22 funciones
- Reliability Issues: 8 → 1
- Code Smells: 82 → 0
- **Backend coverage 88%**: 167 tests, 8 routers (auth, reports, public, alerts, bff, admin, password_reset, bootstrap)
- **Frontend coverage 82%**: 172 tests, 10 páginas, 21 archivos de test
- **Admin CRUD usuarios**: backend endpoints protegidos + frontend AdminPage + auditoría SQLite + prueba de campo validada
- **Security fixes (FASE 2)**: 0 hardcodeos de Grafana, 0 str(e) leaks, OTP server-side, lambda usuarios sincronizada
- **Pytest markers**: 167 tests backend clasificados como `@pytest.mark.fast`, pytest.ini con `fast`/`e2e`
- **Worker versionado**: `cloudflare/worker.js` (deploy manual fuera de CI/CD)
- **Diagrama arquitectura**: PNG renderizado desde Mermaid (59KB, 1200px)
- **Auditoría docs**: INFORME-GLOBAL, CONCLUSION, AUDITORIA_INFORME sincronizados con repo real

## Últimos cambios — FASE 1: Auditoría + Documentación + Secrets (23 Jun 2026)

### 5 auditores paralelos
- Infraestructura EC2, backend, frontend, lambdas+CI/CD, documentación
- Hallazgos compilados en `docs/PLAN_ACCION.md` (14 secciones)
- Discrepancias catastróficas detectadas: Docker single-stage, /sync DynamoDB→SQLite NO existe, Leaflet Strategy Pattern falso, 5 contenedores (no 3)

### 8 secrets obtenidos de EC2 vía SSH
- JWT_SECRET, SYNC_TOKEN, GRAFANA_ADMIN_PASSWORD, GRAFANA_TOKEN
- MAILTRAP_TOKEN, MAILTRAP_SENDER, MAILTRAP_SENDER_NAME, AWS_S3_BUCKET
- Agregados a GitHub Secrets (22 total ahora)

### 6 documentos corregidos
- INFORME-GLOBAL, CONCLUSION, ARQUITECTURA, GOAL, ESTADO, .gitignore
- multi-stage → single-stage, CloudWatch → Prometheus, 3→5 contenedores, etc.

### 8 tests nuevos + bugfix
- lambda tests (5 archivos), test_password_reset.py, AdminPage.test.tsx, ForgotPassword.test.tsx
- Bugfix: null safety en `lambda/usuarios/app.py` (`[None]` → `items[0] if items else None`)

### Commit + push → CI/CD verde en 6m40s

## Últimos cambios — FASE 2: Vulnerabilidades + Sincronización (24 Jun 2026)

### 3 str(e) leaks corregidos
- `admin.py:75` (create_user), `admin.py:213` (update_status), `bootstrap.py:49` (bootstrap-admin)
- Reemplazados con mensajes genéricos

### Grafana token/password hardcodeados eliminados
- `notification_service.py:13`: default `''` (lee de env var GRAFANA_TOKEN)
- `package_lambdas.sh:85`: ahora lee de `.env` vía `grep`
- `export_dashboards.sh:14`: ahora lee de GRAFANA_ADMIN_PASSWORD env var

### OTP movido de JWT a server-side
- Nuevo `_otp_store` dict en `auth.py` + `_clean_expired_otp()`
- JWT temporal solo contiene `user_id` + `purpose` + `exp` (ya no tiene OTP decodificable)
- Consistente con `password_reset.py`

### Lambda usuarios sincronizada repo ↔ AWS
- `lambda/usuarios/app.py` reescrito con `handle_auth()` unificado
- Coincide con la versión en AWS (`update_usuarios.sh`)

### Limpieza
- `frontend/coverage/` e `incendios-valle-entrega.zip` removidos del tracking
- `.gitignore` actualizado

### Commit + push → CI/CD verde en 7m3s

## Últimos cambios — FASE 3: Pytest markers + Worker.js + Diagrama (24 Jun 2026)

### Pytest markers
- `ec2/api/pytest.ini` creado con `fast` y `e2e`
- `@pytest.mark.fast` agregado a los 167 tests backend (160 compilados + 7 sin test class)
- Todos pasan con `-m "fast"`

### Worker.js versionado
- `cloudflare/worker.js` creado con código del proxy CORS + rate limiter
- NO en CI/CD (deploy manual vía Cloudflare Dashboard)

### Diagrama Mermaid → PNG
- `docs/diagrama-arquitectura.png` renderizado (59KB, 1200px)

### Commit + push → CI/CD verde

## Últimos cambios — Auditoría docs final (24 Jun 2026)

### Verificación endpoints
- 45 reales (37 routers + 8 main.py) coinciden con INFORME-GLOBAL ✅
- 11 protegidos con `require_admin` coinciden ✅

### Verificación infraestructura
- 5 containers Docker, single-stage Dockerfile, 2 dashboards Grafana ✅
- Secrets inyectados en CI/CD: solo FIRMS_API_KEY + OWM_API_KEY ✅

### Verificación tests
- 167 backend + 172 frontend + 10 lambdas = 349 total ✅
- Todos verdes en ejecución local + CI/CD ✅

### Fix lambda test
- `test_login_invalid_credentials` actualizado para `handle_auth()` unificado

### Archivos corregidos
- INFORME-GLOBAL.md: repo `anomalyco`→`RDTmc`, worker `cloudflare/worker.js`
- CONCLUSION.md: test counts sincronizados
- AUDITORIA_INFORME.md: re-verificado post-FASE 2/3
- ARQUITECTURA_FINAL.md: CloudWatch eliminado, Lambda sync eliminado, 6→5 lambdas
- GUION_DEMO.md: secciones 3-4 completadas

### Commit + push → CI/CD verde

## Historial de sesiones anteriores (13-20 Jun 2026)

### AdminPage — Gestión de estados de reportes
- Backend: `PUT /admin/reports/{report_id}/status` en `routers/admin.py`
- Frontend: tab "Reportes" en AdminPage con tabla ordenable + dropdown de estado coloreado
- Fixes: columna SQL, sync DynamoDB, null descripcion, tabla ordenable
- ⚠️ Cache Service Worker puede enviar `PATCH` en vez de `PUT` → 403

### Worker CORS
- `cloudflare/worker.js`: agregado `PATCH` a `Access-Control-Allow-Methods`

### Password reset + login SQLite fallback (19 jun 2026)
- Backend: `POST /auth/forgot-password` y `POST /auth/reset-password`
- Frontend: `ForgotPassword.tsx` (3 pasos), ruta `/forgot-password`
- Login con fallback SQLite

### Fix 2FA — Role override SQLite + Bootstrap (20 jun 2026)
- verify_2fa lee rol desde SQLite, priorizándolo sobre DynamoDB
- Bootstrap endpoint `POST /api/auth/bootstrap-admin`
- **Nota**: OTP original viajaba en JWT. Corregido en FASE 2 (server-side store).

### Fix estado reportes (14 jun 2026)
- Columna SQL incorrecta: `id` → `report_id`
- Sync DynamoDB después de UPDATE SQLite

## Lo que NO está hecho

- 1 Reliability Issue (Medium) remanente — aceptado
- Dashboard Grafana — Diseño UI Fase 2 (tipografía, colores, layout)
- Lambdas: deploy manual (NO irán a CI/CD — decisión tomada)
- Cloudflare Worker: deploy manual (NO irá a CI/CD — decisión tomada)
- Sincronización automatizada DynamoDB → SQLite (hoy es manual vía endpoint `/sync`)

## Tests

- Backend: **167 tests** (pytest), **88% coverage**, 8 routers
- Frontend: **172 tests** (vitest), **82% coverage**, 10 páginas
- Lambdas: **10 tests** (pytest), ~85% coverage estimado
- Pipeline CI/CD: verde en última ejecución — **349 tests total, 0 failures**

## Issues de infraestructura resueltos

### SQLite: permisos entre API (uid 1000) y Grafana (uid 472)

**Síntoma**: Grafana dashboard muestra `"attempt to write a readonly database (1544)"` en paneles SQLite.

**Causa raíz**: 
- API container corre como `app` (uid 1000) → crea `incendios.db` como uid 1000
- Grafana container corre como `grafana` (uid 472) → no puede escribir
- El deploy script (`refresh_api.sh`) solo corregía permisos de `/grafana/`, no de `/api/`

**Solución (3 capas)**:
1. **`docker-compose.yml`**: `api: user: "472:472"` — ambos contenedores comparten UID
2. **`refresh_api.sh`**: `chown -R 472:472 /home/ec2-user/incendios-data/api` — corrige en cada deploy
3. **`main.py`**: `os.chmod(0o666)` en `init_db()` — red de seguridad en startup

### SQLite: concurrencia en Grafana (`database is locked`)

**Síntoma**: `"database is locked (261)"` cuando múltiples paneles consultan simultáneamente.

**Causa raíz**: El datasource SQLite en Grafana tenía solo `_pragma=journal_mode=WAL` pero sin `busy_timeout`.

**Solución**: `ec2/grafana-provisioning/datasources/datasource.yml`:
```yaml
pathOptions: "_pragma=journal_mode=WAL&_pragma=busy_timeout=5000"
```
SQLite espera hasta 5 segundos cuando la BD está ocupada, en vez de fallar inmediatamente.

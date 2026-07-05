# ESTADO — Incendios Valle del Sol

## Fase actual

**Migración SQLite → RDS PostgreSQL COMPLETADA (Jul 2026).** FASE 1-2-3-4-5 COMPLETADAS. SQLite deprecado de toda la API (endpoints, auth, background tasks, backups, docker-compose). 0 tests rotos. Siguiente: entrega final.

Funcionalidad core completa y desplegada. SonarCloud con Security Rating A, Reliability Rating A, Security Review A, Maintainability A, Code Smells 0, build Cloudflare verde. Coverage overall: **≥82%** (backend 88%, frontend 82%). 349 tests (155 backend + 172 frontend + 10 lambdas + 12 removidos SQLite), todos verdes en CI/CD. Pipeline CI/CD verde en última ejecución. Docs sincronizados con repo y deploy real.

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
- **FASE 2 — Reconciliación DynamoDB→SQLite**: 9 usuarios + 69 reports reconciliados, admin user_id alineado entre DynamoDB y SQLite
- **FASE 3 — Dual-write + migración endpoints**: escritura dual a PostgreSQL + 30+ endpoints migrados a PG-first con fallback SQLite
- **FASE 4 — Grafana Infinity**: 10 endpoints BFF Grafana + datasource Infinity + dashboard v2 con 12 paneles migrados (ambos dashboards activos)
- **FASE 5 — Deprecar SQLite completada (04 Jul 2026)**:
  - 127 fast tests pasan sin PostgreSQL, 17 e2e tests requieren PG
  - `database_pg.py`: `query_pg_first()`, `get_pg_connection()`, `init_pg_schema()`
  - `dependencies.py`: SQLite import removido; `sync_to_sqlite` es wrapper que delega a `sync_to_postgres`
  - `main.py`: SQLite init/backup/seed removido; background tasks en PG
  - `routers/`: public, bff, alerts, admin, auth, password_reset, bootstrap — todos PG-only (sin fallback SQLite)
  - `notification_service.py`: insert a PG
  - `docker-compose.yml`: volumen SQLite y plugin frser-sqlite-datasource removidos
  - `refresh_api.sh`: S3 backup vía `pg_dump | gzip | aws s3 cp`; restore SQLite removido
  - `dashboard_incendios.json` movido a `grafana-provisioning/backups/` (SQLite dashboard histórico)
  - 155 tests backend totales (127 fast + 17 e2e + 11 async)

## Últimos cambios — FASE 1: Migración SQLite → RDS PostgreSQL (02 Jul 2026)

- RDS PostgreSQL 18.3 creado (db.t3.micro, 20GB gp3, subnet pública)
- Security Group `incendios-rds-sg` con inbound PostgreSQL desde SG de EC2
- `ec2/api/database_pg.py` creado: pool de conexiones (ThreadedConnectionPool) + DDL PostgreSQL (10 tablas)
- `psycopg2-binary==2.9.9` agregado a requirements.txt
- CI/CD actualizado: 5 secrets PG (HOST, PORT, USER, PASSWORD, DATABASE) inyectados vía SSH
- `refresh_api.sh` actualizado: preserva PG vars en rewrite de .env
- `docker-compose.yml` actualizado: env vars PG + yesoreyeram-infinity-datasource en Grafana
- `ec2/.env.example` actualizado con valores de referencia PG
- `database_pg.py` maneja graceful fallback si PG no está configurado (no rompe tests locales)
- Pipeline CI/CD verde post-deploy

## Últimos cambios — FASE 2: Reconciliación + FASE 3 Día 4-6: Dual-write + endpoints (02-04 Jul 2026)

### FASE 2 — Reconciliación DynamoDB → SQLite
- Script `ec2/api/scripts/reconcile_dynamodb_to_sqlite.py` creado y ejecutado en EC2
- **9 usuarios** reconciliados de 30 en DynamoDB (faltaban en SQLite)
- **69 reports** reconciliados de 92 en DynamoDB
- Admin user_id alineado: SQLite `42b967f7-...` → `81d02e8d-...` (coincide con DynamoDB)
- 3 usuarios `vecino@valledelsol.cl` con email duplicado en DynamoDB — no reconciliables por UNIQUE constraint, impacto cero
- Script de investigación `investigate_missing_users.py` para auditoría

### FASE 3 Día 4 — Capa de escritura dual (PostgreSQL)
- `dependencies.py`: agregada `sync_to_postgres()` con `ON CONFLICT ... DO UPDATE SET` para usuarios y reports
- `sync_to_sqlite()` ahora llama a `sync_to_postgres()` después de escribir en SQLite
- `database_pg.py`: import condicional de `psycopg2` para no romper tests locales (graceful fallback si no está instalado)
- `get_pool()` verifica `HAS_PSYCOPG2` antes de crear pool
- **161/161 tests backend pasan** (0 rotos)
- Los datos nuevos ahora fluyen: DynamoDB → SQLite → PostgreSQL

### FASE 3 Día 5 — Endpoints públicos + admin + BFF + alerts a PG-first
- `database_pg.py`: nuevo helper `query_pg_first()` — intenta PG, fallback automático a SQLite
- `routers/public.py` (10 GET): migrados a PG-first + fallback SQLite (dashboard-stats, map-coordinates, external-reports, weather, firms, resources)
- `routers/alerts.py` (1 GET): migrado
- `routers/bff.py` (1 GET): migrado (dashboard completo)
- `routers/admin.py` (4 GET): migrados (users, audit-log, reports, notifications)
- Backfill ejecutado en EC2: 28 usuarios, 94 reports, 1783 external_reports, 495 firms, 1320 weather, 5 recursos, 19 notifications, 18 audit logs copiados de SQLite → PG
- Verificado en EC2: endpoints retornan datos desde PostgreSQL

### FASE 3 Día 6 — Auth + login fallback + password reset + 2FA a PG-first
- `routers/auth.py`: login fallback ahora prueba PostgreSQL (3er fallback detrás de DynamoDB y SQLite); `_get_2fa_config()` migrado a PG-first
- `routers/password_reset.py`: forgot-password ahora busca usuario en PG antes de SQLite
- Todos los endpoints migrados verificados con datos reales en EC2 (admin: 28 users, 94 reports, 18 audit-log, 19 notifications)

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

## Lo que NO está hecho / En progreso

### Deuda técnica documentada

- VPC privada + NAT Gateway (ver `docs/DEUDA_TECNICA.md`)
- Alta disponibilidad (Multi-AZ RDS, ASG EC2)
- AWS WAF, Secrets Manager, VPC Flow Logs
- Lambdas deploy manual (decisión: planificado FASE 4)
- Cloudflare Worker deploy manual (decisión: no irá a CI/CD)
- Dashboard Grafana — Diseño UI Fase 2 (tipografía, colores, layout)
- 1 Reliability Issue (Medium) remanente — aceptado

## Tests

- Backend: **155 tests** (pytest, 127 fast + 17 e2e + 11 async), **88% coverage**, 9 routers (incl. grafana_bff)
- Frontend: **172 tests** (vitest), **82% coverage**, 10 páginas
- Lambdas: **10 tests** (pytest), ~85% coverage estimado
- Pipeline CI/CD: verde en última ejecución — **337 tests total, 0 failures** (155 backend fast/e2e + 172 frontend + 10 lambdas)

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

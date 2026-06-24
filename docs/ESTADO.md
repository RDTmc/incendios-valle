# ESTADO — Incendios Valle del Sol

## Fase actual

Funcionalidad core completa y desplegada. SonarCloud con Security Rating A, Reliability Rating A, Security Review A, Maintainability A, Code Smells 0, build Cloudflare verde. Coverage overall: **≥82%** (backend 88%, frontend 82%).

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
- str(e) leaks eliminados de 24 endpoints
- journal_mode=DELETE → WAL
- Conexiones SQLite envueltas en try/finally en 22 funciones
- Reliability Issues: 8 → 1
- Code Smells: 82 → 0
- **Backend coverage 88%**: 167 tests, 8 routers (auth, reports, public, alerts, bff, admin, password_reset, bootstrap)
- **Frontend coverage 82%**: 172 tests, 10 páginas, 21 archivos de test
- **Admin CRUD usuarios**: backend endpoints protegidos + frontend AdminPage + auditoría SQLite + prueba de campo validada

## Últimos cambios — Sesión 13 jun 2026

### AdminPage — Gestión de estados de reportes
- Backend: `PUT /admin/reports/{report_id}/status` en `routers/admin.py` (commit `ac520f8`, original PATCH → PUT)
- Frontend: tab "Reportes" en AdminPage con tabla ordenable + dropdown de estado coloreado
- Fixes aplicados:
  - `r.id` → `r.report_id` (commit `e1b7c2b`)
  - `r.latitud?.toFixed(4)` → `Number(r.latitud).toFixed(4)` (commit `95c8e4a`)
  - Null descripcion short-circuit (commit `95c8e4a`)
  - Tabla ordenable por columna + logo municipal blanco (commit `65e223c`)
  - PATCH → PUT para compatibilidad API Gateway (commit `ac520f8`)
- ⚠️ **Bloqueado**: navegador del usuario sirve JS cacheados (Service Worker), envía `PATCH` en vez de `PUT`. API Gateway responde `IncompleteSignatureException` (403).

### Worker CORS
- `cloudflare-worker.js`: agregado `PATCH` a `Access-Control-Allow-Methods`, desplegado manualmente

### Password reset + login SQLite fallback (19 jun 2026)
- Backend: `POST /auth/forgot-password` y `POST /auth/reset-password` en `routers/password_reset.py`
- Frontend: `ForgotPassword.tsx` (3 pasos: email → OTP+contraseña → éxito), ruta `/forgot-password`
- Login con fallback SQLite: si DynamoDB no encuentra usuario, prueba SQLite
- Tests: 167 backend + 172 frontend, todos verdes ✅

### Fix 2FA — OTP en JWT + Role override SQLite (20 jun 2026)
- OTP viaja dentro del JWT `temp_token` (sin store externo — ni memoria ni SQLite)
- verify_2fa lee rol desde SQLite, priorizándolo sobre DynamoDB
- Bootstrap endpoint `POST /api/auth/bootstrap-admin` para recuperar acceso admin
- Prueba de campo exitosa, login admin funcional ✅

## Últimos cambios — Sesión 14 jun 2026

### Fix 500 al cambiar estado — columna SQL incorrecta
- **Problema**: `admin_update_report_status` usaba `WHERE id = ?` pero la columna en SQLite se llama `report_id` → SQLException → 500
- **Fix**: `SELECT id` → `SELECT report_id`, `WHERE id` → `WHERE report_id` en `admin.py:132-135`
- Commits: `a7323fe`
- CI/CD verde ✅

### Fix dropdown no actualiza — sync DynamoDB
- **Problema**: `admin_update_report_status` solo actualizaba SQLite, pero `list_reports` lee de DynamoDB → dropdown seguía viendo estado viejo
- **Fix**: agregar `repo.update(report_id, estado=estado_upper)` después del UPDATE SQLite para sincronizar DynamoDB
- Commit: incluido en `a7323fe`

## Lo que NO está hecho

- 1 Reliability Issue (Medium) remanente — aceptado
- Dashboard Grafana — Diseño UI Fase 2 (tipografía, colores, layout)
- Lambdas no están en pipeline CI/CD (deploy manual todas)
- Cloudflare Worker no está en pipeline CI/CD (deploy manual)
- Sincronización automatizada DynamoDB Streams → SQLite (hoy es manual vía endpoint `/sync`)

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

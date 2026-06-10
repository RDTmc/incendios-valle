# TAREAS — Incendios Valle del Sol

Orden de prioridad. NO saltarse pasos sin consultar al usuario.

## ✅ COMPLETADO (junio 2026 — lote notificaciones)

### SNS + Grafana annotations pipeline
- **SNS welcome notification**: `notification_service.notify_new_user()` publica JSON a SNS topic `incendios-alerts` y guarda en SQLite (`notifications` table)
- **Backend endpoints**: `POST /register` y `POST /admin/create-user` llaman `notify_new_user`
- **Admin panel Notificaciones**: tab en AdminPage con historial (email, nombre, status, SNS ID, fecha)
- **Grafana annotation directa desde API**: `_create_grafana_annotation()` POSTea a `http://incendios-grafana:3000/api/annotations` vía Docker internal network. Se eliminó dependencia de Lambda sns-to-grafana (devolvía 403).
- **Grafana token persistido**: agregado `GRAFANA_TOKEN` a docker-compose.yml y refresh_api.sh
- **Commit**: `0b8ac34` (Grafana directo desde API, salta Lambda)

### PWA UX improvements
- **Historial**: spinner + toast error en carga/fallo
- **AdminPage**: spinner + toast en cada tab (Usuarios, Auditoría, Notificaciones)
- **Confirmacion**: guard contra navegación directa + toast warning si no hay location state
- **Reporte**: spinner animado durante upload de foto
- **AlertBanner**: loading spinner inicial mientras carga alertas

### Cobertura final
- Backend: **157 tests**, routers 100%, overall **97%**
- Frontend: **165 tests**, **96.49%** coverage, MapboxStrategy 100%
- **Total: 322 tests, 0 failures**

### Lotes anteriores (completados)
- Security Rating: C → A (0 issues, 0 hotspots)
- Security Review Rating: E → A (todos revisados)
- Reliability Rating: C → A (1 Medium issue remanente en frontend)
- ErrorBoundary global con botón Reintentar
- Interceptor 401: auto-logout + toast "Sesión expirada"
- OfflineBanner con eventos online/offline
- Migración a componentes UI (Button, Input, Card)
- Grafana: restart limpio y permisos SQLite corregidos
- Datasource SQLite: WAL mode + busy_timeout para concurrencia
- **Fix SQLite readonly (1544)**: API como uid 472, chown en deploy, chmod en startup
- **Fix SQLite locked (261)**: busy_timeout=5000 en datasource Grafana
- **8 Reliability Issues (Medium) → 1**: backend (try/finally en 22 conexiones DB + dead code) + frontend (parseFloat→Number.parseFloat, isNaN→Number.isNaN, labels con htmlFor)
- **Pipeline CI/CD verde**: 322 tests
- **Code Smells: 82 → 0** — 4 batches completados
- **Fix build Cloudflare**: tipo navigate en renderReportList + exclude __tests__ de tsc
- **Coverage backend**: 97% overall, routers 100%, s3_service/lambda_service 0→100%
- **Coverage frontend 96.49%**: MapboxStrategy 16.9%→100%

## ALTA PRIORIDAD

1. ✅ **Resolver 8 Reliability Issues (Medium)** — 1 remanente aceptado
2. ✅ **Reducir Code Smells (82 → 0)** — Completado
3. ✅ **Mejorar coverage 34.1% → 96.49%** — Completado
4. ✅ **SNS + Grafana annotations** — Completado

## MEDIA PRIORIDAD

5. **SendGrid welcome email**
   - API key, `send_welcome_email()` en notification_service.py
   - Probar flujo completo: registro → SNS broadcast + SendGrid + Grafana annotation
6. **Dashboard Grafana**
   - Persistencia de configuraciones (allowUiUpdates)
   - DevOps dashboard con logs en tiempo real

## BAJA PRIORIDAD

7. **Guión demo**
   - Preparar escenarios de demostración
   - Datos de prueba precargados
8. **Documentación**
   - Actualizar docs existentes
   - README con instrucciones de desarrollo local

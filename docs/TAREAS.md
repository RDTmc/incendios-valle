# TAREAS — Incendios Valle del Sol

Orden de prioridad. NO saltarse pasos sin consultar al usuario.

## ✅ COMPLETADO (junio 2026)

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
- **Pipeline CI/CD verde**: 157 backend + 162 frontend tests
- **Code Smells: 82 → 0** — 4 batches completados (S8415, S8410, S7764, S6759, S2004, S4325, S6481, S3358, S112, S3457, S1515, S6262, S1192, S1481, S3776, S6819, S6853)
- **Fix build Cloudflare**: tipo navigate en renderReportList + exclude __tests__ de tsc
- **Coverage backend**: 97% overall, **todos los routers al 100%** (bff, auth, alerts, public, reports), s3_service/lambda_service 0→100%
- **Coverage frontend 96.49%**: todos los componentes >90% excepto main.tsx (0%, bootstrap) y ui/index.ts (0%, re-exports). **MapboxStrategy 16.9%→100%**

## ALTA PRIORIDAD

1. ✅ **Resolver 8 Reliability Issues (Medium)** — 1 remanente aceptado
2. ✅ **Reducir Code Smells (82 → 0)** — Completado
3. ✅ **Mejorar coverage 34.1% → 96.49%** — Completado
   - Backend: **97%** coverage, routers 100%
   - Frontend: **96.49%** coverage, **MapboxStrategy 100%**

## ✅ COMPLETADO

4. ✅ **Admin CRUD usuarios con notificaciones y auditoría**
   - Endpoints crear/modificar/eliminar usuarios — ✅
   - Frontend AdminPage con tabla, búsqueda, modales crear/editar, confirmación eliminar — ✅
   - Log de auditoría en tabla SQLite — ✅
   - Prueba de campo: VECINO registrado aparece en panel admin — ✅ (10 jun 2026)

## MEDIA PRIORIDAD

5. **Dashboard Grafana**
   - Persistencia de configuraciones (allowUiUpdates)
   - DevOps dashboard con logs en tiempo real
6. **PWA UX restante**
   - Feedback visual al usuario (loading states, errores amigables)

## BAJA PRIORIDAD

8. **Guión demo**
   - Preparar escenarios de demostración
   - Datos de prueba precargados
9. **Documentación**
   - Actualizar docs existentes
   - README con instrucciones de desarrollo local

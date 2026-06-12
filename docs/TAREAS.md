# TAREAS — Incendios Valle del Sol

Orden de prioridad. NO saltarse pasos sin consultar al usuario.

## ✅ COMPLETADO (junio 2026 — lote notificaciones)

### SNS + Grafana annotations pipeline
- **SNS welcome notification**: `notification_service.notify_new_user()` publica JSON a SNS topic `incendios-alerts` y guarda en SQLite (`notifications` table)
- **Grafana annotation al crear reporte**: `notification_service.notify_new_report()` crea anotación en Grafana vía Docker internal network
- **Backend endpoints**: `POST /register` y `POST /admin/create-user` llaman `notify_new_user`; `POST /reports` llama `notify_new_report`
- **Admin panel Notificaciones**: tab en AdminPage con historial (email, nombre, status, SNS ID, fecha)
- **Grafana token persistido**: agregado `GRAFANA_TOKEN` a docker-compose.yml y refresh_api.sh
- **Commits**: `8fd45f9` (SNS welcome), `4815999` (JSON para Grafana), `87101e5` (Lambda Grafana), `0b8ac34` (Grafana directo desde API), `9bca859` (notify_new_report)

### PWA UX improvements
- **Historial**: spinner + toast error en carga/fallo
- **AdminPage**: spinner + toast en cada tab (Usuarios, Auditoría, Notificaciones)
- **Confirmacion**: guard contra navegación directa + toast warning si no hay location state
- **Reporte**: spinner animado durante upload de foto
- **AlertBanner**: loading spinner inicial mientras carga alertas

### Fix UI AdminPage
- **Card.tsx**: quitado `bg-white` forzado — cada llamador decide su fondo
- **AdminPage**: Card con `bg-gray-800` (fondo grafito) para tabla legible
- **Login/Registro/Historial/Reporte/Confirmacion**: `bg-white` explícito (sin cambio visual)
- **Empty states**: `text-gray-400` → `text-gray-300` para mejor contraste sobre grafito
- **Commit**: `416e6ae` (fix bg-white en Card, AdminPage grafito)

### Mailtrap welcome email
- **Mailtrap Email API**: cuenta creada, dominio `keogh.lat` verificado (4 registros DNS en Cloudflare)
- **`_send_email_via_mailtrap()`**: implementado con `http.client` (reemplazó `urllib.request` que daba 403)
- **Config persistida**: `MAILTRAP_TOKEN`, `MAILTRAP_SENDER`, `MAILTRAP_SENDER_NAME` en docker-compose.yml y refresh_api.sh
- **Prueba de campo exitosa**: usuario nuevo recibe correo de bienvenida vía Mailtrap
- **Commits**: `acfd206` (Mailtrap init), `581059a` (Bearer fix), `21fe77d` (http.client fix)

### Fix imágenes en Grafana — presigned URL 7 días (junio 2026)
- **Problema ACL**: bucket S3 no permite ACLs (nuevo default), `BlockPublicAcls` forzado por AWS Academy
- **Lambda `upload-proxy`**: se extendió presigned URL de 2h → **7 días (604800s)**
- **Lifecycle rule**: `reportes/` → expire a los **30 días** (modificada desde rule `Borrar_24h`)
- **Panel 5 "Reportes Ciudadanos"**: pendiente ajuste manual en UI Grafana (cell type Image + data link)
- **Commits**: `dccb337` (ACL public-read, revertido), `5994cc4` (presigned a 7 días, sin ACL)

### Diagnóstico imágenes corruptas en S3 (13 jun 2026)
- **Causa raíz confirmada**: las imágenes JPEG en S3 están corruptas. La imagen `801270b6` tiene primeros bytes `EF BF BD EF BF BD` (caracteres UTF-8 de reemplazo U+FFFD) en vez de `FF D8 FF E0` (JPEG header). Las otras 11 tienen URLs presigned expiradas (403).
- **Patrón de corrupción**: compatible con `bytes.decode('utf-8', errors='replace').encode('utf-8')` en algún punto del pipeline (posiblemente una versión anterior del código).
- **Pipeline actual funciona**: Lambda invocada manualmente con JPEG válido → imagen correcta en S3. Direct boto3 upload → se ve en Grafana.
- **EC2 instance caída** (13 jun): SSH timeout, Grafana 530/502. Pendiente reinicio desde consola AWS.
- **Solución**: tomar foto nueva desde PWA tras reiniciar instancia. Las imágenes nuevas se guardarán correctamente.

### Fix imágenes — Causa raíz: Cloudflare corrompe multipart/form-data (13 jun 2026)
- **Evidencia**: 
  - Directo a API Gateway (`execute-api` URL) → JPEG válido ✅ (259 bytes)
  - Directo a custom domain endpoint (sin Cloudflare) → JPEG válido ✅ (259 bytes)
  - Via Cloudflare (`api.keogh.lat` proxied) → JPEG corrupto ❌ (283 bytes, `efbfbd...`)
- **Causa raíz**: Cloudflare estaba decodificando el body multipart/form-data como UTF-8, corrompiendo los bytes JPEG binarios no-UTF8
- **Fix API Gateway**: agregué `multipart/form-data` a `binaryMediaTypes` + redeploy (necesario para el fix completo)
- **Fix aplicado**: Opción 1 — DNS-only para `api.keogh.lat` en Cloudflare (nube gris). Ahora resuelve directo a API Gateway regional endpoint
- **Verificado**: upload de prueba POST-fix → JPEG de 259 bytes, header `ffd8ffe0`, 0 patrones U+FFFD ✅

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

## ALTA PRIORIDAD (nuevo)

6. ☐ **AdminPage — Gestión de estados de reportes**
   - ☐ Backend: `PATCH /api/reports/{id}/status` → cambiar estado (PENDIENTE/ACTIVO/CONTROLADO/EXTINGUIDO)
   - ☐ Frontend: nuevo tab "Reportes" en AdminPage con tabla + selector de estado
   - ☐ Auth: solo admin (Bearer token, role=admin)
   - ☐ Notificar cambio via SNS? (evaluar)

## MEDIA PRIORIDAD

5. ✅ **Mailtrap welcome email** — Completado (reemplazó SendGrid, bloqueado por Twilio)
7. ☐ **Dashboard Grafana — Diseño UI**
   - ✅ Persistencia validada: export → commit → CI/CD preserva cambios
   - ☐ **Fase 2 — Diseño UI**: tipografía, colores, layout, imágenes en cada panel
     - ✅ **Panel 5 — Imágenes**: Lambda + proxy + data link funcionando
     - ☐ Rediseñar los 9 paneles con la nueva configuración visual
     - ☐ Exportar JSON + commit + CI/CD

## BAJA PRIORIDAD

8. ☐ **Guión demo** — Iniciado en `docs/GUION_DEMO.md`
   - ✅ Persistencia (bind mount EBS) documentada
   - ☐ Escenarios de demostración
   - ☐ Datos de prueba precargados
9. **Documentación**
   - Actualizar docs existentes
   - README con instrucciones de desarrollo local

### Fix doble encoding "Ver imagen" — Opción B: endpoint proxy (12–13 jun 2026)
- **Problema**: data link "Ver imagen" en Grafana panel 5 daba `InvalidToken` porque el motor Go `html/template` de Grafana URL-escapaba el `href`, convirtiendo `%2B` → `%252B`
- **Solución elegida**: Opción B — API genera presigned URL al vuelo y redirige 302, eliminando caracteres URL-encoded de las URLs almacenadas
- **Lambda `upload-proxy`**: cambiada para devolver solo key S3 (`reportes/uuid.jpg`) en vez de presigned URL completa (deploy MANUAL)
- **API `main.py`**: nuevo endpoint `GET /images/{key:path}` → presigned URL + 302 redirect. Upload construye `foto_url` como ruta de API
- **✅ Completado**: URL absoluta (`https://api.keogh.lat/api/images/{key}`), data link restaurado, prueba de campo exitosa
- **Commits**: `9b17f8d` (Opción B), `1bf0efd` (URL absoluta + data link), `4dd97fc` (restaurar diseño desde backup), `6e10b02` (validar persistencia con cambio UI)
- **Lambda**: commit `5994cc4` (presigned 7 días) → deploy manual con cambio a solo key

### Fix: Persistencia de cambios UI en Grafana (13 jun 2026)
- **Problema**: al reiniciar Grafana, provisioning sobrescribía los cambios hechos desde UI
- **Solución**: exportar dashboard después de cambios UI → commit JSON → CI/CD deploya el mismo JSON
- **Flujo validado**: cambio "Focos Activos" sobrevivió a deploy completo
- **Script**: `export_dashboards.sh` actualizado con admin credentials (GRAFANA_TOKEN expiró con restore DB)
- **Docs**: flujo documentado en `AGENTS.md`
- **Commits**: `b1688e9` (docs + fix export_dashboards.sh)

## BAJA PRIORIDAD

7. ☐ **Guión demo** — Iniciado en `docs/GUION_DEMO.md`
   - ✅ Persistencia (bind mount EBS) documentada
   - ☐ Escenarios de demostración
   - ☐ Datos de prueba precargados
8. **Documentación**
   - Actualizar docs existentes
   - README con instrucciones de desarrollo local

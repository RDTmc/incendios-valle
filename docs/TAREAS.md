# TAREAS — Incendios Valle del Sol

Orden de prioridad. NO saltarse pasos sin consultar al usuario.

## ✅ COMPLETADO

### AdminPage — Gestión de estados de reportes (13 jun 2026)
- Backend: `PATCH /admin/reports/{report_id}/status` en `routers/admin.py` (commit `a3c5511`)
- Frontend: tab "Reportes" en AdminPage con tabla + dropdown de estado coloreado
- Auth: solo admin (require_admin), log de auditoría con `update_report_status`
- CI/CD verde, builds OK

### Fix doble encoding "Ver imagen" — Opción B: endpoint proxy (12–13 jun 2026)
- **Problema**: data link "Ver imagen" en Grafana panel 5 daba `InvalidToken` por URL-escaping doble de Grafana (`%2B` → `%252B`)
- **Solución**: Opción B — API genera presigned URL al vuelo y redirige 302 (elimina caracteres URL-encoded de URLs almacenadas)
- **Lambda `upload-proxy`**: cambiada para devolver solo key S3 (`reportes/uuid.jpg`) en vez de presigned URL (deploy MANUAL)
- **API `main.py`**: endpoint `GET /images/{key:path}` → presigned URL + 302 redirect. Upload construye URL absoluta (`https://api.keogh.lat/api/images/{key}`)
- Prueba de campo exitosa, todos los paneles se actualizan con nuevos reportes
- Commits: `9b17f8d`, `1bf0efd`, `4dd97fc`, `6e10b02`

### Fix: Persistencia de cambios UI en Grafana (13 jun 2026)
- **Problema**: provisioning sobrescribía cambios UI al reiniciar Grafana
- **Solución**: exportar dashboard → commit JSON → CI/CD deploya el mismo JSON
- **Flujo validado**: cambio "Focos Activos" sobrevivió a deploy completo
- **Script**: `export_dashboards.sh` actualizado con admin credentials (GRAFANA_TOKEN expiró con restore DB)
- Docs actualizados en `AGENTS.md`
- Commit: `b1688e9`

### Fix imágenes — Causa raíz Cloudflare (13 jun 2026)
- **Causa raíz**: Cloudflare corrompía multipart/form-data al decodificar bytes JPEG binarios como UTF-8
- **Evidencia**: directo a API Gateway → JPEG válido ✅; via Cloudflare → JPEG corrupto ❌ (`efbfbd...`)
- **Fix**: DNS-only para `api.keogh.lat` (nube gris) + `binaryMediaTypes` en API Gateway
- Verificado: upload POST-fix produce JPEG de 259 bytes, header `ffd8ffe0`

### SNS + Grafana annotations pipeline
- `notification_service.notify_new_user()` publica JSON a SNS topic `incendios-alerts`
- `notification_service.notify_new_report()` crea anotación en Grafana vía Docker internal network
- Admin panel Notificaciones en AdminPage
- GRAFANA_TOKEN persistido en docker-compose.yml y refresh_api.sh

### PWA UX improvements
- Historial/AdminPage/Reporte: spinners, toasts, loading states
- Confirmacion: guard contra navegación directa
- AlertBanner: loading spinner inicial
- Card.tsx: quitado bg-white forzado, AdminPage con bg-gray-800

### Mailtrap welcome email
- Cuenta creada, dominio `keogh.lat` verificado (4 registros DNS en Cloudflare)
- Implementado con `http.client`, config persistida en docker-compose.yml
- Prueba de campo exitosa

### Cobertura y calidad
- Backend: 157 tests, routers 100%, overall 97%
- Frontend: 165 tests, 96.49% coverage
- Total: 322 tests, 0 failures
- Security: C→A, Reliability: C→A, Code Smells: 82→0

## ALTA PRIORIDAD

1. ☐ **Dashboard Grafana — Diseño UI** (Fase 2)
   - Rediseñar los 9 paneles con nueva configuración visual (tipografía, colores, layout)
   - Exportar JSON + commit + CI/CD

## MEDIA PRIORIDAD

2. ☐ **Agregar Lambda `upload-proxy` al pipeline CI/CD**
   - Actualmente se deploya manualmente desde AWS Console

3. ☐ **Notificar cambio de estado de reporte via SNS?** (evaluar si es necesario)

## BAJA PRIORIDAD

4. ☐ **Guión demo** — `docs/GUION_DEMO.md`
   - Escenarios de demostración, datos de prueba precargados

5. **Documentación**
   - Actualizar docs existentes
   - README con instrucciones de desarrollo local

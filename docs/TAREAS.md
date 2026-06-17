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

### Fix 500 al cambiar estado de reporte — columna SQL incorrecta (14 jun 2026)
- **Problema**: `admin_update_report_status` usaba `WHERE id = ?` pero columna SQLite es `report_id` → SQLException → 500
- **Fix**: cambiar a `SELECT report_id` y `WHERE report_id`
- **Detectado**: request mostraba `PUT 500` en modo incógnito con headers `x-amzn-remapped-server: nginx`

### Fix — dropdown no actualiza estado tras cambio (14 jun 2026)
- **Problema**: `admin_update_report_status` solo actualizaba SQLite, pero `list_reports` (tabla AdminPage) lee de DynamoDB
- **Fix**: agregar `repo.update(report_id, estado=estado_upper)` para sync DynamoDB después del UPDATE SQLite
- Validado: Grafana ya veía el cambio (lee SQLite), ahora AdminPage también
- Commit: `a7323fe` — CI/CD verde ✅

### Fix report_id null desde SQLite (14 jun 2026)
- **Problema**: endpoint `admin/reports` (SQLite) devolvía reportes con `report_id = null` → crash frontend `can't access property "slice"`
- **Fix**: filtrar filas sin `report_id` en backend + safe guard `r.report_id?.slice` en frontend
- Commit: `2059277` — CI/CD verde ✅

### Primer respaldo dashboard Grafana (14 jun 2026)
- Flujo validado: editar UI → `ssh + bash export_dashboards.sh` → `scp` → `commit + push`
- ✅ Se exportaron los 2 dashboards (Incendios + DevOps)
- ✅ JSON cambios detectados: 101 insertions, 42 deletions
- Commit: `a50c910` — CI/CD verde
- ⚠️ Nota: el script `export_dashboards.sh` tiene output buffer de Python. Para ver progreso en tiempo real, añadir `flush=True` a los prints o ejecutar con `python3 -u`. El export funciona correctamente aunque no se vean mensajes "OK".

## 🔁 RETROSPECTIVA — Lecciones aprendidas (14 jun 2026)

Esta sección documenta errores recurrentes para revisar ANTES de implementar cualquier cambio futuro.

### Error 1: Asumir permisos sin verificar
- **Qué pasó**: Agregué `repo.update()` a DynamoDB sin verificar si el rol IAM de EC2 tiene permisos de escritura. Funcionaba en local (tests con mock) pero producía 500 en producción.
- **Lección**: Verificar permisos reales del entorno de producción (IAM, red, etc.) antes de agregar operaciones de escritura a recursos externos.

### Error 2: No mapear el flujo de datos completo antes de un cambio
- **Qué pasó**: El cambio de estado se escribía solo en SQLite, pero el frontend leía de DynamoDB. Primero intenté sync a DynamoDB (error 1), luego creé endpoint SQLite sin considerar que datos pueden diferir entre fuentes.
- **Lección**: Antes de tocar código, trazar: `frontend → endpoint → fuente de datos (DynamoDB vs SQLite) → otras fuentes`. Verificar de dónde lee cada componente.

### Error 3: Asumir limpieza de datos en SQLite
- **Qué pasó**: El endpoint SQLite retornó reportes con `report_id = null` porque la tabla tenía filas sin ese campo. En DynamoDB era imposible (clave de tabla), pero SQLite lo permite.
- **Lección**: SQLite no tiene las mismas restricciones que DynamoDB. Siempre filtrar/validar datos al leer desde SQLite.

### Regla para futuros cambios
1. Trazar flujo de datos completo (frontend → Worker → API Gateway → backend → fuente de datos)
2. Verificar permisos IAM/red antes de tocar recursos AWS externos
3. Revisar esquemas y datos reales de SQLite (puede tener filas inválidas)
4. Testear siempre en producción con un usuario/sesión real después del deploy
5. NO asumir que tablas "equivalentes" (DynamoDB vs SQLite) tienen los mismos datos

## ALTA PRIORIDAD

### En ejecución — Dashboard DevOps con Prometheus (14 jun 2026)

**Contexto:** Primero se intentó CloudWatch, pero el LabRole de AWS Academy no tiene permisos para `iam:AttachRolePolicy` ni `CloudWatchReadOnlyAccess`. Se optó por Prometheus + node_exporter corriendo como containers Docker en la misma EC2.

**Fase — Implementación Prometheus**

| Archivo | Acción |
|---|---|
| `ec2/prometheus/prometheus.yml` | **Nuevo** — config scrape: node_exporter (:9100) + API (:8000) |
| `ec2/docker-compose.yml` | +2 servicios: prometheus + node-exporter |
| `ec2/grafana-provisioning/datasources/datasource.yml` | CloudWatch → Prometheus datasource |
| `ec2/grafana-provisioning/dashboards/devops_dashboard.json` | Recablear 4 paneles a PromQL (CPU, Network, Memory, Disk) |
| `docs/TAREAS.md` | Documentar estado |

**Layout dashboard DevOps (post-Prometheus):**

| Panel | Datasource | Query PromQL |
|---|---|---|
| CPU Utilization | Prometheus | `100 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m]))` |
| Network Activity | Prometheus | `rate(node_network_receive_bytes_total[1m])` + Out |
| Memory Usage | Prometheus | `(MemTotal - MemAvailable) / MemTotal * 100` |
| API Healthcheck | SQLite | `SELECT 1` (sin cambios) |
| Disk Usage | Prometheus | `100 - (avail / size * 100)` |
| Alertas Recientes | SQLite | alerts table (sin cambios) |

**Riesgo:** Bajo. ~100MB RAM extra sobre ~700MB libres en t3.micro.

**Próximo paso:** ✅ Documentado — implementado y commit. Pendiente validar post-deploy que Prometheus + node-exporter estén corriendo y Grafana pueda consultarlos.

**Fixes aplicados post-deploy:**
1. `datasource.yml`: agregada `url: http://prometheus:9090` (faltaba la URL del servidor)
2. `deploy.yml`: hash de provisioning ampliado de `dashboards/` a toda la carpeta `grafana-provisioning/` (antes no detectaba cambios en `datasource.yml`)
3. `refresh_api.sh`: creación de directorios Prometheus + arranque de servicios

## ✅ FIX — Error 500 en Admin PUT status + readonly database (17 jun 2026)

**Diagnóstico:**
- Síntomas: `PUT /admin/reports/{id}/status` retorna 500 con `{"detail":"Error al actualizar estado: attempt to write a readonly database"}`
- **Causa raíz encontrada**: El `deploy.yml` hacía un **2do `aws s3 cp`** (línea 167-168) después de que `refresh_api.sh` ya había aplicado `chmod 664`. Este segundo restore sobrescribía el archivo con dueño `ec2-user` y permisos 644. Luego el bloque de permisos (líneas 195-199) solo hacía `chmod 644` **sin `chown 472:472`** para el API (solo se hacía para Grafana). El API (uid 472) solo podía leer.
- Lecturas (SELECT) funcionaban, escrituras fallaban.

**Fix aplicado (commit `592ec01`):**
1. `deploy.yml`: `sudo chown -R 472:472` sobre `/home/ec2-user/incendios-data/api`
2. `deploy.yml`: `sudo chmod 775` al directorio + `sudo chmod 664` al archivo `.db`
3. `deploy.yml`: `docker-compose up -d --no-deps --force-recreate api` después del fix

**Dashboard TI (Grafana DevOps):** funcionando correctamente.
- CPU, Network, Memory, Disk Usage con datos Prometheus ✅
- API Healthcheck y Alertas SQLite OK ✅
- Node-exporter con `--path.rootfs=/host` para métricas de disco ✅
- Resolver dinámico DNS en nginx para evitar 502 por stale upstream ✅

## ✅ FIX — Auto-refresh dashboard emergencia (17 jun 2026)

**Diagnóstico:**
- Panel "Estatus de Reportes" y "Reportes Ciudadanos" no se actualizaban sin F5
- `dashboard_incendios.json` línea 1804: `"refresh": ""` (vacío) — sin auto-refresh
- `devops_dashboard.json` línea 288: `"refresh": "30s"` — funcionaba correctamente

**Fix (commit `f2a0302` → `3b9af58`):**
- Cambiado `"refresh": ""` a `"refresh": "3s"` en dashboard_incendios.json
- **Justificación del intervalo**: 3s porque los cambios de estado son manuales (AdminPage), no automáticos. Las queries son livianas (`GROUP BY` sobre ~24 filas, `LIMIT 10`). Incluso con 1000 reportes, cada query se resuelve en < 1ms en SQLite. No hay riesgo de saturación en t3.micro.

**Pendiente para pruebas futuras:**
- Verificar comportamiento bajo carga simulada (1000+ reportes, escrituras concurrentes)
- Confirmar que 3s no impacta rendimiento en escenario de emergencia con múltiples operadores
- Documentar métricas de tiempo de respuesta SQLite bajo carga para rúbrica de testing

## ✅ Notificar cambio de estado via SNS + Grafana annotation (17 jun 2026)

**Qué se implementó:**
- Nueva función `notify_status_change()` en `notification_service.py`
  - Crea anotación Grafana directa (internal Docker network)
  - Publica a SNS topic `incendios-alerts` (email + Lambda sns-to-grafana)
- `admin.py`: captura `estado_anterior` y llama a `notify_status_change` después de persistir el cambio
- **Patrón fail-open**: cualquier error en notificación se loguea y no bloquea el endpoint

**Infraestructura existente reutilizada:**
- SNS topic `incendios-alerts` ya operativo (usado por `notify_new_user`)
- Lambda `sns-to-grafana` ya parsea el formato JSON que enviamos (`text`, `tags`, `timestamp`)
- Suscriptor email ya confirmado

**Lo que se conserva intacto:**
- `admin_update_report_status` sigue funcionando exactamente igual — la notificación es post-facto
- Dashboard auto-refresh 3s sin cambios
- Pipeline CI/CD sin cambios

**Pendiente:**
- Revisar cabeceras email para evitar SPAM (SNS envía JSON plano como body)

## MEDIA PRIORIDAD

2. ☐ **Agregar Lambda `upload-proxy` al pipeline CI/CD**
   - Actualmente se deploya manualmente desde AWS Console

## BAJA PRIORIDAD

4. ☐ **Guión demo** — `docs/GUION_DEMO.md`
   - Escenarios de demostración, datos de prueba precargados

6. **Documentación**
   - Actualizar docs existentes
   - README con instrucciones de desarrollo local

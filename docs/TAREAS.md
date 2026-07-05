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

## 🔄 EN PROGRESO — Migración Infinity → PostgreSQL directo en Grafana (06 Jul 2026)

### Contexto
El plugin Infinity v3.10.1 crashea con `can't access property "map", e is null` al procesar datos JSON desde los BFF endpoints. Alternativa: usar el datasource PostgreSQL nativo de Grafana (built-in desde v8.x).

### Panel 1 validado ✅ (commit `ebed222`)
- Datasource `pg-incendios` creado vía provisioning template
- Panel 1 (Focos Activos): 78 focos activos visibles, sin errores
- SQL directo: `SELECT COUNT(*) AS focos_activos FROM reports WHERE estado IN ('ACTIVO','PENDIENTE')`

### Pendiente — Migrar 11 paneles restantes a PostgreSQL directo
| Panel | Tipo | SQL |
|-------|------|-----|
| 2 — Distribución Tipo Incendio | piechart | `SELECT tipo, COUNT(*) FROM reports GROUP BY tipo` |
| 3 — Estatus de Reportes | bargauge | `SELECT estado, COUNT(*) FROM reports GROUP BY estado` |
| 4 — Focos por Estado #1 | geomap | `SELECT lat/lng, estado, tipo FROM reports WHERE lat IS NOT NULL` |
| 5 — Reportes Ciudadanos | table | `SELECT id, imagen, descripcion FROM reports ORDER BY created_at DESC LIMIT 10` |
| 6 — Recursos por Incidente | table | `SELECT ir.*, r.* FROM incident_resources ir LEFT JOIN reports r` |
| 7 — Histórico CONAF | geomap | `SELECT lat/lng FROM external_reports ORDER BY fh_inicio DESC LIMIT 500` |
| 8 — Clima 30-30-30 | table | `SELECT region, temp, hum, wind, riesgo FROM weather_readings ...` |
| 9 — Focos Satelital | geomap | `SELECT lat/lng, frp FROM firms_hotspots WHERE acq_date >= NOW() - 3d` |
| 10 — Focos por Estado #2 | geomap | `SELECT lat/lng FROM reports WHERE lat IS NOT NULL` |
| 11 — Reportes vs Recursos | table | `SELECT r.id, COUNT(ir.id) FROM reports r LEFT JOIN incident_resources ir GROUP BY r.id` |
| 12 — Estado Recursos | bargauge | `SELECT estado, COUNT(*) FROM incident_resources GROUP BY estado` |

### Nota sobre APIs externas
Los paneles 7 (CONAF), 8 (Clima), 9 (FIRMS) obtienen datos de APIs externas PERO los datos ya están precargados en tablas PostgreSQL por los background tasks. No requieren llamadas HTTP en tiempo real. El cálculo de riesgo 30-30-30 se puede replicar en SQL con `CASE WHEN`.

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

## ✅ 2FA Email OTP + backup codes para admins (17 jun 2026)

**Decisión:** Se optó por Email OTP (vía Mailtrap) + códigos de backup como método de doble factor para usuarios admin.

**Por qué esta opción:**
- Mailtrap ya está operativo y con SPF configurado → $0 adicional
- Sin apps externas (el admin recibe código en su correo)
- Esfuerzo mínimo (~30 líneas backend)

**Implementado (commit `628e15d`):**

| Endpoint | Método | Descripción |
|---|---|---|
| `/auth/login` | POST | Si admin tiene 2FA, responde `two_factor_required` + envía OTP al email |
| `/auth/2fa/verify` | POST | Verifica código OTP o backup code, emite JWT |
| `/admin/2fa/setup` | POST | Activa 2FA + genera 10 backup codes |
| `/admin/2fa/disable` | POST | Desactiva 2FA |
| `/admin/2fa/status` | GET | Estado actual + códigos restantes |

**Frontend:**
- Login.tsx: flujo en 2 pasos (password → input OTP 6 dígitos con auto-focus)
- Admin2FATab.tsx: componente separado con lógica 2FA desacoplada de AdminPage (commit `17517a4`)
- Códigos mostrados UNA vez al activar, guardados en SQLite

**Lo que NO se rompe:**
- Login normal (sin 2FA) funciona exactamente igual
- AdminPage tabs existentes (usuarios, auditoría, notificaciones, reportes) intactos
- Usuarios no-admin no tienen opción de 2FA

**Pipeline fixes aplicados (3 errores corregidos):**
1. Backend: `test_login_invalid_credentials` esperaba mensaje en inglés ("Invalid credentials") → cambiado a español ("Credenciales inválidas") — commit `f66126a`
2. Frontend: `Login.test.tsx` mockeaba `login()` pero el componente ahora usa `API.login` + `setAuthFrom2FA` — commit `31a956d`
3. Frontend: `AdminPage.tsx` — hooks 2FA quedaron FUERA del componente por `}` prematuro → movidos a Admin2FATab.tsx desacoplado — commit `9accd4d` + `17517a4`

**Detalle:** El botón del tab 2FA muestra "2FA" fijo (sin indicador 🔒/🔓) porque el estado `twoFAEnabled` se movió al subcomponente. Se puede restaurar pasando el estado como prop si es necesario.

**Pendiente:**
- ✅ Prueba de campo post-deploy (recomendada antes de considerar estable)

## ✅ Limpieza de archivos en repo (17 jun 2026)

**Motivación:** El repo contenía archivos que no debían estar públicos: secretos, artefactos generados, scripts one-time, duplicados y docs internos.

**Ejecutado (commit `220de7e`):**
- 83 archivos destrackeados con `git rm --cached` (ninguno borrado del disco)
- `.gitignore` actualizado con reglas para cada categoría
- Revert seguro: `git revert 220de7e` restaura todo

**Categorías limpiadas:**
- Secretos (`frontend/.env`, `ec2/incendios-key.pem`)
- Base de datos local (`ec2/api/incendios.db`)
- Coverage generado (`htmlcov/`, `.coverage`, `coverage.xml`)
- Build frontend (`frontend/dist/`)
- Debug scripts (`ec2/api/debug/` — 32 archivos)
- Scripts migración one-time (`ec2/patch_*.py`, `ec2/fix_*.py`, etc.)
- Duplicados (`ec2/grafana-dashboards/`, `ec2/lambda/`)
- Monitoring CloudWatch obsoleto (`ec2/monitoring/`)
- Screenshots, docs internos, planning, archivos huérfanos

## ✅ Password reset automático — flujo unificado VECINO/ADMIN (19 jun 2026)

**Decisión:** Password reset sin intervención humana, con OTP email + backup code condicional.

**Implementado:**

| Endpoint | Método | Descripción |
|---|---|---|
| `/auth/forgot-password` | POST | Envía OTP de 6 dígitos al email (vía Mailtrap) |
| `/auth/reset-password` | POST | Verifica OTP + contraseña nueva + backup code opcional |

**Flujo:**
1. Usuario ingresa email → recibe OTP de 6 dígitos (vence 10 min)
2. Ingresa OTP + nueva contraseña + confirmación
3. Si el usuario tiene 2FA activo:
   - Puede ingresar backup code → se consume y permite cambio
   - Si no tiene backup code → 2FA se auto-desactiva y permite cambio igual
4. Contraseña se guarda como bcrypt hash en columna `password_hash` de SQLite
5. OTP se elimina del store al completar

**Frontend:**
- `ForgotPassword.tsx`: flujo 3 pasos (email → OTP+password → éxito)
- Ruta `/forgot-password` en App.tsx
- Link "¿Olvidaste tu contraseña?" en Login.tsx

**Login con fallback SQLite:**
- `auth.py`: si DynamoDB no encuentra usuario o no coincide password, intenta SQLite
- Si SQLite tiene el usuario con `password_hash` correcto, login procede igual
- Esto permite que usuarios creados con password reset puedan hacer login aunque no existan en DynamoDB

**Tests:** 157 backend + 165 frontend, todos verdes ✅

## ✅ Fix masivo 2FA — OTP en JWT + Role override SQLite (20 jun 2026)

**Problema:** 9 deploys consecutivos sin resolver 2FA. El OTP se almacenaba en memoria/SQLite pero verify nunca lo encontraba ("Código inválido"). Adicionalmente, el login con fallback SQLite ignoraba el rol ADMIN y redirigía a /reporte.

**Causas raíz identificadas y corregidas:**

| # | Error | Causa | Fix |
|---|---|---|---|
| 1 | `NameError` | Función `_clean_expired_otp` duplicada; la vieja referenciaba `_otp_store` (dict) que ya no existía | Eliminar función duplicada (commit `6b76dd3`) |
| 2 | "Código inválido" | OTP store en memoria se perdía con restart deploy; store en SQLite fallaba silenciosamente por tabla no creada | OTP viaja DENTRO del JWT temp_token (commit `ee41b1e`). No hay store — ni memoria, ni SQLite |
| 3 | Redirect a /reporte | verify_2fa usaba `user.get('rol', 'VECINO')` de DynamoDB ignorando SQLite | verify_2fa ahora lee rol desde SQLite y lo sobreescribe (commit `dd5c4ac`) |
| 4 | Bootstrap pisado | Login sincronizaba rol DynamoDB → SQLite, sobrescribiendo ADMIN con VECINO | Eliminar sync (commit `1c2b20b`) |

**Solución final del 2FA:**

- **Login**: `temp_token = jwt.encode({user_id, purpose, otp, exp})` — el OTP va firmado dentro del JWT
- **Verify**: `jwt.decode(req.temp_token)` → compara `payload["otp"] == req.code` — sin store externo
- **Backup codes**: se mantienen en SQLite (admin_2fa), verificados si el OTP no match
- **Role override**: verify_2fa consulta SQLite para el rol, priorizándolo sobre DynamoDB

**Bootstrap endpoint (creado para recuperar acceso):**
- `POST /api/auth/bootstrap-admin` — actualiza rol a ADMIN en SQLite sin requerir auth
- Usado para recuperar acceso cuando DynamoDB no permite escritura (LabRole)
- `ec2/api/routers/bootstrap.py`
- `ec2/api/scripts/fix_admin_role.py` — script para ejecutar en servidor

**Prueba de campo exitosa:**
1. `curl -X POST` a bootstrap-admin → rol actualizado a ADMIN ✅
2. Login con OTP → verify desde JWT → funciona al primer intento ✅
3. Redirección a /admin correcta ✅
4. Admin secundario creado desde panel ✅

**Tests:** 157 backend, 165 frontend, todos verdes ✅

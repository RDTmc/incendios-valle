# Registro de Incidentes — Dashboard Grafana

## INC-001: Dashboard roto post-migración PostgreSQL (05 Jul 2026)

### Síntomas
- Dashboard "Incendios - Valle del Sol" muestra error en todos los paneles
- **Error 1**: `Status: 500 — unable to open database file: out of memory (14)` con `ds_type=frser-sqlite-datasource`
- **Error 2**: `Minified React error #130` en plugin `yesoreyeram-infinity-datasource` (targets incompletos)
- CI/CD pipeline verde pero dashboard roto

### Causa raíz

**Causa 1 — UID duplicado en provisioning** (bloqueador principal)
```
Grafana log: "the same UID is used more than once" uid=incendios-valle-main times=2
Grafana log: "Not saving new dashboard due to restricted database access"
```
En EC2 existían 2 archivos JSON con el mismo UID `incendios-valle-main`:
- `dashboard_incendios.json` (44KB) — versión Infinity (correcta, del repo)
- `dashboard_incendios_backup.json` (52KB) — versión SQLite vieja (huérfana, NO en repo)

Grafana detecta el duplicado y **bloquea la escritura** del nuevo provisioning. El dashboard SQLite original persiste en la DB interna de Grafana.

**Causa 2 — SQLite datasource aún provisionado**
`datasource.yml` persistía en EC2 con `frser-sqlite-datasource` e `isDefault: true`. El plugin `frser-sqlite-datasource` fue removido de docker-compose y `incendios.db` ya no existe → todos los paneles que usan este datasource fallan con SQLITE_CANTOPEN (código 14).

**Causa 3 — SCP no elimina archivos huérfanos**
El `appleboy/scp-action` en CI/CD solo sobrescribe archivos existentes en source. Archivos que existen SOLO en destino (EC2) nunca se eliminan:
- `dashboard_incendios_backup.json` (52KB, SQLite, mismo UID)
- `dashboard_incendios_v2.json` (44KB, viejo "Infinity")
- `datasource.yml` (504B, SQLite datasource)

**Causa 4 — Conversión Infinity incompleta (primer intento)**
Commit `e4dd4c8` copió targets del V2 pero omitió `source`, `method`, `parser`. El plugin Infinity 3.10.1 requiere estos campos → React error #130.

### Evidencia recolectada

1. Archivos en EC2 (antes de limpieza):
```
grafana-provisioning/dashboards/dashboard_incendios.json       (44KB, Infinity OK)
grafana-provisioning/dashboards/dashboard_incendios_backup.json (52KB, SQLite, UID duplicado)
grafana-provisioning/dashboards/dashboard_incendios_v2.json     (44KB, viejo, UID diferente)
grafana-provisioning/datasources/datasource.yml                 (504B, SQLite, isDefault=true)
```

2. Grafana logs (04:51:35 UTC):
```
level=warn msg="the same UID is used more than once" uid=incendios-valle-main times=2
level=warn msg="Not saving new dashboard due to restricted database access"
level=error msg="Could not get connection" err="unable to open database file: out of memory (14)"
```

3. Targets duplicados:
- `dashboard_incendios.json` targets tiene: `source=url, method=GET, parser=backend`
- `dashboard_incendios_backup.json` targets tiene: `queryText, rawQueryText` (SQLite)

### Línea de tiempo
| Fecha/Hora | Evento |
|------------|--------|
| 04 Jul 2026 | FASE 5: SQLite deprecado. `datasource.yml` eliminado del repo |
| 04 Jul 23:XX | CI/CD deploya sin `datasource.yml` (pero SCP no borra el de EC2) |
| 05 Jul 00:XX | Se crea `dashboard_incendios_backup.json` en EC2 (origen desconocido, probablemente backup manual) |
| 05 Jul 02:10 | CI/CD deploya `dashboard_incendios_v2.json` a EC2 |
| 05 Jul 03:47 | CI/CD deploya `dashboard_incendios.json` convertido a Infinity |
| 05 Jul 03:47 | Grafana detecta UID duplicado → bloquea provisioning |
| 05 Jul 04:51 | Usuario reporta dashboard roto |
| 05 Jul 05:XX | Auditoría completa, diagnóstico documentado |

### Solución aplicada
1. `rm grafana-provisioning/dashboards/dashboard_incendios_backup.json`
2. `rm grafana-provisioning/dashboards/dashboard_incendios_v2.json`
3. `rm grafana-provisioning/datasources/datasource.yml`
4. `docker restart incendios-grafana`

### Prevención futura
- El CI/CD debe incluir un paso SSH que elimine archivos huérfanos antes del SCP
- Opción: cambiar de SCP a `rsync --delete` para sincronización completa
- Opción: script pre-deploy que liste y elimine archivos no esperados
- Monitorear logs de Grafana post-deploy para detectar "same UID" o "restricted database access"

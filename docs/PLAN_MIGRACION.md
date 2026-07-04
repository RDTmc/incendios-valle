# Plan de Migración: SQLite → RDS PostgreSQL

**Inicio:** 02 Jul 2026  
**Entrega:** 9 Jul 2026 (3 días restantes — 04 Jul)  

**Nota:** Las fases 1-4 se completaron en tiempo récord (2.5 días en vez de 10), dejando ~4.5 días de buffer. El cronograma original sobreestimó la duración de FASE 3-4 porque el dual-write y los endpoints BFF compartían lógica de base de datos ya probada.

**Presupuesto AWS:** $36.6 disponibles de $50  

## Objetivo

Reemplazar SQLite como base de datos local del contenedor FastAPI por una instancia RDS PostgreSQL 15, manteniendo DynamoDB como almacén primario de usuarios y reportes, y migrando Grafana del plugin `frser-sqlite-datasource` al datasource `yesoreyeram-infinity-datasource` (API REST).

## Cronograma

```
FASE 1 — Preparación (días 1-2)      ✅ COMPLETADO
FASE 2 — Reconciliación datos (día 3)  ✅ COMPLETADO
FASE 3 — Dual-write + endpoints (días 4-6) ✅ COMPLETADO
FASE 4 — Opción B: Grafana + CI/CD Lambdas (días 7-10) ✅ COMPLETADO
FASE 5 — Deprecar SQLite + tests + docs (días 11-13)  ← estamos aquí
```

---

## FASE 1 — Preparación (días 1-2) ✅ COMPLETADO

### Día 1 — Crear RDS ✅

```bash
# 1. Crear Security Group para RDS
aws ec2 create-security-group \
  --group-name incendios-rds-sg \
  --description "RDS PostgreSQL access from EC2" \
  --vpc-id <vpc-id>

aws ec2 authorize-security-group-ingress \
  --group-id <rds-sg-id> \
  --protocol tcp --port 5432 \
  --source-group <ec2-sg-id>

# 2. Crear RDS PostgreSQL 15 db.t3.micro
aws rds create-db-instance \
  --db-instance-identifier incendios-pg \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --allocated-storage 20 \
  --master-username postgres \
  --master-user-password <password> \
  --vpc-security-group-ids <rds-sg-id> \
  --db-subnet-group-name default \
  --publicly-accessible \
  --backup-retention-period 0
```

### Día 2 — Dependencias + esquema ✅

1. ✅ Agregar `psycopg2-binary` a `ec2/api/requirements.txt`
2. ✅ Crear `ec2/api/database_pg.py`:
   - `ConnectionPool` con `psycopg2.pool.ThreadedConnectionPool`
   - `get_pg_connection()` (context manager)
   - `init_pg_schema()` con DDL PostgreSQL (10 tablas)
3. ✅ Inyectar variables de entorno en container:
   - `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`

---

## FASE 2 — Reconciliación datos huérfanos (día 3) ✅ COMPLETADO

### Día 3 — Script DynamoDB → SQLite ✅

1. ✅ Leer todos los users de DynamoDB (table.scan())
2. ✅ Leer todos los reports de DynamoDB (table.scan())
3. ✅ Para cada registro no existente en SQLite: INSERT OR REPLACE
4. ✅ Log de cuántos registros se reconciliaron

Crear `ec2/api/scripts/reconcile_dynamodb_to_sqlite.py`:

```python
# 1. Leer todos los users de DynamoDB (table.scan())
# 2. Leer todos los reports de DynamoDB (table.scan())
# 3. Para cada registro no existente en SQLite: INSERT OR REPLACE
# 4. Log de cuántos registros se reconciliaron
```

Ejecutar en EC2:

```bash
ssh ec2-user@<ec2-ip> 'cd /app && python scripts/reconcile_dynamodb_to_sqlite.py'
```

**Validación**: `SELECT COUNT(*) FROM users` y `reports` en SQLite debe coincidir con DynamoDB.

---

## FASE 3 — Dual-write + migrar endpoints (días 4-6) ✅ COMPLETADO

### Día 4 — Capa de escritura dual ✅

1. ✅ Modificar `ec2/api/dependencies.py`:
   - `sync_to_sqlite()` ahora llama también a `sync_to_postgres()`
   - `sync_to_postgres()` usa `INSERT ... ON CONFLICT (col) DO UPDATE SET ...`
2. ✅ Deploy → monitorear logs por 24h

### Día 5 — Endpoints públicos + admin + alerts ✅

- ✅ `query_pg_first()` helper en database_pg.py
- ✅ Backfill datos existentes SQLite → PG (28 usuarios, 94 reports, 1783 external_reports, 495 firms, 1320 weather, 5 recursos, 19 notifications, 18 audit logs)
- ✅ public.py: 10 GET endpoints migrados (dashboard-stats, map-coordinates, external-reports, etc.)
- ✅ admin.py: 4 GET endpoints migrados (users, audit-log, reports, notifications)
- ✅ alerts.py: 1 GET endpoint migrado
- ✅ bff.py: 1 GET endpoint migrado (dashboard completo)

### Día 6 — Auth + password + bootstrap + main ✅

- ✅ auth.py: login fallback prueba PG como tercer origen (DynamoDB → PG → SQLite)
- ✅ auth.py: `_get_2fa_config()` migrado a PG-first
- ✅ password_reset.py: forgot-password busca usuario en PG primero

**SQLite → PostgreSQL equivalencias:**

```sql
-- SQLite
julianday('now') - julianday(created_at)
INSERT OR REPLACE INTO users ...
INSERT OR IGNORE INTO external_reports ...
SELECT MAX(id) FROM weather_readings GROUP BY region

-- PostgreSQL
EXTRACT(EPOCH FROM NOW() - created_at::timestamp) / 86400
INSERT INTO users ... ON CONFLICT (user_id) DO UPDATE SET ...
INSERT INTO external_reports ... ON CONFLICT ON CONSTRAINT ... DO NOTHING
SELECT DISTINCT ON (region) * FROM weather_readings ORDER BY region, id DESC
```

---

## FASE 4 — Opción B: Grafana + CI/CD Lambdas (días 7-10) ✅ COMPLETADO

### Día 7 — Endpoints BFF para Grafana ✅

Crear `ec2/api/routers/grafana_bff.py` — 10 endpoints implementados:

| Endpoint | Datos | Reemplaza panel(es) |
|----------|-------|-------------------|
| `GET /bff/grafana/report-stats` | COUNT por estado + tipo (incl. focos_activos) | 3 panels |
| `GET /bff/grafana/report-geo` | reportes lat/lng + estado + intensidad | 2 geomap panels |
| `GET /bff/grafana/weather-latest` | clima + riesgo calculado | Clima 30-30-30 |
| `GET /bff/grafana/hotspots` | FIRMS últimos 3 días | Focos de Calor Satelital |
| `GET /bff/grafana/resources` | recursos + incidentes + tipo + descripción | 3 panels recursos |
| `GET /bff/grafana/external-reports` | CONAF límite 500 | Histórico CONAF |
| `GET /bff/grafana/alerts-recent` | últimas 20 alertas | Alertas Recientes |
| `GET /bff/grafana/reports-recent` | últimos 10 reportes (ID, Foto, Desc, Tipo, Estado) | Reportes Ciudadanos |
| `GET /bff/grafana/report-resources-summary` | GROUP BY reporte + recursos asignados | Reportes vs Recursos |
| `GET /bff/grafana/resources-status` | COUNT por estado de recurso | Distribución Estado Recursos |

### Días 8-9 — Configurar Infinity datasource + migrar paneles ✅

1. ✅ Plugin `yesoreyeram-infinity-datasource` ya en `GF_INSTALL_PLUGINS`
2. ✅ `ec2/grafana-provisioning/datasources/datasource-infinity.yml` creado (uid: `incendios-api`)
3. ✅ Dashboard original respaldado como `dashboard_incendios_backup.json`
4. ✅ `dashboard_incendios_v2.json` generado con 12 paneles migrados a Infinity (uid: `incendios-valle-v2`)
5. ✅ Ambos dashboards activos en Grafana:
   - `https://dashboard.keogh.lat/d/incendios-valle-main` (SQLite original)
   - `https://dashboard.keogh.lat/d/incendios-valle-v2` (Infinity JSON API)

### Día 8 — CI/CD Lambda upload-proxy (opcional) ⬜ PENDIENTE

Agregar job a `.github/workflows/deploy.yml`:

```yaml
deploy-lambda-upload-proxy:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Package Lambda
      run: |
        cd lambda/upload_proxy
        pip install -r requirements.txt -t .
        zip -r upload-proxy.zip .
    - name: Deploy to AWS
      run: |
        aws lambda update-function-code \
          --function-name upload-proxy \
          --zip-file fileb://lambda/upload_proxy/upload-proxy.zip
```

**Requisito**: Agregar `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` a GitHub Secrets.

---

## FASE 5 — Deprecar SQLite + tests + docs (días 11-13)  ← estamos aquí

### Día 11 — Remover SQLite

1. Remover `sync_to_sqlite()` de `dependencies.py`
2. Remover `get_db_connection()` / `init_db()` / `restore_sqlite_from_s3()` / `backup_sqlite_to_s3()` de `main.py`
3. Backup S3: cambiar `aws s3 cp incendios.db` → `pg_dump | aws s3 cp -`
4. Actualizar `refresh_api.sh`
5. Remover volumen SQLite compartido de `docker-compose.yml`
6. Remover `frser-sqlite-datasource` de `GF_INSTALL_PLUGINS`
7. Remover dashboard SQLite original (respaldar en `ec2/grafana-provisioning/backups/`)

### Día 12 — Tests ✅ COMPLETADO

`ec2/api/tests/test_postgres.py` — 3 tests e2e (marcados `@pytest.mark.e2e`):

| Test | Verifica | Estado |
|------|----------|--------|
| `test_connection_and_schema` | Conexión PG + 10 tablas existen | ✅ Pasa en EC2 |
| `test_insert_and_select_reports` | INSERT + SELECT + DELETE en reports | ✅ Pasa en EC2 |
| `test_public_endpoint_returns_data` | GET /public/dashboard-stats con TestClient | ✅ Pasa en EC2 |

### Día 13 — Documentación final

1. Actualizar `docs/ARQUITECTURA.md`
2. Actualizar `docs/INFORME-GLOBAL.md` (sección migración)
3. Actualizar `AGENTS.md`
4. Buffer de 1 día por imprevistos

---

## Checklist de validación pre-entrega

- [x] RDS PostgreSQL funciona y responde consultas desde EC2
- [x] Script reconciliación ejecutado: datos DynamoDB ≈ datos SQLite
- [x] Dual-write: ambas BD reciben los mismos datos
- [x] Los 30+ endpoints de la API leen de PostgreSQL
- [x] Login fallback funciona contra PostgreSQL
- [x] 2FA funciona contra PostgreSQL
- [x] Password reset funciona contra PostgreSQL
- [x] Infinity datasource configurado en Grafana
- [x] 12 paneles Grafana migrados y validados vs SQLite (dashboard v2)
- [ ] Dashboard SQLite deprecado (respaldado)
- [ ] Backup S3 usa pg_dump
- [x] 3 tests PostgreSQL pasan
- [ ] Lambda upload-proxy en CI/CD (opcional)
- [ ] docs actualizados

# Plan de Migración: SQLite → RDS PostgreSQL

**Inicio:** 26 Jun 2026  
**Entrega:** 9 Jul 2026 (13 días)  
**Presupuesto AWS:** $36.6 disponibles de $50  

## Objetivo

Reemplazar SQLite como base de datos local del contenedor FastAPI por una instancia RDS PostgreSQL 15, manteniendo DynamoDB como almacén primario de usuarios y reportes, y migrando Grafana del plugin `frser-sqlite-datasource` al datasource `yesoreyeram-infinity-datasource` (API REST).

## Cronograma

```
FASE 1 — Preparación (días 1-2)      ← estamos aquí
FASE 2 — Reconciliación datos (día 3)
FASE 3 — Dual-write + endpoints (días 4-6)
FASE 4 — Opción B: Grafana + CI/CD Lambdas (días 7-10)
FASE 5 — Deprecar SQLite + tests + docs (días 11-13)
```

---

## FASE 1 — Preparación (días 1-2)

### Día 1 — Crear RDS

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

### Día 2 — Dependencias + esquema

1. Agregar `psycopg2-binary` a `ec2/api/requirements.txt`
2. Crear `ec2/api/database_pg.py`:
   - `ConnectionPool` con `psycopg2.pool.ThreadedConnectionPool`
   - `get_pg_connection()` (context manager)
   - `init_pg_schema()` con DDL PostgreSQL (10 tablas)
3. Inyectar variables de entorno en container:
   - `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`

---

## FASE 2 — Reconciliación datos huérfanos (día 3)

### Día 3 — Script DynamoDB → SQLite

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

## FASE 3 — Dual-write + migrar endpoints (días 4-6)

### Día 4 — Capa de escritura dual

1. Modificar `ec2/api/dependencies.py`:
   - `sync_to_sqlite()` ahora llama también a `sync_to_postgres()`
   - `sync_to_postgres()` usa `INSERT ... ON CONFLICT (col) DO UPDATE SET ...`
2. Deploy → monitorear logs por 24h

### Día 5 — Endpoints públicos + admin + alerts

Migrar a PostgreSQL:

| Router | Endpoints | Archivo |
|--------|-----------|---------|
| public.py | 10 GET endpoints | `dashboard-stats`, `map-coordinates`, `external-reports`, etc. |
| admin.py | 8 endpoints | CRUD users, reports, audit-log, notifications |
| alerts.py | 3 endpoints | CRUD alerts |
| bff.py | 1 endpoint | BFF dashboard |

### Día 6 — Auth + password + bootstrap + main

| Router | Endpoints | Notas |
|--------|-----------|-------|
| auth.py | login fallback, 2FA (3 endpoints) | `_get_2fa_config()`, `_save_2fa_config()` |
| password_reset.py | forgot + reset | `SELECT user_id FROM users WHERE email = ?` |
| bootstrap.py | bootstrap-admin | `UPDATE users SET rol = ?` |
| main.py | backup/restore, dashboard/stats, sync | Cambiar a PostgreSQL |

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

## FASE 4 — Opción B: Grafana + CI/CD Lambdas (días 7-10)

### Día 7 — Endpoints BFF para Grafana

Crear `ec2/api/routers/grafana_bff.py`:

| Endpoint | Datos | Reemplaza panel(es) |
|----------|-------|-------------------|
| `GET /bff/grafana/report-stats` | COUNT por estado + tipo | 3 panels |
| `GET /bff/grafana/report-geo` | reportes lat/lng + estado | 2 geomap panels |
| `GET /bff/grafana/weather-latest` | clima + riesgo calculado | Clima 30-30-30 |
| `GET /bff/grafana/hotspots` | FIRMS últimos 3 días | Focos de Calor Satelital |
| `GET /bff/grafana/resources` | recursos + incidentes | 3 panels recursos |
| `GET /bff/grafana/external-reports` | CONAF límite 500 | Histórico CONAF |
| `GET /bff/grafana/alerts-recent` | últimas 20 alertas | Alertas Recientes |

### Días 8-9 — Configurar Infinity datasource + migrar paneles

1. Agregar `yesoreyeram-infinity-datasource` a `GF_INSTALL_PLUGINS`
2. Crear `ec2/grafana-provisioning/datasources/datasource-infinity.yml`
3. Duplicar `dashboard_incendios.json` → `dashboard_incendios_v2.json`
4. Panel por panel, reemplazar query SQLite por consulta JSON API
5. Mantener dashboard SQLite original como respaldo

### Día 8 — CI/CD Lambda upload-proxy (opcional, si la migración va estable)

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

## FASE 5 — Deprecar SQLite + tests + docs (días 11-13)

### Día 11 — Remover SQLite

1. Remover `sync_to_sqlite()` de `dependencies.py`
2. Remover `get_db_connection()` / `init_db()` / `restore_sqlite_from_s3()` / `backup_sqlite_to_s3()` de `main.py`
3. Backup S3: cambiar `aws s3 cp incendios.db` → `pg_dump | aws s3 cp -`
4. Actualizar `refresh_api.sh`
5. Remover volumen SQLite compartido de `docker-compose.yml`
6. Remover `frser-sqlite-datasource` de `GF_INSTALL_PLUGINS`
7. Remover dashboard SQLite original (respaldar en `ec2/grafana-provisioning/backups/`)

### Día 12 — Tests

```python
# ec2/api/tests/test_postgres.py
class TestPostgresMigration:
    def test_connection_and_schema(self):
        """Test 1: Conecta a PostgreSQL y verifica que las 10 tablas existen"""
    def test_insert_and_select_reports(self):
        """Test 2: INSERT + SELECT en tabla reports"""
    def test_public_endpoint_returns_data(self):
        """Test 3: GET /public/dashboard-stats devuelve datos desde PostgreSQL"""
```

### Día 13 — Documentación final

1. Actualizar `docs/ARQUITECTURA.md`
2. Actualizar `docs/INFORME-GLOBAL.md` (sección migración)
3. Actualizar `AGENTS.md`
4. Buffer de 1 día por imprevistos

---

## Checklist de validación pre-entrega

- [ ] RDS PostgreSQL funciona y responde consultas desde EC2
- [ ] Script reconciliación ejecutado: datos DynamoDB ≈ datos SQLite
- [ ] Dual-write: ambas BD reciben los mismos datos
- [ ] Los 30+ endpoints de la API leen de PostgreSQL
- [ ] Login fallback funciona contra PostgreSQL
- [ ] 2FA funciona contra PostgreSQL
- [ ] Password reset funciona contra PostgreSQL
- [ ] Infinity datasource configurado en Grafana
- [ ] 13 paneles Grafana migrados y validados vs SQLite
- [ ] Dashboard SQLite deprecado (respaldado)
- [ ] Backup S3 usa pg_dump
- [ ] 3 tests PostgreSQL pasan
- [ ] Lambda upload-proxy en CI/CD (opcional)
- [ ] docs actualizados

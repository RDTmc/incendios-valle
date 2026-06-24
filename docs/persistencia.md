# Descripción de la Persistencia de Datos

## Arquitectura general

El sistema utiliza **tres mecanismos de persistencia** que se complementan según el caso de uso:

| Mecanismo | Datos | Propósito |
|-----------|-------|-----------|
| **DynamoDB** (AWS) | Usuarios, reportes | Persistencia primaria. CRUD desde API Gateway + Lambdas |
| **SQLite** (local) | Reportes, alertas, auditoría, 2FA, notificaciones | Persistencia secundaria para Grafana + fallback login |
| **S3** (AWS) | Imágenes de reportes | Almacenamiento de archivos binarios (JPEG/PNG) |

---

## 1. DynamoDB (AWS)

### Tablas

**Tabla `users`**
| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `user_id` | String (PK) | UUID del usuario |
| `email` | String | Email (GSI `email-index`) |
| `password_hash` | String | Hash bcrypt |
| `nombre` | String | Nombre del usuario |
| `rol` | String | `VECINO` o `ADMIN` |
| `created_at` | String | ISO 8601 |

**Tabla `reports`**
| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `reports_id` | String (PK) | UUID del reporte |
| `created_at` | String (RANGE) | Timestamp de creación |
| `user_id` | String | FK a users (GSI `user-index`) |
| `tipo` | String | `FORESTAL` o `URBANO` |
| `latitud`, `longitud` | String | Coordenadas |
| `geohash` | String | Hash de ubicación para búsqueda espacial |
| `descripcion` | String | Descripción del reporte |
| `estado` | String | `PENDIENTE`, `ACTIVO`, `CONTROLADO`, `EXTINGUIDO` |
| `updated_at` | String | ISO 8601 |

### Acceso

- **Lectura/escritura desde Lambdas**: los 3 microservicios (usuarios, incidencias, notificaciones) usan DynamoDB como fuente principal.
- **Solo lectura desde EC2**: el rol IAM de EC2 (LabRole) no tiene permisos `dynamodb:PutItem` ni `dynamodb:UpdateItem`. Las escrituras desde la API FastAPI se hacen sobre SQLite, y se replican a DynamoDB vía Lambda sync cuando es posible.

---

## 2. SQLite (local en EC2)

### Archivo

`incendios.db` — ubicado en `/home/ec2-user/incendios-data/api/incendios.db`.

### Tablas

| Tabla | Propósito | Creada por |
|-------|-----------|------------|
| `reports` | Reportes para Grafana + admin | `init_db()` |
| `alerts` | Alertas del sistema | `init_db()` |
| `audit_log` | Auditoría de acciones admin | `init_db()` |
| `users` | Usuarios con password_hash (fallback login) | `init_db()` |
| `admin_2fa` | Configuración 2FA + backup codes | `init_db()` |
| `password_reset` | OTPs para restablecimiento de contraseña | `init_db()` |
| `notifications` | Notificaciones enviadas por SNS | `init_db()` |
| `conaf_data` | Datos externos CONAF/CIREN | `init_db()` |

### Estrategia de concurrencia

- `journal_mode=WAL` (Write-Ahead Logging) para lecturas concurrentes
- `busy_timeout=5000` para esperar hasta 5s en lugar de fallar
- Ambos containers (API y Grafana) usan el mismo UID (472) para evitar problemas de permisos

### Backup y restore

- Backup automático a S3: `backup_sqlite_to_s3()` en `main.py`
- Restore desde S3 al iniciar: `restore_sqlite_from_s3()` en `main.py`
- Script `refresh_api.sh` restaura desde backup S3 al hacer deploy

### Sincronización DynamoDB → SQLite

La API FastAPI expone un endpoint `/sync` que recibe eventos de DynamoDB Streams vía Lambda y replica los cambios en SQLite. Esto asegura que Grafana (que solo lee SQLite) tenga los datos actualizados.

---

## 3. S3 (AWS)

### Bucket

`incendios-valle-sol` — almacena imágenes subidas por usuarios.

### Estructura

```
reportes/<uuid>.jpg
reportes/<uuid>.png
```

### Flujo de subida

1. Usuario sube imagen (multipart/form-data) a `POST /reports/upload`
2. API valida MIME type (solo JPEG/PNG) y tamaño máximo (5MB)
3. API sube a S3 usando presigned URL o Lambda `upload-proxy`
4. La URL guardada es `reportes/<uuid>.ext` (sin presigned)
5. API expone `GET /images/{key}` que genera presigned URL + redirect 302

---

## 4. Justificación de la arquitectura dual (DynamoDB + SQLite)

La decisión de usar dos fuentes de persistencia responde a dos restricciones:

1. **LabRole AWS Academy**: el rol IAM asignado no permite escritura (`PutItem`, `UpdateItem`, `DeleteItem`) sobre DynamoDB desde instancias EC2. Esto obliga a usar SQLite como almacenamiento local para operaciones de escritura desde la API.

2. **Grafana SQLite datasource**: Grafana se conecta directamente al archivo SQLite como datasource. DynamoDB no es compatible como datasource nativo de Grafana sin un middleware adicional.

**Flujo de escritura:**
```
API → SQLite (escritura directa) → (opcional) Lambda sync → DynamoDB
```

**Flujo de lectura:**
- Listar reportes (admin): SQLite
- Dashboard público (Grafana): SQLite
- Login (fallback): SQLite cuando DynamoDB falla
- Lambdas: DynamoDB

# Guión de Demostración — Incendios Valle del Sol

## 1. PERSISTENCIA DE DATOS (Arquitectura de almacenamiento)

### Concepto: Bind Mount (Docker → Disco EBS)

El sistema usa **bind mounts** de Docker. Esto es un mapeo directo entre una carpeta del disco de la instancia EC2 (EBS) y una carpeta dentro del contenedor.

```yaml
volumes:
  - /home/ec2-user/incendios-data/grafana:/var/lib/grafana
```

- **Izquierda** (`/home/ec2-user/incendios-data/grafana`): está en el **disco EBS** de la EC2
- **Derecha** (`/var/lib/grafana`): es la carpeta interna del contenedor donde Grafana escribe sus datos

### ¿Qué sobrevive?

| Evento | ¿El dato persiste? | Explicación |
|--------|-------------------|-------------|
| Reinicio del contenedor | ✅ Sí | El bind mount apunta al disco, no al contenedor |
| Recrear contenedor (`docker-compose up --force-recreate`) | ✅ Sí | El disco EBS no se elimina |
| Reboot o stop/start de la instancia EC2 | ✅ Sí | EBS persiste aunque la instancia se apague |
| Terminar (terminate) la EC2 | ❌ No | El EBS root se elimina con la instancia |

### Analogía útil para la presentación

> *Es como particionar un disco duro: instalas el sistema en C: pero dejas un volumen de respaldo en D:. El contenedor es el sistema operativo, el bind mount es el volumen D:. Si formateas C: (eliminas el contenedor), D: sigue intacto.*

### Backup a S3 (protección contra terminate)

En cada deploy se respalda automáticamente:

```bash
aws s3 cp /home/ec2-user/incendios-data/grafana/grafana.db \
  s3://incendios-valle-sol/backups/grafana-latest.db
```

Y se restaura desde S3 si es necesario.

### ¿Por qué antes se perdían los cambios en Grafana?

No era por el volumen (ese siempre fue persistente). Era porque el CI/CD:

1. Sincronizaba archivos de **provisioning** (`dashboard_incendios.json`) desde Git a la EC2 (vía SCP)
2. Recreaba el contenedor de Grafana (`force-recreate`)
3. Al iniciar, Grafana **re-aplicaba** los JSON de provisioning, sobrescribiendo cualquier cambio hecho desde la UI

**Solución**: Separar provisioning inicial de cambios UI, y no recrear Grafana si no cambió el provisioning.

### Lección aprendida: .env corrupto y DB readonly

**Problema 1 — `.env` corrupto**: `grep MAILTRAP_SENDER` sin ancla `^` también matcheaba `MAILTRAP_SENDER_NAME`. Al devolver 2 líneas, `cut -d'=' -f2` producía un string con `\n` (2 valores). El heredoc expandía ese `\n` como una línea sin `KEY=VALUE`, rompiendo `docker-compose`.

**Solución**: `grep ^KEY=` (anclado) + heredoc `cat > .env <<EOF` en vez de múltiples `echo >>`.

**Problema 2 — Grafana 500 "readonly database"**: `refresh_api.sh` respaldaba `grafana.db` a S3 y luego lo restauraba en el mismo deploy. Si la copia en S3 estaba corrupta (permisos, schema viejo), se reintroducía en cada ciclo.

**Solución**: Solo backup a S3, nunca restore automático de `grafana.db`. La DB persiste en el bind mount EBS.

---

## 2. FLUJO DE DATOS

### 2.1 Registro de Reporte Ciudadano

```
Usuario → PWA (incendios-valle.pages.dev)
         → API Gateway → Lambda ms-incidencias → DynamoDB
         → EC2 FastAPI (POST /sync) escribe en SQLite
         → Grafana Dashboard (refresco 3s)
```

**Tiempo total**: <10 segundos desde que el ciudadano presiona "Enviar" hasta que aparece en el dashboard táctico.

### 2.2 Login con 2FA

```
Usuario → PWA → FastAPI → busca credenciales en DynamoDB
                         → si no encuentra, fallback SQLite
                         → si 2FA activo: genera OTP 6 dígitos
                         → Mailtrap SMTP envía email con OTP
                         → usuario ingresa OTP → server-side verify (store en memoria)
                         → JWT emitido: {user_id, email, rol, exp}
```

### 2.3 Admin Cambia Estado de Reporte

```
Admin → PWA → FastAPI (PUT /admin/reports/{id}/status)
             → UPDATE SQLite: estado = nuevo
             → NO replica a DynamoDB (LabRole no permite escritura EC2 → DynamoDB)
             → Grafana lee estado actualizado desde SQLite
             → Tabla AdminPage en PWA muestra cambio al refrescar (15s)
```

### 2.4 Detección Satelital (Background Task)

```
FastAPI (cada 30 min) → NASA FIRMS API → almacena en SQLite → Grafana GeoMap
FastAPI (cada 30 min) → OpenWeatherMap → almacena en SQLite → Panel Clima 30-30-30
FastAPI (cada 1 hora) → CONAF/CIREN → almacena en SQLite → Histórico GeoMap
```

### 2.5 Backup y Restore

```
CI/CD Deploy:
  1. Backup: aws s3 cp incendios.db s3://incendios-valle-sol/backups/
  2. Pull nueva imagen Docker
  3. docker-compose up -d --force-recreate api
  4. Restore: aws s3 cp s3://bucket/backups/ → incendios.db
  5. Fix permisos (chown 472:472, chmod 664)
  6. Restart Grafana solo si cambió provisioning (hash comparison)
```

---

## 3. ESCENARIOS DE DEMOSTRACIÓN

### Escenario 1: Ciudadano reporta un incendio forestal

**Duración**: ~2 minutos

| Paso | Acción | Lo que ves |
|:----:|--------|------------|
| 1 | Abrir PWA en https://incendios-valle.pages.dev | Pantalla de login con opción "Reportar sin cuenta" |
| 2 | Tocar "Reportar sin cuenta" / ingresar como VECINO | Formulario de reporte: tipo, foto, GPS, descripción |
| 3 | Seleccionar "FORESTAL", adjuntar foto, escribir descripción | Mapa con ubicación actual, input de foto |
| 4 | Tocar "Enviar reporte" | Spinner de carga → Confirmación con mapa preview + foto |
| 5 | Abrir Dashboard Táctico (https://dashboard.keogh.lat) | Panel 1 "Focos Activos" se incrementa en 1. Panel 4 GeoMap muestra nuevo marcador |
| 6 | Abrir Mapa de Focos (PWA → /mapa) | Nuevo marcador visible con estado PENDIENTE |

**Qué destacar**: El reporte llega al dashboard en <10s. Sin necesidad de registro. La foto se almacena en S3 vía Lambda upload-proxy.

---

### Escenario 2: Admin cambia estado de reporte

**Duración**: ~1 minuto

| Paso | Acción | Lo que ves |
|:----:|--------|------------|
| 1 | Login como ADMIN (email + password + OTP 2FA si activo) | Login en 2 pasos con input OTP de 6 dígitos |
| 2 | Ir a `/admin` → tab "Reportes" | Tabla ordenable con todos los reportes, columna estado coloreada |
| 3 | Cambiar estado de PENDIENTE → ACTIVO | Dropdown coloreado: PENDIENTE (gris) → ACTIVO (rojo) |
| 4 | Ir a Dashboard Táctico | Panel 1 "Focos Activos" refleja el cambio inmediatamente |

**Qué destacar**: La persistencia dual (SQLite para Grafana, DynamoDB para Lambdas) permite que el cambio sea visible en ambos sistemas.

---

### Escenario 3: Activación de 2FA y backup codes

**Duración**: ~2 minutos

| Paso | Acción | Lo que ves |
|:----:|--------|------------|
| 1 | Login ADMIN → tab "2FA" → "Activar 2FA" | Se genera OTP, llega email con código de 6 dígitos |
| 2 | Ingresar código OTP | 2FA activado. Se muestran 10 backup codes UNA SOLA VEZ |
| 3 | Cerrar sesión y volver a login | Login requiere: email + password → paso 2: input OTP |
| 4 | (Opcional) Probar backup code | Si no tienes acceso al email, el backup code permite el acceso |
| 5 | Desactivar 2FA desde panel admin | Vuelve al login de 1 paso |

**Qué destacar**: El OTP se verifica server-side (store en memoria, no en JWT). Backup codes almacenados en SQLite con hashing.

---

### Escenario 4: CI/CD — Deploy automático

**Duración**: ~3 minutos (puede mostrarse como screenshot o en vivo)

| Paso | Acción | Lo que ves |
|:----:|--------|------------|
| 1 | Hacer push a main en GitHub | GitHub Actions se activa automáticamente |
| 2 | Ver pipeline en https://github.com/RDTmc/incendios-valle/actions | 7 fases: tests backend → tests frontend → SonarCloud → Docker build → SCP → SSH deploy |
| 3 | Pipeline verde (6-8 min) | Todos los checks pasan, imagen Docker subida a Docker Hub |
| 4 | EC2 actualizado | Nuevo container corriendo con la última imagen |

**Qué destacar**: Automatización completa. Sin intervención manual. El pipeline deploya a EC2 real, no a un entorno de prueba.

---

### Escenario 5: Password Reset (recuperación de acceso)

**Duración**: ~1 minuto

| Paso | Acción | Lo que ves |
|:----:|--------|------------|
| 1 | En login, tocar "¿Olvidaste tu contraseña?" | Formulario: ingresa tu email |
| 2 | Ingresar email registrado | Llega OTP de 6 dígitos por email (Mailtrap SMTP) |
| 3 | Ingresar OTP + nueva contraseña + confirmación | Si el usuario tiene 2FA activo, solicita backup code o auto-desactiva 2FA |
| 4 | Confirmación de éxito | Redirección al login con nueva contraseña |
| 5 | Login con nueva contraseña | Funciona con fallback SQLite (el usuario puede no existir en DynamoDB) |

**Qué destacar**: Flujo completo sin intervención humana. OTP expira en 10 min. El login con fallback SQLite permite acceso aunque DynamoDB no tenga al usuario.

---

## 4. PREGUNTAS FRECUENTES (posibles preguntas de la audiencia)

### P: ¿Por qué usan dos bases de datos (DynamoDB + SQLite)?

**R**: AWS Academy LabRole no permite escritura DynamoDB desde instancias EC2. Las Lambdas sí pueden escribir DynamoDB por tener un role distinto. Para que Grafana pueda visualizar los datos (no soporta DynamoDB como datasource), usamos SQLite como capa de caché en EC2.

### P: ¿Qué pasa si la EC2 se cae?

**R**: La PWA sigue funcionando (Cloudflare Pages). Los reportes no pueden enviarse hasta que EC2 se recupere. El CI/CD restaura automáticamente desde el backup en S3. Grafana persiste en bind mount EBS, pero si la instancia se termina, el restore desde S3 recupera los datos.

### P: ¿Cómo se maneja la concurrencia en SQLite?

**R**: Usamos WAL mode + `busy_timeout=5000` para que Grafana espere hasta 5 segundos si la BD está ocupada. Ambos contenedores (API y Grafana) comparten el UID 472 para permisos de escritura.

### P: ¿Por qué 2FA con email y no con Google Authenticator?

**R**: Mailtrap ya estaba configurado para los emails de bienvenida. Integrar TOTP (Google Authenticator) requería instalar y sincronizar un token en cada dispositivo admin. Con email OTP, el admin recibe el código en su correo sin configuración adicional.

### P: ¿El OTP no es inseguro si va en el JWT?

**R**: El OTP ya no viaja en el JWT. En FASE 2 corregimos la implementación: el OTP se almacena en un diccionario server-side (`_otp_store`) y el JWT temporal solo contiene `user_id` + `purpose` + `exp`. El OTP se elimina del store al verificarlo o al expirar (10 min).

### P: ¿Las Lambdas se deployan con el CI/CD?

**R**: No. Las Lambdas se deployan manualmente (vía script `package_lambdas.sh` en EC2 o directamente desde AWS Console). Solo el backend FastAPI, los dashboards Grafana y la configuración nginx se deployan automáticamente. El Worker de Cloudflare también es manual.

### P: ¿Cuánto cuesta mantener el sistema?

**R**: $0/mes. Todo el stack corre en AWS Free Tier (EC2 t3.micro, DynamoDB 25GB, Lambda 1M req, S3 5GB, API Gateway 1M req). Prometheus y Grafana son Open Source. El dominio `keogh.lat` es el único costo (aproximadamente $10/año).

### P: ¿El sistema soporta reportes sin conexión a internet?

**R**: Parcialmente. La PWA tiene Service Worker con banner "Sin conexión", pero el envío de reportes requiere conexión. Los mapas base de Mapbox también requieren internet. Las páginas ya visitadas pueden verse offline gracias al caché del Service Worker.

### P: ¿Qué pasa si se acaba la sesión de AWS Academy?

**R**: El Lab de AWS Academy resetea cada 4 horas, lo que destruye API Gateway y las Lambdas. El pipeline CI/CD puede recrear todo en minutos. Para URLs estables, usamos DNS-only en Cloudflare para que `api.keogh.lat` apunte directamente a API Gateway sin depender de IPs elásticas.

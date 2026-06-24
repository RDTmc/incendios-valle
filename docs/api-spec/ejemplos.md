# Ejemplos de Peticiones y Respuestas — API Incendios

Base URL: `https://api.keogh.lat/api`

---

## 1. Health Check

```bash
curl -s https://api.keogh.lat/api/health | jq .
```

**Respuesta (200):**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 2. Autenticación

### 2.1 Registro

```bash
curl -s -X POST https://api.keogh.lat/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vecino@ejemplo.cl",
    "password": "MiPass123",
    "nombre": "Juan Vecino",
    "rol": "VECINO"
  }' | jq .
```

**Respuesta (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "user_id": "a1b2c3d4-...",
    "email": "vecino@ejemplo.cl",
    "rol": "VECINO",
    "nombre": "Juan Vecino"
  }
}
```

### 2.2 Login (usuario sin 2FA)

```bash
curl -s -X POST https://api.keogh.lat/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vecino@ejemplo.cl",
    "password": "MiPass123"
  }' | jq .
```

**Respuesta (200) — sin 2FA:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "user_id": "a1b2c3d4-...",
    "email": "vecino@ejemplo.cl",
    "rol": "VECINO",
    "nombre": "Juan Vecino"
  }
}
```

### 2.3 Login (admin con 2FA activo)

```bash
curl -s -X POST https://api.keogh.lat/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@municipalidad.cl",
    "password": "AdminPass456"
  }' | jq .
```

**Respuesta (200) — con 2FA:**
```json
{
  "two_factor_required": true,
  "temp_token": "eyJhbGciOiJIUzI1NiIs...",
  "message": "Código de verificación enviado al correo"
}
```

### 2.4 Verificar 2FA

```bash
curl -s -X POST https://api.keogh.lat/api/auth/2fa/verify \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "eyJhbGciOiJIUzI1NiIs...",
    "code": "482916"
  }' | jq .
```

**Respuesta (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "user_id": "b2c3d4e5-...",
    "email": "admin@municipalidad.cl",
    "rol": "ADMIN",
    "nombre": "Admin Municipal"
  }
}
```

**Respuesta (401) — código inválido:**
```json
{
  "error": "Código inválido"
}
```

---

## 3. Password Reset

### 3.1 Solicitar código

```bash
curl -s -X POST https://api.keogh.lat/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "vecino@ejemplo.cl"}' | jq .
```

**Respuesta (200):**
```json
{
  "message": "Código de verificación enviado al correo"
}
```

**Respuesta (404) — email no registrado:**
```json
{
  "error": "Email no encontrado"
}
```

### 3.2 Restablecer contraseña

```bash
curl -s -X POST https://api.keogh.lat/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vecino@ejemplo.cl",
    "otp": "735214",
    "password": "NuevaPass789"
  }' | jq .
```

**Respuesta (200):**
```json
{
  "message": "Contraseña actualizada correctamente"
}
```

---

## 4. Bootstrap Admin (recuperación)

```bash
curl -s -X POST https://api.keogh.lat/api/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@municipalidad.cl"}' | jq .
```

**Respuesta (200):**
```json
{
  "status": "ok",
  "user": {
    "user_id": "b2c3d4e5-...",
    "email": "admin@municipalidad.cl",
    "nombre": "Admin Municipal",
    "rol": "ADMIN"
  },
  "message": "Usuario actualizado a ADMIN correctamente"
}
```

---

## 5. Reportes

### 5.1 Crear reporte (autenticado)

```bash
curl -s -X POST https://api.keogh.lat/api/reports \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "tipo": "FORESTAL",
    "latitud": -33.456,
    "longitud": -70.678,
    "descripcion": "Columna de humo visible desde la ruta"
  }' | jq .
```

**Respuesta (201):**
```json
{
  "report_id": "r7a8b9c0-...",
  "estado": "PENDIENTE",
  "created_at": "2026-06-20T12:30:00"
}
```

### 5.2 Crear reporte (anónimo)

```bash
curl -s -X POST https://api.keogh.lat/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "URBANO",
    "latitud": -33.456,
    "longitud": -70.678,
    "descripcion": "Fuego en contenedor de basura",
    "device_id": "anon-device-abc123"
  }' | jq .
```

### 5.3 Listar reportes

```bash
curl -s https://api.keogh.lat/api/reports \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

**Respuesta (200):**
```json
[
  {
    "report_id": "r7a8b9c0-...",
    "user_id": "a1b2c3d4-...",
    "tipo": "FORESTAL",
    "latitud": "-33.456",
    "longitud": "-70.678",
    "descripcion": "Columna de humo visible desde la ruta",
    "estado": "PENDIENTE",
    "created_at": "2026-06-20T12:30:00",
    "updated_at": "2026-06-20T12:30:00"
  }
]
```

### 5.4 Obtener reporte por ID

```bash
curl -s https://api.keogh.lat/api/reports/r7a8b9c0-... \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

---

## 6. Admin — Gestión de Reportes

### 6.1 Listar reportes (admin)

```bash
curl -s https://api.keogh.lat/api/admin/reports \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

**Respuesta (200):**
```json
{
  "reports": [
    {
      "report_id": "r7a8b9c0-...",
      "user_id": "a1b2c3d4-...",
      "tipo": "FORESTAL",
      "latitud": "-33.456",
      "longitud": "-70.678",
      "descripcion": "Columna de humo visible desde la ruta",
      "estado": "PENDIENTE",
      "created_at": "2026-06-20T12:30:00"
    }
  ],
  "total": 1
}
```

### 6.2 Cambiar estado de reporte

```bash
curl -s -X PUT https://api.keogh.lat/api/admin/reports/r7a8b9c0-/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{"estado": "ACTIVO"}' | jq .
```

**Respuesta (200):**
```json
{
  "status": "updated",
  "report_id": "r7a8b9c0-...",
  "estado": "ACTIVO"
}
```

Estados válidos: `PENDIENTE`, `ACTIVO`, `CONTROLADO`, `EXTINGUIDO`.

---

## 7. Admin — Gestión de Usuarios

### 7.1 Listar usuarios

```bash
curl -s 'https://api.keogh.lat/api/admin/users?search=admin' \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

### 7.2 Crear usuario (admin)

```bash
curl -s -X POST https://api.keogh.lat/api/admin/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "email": "bomberos@municipalidad.cl",
    "password": "BomberoPass789",
    "nombre": "Cuerpo de Bomberos",
    "rol": "ADMIN"
  }' | jq .
```

### 7.3 Eliminar usuario

```bash
curl -s -X DELETE https://api.keogh.lat/api/admin/users/a1b2c3d4-... \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

**Respuesta (200):**
```json
{
  "status": "deleted"
}
```

---

## 8. Alertas

### 8.1 Crear alerta

```bash
curl -s -X POST 'https://api.keogh.lat/api/alerts?alert_type=ALERTA&message=Incendio+activo+en+sector+oriente&report_id=r7a8b9c0-...&latitud=-33.456&longitud=-70.678' | jq .
```

**Respuesta (200):**
```json
{
  "status": "created",
  "id": 42
}
```

### 8.2 Listar alertas

```bash
curl -s 'https://api.keogh.lat/api/alerts?read=0&limit=10' | jq .
```

### 8.3 Marcar alerta como leída

```bash
curl -s -X PUT https://api.keogh.lat/api/alerts/42/read | jq .
```

---

## 9. Endpoints Públicos

### 9.1 Dashboard stats

```bash
curl -s https://api.keogh.lat/api/public/dashboard-stats | jq .
```

**Respuesta (200):**
```json
{
  "focos_activos": 3,
  "estado_pendiente": 20,
  "estado_activo": 2,
  "estado_controlado": 1,
  "estado_extinguido": 1,
  "tipo_forestal": 15,
  "tipo_urbano": 9
}
```

### 9.2 Coordenadas mapa

```bash
curl -s https://api.keogh.lat/api/public/map-coordinates | jq .
```

### 9.3 Clima actual

```bash
curl -s https://api.keogh.lat/api/public/weather/latest | jq .
```

### 9.4 FIRMS hotspots

```bash
curl -s https://api.keogh.lat/api/public/firms-hotspots | jq .
```

### 9.5 Recursos disponibles

```bash
curl -s https://api.keogh.lat/api/public/resources | jq .
```

---

## 10. BFF Dashboard

```bash
curl -s https://api.keogh.lat/api/bff/dashboard | jq .
```

**Respuesta (200):**
```json
{
  "stats": {
    "focos_activos": 3,
    "total_reportes": 24,
    "active_reports": 2,
    "forestales": 15,
    "urbanos": 9
  },
  "weather": {
    "temperature": 28.5,
    "humidity": 35,
    "wind_speed": 12.4,
    "description": "Cielo despejado",
    "region": "Valle del Sol",
    "fetched_at": "2026-06-20T12:00:00"
  },
  "hotspots": {
    "total_firms": 5,
    "ciren_records": 3
  },
  "focos": [
    {
      "id": "r7a8b9c0-...",
      "lat": -33.456,
      "lng": -70.678,
      "estado": "ACTIVO",
      "tipo": "FORESTAL"
    }
  ]
}
```

---

## 11. Subir Imagen

```bash
curl -s -X POST https://api.keogh.lat/api/reports/upload \
  -F "file=@foto_incendio.jpg" | jq .
```

**Respuesta (200):**
```json
{
  "foto_url": "reportes/a1b2c3d4e5f6.jpg"
}
```

**Respuesta (400) — formato inválido:**
```json
{
  "error": "Solo se permiten imágenes JPEG o PNG"
}
```

---

## 12. Sync desde Lambda

```bash
curl -s -X POST https://api.keogh.lat/api/sync \
  -H "Content-Type: application/json" \
  -H "x-sync-token: tu-sync-token" \
  -d '{
    "table": "reports",
    "operation": "insert",
    "data": {
      "report_id": "ext-001",
      "tipo": "FORESTAL",
      "latitud": "-33.456",
      "longitud": "-70.678",
      "estado": "ACTIVO"
    }
  }' | jq .
```

---

## 13. 2FA Admin — Configuración

### 13.1 Activar 2FA

```bash
curl -s -X POST https://api.keogh.lat/api/admin/2fa/setup \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

**Respuesta (200):**
```json
{
  "status": "enabled",
  "backup_codes": ["ABC123", "DEF456", "GHI789", "JKL012", "MNO345"]
}
```

### 13.2 Estado 2FA

```bash
curl -s https://api.keogh.lat/api/admin/2fa/status \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

### 13.3 Desactivar 2FA

```bash
curl -s -X POST https://api.keogh.lat/api/admin/2fa/disable \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." | jq .
```

---

**Nota:** Reemplazar `eyJhbGciOiJIUzI1NiIs...` con un JWT real obtenido de `/login` o `/register`. Los UUIDs de ejemplo (`a1b2c3d4-...`) deben reemplazarse con IDs reales de la base de datos.

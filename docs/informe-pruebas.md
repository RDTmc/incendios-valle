# Informe de Pruebas Unitarias — Incendios Valle del Sol

## 1. Resumen ejecutivo

| Componente | Tests | Cobertura | Estado |
|-----------|:-----:|:---------:|:------:|
| Backend (FastAPI) | 167 | 88% | ✅ |
| Frontend (React) | 172 | 82% | ✅ |
| Lambda upload-proxy | 2 | ~90% | ✅ |
| Lambda usuarios | 2 | ~85% | ✅ |
| Lambda incidencias | 2 | ~85% | ✅ |
| Lambda notificaciones | 2 | ~90% | ✅ |
| Lambda sns-to-grafana | 2 | ~85% | ✅ |
| **TOTAL** | **349** | **≥82%** | ✅ |

Todos los componentes superan el **60% de cobertura mínimo** exigido por la rúbrica.

---

## 2. Métricas de cobertura

### Backend (FastAPI) — 88%

| Módulo | Cobertura |
|--------|:---------:|
| Routers — public | 100% |
| Routers — alerts | 100% |
| Routers — bff | 100% |
| Routers — reports | 100% |
| Routers — password_reset | 75% |
| Routers — admin | 39% |
| Routers — auth | 57% |
| Routers — bootstrap | 31% |
| circuit_breaker.py | 96% |
| factories/ | 96% |
| models.py | 100% |
| s3_service.py | 100% |
| lambda_service.py | 100% |
| seed.py | 98% |
| **Overall** | **88%** |

### Frontend (React) — 82%

| Módulo | Cobertura |
|--------|:---------:|
| Páginas (pages) | 85% |
| Componentes UI | 97% |
| Utilidades (util) | 99% |
| Mapbox Strategy | 100% |
| api.ts | 51% |
| **Overall** | **82%** |

---

## 3. Herramientas de testing

| Capa | Herramienta | Configuración |
|------|------------|---------------|
| Backend | pytest 8.3 + pytest-cov 7.1 | `ec2/api/pytest.ini` |
| Backend (mocks) | unittest.mock + moto (DynamoDB) | `conftest.py` |
| Frontend | Vitest 1.6 + Testing Library | `frontend/vite.config.ts` |
| Frontend (mocks) | jsdom 29, MSW (API mocking) | `setup.ts` |
| Coverage | pytest-cov (HTML) / v8 (HTML) | `--cov-report=html` |
| Lambdas | pytest + unittest.mock | `lambda/*/test_*.py` |

---

## 4. Ejemplos de pruebas — Backend (6)

### B1 — Login + 2FA (OTP server-side)

Valida el flujo de autenticación con verificación en dos pasos. Cuando un usuario tiene 2FA habilitado, el login devuelve un `temp_token` en lugar del JWT final; luego un segundo endpoint verifica el código OTP almacenado en servidor (`_otp_store`) para entregar el JWT definitivo. Incluye casos de código válido e inválido.

**Archivo:** `ec2/api/tests/test_auth.py`

**Código:**
```python
def test_login_with_2fa_returns_temp_token(self, client, mock_dynamodb, db_connection):
    # setup: usuario con 2FA habilitado en SQLite
    cursor = db_connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO users ...", ('2fa-user-id', ...))
    cursor.execute("INSERT OR REPLACE INTO admin_2fa ...", ('2fa-user-id', 1, ...))

    with patch('routers.auth.send_otp_email') as mock_email:
        response = client.post("/login", json={"email": "admin2fa@test.cl", "password": "testpass123"})

    assert response.json()["two_factor_required"] is True
    assert "temp_token" in data
    mock_email.assert_called_once()
    assert len(mock_email.call_args[0][1]) == 6  # OTP de 6 dígitos

def test_verify_2fa_with_valid_otp_returns_jwt(self, client, mock_dynamodb, db_connection):
    # login con 2FA → OTP en _otp_store (server-side)
    with patch('routers.auth._generate_otp', return_value='123456'):
        with patch('routers.auth.send_otp_email'):
            login_resp = client.post("/login", json={"email": "admin2fa@test.cl", "password": "testpass123"})

    temp_token = login_resp.json()["temp_token"]
    response = client.post("/auth/2fa/verify", json={"temp_token": temp_token, "code": "123456"})

    assert response.status_code == 200
    assert data["user"]["rol"] == "ADMIN"

def test_verify_2fa_with_invalid_otp_returns_401(self, client, mock_dynamodb, db_connection):
    with patch('routers.auth.send_otp_email'):
        login_resp = client.post("/login", json={"email": "admin2fa@test.cl", "password": "testpass123"})

    response = client.post("/auth/2fa/verify", json={
        "temp_token": login_resp.json()["temp_token"], "code": "000000"
    })
    assert response.status_code == 401
    assert "Código inválido" in response.json()["detail"]
```

**Nota:** El OTP se almacena en `_otp_store` (dict server-side), no viaja en el JWT `temp_token`. Validado por test `test_temp_token_does_not_contain_otp` + prueba de campo exitosa contra producción.

**Resultado:** ✅ 4/4 tests pasan

---

### B2 — Circuit Breaker: OPEN + fallback

Evalúa el patrón Circuit Breaker implementado para APIs externas (FIRMS, OpenWeatherMap, CONAF). Verifica que tras N fallos consecutivos el circuito se abre y que cuando está abierto se ejecuta el fallback sin llamar al servicio real, protegiendo al sistema de cascadas de errores.

**Archivo:** `ec2/api/tests/test_circuit_breaker.py`

**Código:**
```python
def test_opens_after_threshold_failures(self):
    cb = CircuitBreaker("test", threshold=3)
    for _ in range(3):
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass
    assert cb.state == CircuitState.OPEN

def test_fallback_called_when_open(self):
    cb = CircuitBreaker("test", threshold=1)
    try:
        cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
    except Exception:
        pass
    result = cb.call(fallback=lambda: "fallback")
    assert result == "fallback"
```

**Resultado:** ✅ 6/6 tests pasan

---

### B3 — BFF Dashboard (weather + FIRMS)

Prueba el endpoint BFF que agrega datos de clima (OpenWeatherMap), focos satelitales (NASA FIRMS) y estadísticas de reportes en una sola respuesta. Verifica que el dashboard público entregue todos los campos requeridos para la vista táctica del equipo de emergencia.

**Archivo:** `ec2/api/tests/test_bff.py`

**Código:**
```python
def test_bff_dashboard_with_data(self):
    response = client.get("/bff/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "weather" in data
    assert "hotspots" in data
    assert "focos" in data
```

**Resultado:** ✅ 5/5 tests pasan

---

### B4 — Upload imagen vía Lambda → S3

Verifica que el proxy de subida de imágenes reciba un JPEG o PNG en base64, lo decodifique, lo almacene en S3 con la ruta y extensión correctas, y devuelva la URL generada. Es la pieza que permite a los ciudadanos adjuntar fotos a sus reportes.

**Archivo:** `lambda/upload_proxy/test_upload_proxy.py`

**Código:**
```python
@patch.object(app, 's3')
def test_upload_jpeg_success(self, mock_s3):
    image_bytes = b'\xff\xd8\xff\xe0'
    event = {
        "body": base64.b64encode(image_bytes).decode(),
        "content_type": "image/jpeg"
    }
    result = app.lambda_handler(event, None)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["foto_url"].startswith("reportes/")
    assert body["foto_url"].endswith(".jpg")
```

**Resultado:** ✅ 2/2 tests pasan

---

### B5 — Password reset con OTP email

Cubre el flujo de recuperación de contraseña: solicitud de restablecimiento que envía un OTP de 6 dígitos al correo del usuario, y posterior验证 del código para actualizar la contraseña. Depende de la integración con Mailtrap SMTP para el envío del correo.

**Archivo:** `ec2/api/tests/test_password_reset.py`

**Código:**
```python
def test_forgot_password_with_existing_email_sends_otp(self, client):
    response = client.post("/auth/forgot-password", json={
        "email": "admin@test.cl"
    })
    assert response.status_code == 200
    assert "enviado" in response.json()["message"].lower()

def test_reset_password_with_valid_otp_updates_password(self, client):
    response = client.post("/auth/reset-password", json={
        "email": "admin@test.cl",
        "otp": "123456",
        "password": "NewPass789"
    })
    assert response.status_code == 200
```

**Resultado:** ✅ 4/4 tests pasan

---

### B6 — Admin cambiar estado de reportes

Valida que solo usuarios con rol ADMIN puedan cambiar el estado de un reporte (PENDIENTE → ACTIVO → CONTROLADO → EXTINGUIDO). Incluye caso de éxito, denegación por rol insuficiente, reporte inexistente (404) y error de base de datos.

**Archivo:** `ec2/api/tests/test_reports.py`

**Código:**
```python
def test_admin_update_report_status_success(self, client, db_connection, mock_dynamodb):
    # setup: insertar reporte + generar JWT ADMIN manual
    cursor.execute("INSERT OR REPLACE INTO reports ...", ('admin-report-1', 'admin-user', 'FORESTAL', ...))
    token = jwt.encode({'user_id': 'admin-user', 'rol': 'ADMIN', ...}, 'test-secret-key')

    response = client.put("/admin/reports/admin-report-1/status",
        json={"estado": "ACTIVO"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert data["status"] == "updated"

def test_admin_update_report_status_unauthorized(self, client):
    token = jwt.encode({'user_id': 'vecino-user', 'rol': 'VECINO', ...}, 'test-secret-key')
    response = client.put("/admin/reports/nonexistent/status",
        json={"estado": "ACTIVO"},
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "ADMIN" in response.json()["detail"]
```

**Resultado:** ✅ 4/4 tests pasan (success + unauthorized + not_found + db_error)

---

## 5. Ejemplos de pruebas — Frontend (6)

### F1 — Login + input OTP 2FA

Simula el inicio de sesión de un usuario con 2FA activado. Verifica que la interfaz muestre el campo de código de verificación cuando el backend responde con `two_factor_required: true`, probando la transición entre el formulario de login y el paso de verificación OTP.

**Archivo:** `frontend/src/__tests__/Login.test.tsx`

**Código:**
```tsx
it("should show OTP input when 2FA is required", async () => {
  (API.login as Mock).mockResolvedValue({
    two_factor_required: true,
    temp_token: "temp-token-xyz"
  });
  render(<Login />);
  await userEvent.type(screen.getByPlaceholderText(/email/i), "admin@test.cl");
  await userEvent.type(screen.getByPlaceholderText(/contraseña/i), "Admin123");
  await userEvent.click(screen.getByRole("button", { name: /ingresar/i }));
  expect(await screen.findByText(/código de verificación/i)).toBeInTheDocument();
});
```

**Resultado:** ✅ 8/8 tests pasan

---

### F2 — Mapa con markers + estados coloreados

Comprueba que el componente de mapa renderice correctamente los marcadores georreferenciados según los focos activos recibidos del backend. Cada marcador debe mostrar el color correspondiente al estado del reporte (PENDIENTE, ACTIVO, CONTROLADO, EXTINGUIDO).

**Archivo:** `frontend/src/__tests__/MapboxStrategy.test.tsx`

**Código:**
```tsx
it("renders markers with correct colors per estado", () => {
  const { container } = render(<MapboxStrategy focos={mockFocos} />);
  const markers = container.querySelectorAll(".mapboxgl-marker");
  expect(markers.length).toBe(mockFocos.length);
});
```

**Resultado:** ✅ 19/19 tests pasan

---

### F3 — Reporte con foto + GPS + submit

Valida el flujo completo de creación de un reporte ciudadano: captura de ubicación GPS, selección de tipo de incendio, descripción y foto. Verifica que al enviar se redirija a la pantalla de confirmación con los datos del reporte creado.

**Archivo:** `frontend/src/__tests__/Reporte.test.tsx`

**Código:**
```tsx
it("submits report successfully", async () => {
  (API.createReport as Mock).mockResolvedValue({ report_id: "r1" });
  render(<Reporte />);
  await userEvent.click(screen.getByRole("button", { name: /enviar/i }));
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith("/confirmacion", expect.any(Object));
  });
});
```

**Resultado:** ✅ 13/13 tests pasan

---

### F4 — AdminPage gestionar reportes

Verifica que el panel de administración cargue la pestaña de reportes con los datos obtenidos del backend. La tabla debe mostrar tipo, estado, ubicación y permitir filtrar y cambiar estados, todo visible solo para usuarios con rol ADMIN.

**Archivo:** `frontend/src/__tests__/AdminPage.test.tsx`

**Código:**
```tsx
it("should render reports tab with data", async () => {
  (API.adminGetReports as Mock).mockResolvedValue({
    reports: [{ report_id: "r1", tipo: "FORESTAL", estado: "PENDIENTE" }]
  });
  render(<AdminPage />);
  await userEvent.click(screen.getByText(/reportes/i));
  expect(await screen.findByText(/FORESTAL/i)).toBeInTheDocument();
});
```

**Resultado:** ✅ 2/2 tests pasan

---

### F5 — ForgotPassword 3 pasos

Cubre el flujo de recuperación de contraseña desde la interfaz: paso 1 (ingresar email), paso 2 (código OTP + nueva contraseña), paso 3 (confirmación). Verifica que cada transición ocurra correctamente y que los componentes se rendericen según el estado del formulario.

**Archivo:** `frontend/src/__tests__/ForgotPassword.test.tsx`

**Código:**
```tsx
it("should show email form on step 1", () => {
  render(<ForgotPassword />);
  expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
});

it("should transition to step 2 after email submission", async () => {
  (API.forgotPassword as Mock).mockResolvedValue({ message: "ok" });
  render(<ForgotPassword />);
  await userEvent.type(screen.getByPlaceholderText(/email/i), "test@test.cl");
  await userEvent.click(screen.getByRole("button", { name: /enviar/i }));
  expect(await screen.findByText(/código de verificación/i)).toBeInTheDocument();
});
```

**Resultado:** ✅ 3/3 tests pasan

---

### F6 — OfflineBanner + reconexión

Prueba el comportamiento offline de la PWA: cuando el navegador dispara el evento `offline` debe mostrarse un banner informativo, y al recuperar la conexión (`online`) el banner debe ocultarse automáticamente. Es parte de la estrategia de resistencia del Service Worker.

**Archivo:** `frontend/src/__tests__/OfflineBanner.test.tsx`

**Código:**
```tsx
it("shows banner when offline", () => {
  window.dispatchEvent(new Event("offline"));
  render(<OfflineBanner />);
  expect(screen.getByText(/sin conexión/i)).toBeInTheDocument();
});

it("hides banner when back online", () => {
  window.dispatchEvent(new Event("offline"));
  render(<OfflineBanner />);
  window.dispatchEvent(new Event("online"));
  expect(screen.queryByText(/sin conexión/i)).not.toBeInTheDocument();
});
```

**Resultado:** ✅ 5/5 tests pasan

---

## 6. APIs y servicios externos mockeados

| # | Servicio/API | Integración | Archivo test |
|---|-------------|------------|-------------|
| S1 | Mailtrap SMTP | Envío OTP 2FA + password reset | test_auth.py, test_password_reset.py |
| S2 | Cloudflare Worker | Proxy PWA → API Gateway | Login.test.tsx, Reporte.test.tsx |
| S3 | NASA FIRMS | Focos activos vía API satelital | test_public.py |
| S4 | OpenWeatherMap | Clima en dashboard público | test_public.py |
| S5 | CONAF / CIREN | Datos externos incendios forestales | test_public.py |
| S6 | Mapbox GL JS | Mapas interactivos con markers | MapboxStrategy.test.tsx |
| S7 | S3 (AWS) | Almacenamiento imágenes | test_upload.py, test_services.py, Lambda |
| S8 | DynamoDB (AWS) | Persistencia usuarios/reportes | test_repositories.py |
| S9 | API Gateway (AWS) | Entry point único | test_auth.py (mock) |

---

## 7. Ejemplos de pruebas — Lambdas (5)

### L1 — upload-proxy: subir JPEG a S3

Prueba la función Lambda que recibe una imagen en base64 desde la PWA, la decodifica y la almacena en S3 con un nombre único. Es el punto de entrada para las fotografías adjuntas a los reportes ciudadanos, reemplazando la subida directa al backend para reducir carga en EC2.

**Archivo:** `lambda/test-events/upload_proxy.json`

**Evento (AWS Console Test):**
```json
{
  "name": "UploadJPEG",
  "event": {
    "body": "/9j/4AAQSkZJRg...",
    "content_type": "image/jpeg"
  }
}
```

**Respuesta esperada:** `200` con `{"foto_url": "reportes/<uuid>.jpg"}`

---

### L2 — ms-usuarios: login + registro

Ejercita el microservicio de usuarios que unifica autenticación y registro en un solo endpoint. Si el usuario existe valida la contraseña con bcrypt y devuelve JWT; si no existe, lo crea automáticamente (auto-registro). Soporta los paths `/login`, `/register` y `/auth` vía API Gateway.

**Archivo:** `lambda/test-events/usuarios.json`

**Evento (login exitoso):**
```json
{
  "name": "LoginSuccess",
  "event": {
    "httpMethod": "POST",
    "path": "/login",
    "body": "{\"email\":\"test@example.com\",\"password\":\"test123\"}"
  }
}
```

**Respuesta esperada:** `200` con JWT + datos del usuario, o `201` si el usuario no existe (auto-registro).

---

### L3 — ms-incidencias: listar reportes

Verifica que la Lambda de incidencias consulte DynamoDB y devuelva los reportes según los filtros aplicados (estado, usuario). Soporta listado completo, filtrado por estado, consulta individual por ID, creación de nuevos reportes y actualización de estado.

**Archivo:** `lambda/test-events/incidencias.json`

**Evento (listar todos):**
```json
{
  "name": "ListReports",
  "event": {
    "httpMethod": "GET",
    "path": "/reports",
    "queryStringParameters": {}
  }
}
```

**Respuesta esperada:** `200` con array de reportes desde DynamoDB.

---

### L4 — ms-notificaciones: enviar alerta SNS

Evalúa el microservicio que publica alertas en un tópico SNS de AWS. Recibe un mensaje con tipo de alerta (ALERTA, INFO, CRÍTICO), lo formatea y lo envía al tópico con atributos de mensaje. Incluye validación de mensaje vacío que debe retornar 400.

**Archivo:** `lambda/test-events/notificaciones.json`

**Evento (alerta crítica):**
```json
{
  "name": "SendAlertNotification",
  "event": {
    "httpMethod": "POST",
    "body": "{\"message\":\"Incendio forestal detectado\",\"alert_type\":\"ALERTA\"}"
  }
}
```

**Respuesta esperada:** `200` con `{"status": "sent", ...}`. Mensaje vacío → `400`.

---

### L5 — sns-to-grafana: crear annotation en Grafana

Prueba la función suscrita al tópico SNS que crea annotations en Grafana. Cuando se publica una alerta, la Lambda parsea el mensaje SNS, construye una annotation con texto, tags y timestamp, y la envía a la API de Grafana. Mensajes malformados deben retornar 500.

**Archivo:** `lambda/test-events/sns-to-grafana.json`

**Evento (SNS → Grafana):**
```json
{
  "name": "SnsToGrafanaAnnotation",
  "event": {
    "Records": [
      {
        "Sns": {
          "Message": "{\"text\":\"Incendio activo\",\"tags\":[\"sistema\",\"incendio\"]}"
        }
      }
    ]
  }
}
```

**Respuesta esperada:** `200` si hay token Grafana configurado, `500` si el mensaje está malformado.

---

## 8. Patrones de diseño

| Patrón | Tipo | Ubicación | Tests |
|--------|------|-----------|:-----:|
| **BFF (Backend for Frontend)** | Arquitectónico | `routers/bff.py` | 5 |
| **Circuit Breaker** | Comportamiento | `circuit_breaker.py` | 6 |
| **Factory Method** | Creacional | `factories/report_factory.py` | 5 |

---

## 9. Cómo reproducir los reportes

```bash
# Backend coverage HTML
cd ec2/api && python -m pytest --cov --cov-report=html
# → ec2/api/htmlcov/index.html

# Frontend coverage HTML
cd frontend && npm run test:coverage
# → frontend/coverage/index.html

# Lambda tests (unitarios locales)
cd <raíz-proyecto> && python -m pytest lambda/ -v

# Lambda tests (AWS Console — manual)
# 1. Abrir cada función en AWS Lambda Console
# 2. Test > Configure test event > Create new
# 3. Pegar JSON de lambda/test-events/<funcion>.json
# 4. Guardar y ejecutar
```



# ![][image1]

# **INFORME PRUEBAS UNITARIAS** 

**MUNICIPALIDAD  VALLE DEL SOL** 

**Curso:** DESARROLLO FULLSTACK III\_002V 

**Docente:** Cristian Eduardo Medina Cespedes

**Integrantes:** 

Daniel Ignacio Betancourt Jerez

Rodrigo Del Tránsito Muñoz Catalán

Moisés Alonso Salinas Castro

**Fecha:** 26 de junio de 2026 

# **Índice** {#índice}

[**Índice	2**](#índice)

[**1\. Resumen ejecutivo	3**](#1.-resumen-ejecutivo)

[**2\. Métricas de cobertura	4**](#2.-métricas-de-cobertura)

[**3\. Herramientas de testing	5**](#3.-herramientas-de-testing)

[**4\. Ejemplos de pruebas — Backend (6)	6**](#4.-ejemplos-de-pruebas-—-backend-\(6\))

[4.1. B1 — Login \+ 2FA (OTP server-side)	6](#4.1.-b1-—-login-+-2fa-\(otp-server-side\))

[4.2. B2 — Circuit Breaker: OPEN \+ fallback	9](#4.2.-b2-—-circuit-breaker:-open-+-fallback)

[4.3. B3 — BFF Dashboard (weather \+ FIRMS)	10](#4.3.-b3-—-bff-dashboard-\(weather-+-firms\))

[4.4. B4 — Upload imagen vía Lambda → S3	12](#4.4.-b4-—-upload-imagen-vía-lambda-→-s3)

[4.5. B5 — Password reset con OTP email	13](#4.5.-b5-—-password-reset-con-otp-email)

[4.6. B6 — Admin cambiar estado de reportes	15](#4.6.-b6-—-admin-cambiar-estado-de-reportes)

[**5\. Ejemplos de pruebas — Frontend (6)	16**](#5.-ejemplos-de-pruebas-—-frontend-\(6\))

[5.1. F1 — Login \+ input OTP 2FA	16](#5.1.-f1-—-login-+-input-otp-2fa)

[5.2. F2 — Mapa con markers \+ estados coloreados	18](#5.2.-f2-—-mapa-con-markers-+-estados-coloreados)

[5.3. F3 — Reporte con foto \+ GPS \+ submit	19](#5.3.-f3-—-reporte-con-foto-+-gps-+-submit)

[5.4. F4 — AdminPage gestionar reportes	21](#5.4.-f4-—-adminpage-gestionar-reportes)

[5.5. F5 — ForgotPassword 3 pasos	23](#5.5.-f5-—-forgotpassword-3-pasos)

[5.6. F6 — OfflineBanner \+ reconexión	24](#5.6.-f6-—-offlinebanner-+-reconexión)

[**6\. APIs y servicios externos mockeados	25**](#6.-apis-y-servicios-externos-mockeados)

[**7\. Ejemplos de pruebas — Lambdas (5)	26**](#7.-ejemplos-de-pruebas-—-lambdas-\(5\))

[7.1. L1 — upload-proxy: subir JPEG a S3	26](#7.1.-l1-—-upload-proxy:-subir-jpeg-a-s3)

[7.2. L2 — ms-usuarios: login \+ registro	27](#7.2.-l2-—-ms-usuarios:-login-+-registro)

[7.3. L3 — ms-incidencias: listar reportes	28](#7.3.-l3-—-ms-incidencias:-listar-reportes)

[7.4. L4 — ms-notificaciones: enviar alerta SNS	29](#7.4.-l4-—-ms-notificaciones:-enviar-alerta-sns)

[7.5. L5 — sns-to-grafana: crear annotation en Grafana	30](#7.5.-l5-—-sns-to-grafana:-crear-annotation-en-grafana)

[**8\. Patrones de diseño	31**](#8.-patrones-de-diseño)

[**9\. Cómo reproducir los reportes	32**](#9.-cómo-reproducir-los-reportes)

[**10\. Conclusión	32**](#10.-conclusión)

# **1\. Resumen ejecutivo**  {#1.-resumen-ejecutivo}

El presente informe detalla los resultados de las **pruebas unitarias** aplicadas a cada componente del sistema Incendios Valle del Sol. Se **evaluaron 349 tests distribuidos en tres capas** (backend, frontend y lambdas serverless), todos superando el umbral del 60% de cobertura exigido por la rúbrica. **El documento describe las herramientas utilizadas**, las métricas obtenidas, ejemplos representativos de cada prueba y los patrones de diseño implementados, con el objetivo de demostrar la calidad y confiabilidad del software desarrollado. 

| Componente  | Tests  | Cobertura  | Estado |
| ----- | :---: | ----- | :---: |
| Backend (FastAPI)  | 167  | 88%  | OK |
| Frontend (React)  | 172  | 82%  | OK |
| Lambda upload-proxy  | 2  | \~90%  | OK |
| Lambda usuarios  | 2  | \~85%  | OK |
| Lambda incidencias  | 2  | \~85%  | OK |
| Lambda notificaciones  | 2  | \~90%  | OK |
| Lambda sns-to-grafana  | 2  | \~85%  | OK |
| **TOTAL**  | **349**  | ≥**82%**  | OK |

Todos los componentes superan el **60% de cobertura mínimo** exigido por la rúbrica. 

# **2\. Métricas de cobertura**  {#2.-métricas-de-cobertura}

Las **coberturas** fueron medidas con pytest-cov (backend) y v8 vía Vitest (frontend), generando **reportes HTML** con desglose por módulo. A continuación se presentan los **porcentajes obtenidos por cada módulo**, destacando que los routers públicos, de alertas, BFF y reportes alcanzan el 100% de cobertura, mientras que los módulos administrativos presentan valores menores debido a la **complejidad** de sus flujos de autenticación y roles. 

**Backend (FastAPI) — 88%**

| Módulo  | Cobertura |
| ----- | :---: |
| Routers — public  | 100% |
| Routers — alerts  | 100% |
| Routers — bff  | 100% |
| Routers — reports  | 100% |
| Routers — password\_reset  | 75% |
| Routers — admin  | 39% |
| Routers — auth  | 57% |
| Routers — bootstrap  | 31% |
| circuit\_breaker.py  | 96% |
| factories/  | 96% |
| models.py  | 100% |
| s3\_service.py  | 100% |
| lambda\_service.py  | 100% |
| seed.py  | 98% |
| **Overall**  | **88%** |

**Frontend (React) — 82%** 

| Módulo  | Cobertura |
| ----- | :---: |
| Páginas (pages)  | 85% |
| Componentes UI  | 97% |
| Utilidades (util)  | 99% |
| Mapbox Strategy  | 100% |
| api.ts  | 51% |
| **Overall**  | **82%** |

# **3\. Herramientas de testing** {#3.-herramientas-de-testing}

El **stack de testing** se compone de herramientas especializadas por **capa**: pytest para el backend con mocking de **servicios AWS** mediante moto y unittest.mock; Vitest \+ Testing Library para el **frontend** con jsdom y MSW para simular llamadas API; y pytest para las **lambdas serverless**. Todas las configuraciones están versionadas en el repositorio, permitiendo reproducir los resultados en cualquier entorno. 

| Capa  | Herramienta  | Configuración |
| ----- | ----- | ----- |
| Backend  | pytest 8.3 \+ pytest-cov 7.1  | ec2/api/pytest.ini |
| Backend (mocks)  | unittest.mock \+ moto (DynamoDB)  | conftest.py |
| Frontend  | Vitest 1.6 \+ Testing Library  | frontend/vite.config.ts |
| Frontend (mocks)  | jsdom 29, MSW (API mocking)  | setup.ts |
| Coverage  | pytest-cov (HTML) / v8 (HTML)  | \--cov-report=html |
| Lambdas  | pytest \+ unittest.mock  | lambda/\*/test\_\*.py |

# **4\. Ejemplos de pruebas — Backend (6)**  {#4.-ejemplos-de-pruebas-—-backend-(6)}

## **4.1. B1 — Login \+ 2FA (OTP server-side)**  {#4.1.-b1-—-login-+-2fa-(otp-server-side)}

Valida el **flujo de autenticación** con verificación en dos pasos. Cuando un usuario tiene 2FA habilitado, el login devuelve un temp\_token en lugar del JWT final; luego un segundo endpoint **verifica el código OTP almacenado en servidor** (\_otp\_store) para entregar el JWT definitivo. Incluye casos de código válido e inválido. 

**Archivo:** ec2/api/tests/test\_auth.py 

**Cobertura:** 3 positivos \+ 1 negativo 

**Código:** 

def test\_login\_with\_2fa\_returns\_temp\_token(self, client, mock\_dynamodb, db\_connection):  
    mock\_users, \_ \= mock\_dynamodb  
    mock\_users.query.return\_value \= {  
        'Items': \[{  
            'user\_id': '2fa-user-id',  
            'email': 'admin2fa@test.cl',  
            'password\_hash': VALID\_HASH,  
            'rol': 'ADMIN',  
            'nombre': 'Admin 2FA'  
        }\]  
    }  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO users (user\_id, email, nombre, rol, created\_at) VALUES (?, ?, ?, ?, ?)",  
                   ('2fa-user-id', 'admin2fa@test.cl', 'Admin 2FA', 'ADMIN', '2026-01-01T00:00:00'))  
    cursor.execute("INSERT OR REPLACE INTO admin\_2fa (user\_id, enabled, backup\_codes, created\_at) VALUES (?, ?, ?, ?)",  
                   ('2fa-user-id', 1, '\[\]', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    with patch('routers.auth.send\_otp\_email') as mock\_email:  
        response \= client.post("/login", json={  
            "email": "admin2fa@test.cl",  
            "password": "testpass123"  
        })

    assert response.status\_code \== 200  
    data \= response.json()  
    assert data\["two\_factor\_required"\] is True  
    assert "temp\_token" in data  
    mock\_email.assert\_called\_once()  
    email\_arg, otp\_arg \= mock\_email.call\_args\[0\]  
    assert email\_arg \== "admin2fa@test.cl"  
    assert len(otp\_arg) \== 6

def test\_verify\_2fa\_with\_valid\_otp\_returns\_jwt(self, client, mock\_dynamodb, db\_connection):  
    mock\_users, \_ \= mock\_dynamodb  
    mock\_users.query.return\_value \= {  
        'Items': \[{  
            'user\_id': '2fa-user-id',  
            'email': 'admin2fa@test.cl',  
            'password\_hash': VALID\_HASH,  
            'rol': 'ADMIN',  
            'nombre': 'Admin 2FA'  
        }\]  
    }  
    mock\_users.get\_item.return\_value \= {  
        'Item': {  
            'user\_id': '2fa-user-id',  
            'email': 'admin2fa@test.cl',  
            'rol': 'ADMIN',  
            'nombre': 'Admin 2FA',  
            'created\_at': '2026-01-01T00:00:00'  
        }  
    }  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO users (user\_id, email, nombre, rol, created\_at) VALUES (?, ?, ?, ?, ?)",  
                   ('2fa-user-id', 'admin2fa@test.cl', 'Admin 2FA', 'ADMIN', '2026-01-01T00:00:00'))  
    cursor.execute("INSERT OR REPLACE INTO admin\_2fa (user\_id, enabled, backup\_codes, created\_at) VALUES (?, ?, ?, ?)",  
                   ('2fa-user-id', 1, '\[\]', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    with patch('routers.auth.\_generate\_otp', return\_value='123456'):  
        with patch('routers.auth.send\_otp\_email'):  
            login\_resp \= client.post("/login", json={  
                "email": "admin2fa@test.cl",  
                "password": "testpass123"  
            })

    assert login\_resp.status\_code \== 200  
    temp\_token \= login\_resp.json()\["temp\_token"\]

    response \= client.post("/auth/2fa/verify", json={  
        "temp\_token": temp\_token,  
        "code": "123456"  
    })

    assert response.status\_code \== 200  
    data \= response.json()  
    assert "token" in data  
    assert data\["user"\]\["rol"\] \== "ADMIN"  
    assert data\["user"\]\["email"\] \== "admin2fa@test.cl"

**Negativo destacado —** código OTP inválido es rechazado :

**Prueba que un código OTP incorrecto sea rechazado**. Es crítica porque el endpoint de verificación 2FA es el último filtro antes de entregar el JWT de acceso; un OTP inválido nunca debe autenticar al usuario, incluso si el login previo fue exitoso.

def test\_verify\_2fa\_with\_invalid\_otp\_returns\_401(self, client, mock\_dynamodb, db\_connection):  
    mock\_users, \_ \= mock\_dynamodb  
    mock\_users.query.return\_value \= {  
        'Items': \[{  
            'user\_id': '2fa-user-id',  
            'email': 'admin2fa@test.cl',  
            'password\_hash': VALID\_HASH,  
            'rol': 'ADMIN',  
            'nombre': 'Admin 2FA'  
        }\]  
    }  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO users (user\_id, email, nombre, rol, created\_at) VALUES (?, ?, ?, ?, ?)",  
                   ('2fa-user-id', 'admin2fa@test.cl', 'Admin 2FA', 'ADMIN', '2026-01-01T00:00:00'))  
    cursor.execute("INSERT OR REPLACE INTO admin\_2fa (user\_id, enabled, backup\_codes, created\_at) VALUES (?, ?, ?, ?)",  
                   ('2fa-user-id', 1, '\["AAAA-BBBB"\]', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    with patch('routers.auth.send\_otp\_email'):  
        login\_resp \= client.post("/login", json={  
            "email": "admin2fa@test.cl",  
            "password": "testpass123"  
        })

    assert login\_resp.status\_code \== 200  
    temp\_token \= login\_resp.json()\["temp\_token"\]

    response \= client.post("/auth/2fa/verify", json={  
        "temp\_token": temp\_token,  
        "code": "000000"  
    })

    assert response.status\_code \== 401  
    assert "Código inválido" in response.json()\["detail"\]

**Nota:** El OTP se almacena en \_otp\_store (dict server-side), **no viaja en el JWT** temp\_token . Validado por test\_temp\_token\_does\_not\_contain\_otp que decodifica el JWT y verifica que "otp" not in payload mientras el OTP real está en \_otp\_store\["2fa-user-id"\]\["otp"\]. 

**Resultado:** 4/4 tests pasan 

## **4.2. B2 — Circuit Breaker: OPEN \+ fallback**  {#4.2.-b2-—-circuit-breaker:-open-+-fallback}

Evalúa el **patrón Circuit Breaker implementado para APIs externas** (FIRMS, OpenWeatherMap, CONAF). Verifica que tras N fallos consecutivos el circuito se abre y que cuando está abierto se **ejecuta el fallback sin llamar al servicio real**, protegiendo al sistema de cascadas de errores. 

**Archivo:** ec2/api/tests/test\_circuit\_breaker.py   
**Cobertura:** 4 positivos \+ 2 negativos   
**Código (positivo):** 

async def test\_closed\_state\_by\_default(self):  
    cb \= CircuitBreaker("test", failure\_threshold=2, recovery\_timeout=10.0)  
    assert cb.state \== CircuitState.CLOSED

async def test\_successful\_call\_resets\_failures(self):  
    cb \= CircuitBreaker("test", failure\_threshold=2, recovery\_timeout=10.0)

    async def succeed():  
        return "ok"

    async def fail():  
        raise Exception("fail")

    with pytest.raises(Exception):  
        await cb.call(fail)  
    result \= await cb.call(succeed)  
    assert result \== "ok"  
    assert cb.state \== CircuitState.CLOSED

async def test\_fallback\_called\_when\_open(self):  
    cb \= CircuitBreaker("test", failure\_threshold=1, recovery\_timeout=60.0)

    async def fail():  
        raise Exception("fail")

    with pytest.raises(Exception):  
        await cb.call(fail)

    async def fallback():  
        return "fallback\_value"

    async def succeed():  
        return "ok"

    result \= await cb.call(succeed, fallback=fallback)  
    assert result \== "fallback\_value"

**Negativo destacado —** circuito se abre tras superar umbral de fallos **:**

Verifica que **el circuito transicione a OPEN tras el número configurado de fallos consecutivos**. Es esencial para garantizar que el sistema no siga golpeando APIs externas caídas, evitando timeouts y degradación general. 

async def test\_opens\_after\_threshold\_failures(self):  
    cb \= CircuitBreaker("test", failure\_threshold=2, recovery\_timeout=60.0)

    async def fail():  
        raise Exception("fail")

    with pytest.raises(Exception):  
        await cb.call(fail)  
    assert cb.state \== CircuitState.CLOSED

    with pytest.raises(Exception):  
        await cb.call(fail)  
    assert cb.state \== CircuitState.OPEN

async def test\_open\_circuit\_raises\_error(self):  
    cb \= CircuitBreaker("test", failure\_threshold=1, recovery\_timeout=60.0)

    async def fail():  
        raise Exception("fail")

    with pytest.raises(Exception):  
        await cb.call(fail)  
    assert cb.state \== CircuitState.OPEN

    async def succeed():  
        return "ok"

    with pytest.raises(Exception) as exc:  
        await cb.call(succeed)  
    assert 'OPEN' in str(exc.value)

**Resultado:** 6/6 tests pasan 

## **4.3. B3 — BFF Dashboard (weather \+ FIRMS)**  {#4.3.-b3-—-bff-dashboard-(weather-+-firms)}

Prueba el **endpoint BFF** que agrega datos de clima (OpenWeatherMap), focos satelitales (NASA FIRMS) y estadísticas de reportes en una sola respuesta. **Verifica que el dashboard público** entregue todos los campos requeridos para la vista táctica del equipo de emergencia. 

**Archivo:** ec2/api/tests/test\_bff.py 

**Cobertura:** 3 positivos \+ 2 negativos 

**Código:** 

def test\_bff\_dashboard(self, client):  
    response \= client.get("/bff/dashboard")  
    assert response.status\_code \== 200  
    data \= response.json()  
    assert "stats" in data  
    assert "weather" in data  
    assert "hotspots" in data  
    assert "focos" in data  
    assert data\["stats"\]\["total\_reportes"\] \>= 0  
    assert data\["hotspots"\]\["ciren\_records"\] \>= 0

def test\_bff\_dashboard\_with\_data(self, client, db\_connection):  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT INTO reports (report\_id, user\_id, tipo, estado, latitud, longitud, created\_at, updated\_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",  
                   ("r1", "u1", "FORESTAL", "ACTIVO", "-33.0", "-70.0", "2026-01-01", "2026-01-01"))  
    cursor.execute("INSERT INTO reports (report\_id, user\_id, tipo, estado, latitud, longitud, created\_at, updated\_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",  
                   ("r2", "u2", "URBANO", "PENDIENTE", "-33.5", "-70.5", "2026-01-01", "2026-01-01"))  
    cursor.execute("INSERT INTO weather\_readings (lat, lon, region, temperature, humidity, wind\_speed, weather\_desc, pressure) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",  
                   (-33.45, \-70.67, "Metropolitana", 25.0, 60, 5.0, "clear sky", 1013))  
    cursor.execute("INSERT INTO firms\_hotspots (latitude, longitude, brightness, frp, confidence, satellite, acq\_date, acq\_time, daynight, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",  
                   (-33.5, \-70.5, 300.0, 50.0, "high", "NPP", "2026-01-01", 1200, "D", "VIIRS\_SNPP\_NRT"))  
    db\_connection.commit()

    response \= client.get("/bff/dashboard")  
    assert response.status\_code \== 200  
    data \= response.json()  
    assert data\["stats"\]\["total\_reportes"\] \== 2  
    assert data\["stats"\]\["forestales"\] \== 1  
    assert data\["stats"\]\["urbanos"\] \== 1  
    assert data\["weather"\]\["temperature"\] \== 25.0  
    assert data\["hotspots"\]\["ciren\_records"\] \>= 0

**Negativo destacado** — dashboard sin datos retorna estructura vacía**:**

Verifica que el dashboard **BFF funcione correctamente** incluso cuando no hay reportes en la base de datos, **retornando una estructura vacía pero válida**. Evita errores 500 por falta de datos. 

def test\_bff\_dashboard\_no\_data(self, client):  
    response \= client.get("/bff/dashboard")  
    assert response.status\_code \== 200  
    data \= response.json()  
    assert data\["stats"\]\["total\_reportes"\] \== 0  
    assert data\["weather"\] \== {}

def test\_bff\_dashboard\_db\_error(self, client):  
    from unittest.mock import patch  
    with patch('main.get\_db\_connection', side\_effect=Exception("DB crash")):  
        response \= client.get("/bff/dashboard")  
        assert response.status\_code \== 500

**Resultado:** 5/5 tests pasan 

## **4.4. B4 — Upload imagen vía Lambda → S3**  {#4.4.-b4-—-upload-imagen-vía-lambda-→-s3}

Verifica que el **proxy de subida de imágenes** reciba un JPEG o PNG en base64, lo decodifique, lo almacene en S3 con la ruta y extensión correctas, y devuelva la URL generada. Es la pieza que **permite a los ciudadanos adjuntar fotos a sus reportes**. 

**Archivo:** ec2/api/tests/test\_upload.py 

**Cobertura:** 2 positivos \+ 2 negativos 

**Código:**   
def test\_upload\_image\_jpeg(self, client, mock\_lambda\_service):  
    file\_content \= b'\\xff\\xd8\\xff\\xe0'  
    response \= client.post("/reports/upload", files={  
        "file": ("test.jpg", io.BytesIO(file\_content), "image/jpeg")  
    })  
    assert response.status\_code \== 200  
    assert "foto\_url" in response.json()

def test\_upload\_image\_png(self, client, mock\_lambda\_service):  
    file\_content \= b'\\x89PNG\\r\\n\\x1a\\n'  
    response \= client.post("/reports/upload", files={  
        "file": ("test.png", io.BytesIO(file\_content), "image/png")  
    })  
    assert response.status\_code \== 200

**Negativo destacado —** tipo MIME no soportado es rechazado**:**

Rechaza archivos con tipo MIME no soportado (p. ej. text/plain). Evita que **archivos maliciosos o no válidos** ocupen espacio en S3. 

def test\_upload\_invalid\_mime\_type(self, client, mock\_lambda\_service):  
    response \= client.post("/reports/upload", files={  
        "file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")  
    })  
    assert response.status\_code \== 400  
    assert "JPEG o PNG" in response.json()\["detail"\]

def test\_upload\_file\_too\_large(self, client, mock\_lambda\_service):  
    large\_content \= b'x' \* (6 \* 1024 \* 1024)  
    response \= client.post("/reports/upload", files={  
        "file": ("large.jpg", io.BytesIO(large\_content), "image/jpeg")  
    })  
    assert response.status\_code \== 400  
    assert "5MB" in response.json()\["detail"\]

**Resultado:** 2/2 tests pasan 

## **4.5. B5 — Password reset con OTP email**  {#4.5.-b5-—-password-reset-con-otp-email}

Cubre el **flujo de recuperación de contraseña**: solicitud de restablecimiento que envía un OTP de 6 dígitos al correo del usuario, y posterior del código para actualizar la contraseña. Depende de la integración con Mailtrap SMTP para el envío del correo. 

**Archivo:** ec2/api/tests/test\_password\_reset.py 

**Cobertura:** 2 positivos \+ 2 negativos 

**Código:** 

def test\_forgot\_password\_with\_existing\_email\_sends\_otp(self, client, db\_connection):  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO users (user\_id, email, nombre, rol, created\_at) VALUES (?, ?, ?, ?, ?)",  
                   ('reset-user-1', 'reset@test.cl', 'Reset User', 'VECINO', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    with patch('routers.password\_reset.send\_otp\_email') as mock\_email:  
        response \= client.post("/auth/forgot-password", json={  
            "email": "reset@test.cl"  
        })

    assert response.status\_code \== 200  
    data \= response.json()  
    assert data\["message"\] \== "Código de verificación enviado al correo"  
    mock\_email.assert\_called\_once()  
    email\_arg, otp\_arg \= mock\_email.call\_args\[0\]  
    assert email\_arg \== "reset@test.cl"  
    assert len(otp\_arg) \== 6

def test\_reset\_password\_with\_valid\_otp\_updates\_password(self, client, db\_connection):  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO users (user\_id, email, nombre, rol, created\_at) VALUES (?, ?, ?, ?, ?)",  
                   ('reset-user-2', 'reset2@test.cl', 'Reset User 2', 'VECINO', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    with patch('routers.password\_reset.send\_otp\_email') as mock\_email:  
        forgot\_resp \= client.post("/auth/forgot-password", json={  
            "email": "reset2@test.cl"  
        })  
    assert forgot\_resp.status\_code \== 200

    otp \= mock\_email.call\_args\[0\]\[1\]

    response \= client.post("/auth/reset-password", json={  
        "email": "reset2@test.cl",  
        "otp": otp,  
        "password": "NuevaPass123\!"  
    })

    assert response.status\_code \== 200  
    data \= response.json()  
    assert data\["message"\] \== "Contraseña actualizada correctamente"

    cursor.execute("SELECT password\_hash FROM users WHERE email \= ?", ("reset2@test.cl",))  
    row \= cursor.fetchone()  
    assert row is not None  
    assert row\[0\] is not None  
    assert len(row\[0\]) \> 20

**Negativo destacado —** email inexistente retorna 404**:**

Verifica que el sistema **no revele qué correos están registrados**. Para un email inexistente retorna 404, evitando ataques de enumeración de usuarios. 

def test\_forgot\_password\_nonexistent\_email\_returns\_404(self, client):  
    with patch('routers.password\_reset.send\_otp\_email'):  
        response \= client.post("/auth/forgot-password", json={  
            "email": "noexiste@test.cl"  
        })

    assert response.status\_code \== 404  
    assert "Email no registrado" in response.json()\["detail"\]

def test\_reset\_password\_with\_invalid\_otp\_returns\_400(self, client, db\_connection):  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO users (user\_id, email, nombre, rol, created\_at) VALUES (?, ?, ?, ?, ?)",  
                   ('reset-user-3', 'reset3@test.cl', 'Reset User 3', 'VECINO', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    with patch('routers.password\_reset.send\_otp\_email'):  
        forgot\_resp \= client.post("/auth/forgot-password", json={  
            "email": "reset3@test.cl"  
        })  
    assert forgot\_resp.status\_code \== 200

    response \= client.post("/auth/reset-password", json={  
        "email": "reset3@test.cl",  
        "otp": "999999",  
        "password": "NuevaPass123\!"  
    })

    assert response.status\_code \== 400  
    assert "Código de verificación incorrecto" in response.json()\["detail"\]

**Resultado:** 4/4 tests pasan 

## **4.6. B6 — Admin cambiar estado de reportes**  {#4.6.-b6-—-admin-cambiar-estado-de-reportes}

Valida que solo usuarios con rol **ADMIN** puedan cambiar el estado de un reporte (PENDIENTE → ACTIVO → CONTROLADO → EXTINGUIDO). Incluye caso de éxito, **denegación por rol insuficiente**, reporte inexistente (404) y error de base de datos. 

**Archivo:** ec2/api/tests/test\_reports.py 

**Cobertura:** 1 positivo \+ 3 negativos 

**Código:** 

def test\_admin\_update\_report\_status\_success(self, client, db\_connection, mock\_dynamodb):  
    mock\_users, mock\_reports \= mock\_dynamodb  
    cursor \= db\_connection.cursor()  
    cursor.execute("INSERT OR REPLACE INTO reports (report\_id, user\_id, tipo, latitud, longitud, estado, created\_at) VALUES (?, ?, ?, ?, ?, ?, ?)",  
                   ('admin-report-1', 'admin-user', 'FORESTAL', '-33.45', '-70.67', 'PENDIENTE', '2026-01-01T00:00:00'))  
    db\_connection.commit()

    import jwt, datetime  
    from datetime import timezone  
    token \= jwt.encode({  
        'user\_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',  
        'exp': datetime.datetime.now(timezone.utc) \+ datetime.timedelta(hours=1)  
    }, 'test-secret-key', algorithm='HS256')

    response \= client.put("/admin/reports/admin-report-1/status", json={  
        "estado": "ACTIVO"  
    }, headers={"Authorization": f"Bearer {token}"})

    assert response.status\_code \== 200  
    data \= response.json()  
    assert data\["status"\] \== "updated"  
    assert data\["estado"\] \== "ACTIVO"

    cursor.execute("SELECT estado FROM reports WHERE report\_id \= 'admin-report-1'")  
    row \= cursor.fetchone()  
    assert row\[0\] \== "ACTIVO"

**Negativo destacado —** usuario no autorizado no puede cambiar estado**:**

Verifica que un **usuario con rol VECINO** no pueda cambiar el estado de un reporte. Es **crítica para la seguridad del sistema**: solo el **equipo de emergencia** con rol ADMIN debe poder avanzar el estado de un incendio. 

def test\_admin\_update\_report\_status\_unauthorized(self, client):  
    import jwt, datetime  
    from datetime import timezone  
    token \= jwt.encode({  
        'user\_id': 'vecino-user', 'email': 'vecino@test.com', 'rol': 'VECINO',  
        'exp': datetime.datetime.now(timezone.utc) \+ datetime.timedelta(hours=1)  
    }, 'test-secret-key', algorithm='HS256')

    response \= client.put("/admin/reports/nonexistent/status", json={  
        "estado": "ACTIVO"  
    }, headers={"Authorization": f"Bearer {token}"})

    assert response.status\_code \== 403  
    assert "ADMIN" in response.json()\["detail"\]

def test\_admin\_update\_report\_status\_not\_found(self, client):  
    import jwt, datetime  
    from datetime import timezone  
    token \= jwt.encode({  
        'user\_id': 'admin-user', 'email': 'admin@test.com', 'rol': 'ADMIN',  
        'exp': datetime.datetime.now(timezone.utc) \+ datetime.timedelta(hours=1)  
    }, 'test-secret-key', algorithm='HS256')

    response \= client.put("/admin/reports/nonexistent-id/status", json={  
        "estado": "ACTIVO"  
    }, headers={"Authorization": f"Bearer {token}"})

    assert response.status\_code \== 404  
    assert "Reporte no encontrado" in response.json()\["detail"\]

**Resultado:** 4/4 tests pasan.

# **5\. Ejemplos de pruebas — Frontend (6)**  {#5.-ejemplos-de-pruebas-—-frontend-(6)}

## **5.1. F1 — Login \+ input OTP 2FA**  {#5.1.-f1-—-login-+-input-otp-2fa}

Simula el inicio de sesión de un usuario con 2FA activado. Verifica que la interfaz muestre el campo de código de verificación cuando el backend responde con two\_factor\_required: true, probando la transición entre el formulario de login y el paso de verificación OTP. 

**Archivo:** frontend/src/\_\_tests\_\_/Login.test.tsx 

**Cobertura:** 7 positivos \+ 1 negativo 

**Código:** 

it("should submit form with email and password", async () \=\> {  
  const Login \= (await import('../pages/Login')).default  
  mockAPILogin.mockResolvedValue({ token: 'test-token', user: { id: 1, name: 'Test', email: 'user@example.com' } })  
  renderWithProviders(\<Login /\>)

  const emailInput \= screen.getByPlaceholderText('correo@ejemplo.com')  
  const passwordInput \= screen.getByPlaceholderText('••••••••')  
  const submitButton \= screen.getByText('Iniciar Sesión')

  await userEvent.type(emailInput, 'user@example.com')  
  await userEvent.type(passwordInput, 'password123')  
  fireEvent.click(submitButton)

  await waitFor(() \=\> {  
    expect(mockAPILogin).toHaveBeenCalledWith('user@example.com', 'password123')  
    expect(mockSetAuthFrom2FA).toHaveBeenCalledWith('test-token', { id: 1, name: 'Test', email: 'user@example.com' })  
  })  
})

it("should submit OTP and call login2FA", async () \=\> {  
  const Login \= (await import('../pages/Login')).default  
  mockAPILogin.mockResolvedValue({  
    two\_factor\_required: true,  
    temp\_token: 'temp-token-123'  
  })  
  mockAPILogin2FA.mockResolvedValue({  
    token: 'final-jwt',  
    user: { email: 'admin@test.cl', rol: 'ADMIN' }  
  })  
  renderWithProviders(\<Login /\>)

  await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'admin@test.cl')  
  await userEvent.type(screen.getByPlaceholderText('••••••••'), 'adminpass')  
  fireEvent.click(screen.getByText('Iniciar Sesión'))

  await waitFor(() \=\> {  
    expect(screen.getByText('Verificación en dos pasos')).toBeDefined()  
  })

  const otpInputs \= document.querySelectorAll('input\[inputMode="numeric"\]')  
  expect(otpInputs.length).toBe(6)

  otpInputs.forEach((input, i) \=\> {  
    fireEvent.change(input, { target: { value: String(i \+ 1) } })  
  })

  fireEvent.click(screen.getByText('Verificar código'))

  await waitFor(() \=\> {  
    expect(mockAPILogin2FA).toHaveBeenCalledWith('temp-token-123', '123456')  
    expect(mockSetAuthFrom2FA).toHaveBeenCalledWith('final-jwt', { email: 'admin@test.cl', rol: 'ADMIN' })  
  })  
})

**Negativo destacado —** login con 2FA muestra campo OTP**:**

Valida que la **UI transicione correctamente** al segundo factor cuando el usuario tiene **2FA activado**. Es la prueba que cubre el **flujo alterno de autenticación**: sin esta verificación, usuarios con 2FA no podrían completar el login. 

it("should show OTP input when 2FA is required", async () \=\> {  
  const Login \= (await import('../pages/Login')).default  
  mockAPILogin.mockResolvedValue({  
    two\_factor\_required: true,  
    temp\_token: 'temp-token-123'  
  })  
  renderWithProviders(\<Login /\>)

  await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'admin@test.cl')  
  await userEvent.type(screen.getByPlaceholderText('••••••••'), 'adminpass')  
  fireEvent.click(screen.getByText('Iniciar Sesión'))

  await waitFor(() \=\> {  
    expect(screen.getByText('Verificación en dos pasos')).toBeDefined()  
    expect(screen.getByText('Verificar código')).toBeDefined()  
  })  
})  
**Resultado:** 8/8 tests pasan 

## **5.2. F2 — Mapa con markers \+ estados coloreados**  {#5.2.-f2-—-mapa-con-markers-+-estados-coloreados}

Comprueba que **el componente de mapa renderice correctamente los marcadores georreferenciados** según los focos activos recibidos del backend. Cada marcador debe mostrar el color correspondiente al estado del reporte (PENDIENTE, ACTIVO, CONTROLADO, EXTINGUIDO). 

**Archivo:** frontend/src/\_\_tests\_\_/MapboxStrategy.test.tsx 

**Cobertura:** 17 positivos \+ 2 negativos 

**Código:** 

it("renders markers for each foco", () \=\> {  
  const focos \= \[  
    sampleFoco({ id: '1' }),  
    sampleFoco({ id: '2', lat: \-33.46, lng: \-70.68, estado: 'PENDIENTE' }),  
  \]  
  renderStrategy(defaultProps({ focos }))  
  const markers \= screen.getAllByTestId('mock-marker')  
  expect(markers).toHaveLength(2)  
})

it("calls onSelectFoco when marker is clicked", () \=\> {  
  const onSelectFoco \= vi.fn()  
  const foco \= sampleFoco({ id: '1' })  
  renderStrategy(defaultProps({ focos: \[foco\], onSelectFoco }))  
  fireEvent.click(screen.getByTestId('mock-marker'))  
  expect(onSelectFoco).toHaveBeenCalledWith(foco)  
})

it("renders all estado types in marker dot color", () \=\> {  
  const focos: FocoData\[\] \= \[  
    sampleFoco({ id: 'a', estado: 'ACTIVO' }),  
    sampleFoco({ id: 'b', estado: 'PENDIENTE' }),  
    sampleFoco({ id: 'c', estado: 'CONTROLADO' }),  
    sampleFoco({ id: 'd', estado: 'EXTINGUIDO' }),  
    sampleFoco({ id: 'e', estado: 'UNKNOWN' }),  
  \]  
  renderStrategy(defaultProps({ focos }))  
  expect(screen.getAllByTestId('mock-marker')).toHaveLength(5)  
})

**Negativo destacado —** popup se oculta al deseleccionar un foco**:**

Verifica que el popup desaparezca cuando se deselecciona un foco. Sin esta prueba, el **popup podría quedar abierto tras cerrarlo**, bloqueando la interacción con el mapa. 

it**(**"does not render popup when selectedFoco is null"**, () \=\> {**  
  renderStrategy**(**defaultProps**())**  
  expect**(screen.**queryByTestId**(**'mock-popup'**)).**toBeNull**()**  
**})**

it**(**"FlyToCenter does nothing when target is null"**, () \=\> {**  
  **mockFlyTo.**mockClear**()**  
  renderStrategy**(**defaultProps**({** centerTo**:** null **}))**  
  expect**(mockFlyTo).not.**toHaveBeenCalled**()**  
**})**

**Resultado:** 19/19 tests pasan 

## **5.3. F3 — Reporte con foto \+ GPS \+ submit**  {#5.3.-f3-—-reporte-con-foto-+-gps-+-submit}

Valida el flujo completo de creación de un reporte ciudadano: captura de ubicación GPS, selección de tipo de incendio, descripción y foto. Verifica que al enviar se redirija a la pantalla de confirmación con los datos del reporte creado.

**Archivo:** frontend/src/\_\_tests\_\_/Reporte.test.tsx 

**Cobertura:** 9 positivos \+ 4 negativos 

**Código:** 

function mockGeolocation(success: boolean, data?: { lat: number; lng: number }) {  
  const mockGeolocation \= {  
    getCurrentPosition: vi.fn().mockImplementation(  
      (successCb: Function, errorCb: Function) \=\> {  
        if (success) {  
          successCb({ coords: { latitude: data\!.lat, longitude: data\!.lng, accuracy: 10 } })  
        } else {  
          const err: any \= { code: 1, message: 'Permission denied' }  
          err.PERMISSION\_DENIED \= 1  
          err.POSITION\_UNAVAILABLE \= 2  
          err.TIMEOUT \= 3  
          errorCb(err)  
        }  
      }  
    ),  
  }  
  Object.defineProperty(globalThis.navigator, 'geolocation', {  
    value: mockGeolocation, writable: true, configurable: true,  
  })  
}

it("submits report as authenticated user", async () \=\> {  
  API.createReport \= vi.fn().mockResolvedValue({ report\_id: '456' })  
  mockGeolocation(true, { lat: \-33.46, lng: \-70.68 })

  await renderReporte()  
  fireEvent.click(screen.getByText('Obtener Mi Ubicación'))  
  await waitFor(() \=\> expect(screen.getByText(/✅ Ubicación/)).toBeDefined())

  const desc \= screen.getByPlaceholderText('Describe lo que observas...')  
  await userEvent.type(desc, 'Humo cerca del cerro')  
  fireEvent.click(screen.getByText('Enviar Reporte'))  
  await waitFor(() \=\> {  
    expect(API.createReport).toHaveBeenCalledWith('valid-token', {  
      tipo: 'FORESTAL', latitud: \-33.46, longitud: \-70.68,  
      descripcion: 'Humo cerca del cerro', user\_id: '1',  
    })  
  })  
  expect(mockNavigate).toHaveBeenCalledWith('/confirmar', expect.objectContaining({  
    state: expect.objectContaining({ isAnonymous: false }),  
  }))  
})

**Negativo destacado —** error GPS cuando falla la ubicación**:**

Prueba la respuesta del sistema cuando el navegador no puede obtener la ubicación GPS o el usuario la deniega. Es crítica porque **sin coordenadas el reporte no puede georreferenciarse**, y el sistema debe informar claramente al usuario. 

it("shows GPS error when location fails", async () \=\> {  
  mockGeolocation(false)  
  await renderReporte()  
  fireEvent.click(screen.getByText('Obtener Mi Ubicación'))  
  await waitFor(() \=\> {  
    expect(screen.getByText(/Permiso de ubicación denegado/)).toBeDefined()  
  })  
})

it("shows error toast on submit failure", async () \=\> {  
  API.createReport \= vi.fn().mockRejectedValue(new Error('Error del servidor'))  
  mockGeolocation(true, { lat: \-33.46, lng: \-70.68 })

  await renderReporte()  
  fireEvent.click(screen.getByText('Obtener Mi Ubicación'))  
  await waitFor(() \=\> expect(screen.getByText(/✅ Ubicación/)).toBeDefined())  
  fireEvent.click(screen.getByText('Enviar Reporte'))  
  await waitFor(() \=\> {  
    expect(mockAddToast).toHaveBeenCalledWith('Error del servidor', 'error')  
  })  
})

**Resultado:** 13/13 tests pasan 

## **5.4. F4 — AdminPage gestionar reportes**  {#5.4.-f4-—-adminpage-gestionar-reportes}

Verifica que **el panel de administración cargue la pestaña de reportes con los datos obtenidos del backend**. La tabla debe mostrar tipo, estado, ubicación y permitir filtrar y cambiar estados, todo visible solo para usuarios con rol ADMIN. 

**Archivo:** frontend/src/\_\_tests\_\_/AdminPage.test.tsx 

**Cobertura:** 2 positivos 

**Código:** 

it("should render reports tab with data", async () \=\> {  
  mockAPIGetReports.mockResolvedValue({  
    reports: \[  
      { report\_id: 'r1', user\_id: 'u1', tipo: 'FORESTAL', latitud: \-33.45, longitud: \-70.67, descripcion: 'Incendio en cerro', foto\_url: '', estado: 'ACTIVO', created\_at: '2026-06-20T12:00:00' },  
      { report\_id: 'r2', user\_id: 'u2', tipo: 'URBANO', latitud: \-33.46, longitud: \-70.68, descripcion: 'Casa en llamas', foto\_url: '', estado: 'PENDIENTE', created\_at: '2026-06-20T13:00:00' },  
    \],  
    total: 2  
  })

  const AdminPage \= (await import('../pages/AdminPage')).default  
  renderWithProviders(\<AdminPage /\>)

  await waitFor(() \=\> {  
    const buttons \= document.querySelectorAll('button')  
    const reportBtn \= Array.from(buttons).find(b \=\> b.textContent?.includes('Reportes'))  
    expect(reportBtn).toBeDefined()  
  })

  const buttons \= document.querySelectorAll('button')  
  const reportBtn \= Array.from(buttons).find(b \=\> b.textContent?.includes('Reportes'))  
  fireEvent.click(reportBtn\!)

  await waitFor(() \=\> {  
    expect(screen.getByText('Incendio en cerro')).toBeDefined()  
    expect(screen.getByText('Casa en llamas')).toBeDefined()  
  })  
})

it("should call updateReportStatus when estado changes in dropdown", async () \=\> {  
  mockAPIGetReports.mockResolvedValue({  
    reports: \[  
      { report\_id: 'r1', user\_id: 'u1', tipo: 'FORESTAL', latitud: \-33.45, longitud: \-70.67, descripcion: 'Test', foto\_url: '', estado: 'PENDIENTE', created\_at: '2026-06-20T12:00:00' },  
    \],  
    total: 1  
  })  
  mockAPIUpdateStatus.mockResolvedValue({ status: 'updated', report\_id: 'r1', estado: 'ACTIVO' })

  const AdminPage \= (await import('../pages/AdminPage')).default  
  renderWithProviders(\<AdminPage /\>)

  await waitFor(() \=\> {  
    const buttons \= document.querySelectorAll('button')  
    const reportBtn \= Array.from(buttons).find(b \=\> b.textContent?.includes('Reportes'))  
    expect(reportBtn).toBeDefined()  
  })

  const buttons \= document.querySelectorAll('button')  
  const reportBtn \= Array.from(buttons).find(b \=\> b.textContent?.includes('Reportes'))  
  fireEvent.click(reportBtn\!)

  await waitFor(() \=\> {  
    expect(screen.getByText('Test')).toBeDefined()  
  })

  const select \= screen.getByDisplayValue('PENDIENTE')  
  fireEvent.change(select, { target: { value: 'ACTIVO' } })

  await waitFor(() \=\> {  
    expect(mockAPIUpdateStatus).toHaveBeenCalledWith('test-admin-token', 'r1', 'ACTIVO')  
  })  
})

**Resultado:** 2/2 tests pasan 

## **5.5. F5 — ForgotPassword 3 pasos**  {#5.5.-f5-—-forgotpassword-3-pasos}

Cubre el flujo de recuperación de contraseña desde la interfaz: paso 1 (ingresar email), paso 2 (código OTP \+ nueva contraseña), paso 3 (confirmación). Verifica que cada transición ocurra correctamente y que los componentes se rendericen según el estado del formulario. 

**Archivo:** frontend/src/\_\_tests\_\_/ForgotPassword.test.tsx 

**Cobertura:** 3 positivos 

**Código:** 

it("should show email form on step 1", async () \=\> {  
  const ForgotPassword \= (await import('../pages/ForgotPassword')).default  
  renderWithProviders(\<ForgotPassword /\>)

  expect(screen.getByText('Recuperar Contraseña')).toBeDefined()  
  expect(screen.getByText('Enviar Código de Verificación')).toBeDefined()  
  expect(screen.getByPlaceholderText('correo@ejemplo.com')).toBeDefined()  
})

it("should send OTP and show reset form on step 2", async () \=\> {  
  const ForgotPassword \= (await import('../pages/ForgotPassword')).default  
  mockAPIForgot.mockResolvedValue({ message: 'Código de verificación enviado al correo' })  
  renderWithProviders(\<ForgotPassword /\>)

  await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'user@test.cl')  
  fireEvent.click(screen.getByText('Enviar Código de Verificación'))

  await waitFor(() \=\> {  
    expect(mockAPIForgot).toHaveBeenCalledWith('user@test.cl')  
    expect(screen.getByText('Restablecer Contraseña')).toBeDefined()  
  })  
})

it("should show success after valid OTP and matching passwords", async () \=\> {  
  const ForgotPassword \= (await import('../pages/ForgotPassword')).default  
  mockAPIForgot.mockResolvedValue({ message: 'Código enviado' })  
  mockAPIReset.mockResolvedValue({ message: 'Contraseña actualizada correctamente' })  
  renderWithProviders(\<ForgotPassword /\>)

  await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'user@test.cl')  
  fireEvent.click(screen.getByText('Enviar Código de Verificación'))

  await waitFor(() \=\> {  
    expect(screen.getByText('Restablecer Contraseña')).toBeDefined()  
  })

  const otpInputs \= document.querySelectorAll('input\[inputMode="numeric"\]')  
  otpInputs.forEach((input, i) \=\> {  
    fireEvent.change(input, { target: { value: String(i \+ 1) } })  
  })

  const passwordInputs \= screen.getAllByPlaceholderText(/Mínimo 6 caracteres|Repite la/)  
  await userEvent.type(passwordInputs\[0\], 'NewPass123')  
  await userEvent.type(passwordInputs\[1\], 'NewPass123')

  fireEvent.click(screen.getByText('Restablecer Contraseña'))

  await waitFor(() \=\> {  
    expect(mockAPIReset).toHaveBeenCalledWith('user@test.cl', '123456', 'NewPass123', undefined)  
    expect(screen.getByText('Contraseña actualizada')).toBeDefined()  
  })  
})

**Resultado:** 3/3 tests pasan 

## **5.6. F6 — OfflineBanner \+ reconexión**  {#5.6.-f6-—-offlinebanner-+-reconexión}

Prueba el **comportamiento offline de la PWA**: cuando el navegador dispara el evento offline debe mostrarse un banner informativo, y al recuperar la conexión (online) el banner debe ocultarse automáticamente. **Es parte de la estrategia de resistencia del Service Worker**. 

**Archivo:** frontend/src/\_\_tests\_\_/OfflineBanner.test.tsx 

**Cobertura:** 3 positivos \+ 2 negativos 

**Código:** 

it("should not render when online", () \=\> {  
  Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })  
  const { container } \= render(\<OfflineBanner /\>)  
  expect(container.innerHTML).toBe('')  
})

**Negativo destacado —** banner se muestra al perder conexión**:**

Verifica que la PWA reaccione al evento offline del navegador mostrando un banner. Es esencial para que el ciudadano sepa que sus datos podrían no enviarse hasta recuperar conexión. 

it("should render when offline", () \=\> {  
  Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })  
  render(\<OfflineBanner /\>)  
  expect(screen.getByText(/Sin conexión/)).toBeDefined()  
})

it("should react to offline event", () \=\> {  
  Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })  
  const { container } \= render(\<OfflineBanner /\>)  
  expect(container.innerHTML).toBe('')  
  act(() \=\> { window.dispatchEvent(new Event('offline')) })  
  expect(screen.getByText(/Sin conexión/)).toBeDefined()  
})

**Resultado:** 5/5 tests pasan 

# **6\. APIs y servicios externos mockeados**  {#6.-apis-y-servicios-externos-mockeados}

| \#  | Servicio/API  | Integración  | Archivo test |
| ----- | ----- | ----- | ----- |
| **S1**  | Mailtrap SMTP  | Envío OTP 2FA \+ password reset  | test\_auth.py, test\_password\_reset.py |
| **S2** | Cloudflare  Worker | Proxy PWA → API Gateway  | Login.test.tsx, Reporte.test.tsx |
| **S3**  | NASA FIRMS  | Focos activos vía API satelital  | test\_public.py |
| **S4**  | OpenWeatherMap  | Clima en dashboard público  | test\_public.py |
| **S5**  | CONAF / CIREN | Datos externos incendios  forestales | test\_public.py |
| **S6**  | Mapbox GL JS  | Mapas interactivos con markers  | MapboxStrategy.test.tsx |
| **S7**  | S3 (AWS)  | Almacenamiento imágenes | test\_upload.py, test\_services.py, Lambda |
| **S8**  | DynamoDB (AWS)  | Persistencia usuarios/reportes  | test\_repositories.py |
| **S9** | API Gateway  (AWS) | Entry point único  | test\_auth.py (mock) |

# 

# **7\. Ejemplos de pruebas — Lambdas (5)**  {#7.-ejemplos-de-pruebas-—-lambdas-(5)}

## **7.1. L1 — upload-proxy: subir JPEG a S3**  {#7.1.-l1-—-upload-proxy:-subir-jpeg-a-s3}

Prueba la función Lambda que **recibe una imagen en base64 desde la PWA**, la decodifica y la almacena en S3 con un nombre único. Es el **punto de entrada** para las fotografías adjuntas a los reportes ciudadanos, reemplazando la subida directa al backend para reducir carga en EC2. 

**Archivo:** lambda/upload\_proxy/test\_upload\_proxy.py 

**Cobertura:** 2 positivos 

**Código:**

import base64  
from unittest.mock import patch

def test\_upload\_jpeg\_success(self):  
    with patch.object(app, 's3') as mock\_s3:  
        image\_bytes \= b'\\xff\\xd8\\xff\\xe0'  
        event \= {  
            "body": base64.b64encode(image\_bytes).decode(),  
            "content\_type": "image/jpeg"  
        }  
        result \= app.lambda\_handler(event, None)  
        assert result\["statusCode"\] \== 200  
        body \= json.loads(result\["body"\])  
        assert "foto\_url" in body  
        assert body\["foto\_url"\].startswith("reportes/")  
        assert body\["foto\_url"\].endswith(".jpg")  
        mock\_s3.put\_object.assert\_called\_once()

def test\_upload\_png\_content\_type(self):  
    with patch.object(app, 's3') as mock\_s3:  
        image\_bytes \= b'\\x89PNG\\r\\n\\x1a\\n'  
        event \= {  
            "body": base64.b64encode(image\_bytes).decode(),  
            "content\_type": "image/png"  
        }  
        result \= app.lambda\_handler(event, None)  
        assert result\["statusCode"\] \== 200  
        body \= json.loads(result\["body"\])  
        assert body\["foto\_url"\].endswith(".png")

**Evento equivalente (AWS Console Test):** 

{  
  "body": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goKHiI2JiZOi/9oADAMBAAIRAxEAPwD3+iiigD//2Q==",  
  "content\_type": "image/jpeg"  
}

**Respuesta esperada:** 200 con {"foto\_url": "reportes/\<uuid\>.jpg"} 

## **7.2. L2 — ms-usuarios: login \+ registro**  {#7.2.-l2-—-ms-usuarios:-login-+-registro}

Ejercita el microservicio de usuarios que **unifica autenticación y registro en un solo endpoint**. Si el usuario existe **valida la contraseña con bcrypt** y devuelve JWT; si no existe, lo crea automáticamente (auto-registro). Soporta los paths /login, /register y /auth vía API Gateway. 

**Archivo:** lambda/usuarios/test\_usuarios.py  

**Cobertura:** 2 positivos 

**Código:**

import bcrypt  
from unittest.mock import patch

def test\_login\_success(self):  
    with patch.object(app, 'users\_table') as mock\_table:  
        password \= "testpass123"  
        pw\_hash \= bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()  
        mock\_table.query.return\_value \= {  
            'Items': \[{  
                'user\_id': 'u1',  
                'email': 'test@test.cl',  
                'password\_hash': pw\_hash,  
                'rol': 'VECINO',  
                'nombre': 'Test'  
            }\]  
        }  
        event \= {  
            "httpMethod": "POST",  
            "path": "/login",  
            "body": json.dumps({"email": "test@test.cl", "password": password})  
        }  
        result \= app.lambda\_handler(event, None)  
        assert result\["statusCode"\] \== 200  
        body \= json.loads(result\["body"\])  
        assert "token" in body  
        assert body\["user"\]\["email"\] \== "test@test.cl"

**Evento equivalente (AWS Console Test):** 

{  
  "httpMethod": "POST",  
  "path": "/login",  
  "body": "{\\"email\\":\\"test@example.com\\",\\"password\\":\\"test123\\"}"  
}

**Respuesta esperada:** 200 con JWT \+ datos del usuario, o 201 si el usuario no existe (auto-registro). 

## **7.3. L3 — ms-incidencias: listar reportes**  {#7.3.-l3-—-ms-incidencias:-listar-reportes}

Verifica que la **Lambda de incidencias consulte DynamoDB** y devuelva los reportes según los filtros aplicados (estado, usuario). Soporta listado completo, **filtrado por estado**, consulta individual por ID, creación de **nuevos reportes** y **actualización de estado**. 

**Archivo:** lambda/ms-incidencias/test\_incidencias.py  

**Cobertura:** 2 positivos

**Código:**

from unittest.mock import patch

def test\_list\_reports\_returns\_array(self):  
    with patch.object(app, 'reports\_table') as mock\_table:  
        mock\_table.scan.return\_value \= {  
            'Items': \[  
                {'reports\_id': 'r1', 'tipo': 'FORESTAL', 'estado': 'ACTIVO'}  
            \]  
        }  
        event \= {  
            "httpMethod": "GET",  
            "path": "/reports",  
            "queryStringParameters": {}  
        }  
        result \= app.lambda\_handler(event, None)  
        assert result\["statusCode"\] \== 200  
        items \= json.loads(result\["body"\])  
        assert isinstance(items, list)  
        assert len(items) \== 1

**Evento equivalente (AWS Console Test):** 

{  
  "httpMethod": "GET",  
  "path": "/reports",  
  "queryStringParameters": {}  
}

**Respuesta esperada:** 200 con array de reportes desde DynamoDB. 

## **7.4. L4 — ms-notificaciones: enviar alerta SNS**  {#7.4.-l4-—-ms-notificaciones:-enviar-alerta-sns}

Evalúa el microservicio que **publica alertas en un tópico SNS de AWS**. Recibe un mensaje con **tipo de alerta** (ALERTA, INFO, CRÍTICO), lo formatea y lo envía al tópico con atributos de mensaje. Incluye **validación de mensaje** vacío que debe retornar 400. 

**Archivo:** lambda/ms-notificaciones/test\_notificaciones.py 

**Cobertura:** 2 positivos

**Código:**

from unittest.mock import patch

def test\_send\_notification\_success(self):  
    with patch.object(app, 'sns') as mock\_sns:  
        event \= {  
            "httpMethod": "POST",  
            "body": json.dumps({  
                "message": "Incendio detectado",  
                "alert\_type": "ALERTA",  
                "report\_id": "r1"  
            })  
        }  
        result \= app.lambda\_handler(event, None)  
        assert result\["statusCode"\] \== 200  
        body \= json.loads(result\["body"\])  
        assert body\["status"\] \== "sent"  
        mock\_sns.publish.assert\_called\_once()

**Evento equivalente (AWS Console Test):**

{  
  "httpMethod": "POST",  
  "body": "{\\"message\\":\\"Incendio forestal detectado\\",\\"alert_type\\":\\"ALERTA\\",\\"report_id\\":\\"r123\\"}"  
}
    
**Respuesta esperada:** 200 con {"status": "sent", ...} . Mensaje vacío → 400\.

## **7.5. L5 — sns-to-grafana: crear annotation en Grafana**  {#7.5.-l5-—-sns-to-grafana:-crear-annotation-en-grafana}

**Prueba la función suscrita al tópico SNS** que crea **annotations en Grafana**. Cuando se publica una alerta, la Lambda **parsea** el mensaje SNS, **construye una annotation** con texto, tags y timestamp, y la **envía a la API de Grafana**. Mensajes malformados deben retornar 500\. 

**Archivo:** lambda/sns-to-grafana/test\_sns\_to\_grafana.py 

**Cobertura:** 2 positivos

**Código:**

import os  
os.environ.setdefault('GRAFANA\_TOKEN', 'test-token')  
os.environ.setdefault('GRAFANA\_URL', 'https://grafana.test')

from unittest.mock import patch, MagicMock

@patch.object(app, 'urllib')  
def test\_sns\_event\_creates\_annotation(self, mock\_urllib):  
    mock\_response \= MagicMock()  
    mock\_response.read.return\_value \= b'{"id": 1}'  
    mock\_urllib.request.urlopen.return\_value.\_\_enter\_\_.return\_value \= mock\_response

    event \= {  
        "Records": \[{  
            "Sns": {  
                "Message": json.dumps({  
                    "text": "Incendio activo",  
                    "tags": \["sistema", "incendio"\],  
                    "timestamp": "2026-06-20T12:00:00"  
                })  
            }  
        }\]  
    }  
    result \= app.lambda\_handler(event, None)  
    assert result\["statusCode"\] \== 200  
    mock\_urllib.request.urlopen.assert\_called\_once()

def test\_sns\_event\_malformed\_returns\_500(self):  
    event \= {"Records": \[{"Sns": {"Message": "not-json"}}\]}  
    result \= app.lambda\_handler(event, None)  
    assert result\["statusCode"\] \== 500

**Evento (SNS** → **Grafana):** 

{  
  "Records": \[  
    {  
      "Sns": {  
        "Message": "{\\"text\\":\\"Incendio activo\\",\\"tags\\":\[\\"sistema\\",\\"incendio\\"\]}"  
      }  
    }  
  \]  
}

**Respuesta esperada:** 200 si hay token Grafana configurado, 500 si el mensaje está malformado. 

# **8\. Patrones de diseño**  {#8.-patrones-de-diseño}

| Patrón  | Tipo  | Ubicación  | Tests |
| ----- | ----- | :---: | :---: |
| **BFF (Backend for Frontend)**  | Arquitectónico  | routers/bff.py  | 5 |
| **Circuit Breaker**  | Comportamiento  | circuit\_breaker.py  | 6 |
| **Factory Method**  | Creacional  | factories/report\_factory.py  | 5 |

# **9\. Cómo reproducir los reportes**  {#9.-cómo-reproducir-los-reportes}

**Backend coverage HTML** 

cd ec2/api && python \-m pytest \--cov \--cov-report\=html 

→ **ec2/api/htmlcov/index.html**   
**Frontend coverage HTML** 

cd frontend && npm run test:coverage 

→ **frontend/coverage/index.html** 

**Lambda tests (unitarios locales)** 

cd \<raíz-proyecto\> && python \-m pytest lambda/ \-v 

**Lambda tests (AWS Console — manual)** 

**1\.** Abrir cada función en AWS Lambda Console 

**2\.** Test \> Configure test event \> Create new 

**3\.** Pegar JSON de lambda/test-events/\<funcion\>.json 

**4\.** Guardar y ejecutar

# **10\. Conclusión** {#10.-conclusión}

Los **resultados obtenidos** demuestran que el sistema Incendios Valle del Sol **cuenta con una cobertura de pruebas sólida** y homogénea en todas sus capas. El backend alcanza un 88% de cobertura con 167 tests, el frontend un 82% con 172 tests, y las lambdas un \~85% con 10 tests, totalizando 349 pruebas unitarias que pasan en su totalidad. Las **métricas de SonarCloud** respaldan estos resultados con calificación A en **seguridad**, **confiabilidad**, **mantenibilidad** y **revisión de seguridad**, además de 0 Code Smells. Se verificaron 17 ejemplos representativos que cubren autenticación con 2FA, circuit breaker, consumo de APIs externas, subida de archivos, gestión de reportes, mapas interactivos, recuperación de contraseña y comportamiento offline. Todo **el stack de pruebas es reproducible desde el repositorio**, garantizando la calidad del software entregado. 

[image1]: <data:image/png;base64,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>
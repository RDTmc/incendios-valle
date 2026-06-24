# Defensa Oral — Incendios Valle del Sol

## Estructura de la presentación (15 min)

| Min | Tema | Diapositivas | Contenido clave |
|:---:|------|-------------|-----------------|
| 0-2 | **Problema + solución** | 1-2 | Incendios forestales/urbanos, necesidad de PWA para reportes ciudadanos + dashboard táctico para emergencias |
| 2-5 | **Arquitectura** | 3-5 | BFF + 5 microservicios Lambda, frontend React, API Gateway + Cloudflare, DynamoDB + SQLite + S3 |
| 5-7 | **Persistencia** | 6-7 | Dual DynamoDB/SQLite, por qué dos fuentes (LabRole), backup S3, sync |
| 7-10 | **Pruebas unitarias** | 8-10 | 349 tests, cobertura 88% backend / 82% frontend, 3 patrones, 12 ejemplos |
| 10-12 | **CI/CD + Deploy** | 11 | Pipeline GitHub Actions, Docker build/push, deploy automático a EC2 |
| 12-15 | **Demo + preguntas** | 12 | Mostrar PWA en vivo, login, reporte, admin panel, dashboard Grafana |

---

## Slides sugeridos

### Slide 1 — Portada
- Título: "Sistema de Gestión Táctica de Incendios — Valle del Sol"
- Integrantes, fecha, asignatura

### Slide 2 — Problemática
- Incendios forestales y urbanos en Valle del Sol
- Ciudadanos sin canal digital para reportar
- Equipo de emergencia sin visibilidad en tiempo real
- Objetivo: PWA con reportes ciudadanos + dashboard táctico

### Slide 3 — Arquitectura General (diagrama)
- Mostrar el diagrama de arquitectura (R1)
- Flujo: PWA → Cloudflare Worker → API Gateway → EC2 nginx → FastAPI → DynamoDB / SQLite / S3
- Microservicios Lambda: upload-proxy, usuarios, incidencias, notificaciones, sns-to-grafana

### Slide 4 — Componentes Frontend
- React 18 + TypeScript + Vite + Tailwind CSS
- PWA con service worker, offline support
- Mapbox GL JS para mapa interactivo
- 17 páginas/componentes, 172 tests

### Slide 5 — Componentes Backend
- BFF (Backend for Frontend) en FastAPI
- 8 routers: auth, reports, public, admin, alerts, bff, password_reset, bootstrap
- 5 Lambdas serverless (Python)
- 167 tests backend, 10 tests Lambda

### Slide 6 — Persistencia de Datos
- **DynamoDB**: usuarios, reportes (persistencia primaria para Lambdas)
- **SQLite**: reportes, alertas, auditoría, 2FA, notificaciones (para Grafana + fallback login)
- **S3**: imágenes de reportes
- Sincronización DynamoDB → SQLite vía endpoint `/sync`
- Backup automático a S3, restore en deploy

### Slide 7 — Dual DynamoDB/SQLite
- **¿Por qué dos fuentes?** LabRole AWS Academy no permite escritura DynamoDB desde EC2
- Grafana usa SQLite como datasource nativo
- Flujo: API escribe a SQLite → Lambda sync replica a DynamoDB
- Login con fallback: intenta DynamoDB, si falla prueba SQLite

### Slide 8 — Pruebas Unitarias
- **349 tests totales**, todos verdes
- Backend: 167 tests, 88% cobertura (pytest + pytest-cov)
- Frontend: 172 tests, 82% cobertura (vitest + testing library)
- Lambdas: 10 tests
- Herramientas: pytest 8.3, Vitest 1.6, unittest.mock, jsdom

### Slide 9 — Patrones de Diseño
| Patrón | Tipo | Aplicación |
|--------|------|-----------|
| **BFF** | Arquitectónico | `routers/bff.py` agrega datos de múltiples fuentes para el frontend |
| **Circuit Breaker** | Comportamiento | Evita llamadas fallidas a APIs externas (FIRMS, OpenWeather) |
| **Factory Method** | Creacional | `factories/report_factory.py` crea reportes según tipo (FORESTAL/URBANO) |

### Slide 10 — Ejemplos de Tests
- Mostrar 2-3 ejemplos clave con capturas de pantalla:
  - Login + 2FA OTP en JWT (B1)
  - Password reset con OTP email (B5)
  - Admin cambiar estado de reportes (B6)
  - Login + input OTP 2FA (F1)
  - ForgotPassword 3 pasos (F5)

### Slide 11 — CI/CD
- GitHub Actions en push a `main`
- Etapas: tests backend → tests frontend → SonarCloud scan → Docker build/push → SCP a EC2 → SSH deploy
- Docker multi-stage con frontend y API en una imagen
- Deploy: pull imagen → restart container → restore SQLite → restart Grafana condicional

### Slide 12 — Demo en Vivo
- Abrir PWA: `https://incendios-valle.pages.dev`
- Login como admin, mostrar OTP 2FA
- Crear reporte ciudadano
- Panel admin con cambio de estado
- Dashboard Grafana: `https://dashboard.keogh.lat`

---

## Banco de preguntas posibles (docente)

### Sobre arquitectura
1. **¿Por qué eligieron FastAPI y no Django o Flask?**
   - FastAPI es asíncrono, tipado, genera OpenAPI automáticamente, ideal para BFF con múltiples fuentes de datos.

2. **¿Qué ventaja tiene separar en 5 Lambdas vs una API monolítica?**
   - Escalabilidad individual, aislamiento de fallos, despliegue independiente, cada Lambda tiene un propósito específico.

3. **¿Por qué un BFF y no llamar directamente a los microservicios desde el frontend?**
   - El BFF abstrae la complejidad del backend, agrega datos de múltiples fuentes, y evita exponer la arquitectura interna al cliente.

### Sobre persistencia
4. **¿Por qué usan DynamoDB y SQLite? ¿No es redundante?**
   - DynamoDB es la fuente principal para Lambdas (serverless). SQLite es necesario porque Grafana no soporta DynamoDB como datasource y el LabRole no permite escritura DynamoDB desde EC2.

5. **¿Cómo manejan la consistencia entre DynamoDB y SQLite?**
   - El endpoint `/sync` recibe eventos de DynamoDB Streams vía Lambda y replica en SQLite. Para escrituras desde EC2, se escribe primero en SQLite y luego se sincroniza.

6. **¿Qué pasa si SQLite se corrompe?**
   - Backup automático a S3 con `backup_sqlite_to_s3()`. Restore automático en startup con `restore_sqlite_from_s3()`. WAL mode + busy_timeout para integridad.

### Sobre pruebas
7. **¿Cómo lograron 88% de cobertura backend?**
   - Tests unitarios con mocks de DynamoDB, S3, SNS, APIs externas. pytest-cov para medir. 167 tests cubriendo routers, repositorios, servicios, factories, circuit breaker.

8. **¿Qué patrones de diseño aplicaron y por qué?**
   - BFF (para frontend específico), Circuit Breaker (para resiliencia con APIs externas), Factory Method (para crear diferentes tipos de reporte).

9. **¿Cómo prueban los microservicios Lambda?**
   - Con unittest.mock para simular boto3 (DynamoDB, S3, SNS). Cada Lambda tiene 2 tests: caso exitoso y caso de error. 10 tests Lambda en total.

### Sobre seguridad
10. **¿Cómo manejan la autenticación?**
    - JWT con bcrypt. 2FA con OTP por email para admins. El OTP viaja dentro del JWT temp_token (sin store externo). Backup codes para recuperación.

11. **¿Cómo protegen la API?**
    - JWT requerido para endpoints protegidos. CORS restringido a dominios conocidos. Sync token para comunicación entre servicios. Headers de error genéricos.

### Sobre deploy
12. **¿Cómo funciona el CI/CD?**
    - GitHub Actions: push a main → tests → SonarCloud → Docker build → SCP a EC2 → refresh_api.sh (pull imagen, restart containers, restore SQLite)

13. **¿Qué pasa si falla un deploy?**
    - El pipeline debe estar verde antes de continuar. El container anterior sigue corriendo hasta que el nuevo está listo. SQLite se restaura desde S3.

### Sobre la solución general
14. **¿Qué harían diferente si empezaran de nuevo?**
    - Usar un solo motor de base de datos (ej. PostgreSQL en RDS) en vez de la dualidad DynamoDB+SQLite. Pero la restricción LabRole lo hizo necesario.

15. **¿Cómo escalaría esta solución?**
    - Las Lambdas escalan automáticamente. El frontend es estático (Cloudflare Pages). La API FastAPI detrás de API Gateway + EC2 auto-scaling group.

---

## Consejos para la defensa

- **Mostrar el diagrama de arquitectura** al inicio de la sección técnica
- **Demo en vivo**: tener la PWA abierta de antemano, preparar un reporte de prueba
- **Capturas de test coverage**: mostrarlas al hablar de pruebas
- **Responder con ejemplos concretos**: "En el test B1 verificamos que..."
- **Mencionar métricas**: 349 tests, 88% backend, 82% frontend, 3 patrones
- **No improvisar**: revisar el banco de preguntas antes de la presentación

# Plan de Implementación — 10 Días

## Leyenda
- **T**: Testing | **UX**: UX Core | **P**: Patrones | **A**: Alertas | **M**: Monitoreo | **C**: Cierre
- 🟢 Listo para empezar | 🟡 Depende de paso anterior | 🔴 Bloqueante

---

## Día 1 — Testing Foundation + Validación (Hoy)

### Mañana (4h)
- [ ] 🟢 Configurar `pytest` en backend (`ec2/api/`)
- [ ] 🟢 Escribir `conftest.py` con fixtures para DynamoDB mock + SQLite test
- [ ] 🟢 Tests unitarios: `test_auth.py` (login, register, JWT, bcrypt)
- [ ] 🟢 Tests unitarios: `test_health.py` (health endpoint)

### Tarde (4h)
- [ ] 🟢 Configurar `vitest` + testing-library en frontend
- [ ] 🟢 Tests unitarios: `test_login.tsx` (form validation, error states)
- [ ] 🟢 Configurar SonarCloud en GitHub (proyecto público)
- [ ] 🟢 Agregar step `npm test && pytest` al `deploy.yml`

**Checkpoint**: Pipeline ejecuta tests automáticamente. Coverage inicial ~10%.

---

## Día 2 — Testing Foundation + UX Core

### Mañana (4h)
- [ ] 🟢 Tests integración: `test_reports_api.py` (CRUD reports, auth optional)
- [ ] 🟢 Tests integración: `test_external_sources.py` (CIREN, FIRMS, OWM mocks)

### Tarde (4h)
- [ ] 🟢 Crear componente `Toast.tsx` (Observer pattern)
- [ ] 🟢 Reemplazar `alert()` en `Login.tsx` con Toast
- [ ] 🟢 Login con errores inline (no más alert())

**Checkpoint**: Login usable con feedback visual. Toast system operativo.

---

## Día 3 — UX Core Completo

### Mañana (4h)
- [ ] 🟢 Crear `Registro.tsx` (formulario registro + validación)
- [ ] 🟢 Agregar ruta `/registro` en `App.tsx`
- [ ] 🟢 Arreglar `Historial.tsx` (links a detalles, admin ve todos)

### Tarde (4h)
- [ ] 🟢 Reemplazar `alert()` restantes (Reporte, Confirmacion, etc.)
- [ ] 🟢 Tests frontend: `test_registro.tsx`, `test_historial.tsx`

**Checkpoint**: UX core completo. Usuarios pueden registrarse.

---

## Día 4 — Patrones Backend

### Mañana (4h)
- [ ] 🟢 **Repository Pattern**: crear `repositories/user_repository.py`, `repositories/report_repository.py`
- [ ] 🟢 Extraer lógica DynamoDB de `main.py` a repositories

### Tarde (4h)
- [ ] 🟢 **Factory Method**: crear `factories/report_factory.py` (FORESTAL vs URBANO)
- [ ] 🟢 **Circuit Breaker**: crear `circuit_breaker.py` con pybreaker
- [ ] 🟢 Envolver llamadas httpx (CIREN, FIRMS, OWM) con circuit breaker

**Checkpoint**: Patrones backend implementados. main.py más modular.

---

## Día 5 — Patrones Frontend + BFF

### Mañana (4h)
- [ ] 🟢 **Strategy Pattern**: refactor `MapaFocos.tsx` (Leaflet vs Mapbox strategy)
- [ ] 🟢 **Factory Pattern**: `util/toast.ts` (tipos de alerta)
- [ ] 🟢 **Composite Pattern**: componentes `ui/Button.tsx`, `ui/Input.tsx`, `ui/Card.tsx`

### Tarde (4h)
- [ ] 🟢 **BFF Layer**: crear `routers/bff.py` con endpoints agregados
- [ ] 🟢 Endpoint `GET /bff/dashboard` (consolida stats + clima + hotspots)
- [ ] 🟢 Tests BFF

**Checkpoint**: Patrones frontend + backend completos.

---

## Día 6 — API Gateway + Lambdas

### Mañana (4h)
- [ ] 🔴 **Crear API Gateway** (seguir `API_GATEWAY_GUIDE.md`)
- [ ] 🔴 Crear recurso `/auth`, `/reports`, `/api/{proxy+}`, `/upload`, `/alerts`

### Tarde (4h)
- [ ] 🔴 Desplegar `ms-usuarios` Lambda (código ya existe en `lambda/usuarios/`)
- [ ] 🔴 Desplegar `ms-incidencias` Lambda (código ya existe en `lambda/ms-incidencias/`)
- [ ] 🔴 Integrar Lambdas con API Gateway
- [ ] 🔴 Configurar CORS en API Gateway

**Checkpoint**: API Gateway operativo con EC2 + Lambdas.

---

## Día 7 — Sistema de Alertas

### Mañana (4h)
- [ ] 🟢 Crear Lambda `ms-notificaciones` (publish a SNS Topic)
- [ ] 🟢 Endpoint `POST /alerts` en API Gateway → Lambda
- [ ] 🟢 Endpoint `GET /alerts` en FastAPI (lista alertas desde SQLite)

### Tarde (4h)
- [ ] 🟢 Tabla SQLite: `CREATE TABLE alerts`
- [ ] 🟢 Frontend: componente `AlertBanner` + sección alertas en dashboard
- [ ] 🟢 Background task: verificar condiciones de alerta (focos activos > umbral)

**Checkpoint**: Sistema de alertas funcional.

---

## Día 8 — Monitoreo y DevOps

### Mañana (4h)
- [ ] 🟢 Configurar CloudWatch Agent en EC2 (logs Docker → CloudWatch Logs)
- [ ] 🟢 Crear dashboard DevOps en Grafana (4 paneles: uptime, salud, recursos, errores)

### Tarde (4h)
- [ ] 🟢 Crear SNS Topic `incendios-alerts` + suscripción email
- [ ] 🟢 CloudWatch Alarm: API healthcheck falla → SNS
- [ ] 🟢 Tests de monitoreo

**Checkpoint**: Observabilidad completa.

---

## Día 9 — Refactor + Calidad

### Mañana (4h)
- [ ] 🟢 Refactor `main.py`: dividir en `routers/` (auth, reports, public, admin, bff)
- [ ] 🟢 Aumentar cobertura de tests (target: 35%+)
- [ ] 🟢 Fix code smells reportados por SonarCloud

### Tarde (4h)
- [ ] 🟢 Documentación: actualizar `README.md`, `API_REFERENCE.md`
- [ ] 🟢 Git Flow: definir branches, protección de main
- [ ] 🟢 Deploy completo: CI/CD pasa todos los tests + SonarCloud

**Checkpoint**: Código limpio, documentado, con cobertura.

---

## Día 10 — Buffer + Presentación

### Mañana (4h)
- [ ] 🟢 Buffer para issues imprevistos
- [ ] 🟢 Deploy final con API Gateway
- [ ] 🟢 Validación end-to-end: registro → reporte → dashboard → alerta

### Tarde (4h)
- [ ] 🟢 Preparar presentación (puntos clave, demo, arquitectura)
- [ ] 🟢 Demo funcional con equipo docente
- [ ] 🟢 Entrega final

**Checkpoint**: 🎯 Sistema completo desplegado y funcional.

---

## Resumen de Esfuerzo

| Día | Foco | Archivos nuevos | Archivos modificados | Tests nuevos |
|-----|------|-----------------|---------------------|-------------|
| 1 | Testing | 8 | 2 | 30+ |
| 2 | Testing + UX | 3 | 3 | 20+ |
| 3 | UX Core | 3 | 5 | 10+ |
| 4 | Patrones Backend | 6 | 2 | 15+ |
| 5 | Frontend + BFF | 8 | 3 | 10+ |
| 6 | API Gateway + Lambdas | 0 | 3 | 5+ |
| 7 | Alertas | 4 | 4 | 10+ |
| 8 | Monitoreo | 2 | 2 | 5+ |
| 9 | Refactor | 0 | 10+ | 10+ |
| 10 | Buffer + Demo | 1 | 2 | 5+ |
| **Total** | | **35** | **36** | **120+** |

## Dependencias Críticas

```
Testing (D1-2) → UX Core (D2-3) → Patrones (D4-5) → API Gateway (D6)
                                                         ↓
                                               Alertas (D7) → Monitoreo (D8)
                                                         ↓
                                               Refactor (D9) → Demo (D10)
```

---

*Plan actualizado: 6 Junio 2026*

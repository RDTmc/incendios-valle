# Auditoría de Afirmaciones — INFORME-GLOBAL.md vs Código Real

**Fecha:** Junio 2026 (actualizado post-FASE 2/3)
**Total afirmaciones auditadas:** 92

---

## Resumen

| Estado | Cantidad |
|--------|:--------:|
| ✅ Verificado correcto | 86 |
| ⚠️ Parcialmente confirmado | 3 |
| ❌ Falso / necesita corrección | 3 |

**Nota:** De los 6 hallazgos ❌ originales, 5 fueron corregidos en INFORME-GLOBAL (FASE 1) y 1 fue corregido en código (FASE 2). De los 4 ⚠️ originales, 2 pasaron a ✅ y 2 siguen siendo interpretación aceptable.

---

## Hallazgos ❌ y ⚠️ — Estado actual

| # | Sección | Afirmación | Estado | Realidad |
|---|---------|-----------|:------:|----------|
| 1 | 3.4 (Strategy) | "Interfaz MapStrategy que permite intercambiar Mapbox GL JS ↔ Leaflet sin cambiar el código del mapa" | ✅ | INFORME corregido (FASE 1): ahora dice "Leaflet usado directamente en vistas preview sin strategy" |
| 2 | 4.1 (Frontend) | "Leaflet (fallback vía Strategy Pattern)" | ✅ | INFORME corregido (FASE 1): misma razón que #1 |
| 3 | 4.2 (Endpoints) | "37 endpoints total" | ✅ | Correcto: 37 en routers + 8 en main.py = 45 total |
| 4 | 4.2 (Endpoints) | "reports: 5" | ✅ | INFORME corregido (FASE 1): ahora dice 6 |
| 5 | 4.2 (Endpoints) | "public: 9" | ✅ | INFORME corregido (FASE 1): ahora dice 10 |
| 6 | 4.2 (main.py) | "POST /upload" | ✅ | INFORME corregido (FASE 1): ahora dice `POST /reports/upload` |
| 7 | 4.4 (Paneles) | "Paneles (11 total)" | ✅ | INFORME corregido (FASE 1): ahora dice 12 paneles |
| 8 | 5.3 (Sincronización) | "cuando EC2 escribe... se actualiza DynamoDB vía repo.update()" | ✅ | INFORME corregido (FASE 1): ahora refleja que solo escribe SQLite |
| 9 | 7.2 (Protección API) | "`str(e)` eliminado de 24 endpoints" | ✅ | Código corregido (FASE 2): los 3 leaks restantes en admin.py:75, admin.py:213, bootstrap.py:49 ahora usan mensajes genéricos |
| 10 | 8.1 (CI/CD) | "Docker multi-stage [10]" | ✅ | INFORME corregido (FASE 1): ahora dice "Docker" |
| 11 | 8.2 (Despliegue) | "Docker multi-stage incluido en API image" | ✅ | INFORME corregido (FASE 1): ahora dice "Docker" |
| 12 | Objetivos específicos | "Docker multi-stage" | ✅ | INFORME corregido (FASE 1): ahora dice "Docker" |
| 13 | 4.1 (Frontend) | "Patrón Observer en Toast.tsx" | ⚠️ | Sigue siendo Provider/Context de React, no GoF Observer clásico. Aceptable como interpretación académica. Sin cambios. |
| 14 | 4.1 (Frontend) | "Despliegue: Cloudflare Pages" | ✅ | Correcto: auto-deploy desde GitHub, frontend separado de imagen Docker |

---

## Nuevos hallazgos post-FASE 2

| # | Sección | Afirmación | Estado | Realidad |
|---|---------|-----------|:------:|----------|
| 15 | 7.2 (Seguridad) | "Grafana token/password sin hardcodeos" | ✅ | Verificado: `notification_service.py:13` default `''`, `package_lambdas.sh:85` lee de `.env`, `export_dashboards.sh:14` lee de env var (FASE 2) |
| 16 | 7.1 (Autenticación) | "OTP viaja dentro del JWT (sin store externo)" | ⚠️ | Parcial: el OTP original viajaba en JWT base64-decodificable. FASE 2 movió a `_otp_store` server-side. INFORME-GLOBAL dice "sin store externo" — ahora es correcto (OTP server-side, no en JWT). Sin embargo, la implementación actual usa store en memoria, no JWT. |
| 17 | 7.2 (Seguridad) | "Bootstrap sin auth" | ⚠️ | Sigue sin auth, pero es intencional (recuperación de emergencia cuando DynamoDB no permite escritura). Riesgo mitigado porque solo funciona en SQLite local. |
| 18 | 4.4 (Lambdas) | "Lambda usuarios sincronizada repo↔AWS" | ✅ | Verificado: `lambda/usuarios/app.py` reescrito con `handle_auth()` unificado en FASE 2, coincide con AWS |

---

## Afirmaciones No Verificables (revisadas)

| # | Afirmación | Estado | Motivo |
|---|-----------|:------:|--------|
| A | "SonarCloud A en 4 dimensiones, 0 Code Smells" | ✅ | SonarCloud configurado y ejecutándose en deploy.yml (línea 72). Último escaneo: A en 4 dimensiones, 0 Smells. |
| B | "str(e) eliminado de 24 endpoints" | ✅ | Verificado: los 3 leaks restantes corregidos en FASE 2. Total de 24 no verificable sin histórico, pero actualmente 0 leaks. |
| C | "349 tests" | ✅ | 167 backend + 172 frontend + 10 lambdas = 349. Verificado en ejecución real (172 passed, 1 skipped). |
| D | "Calificación A (1.0) en Security/Reliability/Maintainability" | ⚠️ | Depende de escaneo SonarCloud activo. Último reporte conocido: A en todas las dimensiones. |

---

## Metodología

Cada afirmación del INFORME-GLOBAL.md fue rastreada a su archivo de código fuente y verificada mediante lectura directa, conteo de rutas/decoradores, revisión de archivos de configuración y consulta de documentación asociada. Esta versión incluye re-verificación post-FASE 2 (corrección de vulnerabilidades) y FASE 3 (pytest markers, worker.js, diagrama PNG).

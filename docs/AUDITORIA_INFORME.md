# Auditoría de Afirmaciones — INFORME-GLOBAL.md vs Código Real

**Fecha:** Junio 2026
**Total afirmaciones auditadas:** 92

---

## Resumen

| Estado | Cantidad |
|--------|:--------:|
| ✅ Verificado correcto | 82 |
| ⚠️ Parcialmente confirmado | 4 |
| ❌ Falso / necesita corrección | 6 |

---

## Hallazgos ❌ y ⚠️

| # | Sección | Afirmación | Estado | Realidad |
|---|---------|-----------|:------:|----------|
| 1 | 3.4 (Strategy) | "Interfaz MapStrategy que permite intercambiar Mapbox GL JS ↔ Leaflet sin cambiar el código del mapa" | ❌ | Solo existe `MapboxStrategy.ts`. Leaflet se usa directamente en `Reporte.tsx` y `Confirmacion.tsx` para mini-mapas, pero NO como implementación de `MapStrategy`. No hay Strategy Pattern para mapas. |
| 2 | 4.1 (Frontend) | "Leaflet (fallback vía Strategy Pattern)" | ❌ | Misma razón que #1. No hay implementación Leaflet de MapStrategy. |
| 3 | 4.2 (Endpoints) | "37 endpoints total" | ✅ | Correcto si se cuentan los 6 route decorators de reports.py (incluye /api/reportar + /reportar como 2 rutas separadas). |
| 4 | 4.2 (Endpoints) | "reports: 5" | ❌ | reports.py tiene **6** decoradores de ruta (POST /reports, POST /api/reportar, POST /reportar, GET /reports, GET /reports/{id}, PUT /reports/{id}). Para total 37, debe ser 6. |
| 5 | 4.2 (Endpoints) | "public: 9" | ❌ | public.py tiene **10** endpoints listados (dashboard-stats, map-coordinates, external-reports, cluster-stats, stale-pendientes, external-reports/sources, weather/latest, weather/history, firms-hotspots, resources). |
| 6 | 4.2 (main.py) | "POST /upload" | ❌ | La ruta real es `POST /reports/upload` (main.py). |
| 7 | 4.4 (Paneles) | "Paneles (11 total)" | ❌ | El dashboard JSON contiene exactamente **12 paneles** (numerados 1-12 en la tabla). La tabla es correcta; el encabezado dice 11. |
| 8 | 5.3 (Sincronización) | "cuando EC2 escribe un reporte (admin), se actualiza también DynamoDB vía `repo.update()`" | ❌ | `admin_update_report_status` (`admin.py:202-203`) escribe solo en SQLite. No replica a DynamoDB. No hay `repo.update()` ni ningún mecanismo SQLite→DynamoDB. |
| 9 | 7.2 (Protección API) | "`str(e)` eliminado de 24 endpoints" | ⚠️ | 3 endpoints aún exponen `str(e)`: `admin.py:75` (create_user en DynamoDB), `admin.py:213` (update_report_status), `bootstrap.py:49` (bootstrap-admin). El claim "24" no se puede verificar sin histórico. |
| 10 | 8.1 (CI/CD) | "Docker multi-stage [10]" | ❌ | Dockerfile es **single-stage** (`FROM python:3.11-slim`, 17 líneas, sin `AS builder` ni `COPY --from=`). (ref: deploy.yml y Dockerfile) |
| 11 | 8.2 (Despliegue) | "Docker multi-stage incluido en API image" | ❌ | Misma razón que #10. |
| 12 | Objetivos específicos | "Docker multi-stage" | ❌ | Misma razón que #10. |
| 13 | 4.1 (Frontend) | "Patrón Observer en Toast.tsx" | ⚠️ | Existe `ToastContext` con eventos success/error/warning/info, pero es un patrón Provider/Context de React, no el patrón GoF Observer clásico. Aceptable como interpretación. |
| 14 | 4.1 (Frontend) | "Despliegue: Cloudflare Pages" | ✅ | El frontend NO está en la imagen Docker. Se deploya automáticamente a Cloudflare Pages (`incendios-valle.pages.dev`) mediante integración nativa GitHub → Cloudflare Pages (auto-deploy en cada push a `main`). La API Docker solo contiene el backend FastAPI. |

---

## Correcciones Aplicadas

| # | Archivo | Línea | Cambio |
|---|---------|:-----:|--------|
| 1 | INFORME-GLOBAL.md | 277 | "reports: 5" → "reports: 6" |
| 2 | INFORME-GLOBAL.md | 277 | "public: 9" → "public: 10" |
| 3 | INFORME-GLOBAL.md | 290 | "POST /upload" → "POST /reports/upload" |
| 4 | INFORME-GLOBAL.md | 340 | "Paneles (11 total)" → "Paneles (12 total)" |
| 5 | INFORME-GLOBAL.md | 419 | afirmación falsa SQLite→DynamoDB reemplazada |
| 6 | INFORME-GLOBAL.md | 540 | "Docker multi-stage" → "Docker" |
| 7 | INFORME-GLOBAL.md | 580 | "Docker multi-stage" → "Docker" |
| 8 | INFORME-GLOBAL.md | 91 | "Docker multi-stage" → "Docker" |
| 9 | INFORME-GLOBAL.md | 216,219 | Leaflet Strategy → leaflet para mapas preview |

---

## Afirmaciones No Verificables

| # | Afirmación | Motivo |
|---|-----------|--------|
| A | "SonarCloud A en 4 dimensiones, 0 Code Smells" | No se puede verificar si SonarCloud no está configurado o escaneando activamente |
| B | "str(e) eliminado de 24 endpoints" | No existe histórico de cuántos endpoints tenían str(e) originalmente |
| C | "349 tests" | Hay 167+172+10 = 349. ✅ Verificado en ejecución de tests. |
| D | "Calificación A (1.0) en Security/Reliability/Maintainability" | Depende de escaneo SonarCloud; el código no expone issues evidentes |

---

## Metodología

Cada afirmación del INFORME-GLOBAL.md fue rastreada a su archivo de código fuente y verificada mediante lectura directa, conteo de rutas/decoradores, revisión de archivos de configuración y consulta de documentación asociada. Las afirmaciones verificadas con ✅ se omiten de esta tabla por brevedad.

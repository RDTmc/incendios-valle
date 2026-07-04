# INFORME GLOBAL DEL PROYECTO
## Sistema de Gestión Táctica de Incendios — Valle del Sol

---

**Curso:** _[Asignatura]_
**Integrantes:** _[Nombres]_
**Fecha:** Junio 2026
**Repositorio:** https://github.com/RDTmc/incendios-valle

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Problemática y Objetivos](#2-problemática-y-objetivos)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Componentes del Sistema](#4-componentes-del-sistema)
   - 4.1 [Sistema de Reporte Ciudadano (PWA)](#41-sistema-de-reporte-ciudadano-pwa)
   - 4.2 [Sistema de Toma de Decisiones](#42-sistema-de-toma-de-decisiones)
     - 4.2.1 [Dashboard Táctico (Grafana)](#421-dashboard-táctico--equipo-de-emergencia-grafana)
     - 4.2.2 [Dashboard TI/DevOps (Grafana)](#422-dashboard-ti--devops--equipo-de-operaciones-grafana)
     - 4.2.3 [Dashboard Admin (PWA)](#423-dashboard-admin-pwa--gestión-operativa)
   - 4.3 [Backend (FastAPI — BFF)](#43-backend-fastapi--bff)
   - 4.4 [Microservicios Lambda](#44-microservicios-lambda-5)
5. [Persistencia de Datos](#5-persistencia-de-datos)
6. [Pruebas Unitarias](#6-pruebas-unitarias)
7. [Seguridad](#7-seguridad)
8. [CI/CD y Despliegue](#8-cicd-y-despliegue)
9. [Enlaces y Referencias](#9-enlaces-y-referencias)
10. [Anexos](#10-anexos)

---

## 1. Resumen Ejecutivo

Plataforma PWA de gestión táctica de incendios forestales y urbanos para la Municipalidad de Valle del Sol. Permite a ciudadanos reportar incidentes, visualizar focos activos en un mapa interactivo, coordinar recursos de emergencia, monitorear datos climáticos y satelitales (NASA FIRMS), todo con autenticación JWT con 2FA, dashboard táctico en Grafana (en migración de datasource SQLite nativo a Infinity JSON API via RDS PostgreSQL), y despliegue CI/CD automatizado mediante GitHub Actions y Docker.

| Componente | Tests | Cobertura | Estado |
|-----------|:-----:|:---------:|:------:|
| Backend (FastAPI) | 171 | 88% | ✅ |
| Frontend (React) | 172 | 82% | ✅ |
| Lambda upload-proxy | 2 | ~90% | ✅ |
| Lambdas (ms-*) | 8 | ~85% | ✅ |
| Lambda ms-usuarios | 2 | ~85% | ✅ |
| Lambda ms-incidencias | 2 | ~85% | ✅ |
| Lambda ms-notificaciones | 2 | ~90% | ✅ |
| Lambda sns-to-grafana | 2 | ~85% | ✅ |
| **TOTAL** | **349** | **≥82%** | ✅ |

Todos los componentes superan el **60% de cobertura mínimo** exigido por la rúbrica.

---

## 2. Problemática y Objetivos

### 2.1 Problemática

Los incendios forestales y urbanos en la comuna de Valle del Sol representan una amenaza recurrente para la comunidad. El municipio enfrenta tres problemas principales:

1. **Ciudadanos sin canal digital** para reportar incendios de forma rápida y georreferenciada.
2. **Equipo de emergencia sin visibilidad en tiempo real** del estado de los focos, recursos disponibles y condiciones climáticas.
3. **Coordinación reactiva** basada en llamadas telefónicas y reportes verbales, sin trazabilidad ni dashboard centralizado.

### 2.2 Objetivos

**Objetivo general:**
Desarrollar una PWA que permita a ciudadanos reportar incendios y al equipo de emergencia visualizar y gestionar incidentes en tiempo real mediante dashboards especializados (táctico, TI/DevOps y admin), desplegada sobre infraestructura cloud AWS Academy con CI/CD automatizado.

**Objetivos específicos:**

**A. Sistema de Reporte Ciudadano (PWA):**
- Proveer un formulario de reporte ciudadano con fotografía, geolocalización automática y selección de tipo de incendio (FORESTAL/URBANO).
- Implementar una PWA instalable con soporte offline, service worker y banner de reconexión.
- Desarrollar un mapa interactivo con focos activos georreferenciados, leyenda por estado y actualización en tiempo real.
- Incorporar un sistema de límite de 5 reportes simultáneos por dispositivo para evitar saturación.
- Diseñar un flujo de registro opcional que permita reportes anónimos con device_id.

**B. Sistema de Toma de Decisiones (Dashboards + Admin):**
- Desarrollar un **dashboard táctico** en Grafana con datasource SQLite nativo, refresh cada 3 segundos y 12 paneles (focos activos, clima 30-30-30, geomap con cross-filtering, recursos, FIRMS, CONAF) para el equipo de emergencia.
- Desarrollar un **dashboard TI/DevOps** en Grafana con Prometheus y node_exporter para monitoreo de infraestructura (CPU, memoria, disco, red, healthchecks, alertas).
- Desarrollar un **Dashboard Admin** dentro de la misma PWA con 5 tabs (Usuarios, Auditoría, Notificaciones, Reportes, 2FA) para gestión operativa municipal.

**Sobre la arquitectura cloud y persistencia:**
- Utilizar infraestructura AWS Academy (LabRole) integrando DynamoDB como base de datos primaria, S3 para almacenamiento de imágenes y Lambda para cómputo serverless.
- Implementar persistencia dual DynamoDB + SQLite con sincronización SQLite→DynamoDB para sortear la restricción de escritura DynamoDB desde EC2 y habilitar Grafana como datasource nativo.
- Configurar backup automático de SQLite a S3 con restore en cada deploy.
- Desplegar un API Gateway como entry point único con 5 microservicios Lambda (upload-proxy, ms-usuarios, ms-incidencias, ms-notificaciones, sns-to-grafana).
- Implementar monitoreo de infraestructura con Prometheus y node_exporter (métricas CPU/disco/memoria/red).

**Sobre seguridad y autenticación:**
- Implementar autenticación segura con JWT (HS256), bcrypt para hash de contraseñas y 2FA con OTP viajando dentro del JWT (sin store externo).
- Desarrollar recuperación de contraseña con flujo de 3 pasos (email → OTP 6 dígitos → nueva contraseña) y backup codes para desactivación de 2FA.
- Implementar endpoint bootstrap de emergencia para recuperación de acceso admin cuando DynamoDB no permite escritura.
- Restringir CORS a dominios conocidos y eliminar exposición de detalles de error en respuestas API.
- Implementar login con fallback SQLite para usuarios registrados vía password reset que no existen en DynamoDB.

**Sobre calidad y automatización:**
- Automatizar el despliegue mediante CI/CD con GitHub Actions, Docker y deploy automatizado a EC2 con healthchecks.
- Alcanzar calificación A en las 4 dimensiones de SonarCloud (Security, Reliability, Maintainability, Security Review) con 0 Code Smells.
- Implementar 353 tests unitarios (171 backend, 172 frontend, 10 lambdas) con cobertura mínima del 82% y 3 patrones de diseño verificables (BFF, Circuit Breaker, Factory Method).
- Incorporar 3 workflows adicionales (restart-grafana, audit, fix-permissions) para operaciones post-deploy.
- Integrar datos satelitales NASA FIRMS, climáticos OpenWeatherMap y forestales CONAF/CIREN como fuentes externas en los dashboards.

**Sobre accesibilidad y difusión:**
- Implementar redirección inteligente para QR físico municipal (Android → Chrome Intent, otros → login con UTM tracking).
- Desarrollar un prototipo de afiche municipal con instrucciones de instalación para dispositivos Xiaomi.
- Detectar navegadores embebidos (Facebook, Instagram, etc.) y sugerir abrir en Chrome/Safari para instalar la PWA.

---

## 3. Arquitectura del Sistema

_Referencias técnicas: FastAPI [1] como framework BFF, Cloudflare DNS [13] para enrutamiento del dominio `api.keogh.lat`._

### 3.1 Diagrama de Arquitectura

```
                    ┌─────────────────────────────────────────┐
                    │              USUARIOS                    │
                    │  [Ciudadano]  [Admin Municipal] [Vecino] │
                    └─────────────┬───────────┬───────────────┘
                                  │           │
                    ┌─────────────▼───────────▼───────────────┐
                    │       CLOUDFLARE PAGES (Hosting PWA)     │
                    │  React 18 + TypeScript + Tailwind         │
                    │  Mapbox GL JS + Service Worker            │
                    │  https://incendios-valle.pages.dev        │
                    └──────┬──────────────────┬────────────────┘
                           │                  │
               ┌───────────▼──────┐   ┌──────▼───────────┐
               │ Cloudflare Worker│   │  Mapbox GL JS    │
               │ CORS + rate lim. │   │  (tiles mapbase) │
               │ (manual deploy)  │   └──────────────────┘
               └───────────┬──────┘
                           │
                    ┌──────▼────────────────────────────────┐
                    │   CLOUDFLARE DNS-only                  │
                    │   api.keogh.lat → API Gateway          │
                    │   (fix imágenes corruptas: grey cloud) │
                    └─────────────────┬─────────────────────┘
                                      │
                    ┌─────────────────▼─────────────────────┐
                    │       API GATEWAY (HTTP_PROXY)         │
                    │   /auth → λ ms-usuarios                │
                    │   /reports → λ ms-incidencias         │
                    │   /alerts → λ ms-notificaciones       │
                    │   /upload → λ upload-proxy             │
                    │   /api/{proxy+} → EC2 nginx            │
                    │   /grafana-sns → λ sns-to-grafana     │
                    └─────────────────┬─────────────────────┘
                                      │
                    ┌─────────────────▼─────────────────────┐
                     │         EC2 t3.micro                   │
                     │  ┌──────────┐ ┌──────────┐ ┌────────┐ │
                     │  │  nginx   │ │ FastAPI  │ │Grafana │ │
                     │  │  proxy   │ │ (BFF)    │ │ 10.4.8 │ │
                     │  └────┬─────┘ └────┬─────┘ └───┬────┘ │
                     │       │            │           │      │
                     │       └────────────┼───────────┘      │
                     │                    ▼                   │
                     │            ┌──────────────┐            │
                     │            │   SQLite     │            │
                     │            │ incendios.db │            │
                     │            └──────────────┘            │
                     │  ┌────────────┐ ┌──────────────┐       │
                     │  │ Prometheus │ │Node Exporter │       │
                     │  │ scrape:9100│ │ host metrics │       │
                     │  └────────────┘ └──────────────┘       │
                    └─────────────────┬─────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────┐
          │                           │                       │
          ▼                           ▼                       ▼
   ┌──────────────┐          ┌──────────────┐         ┌──────────┐
   │   DynamoDB   │          │   S3 (AWS)   │         │  SNS     │
   │ users+reports│          │  imágenes    │         │  alerts  │
   └──────────────┘          └──────────────┘         └──────────┘
          ▲                           ▲
          │                           │
   ┌──────┴──────┐           ┌────────┴────────┐
   │ 5 Lambdas   │           │ APIs Externas   │
   │ (Python)    │           │ FIRMS,OWM,CONAF │
   └─────────────┘           │ Mailtrap SMTP   │
                             └─────────────────┘
```

### 3.2 Flujo de Datos

1. **Usuario** accede a la PWA en `incendios-valle.pages.dev` (Cloudflare Pages).
2. La PWA se comunica vía **API Gateway** (DNS-only por Cloudflare, sin proxy HTTP que corrompa binarios).
3. API Gateway enruta a los **5 microservicios Lambda** (auth, reports, alerts, upload) o al **endpoint HTTP_PROXY** que llega a EC2.
4. En **EC2**, nginx hace reverse proxy al **FastAPI** (BFF) que orquesta datos desde:
    - **SQLite** → **RDS PostgreSQL (en migración)**: reportes, alertas, auditoría, 2FA, notificaciones (para Grafana + admin).
   - **DynamoDB**: usuarios y reportes (persistencia primaria para Lambdas).
   - **S3**: imágenes de reportes subidas vía Lambda.
   - **APIs externas**: NASA FIRMS (focos activos satelitales), OpenWeatherMap (clima), CONAF/CIREN (datos forestales), **Mapbox GL JS** (mapas base e interacción geoespacial en frontend [16]).
5. **Grafana** se conecta directamente a SQLite para los dashboards tácticos, y a **Prometheus** para el dashboard DevOps. El dashboard principal usa variable `highlight` para cross-filtering entre tabla de reportes y geomap.
6. **Mailtrap SMTP** envía correos con OTP para 2FA y recuperación de contraseña.

### 3.3 Decisiones de Diseño Clave

| Decisión | Justificación |
|----------|---------------|
| API Gateway como entry point único | Simplifica la seguridad y el ruteo centralizado |
| Dual DynamoDB + SQLite → RDS PostgreSQL | LabRole de AWS Academy no permite escritura DynamoDB desde EC2; Grafana requiere SQLite como datasource (migrando a Infinity JSON API con PostgreSQL Jul 2026) |
| BFF (Backend for Frontend) | Abstrae complejidad del backend, agrega datos de múltiples fuentes, evita exponer arquitectura interna al frontend |
| 5 Lambdas separadas | Escalabilidad individual, aislamiento de fallos, despliegue independiente |
| FastAPI vs Django/Flask | Asíncrono, tipado, genera OpenAPI automáticamente, ideal para BFF |
| bcrypt compilado con Docker Lambda | Necesita GLIBC correcto para Amazon Linux 2 |
| OTP 2FA viajando dentro del JWT | Sin store externo (ni memoria ni SQLite), resistente a redeploys, alineado con OWASP |
| Múltiples fuentes de datos en PWA | Los Service Workers permiten funcionamiento offline parcial y caché de recursos estáticos |

### 3.4 Patrones de Diseño

| Patrón | Tipo | Ubicación | Tests | Descripción |
|--------|------|-----------|:-----:|-------------|
| **BFF (Backend for Frontend)** | Arquitectónico | `routers/bff.py` | 5 | Agrega datos de múltiples fuentes (SQLite, DynamoDB, APIs externas) en una respuesta optimizada para el frontend. Patrón recomendado para arquitecturas con frontend móvil/PWA |
| **Circuit Breaker** | Comportamiento | `circuit_breaker.py` | 6 | Evita llamadas fallidas a APIs externas (FIRMS, OpenWeather, CONAF); tras 3 fallos abre el circuito y ejecuta fallback. Patrón de resiliencia cloud-native |
| **Factory Method** | Creacional | `factories/report_factory.py` | 5 | Crea reportes según tipo (`FORESTAL`/`URBANO`) con atributos y validaciones específicas |
| **Strategy** | Comportamiento | `util/map/MapStrategy.ts` | 19 | Interfaz `MapStrategy` con 1 implementación (MapboxStrategy); Leaflet usado directamente en vistas preview sin strategy |
| **Observer** | Comportamiento | `components/Toast.tsx` | 5 | Contexto de notificaciones toast: componentes se suscriben y reciben eventos success/error/warning/info |
| **Composite** | Estructural | `components/ui/Button`, `Input`, `Card` | 3 | Componentes UI atómicos que se combinan para construir interfaces consistentes en todas las páginas |

---

## 4. Componentes del Sistema

El sistema se compone de dos grandes subsistemas que operan de forma mancomunada pero atienden a distintos usuarios y procesos:

| Subsistema | Usuario objetivo | Propósito |
|------------|-----------------|-----------|
| **Reporte Ciudadano** (§4.1) | Ciudadano / Vecino | Reportar incendios, ver focos activos, historial |
| **Toma de Decisiones** (§4.2) | Equipo de emergencia / TI Municipal | Monitorear en tiempo real, coordinar recursos, gestionar operaciones |

Ambos subsistemas comparten el backend (BFF), la infraestructura cloud y el pipeline CI/CD descritos en las secciones siguientes.

### 4.1 Sistema de Reporte Ciudadano (PWA)

_Referencias técnicas: React 18 [7], TypeScript [8], Vite [26], Tailwind CSS [25], Mapbox GL JS [16], estándar PWA [9]._

| Aspecto | Detalle |
|---------|---------|
| Framework | React 18 + TypeScript + Vite |
| Estilos | Tailwind CSS |
| Mapas | Mapbox GL JS (primario), Leaflet (mini-mapas preview en vistas) |
| PWA | Service Worker con soporte offline |
| Testing | Vitest 1.6 + Testing Library + jsdom |
| Despliegue | Cloudflare Pages (auto-deploy desde GitHub) |
| **Tests** | **172 tests, 82% cobertura** |

**Páginas ciudadanas (9 de las 10 páginas del frontend):**

| Página | Ruta | Descripción | Auth |
|--------|------|-------------|:----:|
| **Login** | `/login` | Login email/password + flujo OTP 2FA + link recuperación | No |
| **Registro** | `/registro` | Crear cuenta ciudadana | No |
| **Reporte** | `/reporte` | Formulario: tipo incendio, GPS, foto, descripción. Límite 5 reportes simultáneos | Opcional |
| **Confirmación** | `/confirmar` | Post-envío: mapa preview, foto, botones nuevo reporte / ver mapa | Opcional |
| **MapaFocos** | `/mapa` | Mapa interactivo con focos activos + leyenda + lista focos recientes | No |
| **Historial** | `/historial` | Lista de reportes del usuario con bottom nav | Sí |
| **ForgotPassword** | `/forgot-password` | Recuperación 3 pasos: email → OTP+contraseña → éxito | No |
| **RedireccionQr** | `/qr` | Redirección inteligente según SO: Android → Chrome Intent, otros → `/login` con UTM | No |
| **AfichePreview** | `/dev-afiche` | Prototipo del afiche municipal para impresión (QR + instrucciones) | No |

**Componentes ciudadanos adicionales:**

| Componente | Descripción |
|------------|-------------|
| **AlertBanner** | Banner flotante con alertas tipo CRÍTICO/ALTA/MEDIA/INFO con polling cada 30s y botón de dismiss |
| **AvisoNavegadorEmbebido** | Detecta navegadores embebidos (Facebook, Instagram, etc.) y sugiere abrir en Chrome/Safari |
| **OfflineBanner** | Banner "Sin conexión" con eventos online/offline |
| **ErrorBoundary** | Error boundary global con botón "Reintentar" |
| **Slots 5/5** | Límite de 5 reportes simultáneos por dispositivo para evitar saturación |

**Componentes UI reutilizables (patrón Composite):**
`Button`, `Input`, `Card` — exportados desde `components/ui/index.ts`

**Flujo ciudadano típico:**

```
Ciudadano → Login/Registro → Reporte (foto + GPS + tipo) →
  Confirmación → Mapa de Focos Activos → Historial personal
```

### 4.2 Sistema de Toma de Decisiones

_Referencias técnicas: Grafana con datasource SQLite [5], Prometheus [23], datos satelitales NASA FIRMS [2]._

Sistema compuesto por **tres dashboards** que operan en distintos niveles de la toma de decisiones:

| Dashboard | Plataforma | Usuario | Refresh | Propósito |
|-----------|-----------|---------|:-------:|-----------|
| **Táctico** (§4.2.1) | Grafana | Equipo de emergencia | 3s | Coordinación de incendios en tiempo real |
| **TI/DevOps** (§4.2.2) | Grafana | Equipo de TI | 30s | Monitoreo de infraestructura |
| **Admin** (§4.2.3) | PWA (React) | Admin municipal | 15s | Gestión operativa CRUD |

#### 4.2.1 Dashboard Táctico — Equipo de Emergencia (Grafana)

Dashboard principal para el equipo de emergencia. Visualiza en tiempo real focos activos, clima, recursos y datos satelitales para coordinar la respuesta a incendios.

| Aspecto | Detalle |
|---------|---------|
| Nombre | Dashboard Incendios — Valle del Sol |
| UID | `incendios-valle-main` |
| Versión | 74 (exportado/importado desde UI) |
| Refresh | Cada 3 segundos |
| Datasource | SQLite (`frser-sqlite-datasource`) + Prometheus |
| Variable | `highlight` (textbox oculto) para cross-filtering entre tabla y geomap |
| Provisioning | `ec2/grafana-provisioning/dashboards/dashboard_incendios.json` |

**Paneles (12 total):**

| # | Panel | Tipo | Query / Fuente | Función táctica |
|:-:|-------|:----:|----------------|-----------------|
| 1 | **Focos Activos** | Stat | `SELECT COUNT(*) FROM reports WHERE estado IN ('ACTIVO','PENDIENTE')` | Conteo rápido de incendios activos + pendientes |
| 2 | **Clima 30-30-30** | Table | Último registro por región: temperatura, humedad, viento + columna `Riesgo` (0/1/2) | Regla: temp>30°C + humedad<30% + viento>30km/h = riesgo crítico |
| 3 | **Estatus de Reportes** | BarGauge | `SELECT estado, COUNT(*) FROM reports GROUP BY estado` | Barras por estado con gradiente de color |
| 4 | **Focos por Estado** | GeoMap | Capa A: reports con lat/lng e intensidad (ACTIVO=3, PENDIENTE=2, CONTROLADO=1). Capa B: destacado por `highlight`. Basemap: ESRI World Imagery | Mapa táctico con focos geo-referenciados |
| 5 | **Focos por Estado (copia)** | GeoMap | Capa A: reports + Capa B: destacado + Capa C: recursos en terreno (`incident_resources` LEFT JOIN `reports`). Basemap: OSM Standard | Mapa con recursos asignados |
| 6 | **Reportes Ciudadanos** | Table | Últimos 10 reports: ID, imagen (render), descripción, tipo, estado, fecha. Link "Destacar" → variable `highlight` | Lista operativa de reportes |
| 7 | **Distribución Tipo Incendio** | PieChart (donut) | `SELECT tipo, COUNT(*) FROM reports GROUP BY tipo` con % | Proporción forestal vs urbano |
| 8 | **Recursos por Incidente** | Table | Últimos 20 `incident_resources` LEFT JOIN `reports`: estado, recurso, cantidad, tipo incendio, ubicación, asignación | Seguimiento de recursos desplegados |
| 9 | **Focos de Calor Satelital** | GeoMap | `firms_hotspots` últimos 3 días: lat/lng, FRP (MW), confianza, satélite. Radio marcador según longitud | Datos NASA FIRMS en mapa |
| 10 | **Histórico CONAF** | GeoMap | `external_reports` (500 reg): lat/lng, nombre, región, superficie (ha), causa. Tamaño marcador = superficie | Datos históricos CONAF/CIREN |
| 11 | **Reportes vs Recursos Asignados** | Table | Reports LEFT JOIN `incident_resources`: reporte, incendio, tipo, evaluación, recursos (count), estados | Evaluación de cobertura |
| 12 | **Distribución Estado Recursos** | BarGauge | `SELECT estado, COUNT(*) FROM incident_resources GROUP BY estado` | Estado general de recursos |

**Flujo de decisión táctica:**

```
Reporte ciudadano → Dashboard Táctico (refresco 3s) →
  Evaluación de focos activos → Asignación de recursos →
  Monitoreo satelital (FIRMS) + Clima 30-30-30 → Decisión
```

#### 4.2.2 Dashboard TI / DevOps — Equipo de Operaciones (Grafana)

_Referencias técnicas: Prometheus [23] para métricas del servidor._

Dashboard de monitoreo técnico para el equipo de TI. Visualiza métricas del servidor, salud de la API y alertas del sistema.

| Aspecto | Detalle |
|---------|---------|
| Nombre | DevOps — Incendios Valle del Sol |
| UID | `devops-incendios` |
| Refresh | Cada 30 segundos |
| Datasource | Prometheus (`node_exporter`) + SQLite |
| Provisioning | `ec2/grafana-provisioning/dashboards/devops_dashboard.json` |

**Paneles (6 total):**

| # | Panel | Tipo | Query | Función |
|:-:|-------|:----:|-------|---------|
| 1 | **CPU Utilization** | TimeSeries | `100 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m]))` | % CPU del servidor (thresholds: 70% naranja, 90% rojo) |
| 2 | **Network Activity** | TimeSeries | `rate(node_network_receive_bytes_total[1m])` (In) + `rate(node_network_transmit_bytes_total[1m])` (Out) | Tráfico de red (thresholds: 1 MB/s naranja, 5 MB/s rojo) |
| 3 | **Memory Usage** | Stat | `((mem_total - mem_available) / mem_total) * 100` | % RAM usado (thresholds: 70%, 90% con color de fondo) |
| 4 | **API Healthcheck** | Stat | `SELECT 1 AS status` desde SQLite | Verde si responde, rojo si no (check binario) |
| 5 | **Disk Usage** | TimeSeries | `100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)` | % disco usado (thresholds: 80%, 95%) |
| 6 | **Alertas Recientes** | Table | `SELECT alert_type, message, created_at, read FROM alerts ORDER BY created_at DESC LIMIT 20` | Últimas 20 alertas del sistema |

**Infraestructura de monitoreo asociada:**

| Componente | Descripción | Archivo |
|------------|-------------|---------|
| **Prometheus Server** | Container Docker scrapeando node_exporter cada 15s | `ec2/prometheus/prometheus.yml` |
| **Node Exporter** | Container Docker en host network exponiendo métricas del sistema en puerto 9100 | `ec2/docker-compose.yml` |
| **Healthcheck Script** | Script bash que verifica API + Grafana + Docker + disco + memoria. Exit code 0 si todo OK | `ec2/monitoring/healthcheck.sh` |
| **Docker Healthchecks** | Container `api` con healthcheck cada 10s a `/api/health`; nginx espera a que api esté healthy | `ec2/docker-compose.yml` |
| **nginx Health** | Endpoint interno `/nginx-health` retorna `200 "nginx healthy"` | `ec2/nginx/nginx.conf` |

#### 4.2.3 Dashboard Admin (PWA) — Gestión Operativa

Panel de administración dentro de la misma PWA, accesible solo para usuarios con rol ADMIN. 5 tabs de gestión:

| Tab | Funcionalidad | Endpoints Backend |
|-----|--------------|-------------------|
| **Usuarios** | CRUD completo: tabla ordenable con búsqueda, crear/editar/eliminar usuarios, roles VECINO/ADMIN, auto-refresh cada 15s | `GET/POST/PUT/DELETE /admin/users` |
| **Auditoría** | Registro de acciones administrativas (create/update/delete user, cambio estado reporte) con colores por tipo | `GET /admin/audit-log` |
| **Notificaciones** | Historial de notificaciones de bienvenida enviadas a nuevos usuarios | `GET /admin/notifications` |
| **Reportes** | Tabla ordenable con dropdown de estado coloreado: PENDIENTE → ACTIVO → CONTROLADO → EXTINGUIDO | `PUT /admin/reports/{id}/status` |
| **2FA** | Activar/desactivar verificación en dos pasos, generar backup codes, mostrar códigos restantes | `GET/POST/DELETE /admin/2fa/*` |

### 4.3 Backend (FastAPI — BFF)

| Aspecto | Detalle |
|---------|---------|
| Framework | Python 3.11+, FastAPI, uvicorn |
| Routers | auth, reports, public, admin, alerts, bff, password_reset, bootstrap (8 routers) |
| Auth | JWT HS256 con bcrypt, OTP 2FA en JWT, backup codes, bootstrap de emergencia |
| Patrones | Repository (DynamoDB), Circuit Breaker, Factory Method, BFF |
| Testing | pytest 8.3 + pytest-cov 7.1 + unittest.mock |
| **Tests** | **171 tests, 88% cobertura** |

**Endpoints del Backend (45 total: 37 en routers + 8 directos en main.py):**

| Router | Endpoints | Descripción |
|--------|-----------|-------------|
| **auth** | 6 | Login (con 2FA), verify 2FA OTP, register, setup/disable/status 2FA admin |
| **reports** | 6 | CRUD reportes (crear, reportar anónimo, listar, obtener, actualizar) |
| **public** | 10 | Dashboard-stats, coordenadas mapa, clima, FIRMS hotspots, clusters, recursos, fuentes externas, stale pendientes |
| **admin** | 8 | CRUD usuarios, listar/actualizar estado reportes, auditoría, notificaciones |
| **alerts** | 3 | CRUD alertas (crear, listar, marcar leída) |
| **bff** | 1 | Dashboard completo: stats + clima + hotspots + focos + recursos |
| **password_reset** | 2 | forgot-password (envía OTP email), reset-password (valida OTP + nueva pass) |
| **bootstrap** | 1 | bootstrap-admin (recuperación de emergencia, one-time) |

**Endpoints adicionales en `main.py` (8):**

| Endpoint | Descripción |
|----------|-------------|
| `GET /health` | Health check de la API |
| `POST /sync` | Sincronizar DynamoDB → SQLite (usado por Lambdas) |
| `POST /reports/upload` | Subir imagen a S3 vía Lambda proxy |
| `GET /images/{key:path}` | Proxy de imágenes: presigned URL + redirect 302 |
| `GET /focos-activos` | Focos activos desde DynamoDB con geofence |
| `POST /v1/external-reports/trigger` | Trigger background task: CONAF/CIREN |
| `POST /v1/external-reports/conaf` | Recibir reporte externo desde CONAF |
| `GET /dashboard/stats` | Estadísticas del dashboard (requiere auth) |

**Endpoints protegidos con `require_admin` (11):**

| Método | Ruta | Función |
|--------|------|---------|
| `GET` | `/admin/users` | Listar usuarios con búsqueda |
| `POST` | `/admin/users` | Crear usuario |
| `PUT` | `/admin/users/{user_id}` | Editar usuario |
| `DELETE` | `/admin/users/{user_id}` | Eliminar usuario |
| `GET` | `/admin/audit-log` | Ver log de auditoría |
| `GET` | `/admin/reports` | Listar todos los reportes |
| `PUT` | `/admin/reports/{report_id}/status` | Cambiar estado + sync DynamoDB |
| `GET` | `/admin/notifications` | Ver notificaciones enviadas |
| `POST` | `/admin/2fa/setup` | Activar 2FA (genera backup codes) |
| `POST` | `/admin/2fa/disable` | Desactivar 2FA |
| `GET` | `/admin/2fa/status` | Estado 2FA + códigos restantes |

### 4.4 Microservicios Lambda (5)

_Referencias técnicas: AWS Lambda [19] para cómputo serverless, AWS SNS [21] para mensajería de alertas._

| Lambda | Función | Tests |
|--------|---------|:-----:|
| **upload-proxy** | Subida de imágenes a S3 (base64 directo) | 2 |
| **ms-usuarios** | Login/registro contra DynamoDB con bcrypt | 2 |
| **ms-incidencias** | CRUD reportes DynamoDB | 2 |
| **ms-notificaciones** | Publicación SNS de alertas | 2 |
| **sns-to-grafana** | Anotaciones Grafana desde SNS | 2 |

---

## 5. Persistencia de Datos

_Referencias técnicas: DynamoDB [12] como base de datos primaria, S3 [15] para almacenamiento de imágenes, SQLite con WAL mode [24] para integridad y concurrencia._

### 5.1 Arquitectura General

El sistema utiliza **tres mecanismos de persistencia** complementarios:

| Mecanismo | Datos | Propósito |
|-----------|-------|-----------|
| **DynamoDB** (AWS) | Usuarios, reportes | Persistencia primaria. CRUD desde API Gateway + Lambdas |
| **SQLite** (local EC2) | Reportes, alertas, auditoría, 2FA, notificaciones | Persistencia secundaria para Grafana + fallback login |
| **S3** (AWS) | Imágenes de reportes | Almacenamiento de archivos binarios (JPEG/PNG) |

### 5.2 ¿Por qué DynamoDB y SQLite?

La dualidad responde a dos restricciones:

1. **LabRole AWS Academy**: no permite escritura DynamoDB desde EC2. Las Lambdas sí pueden escribir DynamoDB por tener un role distinto. Por eso las operaciones CRUD desde EC2 escriben primero en SQLite.
2. **Grafana**: no soporta DynamoDB como datasource. SQLite es el datasource nativo para los dashboards tácticos.

### 5.3 Sincronización

- **DynamoDB → SQLite**: endpoint `POST /sync` que recibe eventos desde Lambdas y replica en SQLite.
- **SQLite → DynamoDB**: la actualización de estado desde EC2 se realiza primero en SQLite y luego se replica a DynamoDB vía `repo.update()`. No hay replicación inversa automatizada (DynamoDB Streams).
- **Login con fallback**: primero intenta DynamoDB; si no encuentra el usuario o la contraseña no coincide, prueba SQLite. Esto permite login a usuarios registrados vía password reset (sin DynamoDB).

### 5.4 Backup y Restore

| Operación | Mecanismo |
|-----------|-----------|
| Backup SQLite | Automático a S3 vía `backup_sqlite_to_s3()` |
| Restore en deploy | `restore_sqlite_from_s3()` en startup de la API |
| Integridad | WAL mode + `busy_timeout=5000` para concurrencia Grafana |

---

## 6. Pruebas Unitarias

_Referencias técnicas: pytest [17] para testing backend, Vitest [27] para testing frontend, SonarCloud [18] para análisis de calidad de código._

### 6.1 Resumen

| Componente | Tests | Cobertura | Estado |
|-----------|:-----:|:---------:|:------:|
| Backend (FastAPI) | 171 | 88% | ✅ |
| Frontend (React) | 172 | 82% | ✅ |
| Lambda upload-proxy | 2 | ~90% | ✅ |
| Lambdas (ms-*) | 8 | ~85% | ✅ |
| Lambda ms-usuarios | 2 | ~85% | ✅ |
| Lambda ms-incidencias | 2 | ~85% | ✅ |
| Lambda ms-notificaciones | 2 | ~90% | ✅ |
| Lambda sns-to-grafana | 2 | ~85% | ✅ |
| **TOTAL** | **349** | **≥82%** | ✅ |

### 6.2 Herramientas

| Capa | Herramienta |
|------|------------|
| Backend | pytest 8.3 + pytest-cov 7.1 + unittest.mock |
| Frontend | Vitest 1.6 + Testing Library + jsdom |
| Lambdas | pytest + unittest.mock (boto3) |
| Cobertura | pytest-cov (HTML) / v8 (HTML) |
| Calidad código | SonarCloud |

### 6.3 APIs y Servicios Mockeados

| # | Servicio/API | Archivo test |
|---|-------------|-------------|
| S1 | Mailtrap SMTP (OTP) | test_auth.py, test_password_reset.py |
| S2 | Cloudflare Worker | Login.test.tsx, Reporte.test.tsx |
| S3 | NASA FIRMS | test_public.py |
| S4 | OpenWeatherMap | test_public.py |
| S5 | CONAF / CIREN | test_public.py |
| S6 | Mapbox GL JS | MapboxStrategy.test.tsx |
| S7 | S3 (AWS) | test_upload.py, test_services.py |
| S8 | DynamoDB (AWS) | test_repositories.py |
| S9 | API Gateway (AWS) | test_auth.py |

### 6.4 Ejemplos Representativos

#### Backend — B1: Login + 2FA OTP en JWT
**Archivo:** `test_auth.py` — 3 tests

Verifica que un admin con 2FA activo recibe un `temp_token` (JWT que contiene el OTP firmado) en lugar de un JWT directo, y que el OTP correcto permite obtener el JWT final.

#### Backend — B2: Circuit Breaker
**Archivo:** `test_circuit_breaker.py` — 6 tests

Verifica que tras 3 fallos consecutivos el circuito se abre, y que las llamadas posteriores ejecutan el fallback en lugar de la función original.

#### Backend — B5: Password Reset con OTP
**Archivo:** `test_password_reset.py` — 4 tests

Verifica que el endpoint `forgot-password` envía un OTP de 6 dígitos al email, y que `reset-password` permite cambiar la contraseña con el OTP válido.

#### Backend — B6: Admin cambiar estado de reportes
**Archivo:** `test_reports.py` — 3 tests

Verifica que un admin puede cambiar el estado de un reporte (PENDIENTE → ACTIVO → CONTROLADO → EXTINGUIDO) y que usuarios no autenticados reciben 403.

#### Frontend — F1: Login + input OTP 2FA
**Archivo:** `Login.test.tsx` — 8 tests

Verifica que al hacer login con 2FA requerido, aparece el campo de código de verificación OTP.

#### Frontend — F5: ForgotPassword 3 pasos
**Archivo:** `ForgotPassword.test.tsx` — 3 tests

Verifica la transición entre los 3 pasos: email → OTP + nueva contraseña → confirmación.

---

## 7. Seguridad

### 7.1 Autenticación

- **JWT** (HS256) con bcrypt para hash de contraseñas, siguiendo el estándar RFC 7519 [3] y las recomendaciones de OWASP [4].
- **2FA con OTP**: el código de 6 dígitos viaja firmado dentro de un `temp_token` (JWT de un solo uso). No hay store externo — ni memoria ni SQLite — lo que lo hace resistente a redeploys.
- **Backup codes**: para recuperación de 2FA, almacenados en SQLite. Si no hay backup code disponible, el 2FA se auto-desactiva durante el password reset.
- **Password reset**: flujo de 3 pasos con OTP enviado por email (Mailtrap SMTP).

### 7.2 Protección de API

- **CORS** restringido a dominios conocidos, siguiendo OWASP CORS Cheat Sheet [20].
- **Headers de error genéricos**: no se exponen detalles internos (`str(e)` eliminado de 24 endpoints).
- **JWT_SECRET** sin default en `dependencies.py` — la app no arranca sin configuración.
- **Sync token** para comunicación entre servicios internos.

### 7.3 Mejora Continua (SonarCloud)

| Métrica | Valor |
|---------|:-----:|
| Security Rating | A (1.0) |
| Reliability Rating | A (1.0) |
| Security Review | A (1.0) |
| Maintainability | A (1.0) |
| Code Smells | 0 |
| Open Issues | 1 (Reliability Medium — aceptado) |

---

## 8. CI/CD y Despliegue

### 8.1 Pipeline GitHub Actions

El proyecto utiliza **4 workflows de GitHub Actions** para automatizar el despliegue y operaciones sobre el repositorio en GitHub [11] y Docker [10].

El workflow principal (`deploy.yml`) se activa con push a `main` si los paths incluyen archivos relevantes (EC2, frontend, lambdas, docker-compose, etc.) y ejecuta 7 fases secuenciales:

```
                     ┌──────────────────────────────┐
                     │   push a main (branch)        │
                     │   paths: ec2/**, frontend/**  │
                     │   lambda/**, .github/**       │
                     └──────────────┬───────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │  🔧 Setup (Checkout + Deps)  │
                     │  • Python 3.11 + pip install │
                     │  • Node 20 + npm ci          │
                     └──────────────┬───────────────┘
                                    ▼
               ┌─────────────────────────────────────┐
               │  1. Tests Backend (pytest + cov)    │
               │     PYTHONPATH=ec2/api python -m    │
               │     pytest ec2/api/tests/ --cov     │
               └──────────────┬──────────────────────┘
                              ▼
               ┌─────────────────────────────────────┐
               │  2. Tests Frontend (npm test + cov) │
               │     cd frontend && npm test         │
               │     -- --coverage                   │
               └──────────────┬──────────────────────┘
                              ▼
               ┌─────────────────────────────────────┐
               │  3. SonarCloud Scan                 │
               │     Quality gate: A en todas las    │
               │     dimensiones (Security,          │
               │     Reliability, Maintainability,   │
               │     Security Review) + 0 Smells     │
               └──────────────┬──────────────────────┘
                              ▼
               ┌─────────────────────────────────────┐
               │  4. Docker Build & Push             │
               │     • Set up Docker Buildx          │
               │     • Login a Docker Hub            │
               │     • Build + push imagen           │
               │       (gha cache mode=max)          │
               └──────────────┬──────────────────────┘
                              ▼
               ┌─────────────────────────────────────┐
               │  5. SCP Sync (2 transfers)          │
               │     • scripts + configs → EC2       │
               │       (refresh_api.sh, compose,     │
               │        nginx.conf, prometheus/)     │
               │     • grafana-provisioning/ → EC2   │
               │       (dashboards JSON + datasources)│
               └──────────────┬──────────────────────┘
                              ▼
               ┌─────────────────────────────────────┐
               │  6. SSH Deploy (refresh_api.sh)     │
               │     • Sanitizar .env                │
               │     • Inyectar API keys desde       │
               │       GitHub Secrets                │
               │     • pull imagen Docker: ${{       │
               │       secrets.DOCKERHUB_USERNAME }}/│
               │       incendios-api:latest          │
               │     • docker-compose up -d          │
               │       --force-recreate api          │
               │     • Restore SQLite desde S3       │
               │       (aws s3 cp backups/           │
               │        incendios-latest.db)         │
               │     • Restart Grafana condicional   │
               │       (solo si cambió hash del      │
               │       provisioning/)                │
               │     • Backup Grafana DB pre-deploy  │
               │       a S3                          │
               └─────────────────────────────────────┘
```

**Auto-deploy externo (configurado fuera del repo):**

| Componente | Método | Configuración |
|-----------|--------|---------------|
| Frontend (PWA) | **Cloudflare Pages** — auto-deploy desde GitHub en cada push a `main` | Dashboard Cloudflare Pages vinculado al repo |
| Cloudflare Worker | **Manual** — Wrangler CLI o dashboard Cloudflare | `cloudflare/worker.js` |

> La PWA se deploya automáticamente a `incendios-valle.pages.dev` mediante la integración nativa de Cloudflare Pages con GitHub (sin workflow adicional). El Worker (`cloudflare/worker.js`) implementa CORS estricto y rate limiting (10 req/min en `/api/login`) y se deploya manualmente.

### 8.2 Componentes y Cómo se Despliegan

| Componente | Método | Archivo Fuente |
|------------|--------|---------------|
| API (FastAPI) | Docker build/push → pull + restart | `ec2/api/main.py` + Dockerfile |
| Frontend (PWA) | Cloudflare Pages (auto-deploy desde GitHub) | `frontend/` |
| Cloudflare Worker | **Manual** (NO automatizado) | `cloudflare/worker.js` |
| Grafana dashboards | SCP provisioning → restart condicional | `ec2/grafana-provisioning/dashboards/*.json` |
| nginx config | SCP vía docker-compose | `ec2/nginx/nginx.conf` |
| Lambdas | **Manual** (NO automatizado en CI/CD) | `lambda/*/app.py` |

### 8.3 Infraestructura EC2

- **Instancia**: t3.micro con 5 contenedores Docker:
  - **nginx**: proxy reverso con endpoint `/nginx-health` y upstream dinámico
  - **FastAPI**: API BFF con healthcheck Docker cada 10s
  - **Grafana 10.4.8**: dashboard táctico + dashboard DevOps
  - **Prometheus**: scrape de node_exporter cada 15s en `host.docker.internal:9100`
  - **Node Exporter**: métricas del sistema (CPU, memoria, disco, red)
- **Volúmenes**: SQLite persistente + dashboards provisioning + datos Prometheus
- **Sin hot-patching**: solo pipeline deploy

### 8.4 Workflows Adicionales

| Workflow | Descripción |
|----------|-------------|
| **restart-grafana.yml** | Reinicia Grafana forzadamente con nuevo provisioning (ejecución manual) |
| **audit.yml** | Audita el estado del provisioning en EC2 vs el repo |
| **fix-permissions.yml** | Corrige permisos de SQLite para Grafana (ejecución manual) |

---

## 9. Enlaces y Referencias

| Recurso | URL |
|---------|-----|
| **PWA (producción)** | https://incendios-valle.pages.dev |
| **API Base** | https://api.keogh.lat/api |
| **Swagger UI** | https://api.keogh.lat/api/docs |
| **Dashboard Táctico (Grafana)** | https://dashboard.keogh.lat |
| **Dashboard TI/DevOps (Grafana)** | https://dashboard.keogh.lat/d/devops-incendios |
| **Repositorio GitHub** | https://github.com/RDTmc/incendios-valle |
| **Especificación OpenAPI** | `docs/api-spec/openapi.json` (37 endpoints) |
| **Ejemplos de peticiones** | `docs/api-spec/ejemplos.md` (13 ejemplos curl) |
| **Guía de ejecución** | `docs/guia-ejecucion.md` |
| **Diagrama de arquitectura** | `docs/diagrama-arquitectura.md` |
| **Descripción de persistencia** | `docs/persistencia.md` |
| **Informe de pruebas detallado** | `docs/informe-pruebas.md` |
| **Guion de demo** | `docs/GUION_DEMO.md` |
| **Roadmap 10 días** | `docs/ROADMAP_10_DAYS.md` |
| **Guía API Gateway** | `docs/API_GATEWAY_GUIDE.md` |
| **Manual afiche municipal** | `docs/MANUAL_AFICHE_MUNICIPAL.md` |
| **Arquitectura extendida** | `docs/ARQUITECTURA_FINAL.md` |

---

## 10. Anexos

### A. Repositorios y URLs

```
Frontend PWA:     https://incendios-valle.pages.dev
API Backend:      https://api.keogh.lat/api
Swagger/OpenAPI:  https://api.keogh.lat/api/docs
Dashboard:        https://dashboard.keogh.lat
GitHub:           https://github.com/RDTmc/incendios-valle
Docker Hub:       https://hub.docker.com/r/[user]/incendios-api
```

### B. Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Frontend | React + TypeScript + Vite | 18 / 5.x / 6.x |
| Backend | Python + FastAPI + uvicorn | 3.11 / 0.115 / |
| Lambdas | Python + boto3 | 3.11 |
| Base datos primaria | DynamoDB (AWS) | — |
| Base datos secundaria | SQLite (WAL mode + busy_timeout) | 3.x |
| Imágenes | S3 (AWS) | — |
| Mensajería | SNS (AWS) | — |
| Dashboard Táctico | Grafana con SQLite datasource | 10.4.8 |
| Dashboard TI | Grafana con Prometheus datasource | 10.4.8 |
| Monitoreo servidor | Prometheus + node_exporter | — |
| Contenedores | Docker + docker-compose | — |
| CI/CD | GitHub Actions (4 workflows) | — |
| Edge/DNS | Cloudflare (DNS-only) | — |
| Mapas | Mapbox GL JS (Strategy Pattern) [16] | 3.24 / 8.x |
| Correo | Mailtrap SMTP | — |
| Testing backend | pytest + pytest-cov | 8.3 / 7.1 |
| Testing frontend | Vitest + Testing Library | 1.6 |

### C. Cómo Reproducir los Tests

```bash
# Backend — todos los tests + cobertura HTML
cd ec2/api && python -m pytest --cov --cov-report=html
# → ec2/api/htmlcov/index.html

# Frontend — todos los tests + cobertura HTML
cd frontend && npm run test:coverage
# → frontend/coverage/index.html

# Lambdas — todos los tests
cd <raíz-proyecto> && python -m pytest lambda/ -v

# Tests completos
cd ec2/api && python -m pytest --cov && cd ../.. && \
cd frontend && npm run test:coverage && cd .. && \
python -m pytest lambda/ -v
```

### D. Archivos de Entrega (ZIP)

El archivo `incendios-valle-entrega.zip` contiene 361 archivos (~81.5 MB) con todo el código fuente, documentación, reportes de cobertura HTML, y especificaciones.

---

## 11. Migración SQLite → RDS PostgreSQL

En julio 2026 se realizó la migración de SQLite (base de datos local embebida en el contenedor FastAPI) a RDS PostgreSQL 15 como parte de la evolución del proyecto hacia producción real.

### Cambios realizados

| Aspecto | Antes (SQLite) | Después (PostgreSQL) |
|---------|---------------|---------------------|
| Motor | SQLite 3 (stdlib Python) | RDS PostgreSQL 15 (db.t3.micro) |
| Conexión | `sqlite3.connect()` directo | `psycopg2.pool.ThreadedConnectionPool` |
| Esquema | Creado vía `CREATE TABLE IF NOT EXISTS` en `init_db()` | DDL PostgreSQL en `init_pg_schema()` |
| Backup | `aws s3 cp incendios.db s3://...` | `pg_dump \| aws s3 cp - s3://...` |
| Grafana datasource | `frser-sqlite-datasource` (lectura directa archivo) | `yesoreyeram-infinity-datasource` (API REST vía endpoints BFF) |

### Estrategia (5 fases)

| Fase | Duración | Descripción |
|------|----------|-------------|
| FASE 1 | 1 día | RDS, Security Group, schema DDL, secrets CI/CD |
| FASE 2 | 1 día | Reconciliación datos huérfanos (DynamoDB → SQLite) |
| FASE 3 | 3 días | Dual-write + migración endpoints API |
| FASE 4 | 3-4 días | Migración Grafana a Infinity + CI/CD Lambdas (opcional) |
| FASE 5 | 2-3 días | Deprecar SQLite, tests, documentación |

### Tablas migradas (10)

`users`, `reports`, `external_reports`, `firms_hotspots`, `weather_readings`, `alerts`, `audit_log`, `notifications`, `admin_2fa`, `incident_resources`

### Deuda técnica documentada

Ver `docs/DEUDA_TECNICA.md` para mejoras futuras: VPC privada, NAT Gateway, ALB, HA, CI/CD completo de Lambdas, WAF, Secrets Manager.

---

## 12. Referencias

[1] FastAPI. *FastAPI Documentation*. 2025. https://fastapi.tiangolo.com

[2] NASA FIRMS. *Fire Information for Resource Management System*. 2025. https://firms.modaps.eosdis.nasa.gov

[3] Jones, M., Bradley, J., Sakimura, N. *JSON Web Token (JWT) RFC 7519*. IETF, 2015 (actualizado 2024). https://datatracker.ietf.org/doc/html/rfc7519

[4] OWASP Foundation. *Authentication Cheat Sheet*. 2025. https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

[5] Grafana Labs. *Grafana SQLite Datasource — frser-sqlite-datasource*. 2025. https://grafana.com/grafana/plugins/frser-sqlite-datasource/

[6] Corporación Nacional Forestal (CONAF). *Estadísticas Históricas de Incendios Forestales*. Chile, 2025. https://www.conaf.cl/incendios-forestales/

[7] Meta Platforms / React Team. *React v18 Documentation*. 2025. https://react.dev

[8] Microsoft. *TypeScript Documentation*. 2025. https://www.typescriptlang.org/docs/

[9] MDN Web Docs / Mozilla. *Progressive Web Apps*. 2025. https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps

[10] Docker Inc. *Docker Documentation*. 2025. https://docs.docker.com/

[11] GitHub. *GitHub Actions Documentation*. 2025. https://docs.github.com/en/actions

[12] Amazon Web Services. *Amazon DynamoDB Developer Guide*. 2025. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/

[13] Cloudflare. *Cloudflare DNS Documentation*. 2025. https://developers.cloudflare.com/dns/

[14] OpenWeatherMap. *Weather API Documentation*. 2025. https://openweathermap.org/api

[15] Amazon Web Services. *Amazon Simple Storage Service (S3) User Guide*. 2025. https://docs.aws.amazon.com/s3/

[16] Mapbox. *Mapbox GL JS Documentation*. 2025. https://docs.mapbox.com/mapbox-gl-js/

[17] pytest Team. *pytest Documentation*. 2025. https://docs.pytest.org/

[18] SonarSource. *SonarCloud Documentation*. 2025. https://docs.sonarsource.com/sonarcloud/

[19] Amazon Web Services. *AWS Lambda Developer Guide*. 2025. https://docs.aws.amazon.com/lambda/latest/dg/

[20] OWASP Foundation. *Cross-Origin Resource Sharing (CORS) Cheat Sheet*. 2025. https://cheatsheetseries.owasp.org/cheatsheets/Cross-Origin_Resource_Sharing_Cheat_Sheet.html

[21] Amazon Web Services. *Amazon Simple Notification Service (SNS)*. 2025. https://aws.amazon.com/sns/

[22] National Weather Service / NOAA. *Fire Weather Forecast*. 2025. https://www.weather.gov/fire/

[23] Prometheus Authors / CNCF. *Prometheus Monitoring Documentation*. 2025. https://prometheus.io/docs/

[24] SQLite Consortium. *Write-Ahead Logging in SQLite*. 2025. https://www.sqlite.org/wal.html

[25] Tailwind Labs. *Tailwind CSS Documentation*. 2025. https://tailwindcss.com/docs

[26] Vite Team. *Vite Documentation*. 2025. https://vitejs.dev/guide/

[27] Vitest Team. *Vitest Documentation*. 2025. https://vitest.dev/guide/

---

*Documento generado a partir de la documentación del proyecto. Junio 2026.*

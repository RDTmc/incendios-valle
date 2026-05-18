# 📜 MANIFIESTO — ROADMAP OFICIAL
## Plataforma Inteligente de Gestión de Incendios — Valle del Sol

**Tipo:** Proyecto Académico (AWS Academy Learner Lab)  
**Fecha:** 17 de Mayo 2026  
**Estado:** Fase de Auditoría Completa → Fase de Refactorización  
**Restricción Crítica:** Laboratorio se reinicia cada 4 horas

---

## 📊 Resumen de Auditoría

| Categoría | Bugs | Faltantes | Hallazgos Infra |
|-----------|------|-----------|-----------------|
| Backend/API | 11 | 2 | - |
| Infra/Docker | 18 | 3 | 4 (H-001 a H-006) |
| Lambda | 21 | 1 | 1 (H-006) |
| Frontend | 21 | 3 | - |
| Cloudflare | 14 | 0 | 1 (H-004) |
| AWS/Grafana | 3 | 1 | 2 (H-001, H-003) |
| **TOTAL** | **88 bugs** | **13 faltantes** | **6 hallazgos** |

---

## 🔍 Hallazgos Críticos de Infraestructura

| ID | Hallazgo | Impacto | Solución |
|----|---------|---------|----------|
| H-001 | **Grafana SQLite Bridge** no instalado persistentemente | Grafana no puede leer SQLite tras cada reinicio de contenedor | Agregar `GF_INSTALL_PLUGINS=frser-sqlite-datasource` en `docker-compose.yml` |
| H-002 | **API Gateway para Lambdas** no validado | Lambdas no son accesibles externamente | Verificar tras congelar backend |
| H-003 | **GSI en DynamoDB** (`email-index`, `user-index`) no verificados | Queries de login/reports fallan si índices no existen | Verificar en AWS Console → documentar en backlog |
| H-004 | **Elastic IP cambia cada reinicio** de AWS Academy | Worker y Pages Functions apuntan a IP muerta | Evaluar Cloudflare Tunnels o script de auto-actualización |
| H-005 | **SQLite pierde datos** al recrear contenedor | Bind mount `/home/ec2-user/incendios-data` puede no persistir | Verificar permisos y path correcto en EC2 |
| H-006 | **AWS Session Token rota cada 4h** en Lambdas también | Lambdas pierden acceso a DynamoDB tras reinicio | Configurar IAM role en Lambda o inyectar credenciales dinámicamente |

---

## 🔄 Modelo de Trabajo

```
TÚ (Manual)                              YO (Código)
─────────────                            ─────────────
✅ SSH a EC2                             ✅ Generar código corregido
✅ AWS Console (Lambda, DynamoDB, GSI)   ✅ Git commits + push
✅ Docker commands en EC2                ✅ Refactor de archivos
✅ Smoke tests con curl                  ✅ Actualizar documentación
✅ Verificar bind mounts                 ✅ Crear scripts de infra
```

### Reglas de Ejecución

1. **Una tarea a la vez** — no avanzamos hasta validar
2. **Tú ejecutas en AWS/SSH** — yo genero código
3. **Commits atómicos** — cada fix tiene su commit
4. **Smoke test obligatorio** — curl o browser por cada cambio
5. **NO saltar de fase** hasta validar la anterior

---

## FASE 0: Estabilización Inmediata (1-2 días)
**Objetivo:** Sistema funcional end-to-end para demostración

| ID | Tarea | Archivos/Infra | Responsable | Validación |
|----|-------|----------------|-------------|------------|
| P0-1 | Crear Lambda Réplica + DynamoDB Stream | `lambda/replica/app.py` + AWS Console | Yo: código / Tú: Stream | Datos fluyen a SQLite |
| P0-2 | Endpoint `/api/focos-activos` | `main.py` | Yo | `curl` retorna focos reales |
| P0-3 | Seed script (usuario admin) | `ec2/api/seed.py` | Tú (SSH) | Login funciona |
| P0-4 | Credenciales AWS dinámicas | `docker-compose.yml` | Tú (SSH) + Yo (código) | Sin `NoCredentialsError` |
| P0-5 | Fix doble stripping path | `functions/api/[[path]].js` | Yo | `curl POST /api/login` → 200 |
| P0-6 | Persistencia SQLite en EC2 | Verificar bind mounts en EC2 | Tú (SSH) | Datos sobreviven restart |
| P0-7 | Verificar GSI en DynamoDB | AWS Console: `email-index`, `user-index` | Tú | Queries de login funcionan |
| P0-8 | Instalar Grafana SQLite plugin | `docker-compose.yml` → `GF_INSTALL_PLUGINS` | Tú (SSH) + Yo (código) | Grafana lee SQLite |

---

## FASE 1: Seguridad Crítica (2-3 días)

| ID | Tarea | Archivos | Responsable |
|----|-------|----------|-------------|
| P1-1 | bcrypt reemplaza sha256 | `main.py`, `lambda/usuarios/app.py` | Yo |
| P1-2 | Secrets dinámicos JWT/SYNC | `docker-compose.yml`, `.env` | Yo + Tú |
| P1-3 | Grafana password segura | `docker-compose.yml` | Tú |
| P1-4 | CORS restrictivo Worker | `cloudflare-worker.js` | Yo |
| P1-5 | Rate limiting Worker | `cloudflare-worker.js` | Yo |

---

## FASE 2: Robustez del Backend (2-3 días)

| ID | Tarea | Archivos | Responsable |
|----|-------|----------|-------------|
| P2-1 | DynamoDB por request (no módulo) | `main.py` | Yo |
| P2-2 | Try/except en endpoints DynamoDB | `main.py` | Yo |
| P2-3 | Fix `ExpressionAttributeNames=None` | `main.py` | Yo |
| P2-4 | Healthcheck robusto | `Dockerfile`, `main.py` | Yo |
| P2-5 | `datetime.utcnow()` → `utc` | `main.py`, Lambdas | Yo |
| P2-6 | Script auto-actualización IP | `ec2/setup.sh` (actualiza Worker/Pages) | Yo + Tú |
| P2-7 | IAM Role para Lambdas | AWS Console o SAM template | Tú |

---

## FASE 3: Frontend Funcional (2-3 días)

| ID | Tarea | Archivos | Responsable |
|----|-------|----------|-------------|
| P3-1 | Persistencia sesión (localStorage) | `App.tsx` | Yo |
| P3-2 | Fix `res.json()` en errores | `api.ts` | Yo |
| P3-3 | Confirmación real con datos | `Confirmacion.tsx` | Yo |
| P3-4 | MapaFocos con datos reales | `MapaFocos.tsx` + endpoint | Yo |
| P3-5 | Role-based routing | `App.tsx` | Yo |
| P3-6 | Eliminar navegación demo | `Login.tsx` | Yo |

---

## FASE 4: Infraestructura como Código (1-2 días)

| ID | Tarea | Archivos | Responsable |
|----|-------|----------|-------------|
| P4-1 | `requirements.txt` con versiones | `ec2/api/`, `lambda/*/` | Yo |
| P4-2 | Dockerfile multi-stage + HEALTHCHECK | `ec2/api/Dockerfile` | Yo |
| P4-3 | `setup.sh` para EC2 post-reinicio | `ec2/setup.sh` | Yo |
| P4-4 | SAM template para Lambdas | `lambda/template.yml` | Yo |
| P4-5 | Eliminar Pages Functions duplicado | `functions/api/` | Yo |
| P4-6 | API Gateway config | AWS Console o SAM | Tú |

---

## FASE 5: Grafana Dashboard (1 día)

| ID | Tarea | Archivos | Responsable |
|----|-------|----------|-------------|
| P5-1 | Provisioning dashboards JSON | `ec2/grafana-provisioning/dashboards/` | Tú + Yo |
| P5-2 | Dashboard: Reportes por estado/tipo | UI Grafana → export JSON | Tú |
| P5-3 | Dashboard: Mapa de calor geográfico | UI Grafana → export JSON | Tú |

---

## FASE 6: Features Pendientes (opcional)

| ID | Tarea | Archivos | Responsable |
|----|-------|----------|-------------|
| P6-1 | Upload fotos S3 | `Reporte.tsx` + endpoint | Yo + Tú |
| P6-2 | Panel Admin | `frontend/src/pages/AdminPanel.tsx` | Yo |
| P6-3 | Perfil usuario | `frontend/src/pages/Perfil.tsx` | Yo |

---

## 📋 Archivos Auditados

| # | Archivo | Bugs | Críticos |
|---|---------|------|----------|
| 1 | `ec2/api/main.py` | 11 | 2 |
| 2 | `ec2/api/Dockerfile` | 7 | 1 |
| 3 | `ec2/docker-compose.yml` | 11 | 3 |
| 4 | Cloudflare Worker | 9 | 2 |
| 5 | `ec2/nginx/nginx.conf` | 8 | 3 |
| 6 | `ec2/grafana-provisioning/datasources/datasource.yml` | 3 | 1 |
| 7 | `lambda/usuarios/app.py` | 10 | 2 |
| 8 | `lambda/ms-incidencias/app.py` | 11 | 1 |
| 9 | `frontend/src/api.ts` | 5 | 0 |
| 10 | `frontend/src/App.tsx` | 4 | 2 |
| 11 | `frontend/src/pages/Login.tsx` | 3 | 0 |
| 12 | `frontend/src/pages/Reporte.tsx` | 3 | 1 |
| 13 | `frontend/src/pages/Historial.tsx` | 3 | 0 |
| 14 | `frontend/src/pages/MapaFocos.tsx` | 3 | 0 |
| 15 | `frontend/src/pages/Confirmacion.tsx` | 3 | 0 |
| 16 | `frontend/vite.config.ts` | 3 | 0 |
| 17 | `frontend/functions/api/[[path]].js` | 5 | 1 |

---

## 📝 Notas de Ejecución

- **AWS Academy:** Credenciales rotan cada 4 horas → todo debe ser dinámico
- **Elastic IP:** Cambia cada reinicio → usar Cloudflare Tunnels o script auto-actualización
- **Grafana:** Plugin debe instalarse vía `GF_INSTALL_PLUGINS` en docker-compose
- **Lambdas:** Requieren IAM role o credenciales inyectadas dinámicamente
- **Bind mounts:** Verificar que `/home/ec2-user/incendios-data` persiste correctamente

---

**Documento versionado para trazabilidad completa del proyecto académico.**

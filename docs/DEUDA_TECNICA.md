# Deuda Técnica — Mejoras para Producción Real

Documento de hoja de ruta para evolucionar el proyecto actual (académico, AWS Academy Lab) hacia una arquitectura de producción real.

---

## 1. Topología de Red (VPC)

**Problema actual:** La instancia EC2 está en una subnet pública por limitaciones de presupuesto del AWS Academy Lab ($50). No hay NAT Gateway (~$32/mes) ni Application Load Balancer (~$22/mes).

**Riesgo:** Exposición directa de la instancia a internet (mitigado por Security Groups restrictivos + API Gateway como única puerta de entrada).

| Componente | Actual | Producción real |
|-----------|--------|----------------|
| EC2 (FastAPI) | Subnet pública | Subnet privada |
| RDS PostgreSQL | Subnet pública (con SG restrictivo) | Subnet privada |
| NAT Gateway | ❌ No (~$32/mes) | ✅ Sí |
| Application Load Balancer | ❌ No (~$22/mes) | ✅ Sí |
| API Gateway | Público | Privado (VPC Link) o ALB |

**Solución propuesta:**
```
VPC:
  ├── Subnet Pública:  Internet Gateway → ALB (solo puerto 443)
  ├── Subnet Pública:  NAT Gateway (salida a internet)
  └── Subnet Privada:  EC2 + RDS (sin IP pública)
                        Salida a internet vía NAT Gateway
```

**Costo adicional estimado en producción:** ~$54-64/mes.

---

## 2. Alta Disponibilidad

**Problema actual:** Single point of failure en todos los componentes.

| Componente | Actual | Producción real |
|-----------|--------|----------------|
| EC2 | 1 instancia t3.micro | Auto Scaling Group (mín. 2) |
| RDS | 1 instancia Single-AZ | Multi-AZ con réplica síncrona |
| Docker | Single host | ECS Fargate o EKS |

**Solución propuesta:**
- Auto Scaling Group con mín. 2 instancias EC2
- RDS Multi-AZ (réplica automática en diferente AZ)
- Sesiones: ya es stateless (JWT), no se requiere sticky sessions

---

## 3. Monitoreo y Alertas

**Problema actual:** Sin alarmas automáticas. Solo dashboards Grafana con refresco manual.

**Solución propuesta:**
- CloudWatch Alarms para CPU/RAM EC2 (>80% → SNS)
- CloudWatch Alarms para Conexiones RDS (>100 → SNS)
- AWS X-Ray para tracing distribuido (API Gateway → EC2 → RDS)
- Dashboard unificado en Grafana con fuentes: Prometheus (métricas) + RDS (datos de negocio)

---

## 4. CI/CD Completo

**Problema actual:** Lambdas y Cloudflare Worker se deployan manualmente.

| Componente | Actual | Producción real |
|-----------|--------|----------------|
| `upload-proxy` (Lambda) | Manual (zip + AWS Console) | ✅ GitHub Actions |
| `worker.js` (Cloudflare) | Manual (Cloudflare Dashboard) | ✅ GitHub Actions + Cloudflare API token |
| Infraestructura | Manual (AWS Console) | AWS CDK o Terraform |

**Solución propuesta:**
- SAM o AWS CDK para infraestructura como código
- Pipeline CI/CD unificado que deploye: API (Docker), Lambdas (zip), Worker (Cloudflare API), dashboards (provisioning)
- Despliegue blue/green para la API

---

## 5. Seguridad

**Problema actual:**

| Hallazgo | Severidad | Solución |
|----------|-----------|----------|
| EC2 en subnet pública | Alta | VPC privada + NAT Gateway + ALB |
| JWT_SECRET de 15 chars | Media | 32+ bytes (HMAC-SHA256) |
| Sin WAF | Media | AWS WAF frente a API Gateway |
| Sin Secrets Manager | Baja | AWS Secrets Manager para todas las credenciales |
| Sin VPC Flow Logs | Baja | VPC Flow Logs + GuardDuty |

---

## 6. Performance y Escalabilidad

**Problema actual:**

| Aspecto | Actual | Límite |
|---------|--------|--------|
| Conexiones DB | Sin pool (sqlite3.connect cada request) | ThreadedConnectionPool con PostgreSQL |
| Cache | Sin cache | Redis ElastiCache para endpoints públicos frecuentes |
| Tamaño de instancia | t3.micro (1 vCPU, 1 GB RAM) | t3.medium o superior |

**Solución propuesta:**
- Implementar caché Redis para endpoints tipo `/public/dashboard-stats`
- Connection pooling con `psycopg2.pool.ThreadedConnectionPool`
- Migrar a t3.small o t3.medium si la carga lo requiere

---

## Prioridad de implementación

| Prioridad | Mejora | Esfuerzo | Dependencias |
|-----------|--------|----------|-------------|
| 🔴 Alta | VPC privada + NAT Gateway | 2-3 días | Presupuesto |
| 🔴 Alta | CI/CD Lambdas | 1 día | GitHub Secrets |
| 🟡 Media | WAF + Secrets Manager | 1 día | — |
| 🟡 Media | Connection Pooling | 0.5 días | PostgreSQL ya implementado |
| 🟢 Baja | Multi-AZ RDS | 1 día | Presupuesto |
| 🟢 Baja | Auto Scaling EC2 | 2 días | AMI + Load Balancer |
| 🟢 Baja | Redis Cache | 1 día | — |
| 🟢 Baja | X-Ray Tracing | 1 día | — |

---

*Documento generado durante la migración SQLite → PostgreSQL (Junio-Julio 2026).*

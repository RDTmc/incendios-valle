# Guión de Demostración — Incendios Valle del Sol

## 1. PERSISTENCIA DE DATOS (Arquitectura de almacenamiento)

### Concepto: Bind Mount (Docker → Disco EBS)

El sistema usa **bind mounts** de Docker. Esto es un mapeo directo entre una carpeta del disco de la instancia EC2 (EBS) y una carpeta dentro del contenedor.

```yaml
volumes:
  - /home/ec2-user/incendios-data/grafana:/var/lib/grafana
```

- **Izquierda** (`/home/ec2-user/incendios-data/grafana`): está en el **disco EBS** de la EC2
- **Derecha** (`/var/lib/grafana`): es la carpeta interna del contenedor donde Grafana escribe sus datos

### ¿Qué sobrevive?

| Evento | ¿El dato persiste? | Explicación |
|--------|-------------------|-------------|
| Reinicio del contenedor | ✅ Sí | El bind mount apunta al disco, no al contenedor |
| Recrear contenedor (`docker-compose up --force-recreate`) | ✅ Sí | El disco EBS no se elimina |
| Reboot o stop/start de la instancia EC2 | ✅ Sí | EBS persiste aunque la instancia se apague |
| Terminar (terminate) la EC2 | ❌ No | El EBS root se elimina con la instancia |

### Analogía útil para la presentación

> *Es como particionar un disco duro: instalas el sistema en C: pero dejas un volumen de respaldo en D:. El contenedor es el sistema operativo, el bind mount es el volumen D:. Si formateas C: (eliminas el contenedor), D: sigue intacto.*

### Backup a S3 (protección contra terminate)

En cada deploy se respalda automáticamente:

```bash
aws s3 cp /home/ec2-user/incendios-data/grafana/grafana.db \
  s3://incendios-valle-sol/backups/grafana-latest.db
```

Y se restaura desde S3 si es necesario.

### ¿Por qué antes se perdían los cambios en Grafana?

No era por el volumen (ese siempre fue persistente). Era porque el CI/CD:

1. Sincronizaba archivos de **provisioning** (`dashboard_incendios.json`) desde Git a la EC2 (vía SCP)
2. Recreaba el contenedor de Grafana (`force-recreate`)
3. Al iniciar, Grafana **re-aplicaba** los JSON de provisioning, sobrescribiendo cualquier cambio hecho desde la UI

**Solución**: Separar provisioning inicial de cambios UI, y no recrear Grafana si no cambió el provisioning.

### Lección aprendida: .env corrupto y DB readonly

**Problema 1 — `.env` corrupto**: `grep MAILTRAP_SENDER` sin ancla `^` también matcheaba `MAILTRAP_SENDER_NAME`. Al devolver 2 líneas, `cut -d'=' -f2` producía un string con `\n` (2 valores). El heredoc expandía ese `\n` como una línea sin `KEY=VALUE`, rompiendo `docker-compose`.

**Solución**: `grep ^KEY=` (anclado) + heredoc `cat > .env <<EOF` en vez de múltiples `echo >>`.

**Problema 2 — Grafana 500 "readonly database"**: `refresh_api.sh` respaldaba `grafana.db` a S3 y luego lo restauraba en el mismo deploy. Si la copia en S3 estaba corrupta (permisos, schema viejo), se reintroducía en cada ciclo.

**Solución**: Solo backup a S3, nunca restore automático de `grafana.db`. La DB persiste en el bind mount EBS.

---

## 2. FLUJO DE DATOS

## 2. FLUJO DE DATOS

*[Completar más adelante]*

## 3. ESCENARIOS DE DEMOSTRACIÓN

*[Completar más adelante]*

## 4. PREGUNTAS FRECUENTES (posibles preguntas de la audiencia)

*[Completar más adelante]*

# Test Events para AWS Lambda Console

## Cómo usar

1. Ir a **AWS Console > Lambda > [nombre-función]**
2. Click en **Test** (dropdown junto al botón "Test")
3. **Configure test event** > **Create new test event**
4. Template: **JSON**
5. Copiar el contenido del event array correspondiente
6. **Name**: usar el `name` del JSON
7. **Save**
8. Click **Test**

## Eventos disponibles

| Archivo | Función Lambda | Events |
|---------|---------------|--------|
| `upload_proxy.json` | `upload-proxy` | 2 (JPEG, PNG) |
| `usuarios.json` | `ms-usuarios` | 4 (login, register, get user, auth) |
| `incidencias.json` | `ms-incidencias` | 5 (list, filter, get, create, update) |
| `notificaciones.json` | `ms-notificaciones` | 3 (alert, info, empty) |
| `sns-to-grafana.json` | `sns-to-grafana` | 2 (annotation, malformed) |

## Notas

- Algunos eventos requieren IDs reales (usuarios, reportes). Reemplazar `REEMPLAZAR_CON_*` con valores existentes en DynamoDB.
- `sns-to-grafana` y `notificaciones` dependen de recursos reales (Grafana, SNS).
- `upload-proxy` requiere que la Lambda tenga permisos para escribir en S3.

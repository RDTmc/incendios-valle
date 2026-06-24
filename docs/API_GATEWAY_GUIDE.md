# Guía de Creación Manual de API Gateway

## Validación Previa
✅ `apigateway:*` permisos disponibles vía LabRole
✅ `create-rest-api` probado exitosamente
✅ `delete-rest-api` probado exitosamente

## Paso 1: Crear API REST

### Opción A: AWS Console (Recomendada para configuración visual)

1. Ir a **API Gateway** → **Create API** → **REST API (not HTTP)** → **Build**
2. Configurar:
   - **API name**: `Incendios-Valle-API`
   - **Endpoint Type**: `Regional`
   - **API Key Source**: `HEADER`
3. Click **Create API**

### Opción B: AWS CLI

```bash
API_ID=$(aws apigateway create-rest-api \
  --name "Incendios-Valle-API" \
  --description "API Gateway para plataforma de incendios" \
  --endpoint-configuration "types=REGIONAL" \
  --query "id" --output text)

echo "API ID: $API_ID"
# Guardar: API_ID = <output>
```

## Paso 2: Obtener ID del Root Resource

```bash
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[?path=='/'].id" \
  --output text)

echo "Root ID: $ROOT_ID"
```

## Paso 3: Crear Recursos (Rutas)

```bash
# /auth - Login y registro
AUTH_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "auth" \
  --query "id" --output text)

# /reports - CRUD reportes
REPORTS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "reports" \
  --query "id" --output text)

# /api - Proxy hacia EC2
API_ID_RES=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "api" \
  --query "id" --output text)

# /api/{proxy+} - Catch-all para EC2 FastAPI
API_PROXY=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $API_ID_RES \
  --path-part "{proxy+}" \
  --query "id" --output text)

# /upload - Subida de imágenes
UPLOAD_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "upload" \
  --query "id" --output text)

# /alerts - Sistema de alertas
ALERTS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "alerts" \
  --query "id" --output text)
```

## Paso 4: Configurar Métodos

### 4a. Gateway EC2 FastAPI (proxy HTTP)
```bash
# ANY /api/{proxy+} → EC2 Nginx
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $API_PROXY \
  --http-method ANY \
  --authorization-type "NONE" \
  --no-api-key-required

# Integration HTTP proxy to EC2
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $API_PROXY \
  --http-method ANY \
  --type HTTP_PROXY \
  --integration-http-method ANY \
  --uri "http://3.227.186.158/api/{proxy}" \
  --request-parameters "integration.request.path.proxy=method.request.path.proxy"

# ANY /api → EC2 Nginx (raíz)
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $API_ID_RES \
  --http-method ANY \
  --authorization-type "NONE" \
  --no-api-key-required

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $API_ID_RES \
  --http-method ANY \
  --type HTTP_PROXY \
  --integration-http-method ANY \
  --uri "http://3.227.186.158/api"
```

### 4b. Gateway Lambda Usuarios (auth)
```bash
# Obtener ARN de Lambda usuarios (si existe)
LAMBDA_USUARIOS_ARN=$(aws lambda get-function \
  --function-name "ms-usuarios" \
  --query "Configuration.FunctionArn" \
  --output text 2>/dev/null || echo "")

# POST /auth → Lambda Usuarios
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $AUTH_ID \
  --http-method POST \
  --authorization-type "NONE" \
  --no-api-key-required

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $AUTH_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_USUARIOS_ARN/invocations"

# Agregar permiso a Lambda
aws lambda add-permission \
  --function-name "ms-usuarios" \
  --statement-id "api-gateway-auth" \
  --action "lambda:InvokeFunction" \
  --principal "apigateway.amazonaws.com" \
  --source-arn "arn:aws:execute-api:us-east-1:887513569063:$API_ID/*/POST/auth"
```

### 4c. Gateway Upload (Lambda existente)
```bash
LAMBDA_UPLOAD_ARN="arn:aws:lambda:us-east-1:887513569063:function:upload-proxy"

# POST /upload
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $UPLOAD_ID \
  --http-method POST \
  --authorization-type "NONE"

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $UPLOAD_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_UPLOAD_ARN/invocations"

aws lambda add-permission \
  --function-name "upload-proxy" \
  --statement-id "api-gateway-upload" \
  --action "lambda:InvokeFunction" \
  --principal "apigateway.amazonaws.com" \
  --source-arn "arn:aws:execute-api:us-east-1:887513569063:$API_ID/*/POST/upload"
```

## Paso 5: Configurar CORS

```bash
# OPTIONS en cada recurso para CORS
for RES_ID in $AUTH_ID $REPORTS_ID $API_ID_RES $API_PROXY $UPLOAD_ID $ALERTS_ID; do
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RES_ID \
    --http-method OPTIONS \
    --authorization-type "NONE"

  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RES_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false"

  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RES_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\":200}"}'

  aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RES_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters "method.response.header.Access-Control-Allow-Headers='Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',method.response.header.Access-Control-Allow-Methods='GET,POST,PUT,DELETE,OPTIONS',method.response.header.Access-Control-Allow-Origin='https://incendios-valle.pages.dev'"
done
```

## Paso 6: Desplegar API

```bash
# Crear stage "prod"
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name "prod" \
  --stage-description "Producción" \
  --variables "ec2Url=http://3.227.186.158"

# Obtener URL base de la API
echo "API URL: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod/"
```

## Paso 7: Rate Limiting y Throttling

```bash
# Configurar throttling en stage
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name "prod" \
  --patch-operations "op=replace,path=/*/*/throttling/rateLimit,value=1000" \
  "op=replace,path=/*/*/throttling/burstLimit,value=500"
```

## Paso 8: CloudWatch Logging

```bash
# Habilitar CloudWatch logs
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name "prod" \
  --patch-operations "op=replace,path=/*/*/logging/loglevel,value=INFO" \
  "op=replace,path=/*/*/logging/dataTrace,value=true" \
  "op=replace,path=/*/*/metrics/enabled,value=true"
```

## Paso 9: Actualizar Frontend para usar API Gateway

En `frontend/src/api.ts`, cambiar:
```typescript
// const API_URL = import.meta.env.VITE_API_URL || 'https://api.keogh.lat/api'
const API_URL = 'https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/api'
```

## Estructura Final de Rutas

```
https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/
  ├── POST /auth          → Lambda Usuarios (login/register)
  ├── GET  /auth/{id}     → Lambda Usuarios (profile)
  ├── POST /reports       → Lambda Incidencias
  ├── GET  /reports       → Lambda Incidencias
  ├── GET  /reports/{id}  → Lambda Incidencias
  ├── ANY  /api           → EC2 Nginx → FastAPI (proxy)
  ├── ANY  /api/{proxy+}  → EC2 Nginx → FastAPI (proxy)
  ├── POST /upload        → Lambda upload-proxy
  └── POST /alerts        → Lambda Notificaciones
```

## Notas Importantes

1. **LabRole timeout**: La sesión AWS Academy expira cada 4h. Si expira, API Gateway deja de funcionar para las integraciones Lambda (el EC2 proxy HTTP sigue funcionando mientras EC2 esté activa)
2. **NO VPC Link**: LabRole no permite VPC Link. Usamos integración HTTP proxy directa a la IP pública del EC2
3. **Permisos Lambda**: Cada integración con Lambda necesita `aws lambda add-permission` para que API Gateway pueda invocarla
4. **CORS**: API Gateway no pasa headers CORS automáticamente. Hay que configurar manualmente en cada recurso
5. **Cloudflare**: Si queremos mantener `api.keogh.lat` → solo apuntar el DNS a la URL de API Gateway en vez de al EC2 directo

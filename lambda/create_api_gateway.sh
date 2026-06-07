#!/bin/bash
set -euo pipefail
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
EC2_IP="3.227.186.158"

echo "=== Creando API Gateway REST ==="

API_ID=$(aws apigateway create-rest-api \
    --name "Incendios-Valle-API" \
    --description "API Gateway para plataforma de incendios" \
    --endpoint-configuration "types=REGIONAL" \
    --region "$REGION" --query "id" --output text)
echo "API ID: $API_ID"

ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$REGION" --query "items[?path=='/'].id" --output text)
echo "Root ID: $ROOT_ID"

echo ""
echo "=== Creando recursos ==="

AUTH_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$ROOT_ID" --path-part "auth" --region "$REGION" --query "id" --output text)
echo "auth: $AUTH_ID"

REPORTS_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$ROOT_ID" --path-part "reports" --region "$REGION" --query "id" --output text)
echo "reports: $REPORTS_ID"

REPORT_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$REPORTS_ID" --path-part "{id}" --region "$REGION" --query "id" --output text)
echo "reports/{id}: $REPORT_ID"

API_RES_ROOT=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$ROOT_ID" --path-part "api" --region "$REGION" --query "id" --output text)
echo "api: $API_RES_ROOT"

API_PROXY_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$API_RES_ROOT" --path-part "{proxy+}" --region "$REGION" --query "id" --output text)
echo "api/{proxy+}: $API_PROXY_ID"

UPLOAD_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$ROOT_ID" --path-part "upload" --region "$REGION" --query "id" --output text)
echo "upload: $UPLOAD_ID"

ALERTS_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" --parent-id "$ROOT_ID" --path-part "alerts" --region "$REGION" --query "id" --output text)
echo "alerts: $ALERTS_ID"

echo ""
echo "=== Configurando métodos: Lambda auth ==="
# POST /auth → ms-usuarios
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$AUTH_ID" --http-method POST --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$AUTH_ID" --http-method POST \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:ms-usuarios/invocations" \
    --region "$REGION"

echo ""
echo "=== Configurando métodos: Lambda incidencias ==="
# POST /reports
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$REPORTS_ID" --http-method POST --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$REPORTS_ID" --http-method POST \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:ms-incidencias/invocations" \
    --region "$REGION"

# GET /reports
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$REPORTS_ID" --http-method GET --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$REPORTS_ID" --http-method GET \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:ms-incidencias/invocations" \
    --region "$REGION"

# GET /reports/{id}
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$REPORT_ID" --http-method GET --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$REPORT_ID" --http-method GET \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:ms-incidencias/invocations" \
    --region "$REGION"

# PUT /reports/{id}
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$REPORT_ID" --http-method PUT --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$REPORT_ID" --http-method PUT \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:ms-incidencias/invocations" \
    --region "$REGION"

echo ""
echo "=== Configurando métodos: EC2 HTTP Proxy ==="
# ANY /api → EC2
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$API_RES_ROOT" --http-method ANY --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$API_RES_ROOT" --http-method ANY \
    --type HTTP_PROXY --integration-http-method ANY \
    --uri "http://${EC2_IP}/api" \
    --region "$REGION"

# ANY /api/{proxy+} → EC2
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$API_PROXY_ID" --http-method ANY --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$API_PROXY_ID" --http-method ANY \
    --type HTTP_PROXY --integration-http-method ANY \
    --uri "http://${EC2_IP}/api/{proxy}" \
    --request-parameters "integration.request.path.proxy=method.request.path.proxy" \
    --region "$REGION"

echo ""
echo "=== Configurando métodos: Lambda upload ==="
# POST /upload → upload-proxy
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$UPLOAD_ID" --http-method POST --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$UPLOAD_ID" --http-method POST \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:upload-proxy/invocations" \
    --region "$REGION"

echo ""
echo "=== Configurando métodos: Lambda notificaciones ==="
# POST /alerts → ms-notificaciones
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$ALERTS_ID" --http-method POST --authorization-type "NONE" --region "$REGION"
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$ALERTS_ID" --http-method POST \
    --type AWS_PROXY --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:ms-notificaciones/invocations" \
    --region "$REGION"

echo ""
echo "=== Configurando CORS ==="
for RES_ID in $AUTH_ID $REPORTS_ID $REPORT_ID $API_RES_ROOT $API_PROXY_ID $UPLOAD_ID $ALERTS_ID; do
    aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$RES_ID" --http-method OPTIONS --authorization-type "NONE" --region "$REGION" 2>/dev/null || true
    aws apigateway put-method-response \
        --rest-api-id "$API_ID" --resource-id "$RES_ID" --http-method OPTIONS --status-code 200 \
        --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" \
        --region "$REGION" 2>/dev/null || true
    aws apigateway put-integration \
        --rest-api-id "$API_ID" --resource-id "$RES_ID" --http-method OPTIONS \
        --type MOCK --request-templates '{"application/json":"{\"statusCode\":200}"}' \
        --region "$REGION" 2>/dev/null || true
    aws apigateway put-integration-response \
        --rest-api-id "$API_ID" --resource-id "$RES_ID" --http-method OPTIONS --status-code 200 \
        --response-parameters "method.response.header.Access-Control-Allow-Headers='Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',method.response.header.Access-Control-Allow-Methods='GET,POST,PUT,DELETE,OPTIONS',method.response.header.Access-Control-Allow-Origin='https://incendios-valle.pages.dev'" \
        --region "$REGION" 2>/dev/null || true
done

echo ""
echo "=== Desplegando API ==="
aws apigateway create-deployment \
    --rest-api-id "$API_ID" --stage-name "prod" \
    --stage-description "Producción" \
    --variables "ec2Url=http://${EC2_IP}" \
    --region "$REGION"

echo ""
echo "=== Permisos para API Gateway -> Lambda ==="
for LAMBDA in "ms-usuarios" "ms-incidencias" "ms-notificaciones" "upload-proxy"; do
    aws lambda add-permission \
        --function-name "$LAMBDA" \
        --statement-id "api-gw-${LAMBDA}" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*" \
        --region "$REGION" 2>/dev/null || echo "   permiso ya existe para $LAMBDA"
done

echo ""
echo "============================================"
echo "  API Gateway lista!"
echo "  URL: https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/"
echo "============================================"
echo ""
echo "Rutas creadas:"
echo "  POST /auth          -> ms-usuarios"
echo "  POST /reports       -> ms-incidencias"
echo "  GET  /reports       -> ms-incidencias"
echo "  GET  /reports/{id}  -> ms-incidencias"
echo "  PUT  /reports/{id}  -> ms-incidencias"
echo "  ANY  /api           -> EC2 (HTTP proxy)"
echo "  ANY  /api/{proxy+}  -> EC2 (HTTP proxy)"
echo "  POST /upload        -> upload-proxy"
echo "  POST /alerts        -> ms-notificaciones"

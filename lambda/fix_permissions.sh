#!/bin/bash
REGION="us-east-1"
ACCOUNT_ID="887513569063"
API_ID="jywf027zj3"

echo "=== Corrigiendo permisos Lambda para API Gateway ==="

# Remover permisos existentes demasiado amplios
for LAMBDA in "ms-usuarios" "ms-incidencias" "ms-notificaciones" "upload-proxy"; do
    aws lambda remove-permission \
        --function-name "$LAMBDA" \
        --statement-id "api-gw-${LAMBDA}" \
        --region "$REGION" 2>/dev/null || true
done

# Agregar permisos específicos por ruta
# auth -> POST /auth
aws lambda add-permission \
    --function-name "ms-usuarios" \
    --statement-id "api-gw-auth" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/POST/auth" \
    --region "$REGION" 2>&1

# incidencias -> POST,GET /reports y GET,PUT /reports/*
aws lambda add-permission \
    --function-name "ms-incidencias" \
    --statement-id "api-gw-reports-post" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/POST/reports" \
    --region "$REGION" 2>&1
aws lambda add-permission \
    --function-name "ms-incidencias" \
    --statement-id "api-gw-reports-get" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/GET/reports" \
    --region "$REGION" 2>&1
aws lambda add-permission \
    --function-name "ms-incidencias" \
    --statement-id "api-gw-reports-get-id" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/GET/reports/*" \
    --region "$REGION" 2>&1
aws lambda add-permission \
    --function-name "ms-incidencias" \
    --statement-id "api-gw-reports-put" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/PUT/reports/*" \
    --region "$REGION" 2>&1

# notificaciones -> POST /alerts
aws lambda add-permission \
    --function-name "ms-notificaciones" \
    --statement-id "api-gw-alerts" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/POST/alerts" \
    --region "$REGION" 2>&1

# upload -> POST /upload
aws lambda add-permission \
    --function-name "upload-proxy" \
    --statement-id "api-gw-upload" \
    --action "lambda:InvokeFunction" \
    --principal "apigateway.amazonaws.com" \
    --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/POST/upload" \
    --region "$REGION" 2>&1

echo ""
echo "=== Permisos corregidos ==="

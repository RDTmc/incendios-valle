#!/bin/bash
set -euo pipefail

LAMBDA_ROLE="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/LabRole"
REGION="us-east-1"
S3_BUCKET="incendios-valle-sol"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=== Empaquetando Lambdas ==="

package_lambda() {
    local name=$1
    local dir=$2
    echo "--- $name ($dir) ---"
    cd "$dir"
    [ -f requirements.txt ] && pip install -r requirements.txt -t . --quiet --no-cache-dir 2>/dev/null
    zip -r9 "../${name}.zip" . -x "*.pyc" -x "__pycache__/*" >/dev/null
    cd ..
    echo "   -> ${name}.zip creado"
}

# Limpiar zips anteriores
rm -f lambda-*.zip

# 1. ms-usuarios (auth)
package_lambda "ms-usuarios" "usuarios"

# 2. ms-incidencias (reports)
package_lambda "ms-incidencias" "ms-incidencias"

# 3. ms-notificaciones (SNS alerts)
package_lambda "ms-notificaciones" "ms-notificaciones"

echo ""
echo "=== Creando/Actualizando Lambdas ==="

create_or_update() {
    local name=$1
    local handler=$2
    local zipfile="${name}.zip"
    if aws lambda get-function --function-name "$name" --region "$REGION" >/dev/null 2>&1; then
        echo "--- Actualizando $name ---"
        aws lambda update-function-code \
            --function-name "$name" \
            --zip-file "fileb://$zipfile" \
            --region "$REGION" --no-cli-pager
    else
        echo "--- Creando $name ---"
        aws lambda create-function \
            --function-name "$name" \
            --runtime "python3.11" \
            --role "$LAMBDA_ROLE" \
            --handler "$handler" \
            --zip-file "fileb://$zipfile" \
            --region "$REGION" --no-cli-pager
    fi
}

create_or_update "ms-usuarios" "app.lambda_handler"

create_or_update "ms-incidencias" "app.lambda_handler"

create_or_update "ms-notificaciones" "app.lambda_handler"

echo ""
echo "=== Configurando environment variables ==="

aws lambda update-function-configuration \
    --function-name "ms-usuarios" \
    --environment "Variables={JWT_SECRET=$(grep JWT_SECRET /home/ec2-user/.env | cut -d= -f2)}" \
    --region "$REGION" --no-cli-pager 2>/dev/null || true

aws lambda update-function-configuration \
    --function-name "ms-notificaciones" \
    --environment "Variables={SNS_TOPIC_ARN=arn:aws:sns:us-east-1:${ACCOUNT_ID}:incendios-alerts}" \
    --region "$REGION" --no-cli-pager 2>/dev/null || true

echo ""
echo "=== Permisos API Gateway para invocar Lambdas ==="

add_permission() {
    local name=$1
    local stmt_id=$2
    local api_id=$3
    local path=$4
    aws lambda add-permission \
        --function-name "$name" \
        --statement-id "${stmt_id}" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${api_id}/*/${path}" \
        --region "$REGION" 2>/dev/null || echo "   (permiso ya existe o API ID no disponible)"
}

API_ID=${1:-}
if [ -n "$API_ID" ]; then
    add_permission "ms-usuarios" "api-gw-auth" "$API_ID" "POST/auth"
    add_permission "ms-incidencias" "api-gw-reports" "$API_ID" "POST/reports"
    add_permission "ms-incidencias" "api-gw-reports-get" "$API_ID" "GET/reports"
    add_permission "ms-incidencias" "api-gw-reports-get-id" "$API_ID" "GET/reports/*"
    add_permission "ms-incidencias" "api-gw-reports-put" "$API_ID" "PUT/reports/*"
    add_permission "ms-notificaciones" "api-gw-alerts" "$API_ID" "POST/alerts"
fi

echo ""
echo "=== Lambdas listas ==="
aws lambda list-functions --region "$REGION" --query "Functions[?contains(FunctionName, 'ms-') || contains(FunctionName, 'upload')].[FunctionName,Runtime,Handler]" --output table

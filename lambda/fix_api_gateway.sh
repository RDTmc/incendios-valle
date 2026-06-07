#!/bin/bash
API_ID="jywf027zj3"
PROXY_RES="sqvq4d"
AUTH_ID="37swx8"
REPORTS_ID="eiusi0"
REPORT_ID="r7dt6n"
API_RES_ROOT="wfcov9"
UPLOAD_ID="xyxphc"
ALERTS_ID="fvp26q"
REGION="us-east-1"
ACCOUNT_ID="887513569063"

echo "=== Fix proxy integration ==="
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$PROXY_RES" --http-method ANY \
    --type HTTP_PROXY --integration-http-method ANY \
    --uri "http://3.227.186.158/api/{proxy}" \
    --region "$REGION" --no-cli-pager

echo ""
echo "=== CORS ==="
for RES_ID in $AUTH_ID $REPORTS_ID $REPORT_ID $API_RES_ROOT $PROXY_RES $UPLOAD_ID $ALERTS_ID; do
    echo "CORS on $RES_ID"
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
        --response-parameters "method.response.header.Access-Control-Allow-Headers='"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"',method.response.header.Access-Control-Allow-Methods='"'"'GET,POST,PUT,DELETE,OPTIONS'"'"',method.response.header.Access-Control-Allow-Origin='"'"'https://incendios-valle.pages.dev'"'"'" \
        --region "$REGION" 2>/dev/null || true
done

echo ""
echo "=== Deploy ==="
aws apigateway create-deployment \
    --rest-api-id "$API_ID" --stage-name "prod" \
    --stage-description "Producción" \
    --variables "ec2Url=http://3.227.186.158" \
    --region "$REGION" --no-cli-pager

echo ""
echo "=== Permisos Lambda ==="
for LAMBDA in "ms-usuarios" "ms-incidencias" "ms-notificaciones" "upload-proxy"; do
    aws lambda add-permission \
        --function-name "$LAMBDA" \
        --statement-id "api-gw-${LAMBDA}" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*" \
        --region "$REGION" 2>/dev/null && echo "Permiso concedido: $LAMBDA" || echo "Ya existe: $LAMBDA"
done

echo ""
echo "============================================"
echo "  API Gateway lista!"
echo "  URL: https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/"
echo "============================================"

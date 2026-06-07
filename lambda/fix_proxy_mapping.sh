#!/bin/bash
API_ID="jywf027zj3"
PROXY_RES="sqvq4d"

echo "=== Re-creando integracion proxy con mapeo explicito ==="
aws apigateway put-integration \
    --rest-api-id "$API_ID" --resource-id "$PROXY_RES" --http-method ANY \
    --type HTTP_PROXY --integration-http-method ANY \
    --uri "http://3.227.186.158/api/{proxy}" \
    --request-parameters "integration.request.path.proxy=method.request.path.proxy" \
    --region us-east-1 --no-cli-pager

echo "=== Re-deploy ==="
aws apigateway create-deployment \
    --rest-api-id "$API_ID" --stage-name "prod" \
    --stage-description "Producción" \
    --variables "ec2Url=http://3.227.186.158" \
    --region us-east-1 --no-cli-pager

echo ""
echo "=== Verificando integracion ==="
aws apigateway get-integration \
    --rest-api-id "$API_ID" --resource-id "$PROXY_RES" --http-method ANY \
    --query "{uri:uri,type:type,params:requestParameters}" \
    --region us-east-1 --output json

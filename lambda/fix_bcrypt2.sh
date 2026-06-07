#!/bin/bash
set -euo pipefail
cd /home/ec2-user/usuarios

echo "=== Limpiando dependencias previas incompatibles ==="
rm -rf bcrypt* _bcrypt* PyJWT* jwt* *.dist-info __pycache__ 2>/dev/null || true

echo "=== Instalando bcrypt + PyJWT con imagen Docker Lambda ==="
docker run --rm --entrypoint "" \
  -v /home/ec2-user/usuarios:/var/task \
  public.ecr.aws/lambda/python:3.11 \
  pip install bcrypt PyJWT -t /var/task/ --no-cache-dir 2>&1

echo "=== Verificando que bcrypt se instaló ==="
ls -la bcrypt* _bcrypt* 2>/dev/null || echo "bcrypt NO instalado!"

echo "=== Re-empaquetando ==="
rm -f ../ms-usuarios.zip
zip -r9 ../ms-usuarios.zip . -x "requirements.txt" -x "__pycache__/*" -x "*.pyc" 2>&1 | tail -3

echo "=== Actualizando Lambda ==="
aws lambda update-function-code \
  --function-name ms-usuarios \
  --zip-file "fileb://../ms-usuarios.zip" \
  --region us-east-1 --no-cli-pager 2>&1 | grep -E "FunctionName|CodeSize|State"

echo ""
echo "=== Esperando actualización ==="
aws lambda wait function-updated --function-name ms-usuarios --region us-east-1

echo "=== Probando Lambda directamente ==="
aws lambda invoke --function-name ms-usuarios \
  --payload '{"httpMethod":"POST","path":"/login","body":"{\"email\":\"test@test.com\",\"password\":\"test\"}"}' \
  --region us-east-1 /tmp/lambda_response.json 2>&1 && cat /tmp/lambda_response.json

echo ""
echo "=== Listo ==="

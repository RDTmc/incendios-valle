#!/bin/bash
set -euo pipefail
REGION="us-east-1"

echo "=== Re-empaquetando ms-usuarios con bcrypt compatible Lambda ==="

cd /home/ec2-user/usuarios

# Limpiar dependencias instaladas de AL2023 (incompatibles)
rm -rf bcrypt* bcrypt _bcrypt* *.dist-info 2>/dev/null || true

# Usar Docker con la imagen oficial Lambda Python 3.11 para instalar bcrypt
echo "--- Instalando bcrypt en entorno Lambda (Amazon Linux 2 / GLIBC correcto) ---"
docker run --rm -v "$(pwd):/var/task" public.ecr.aws/lambda/python:3.11 \
    pip install bcrypt PyJWT -t /var/task/ --no-cache-dir 2>&1 | tail -5

# Re-empaquetar solo los archivos necesarios (sin boto3 que ya viene en Lambda)
echo "--- Re-empaquetando zip ---"
rm -f ../ms-usuarios.zip
zip -r9 ../ms-usuarios.zip app.py bcrypt* _bcrypt* PyJWT* jwt* *.dist-info 2>/dev/null

# Subir a Lambda
echo "--- Actualizando Lambda ms-usuarios ---"
aws lambda update-function-code \
    --function-name ms-usuarios \
    --zip-file "fileb://../ms-usuarios.zip" \
    --region "$REGION" --no-cli-pager

echo ""
echo "--- Verificando ---"
aws lambda wait function-updated \
    --function-name ms-usuarios \
    --region "$REGION"

aws lambda get-function \
    --function-name ms-usuarios \
    --region "$REGION" \
    --query "{State:Configuration.State,CodeSize:Configuration.CodeSize}" \
    --output json

echo ""
echo "=== ms-usuarios actualizado y compatible con Lambda ==="

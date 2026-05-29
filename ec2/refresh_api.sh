#!/bin/bash
echo "=========================================================="
echo "REFRESH API - Modo Producción Automatizado"
echo "=========================================================="

# 1. Capturar credenciales desde el entorno (inyectadas por el pipeline)
ACCESS_KEY="$AWS_ACCESS_KEY_ID"
SECRET_KEY="$AWS_SECRET_ACCESS_KEY"
SESSION_TOKEN="${AWS_SESSION_TOKEN:-}"

# 2. Resguardar secretos locales para no pisarlos
JWT_ACTUAL=$(grep JWT_SECRET /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
SYNC_ACTUAL=$(grep SYNC_TOKEN /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
GRAFANA_ACTUAL=$(grep GRAFANA_ADMIN_PASSWORD /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=$(grep AWS_S3_BUCKET /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=${S3_BUCKET:-incendios-valle-sol}

echo -e "\n Actualizando archivo .env con Región Fija..."
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY" > /home/ec2-user/.env
echo "AWS_SECRET_ACCESS_KEY=$SECRET_KEY" >> /home/ec2-user/.env
echo "AWS_SESSION_TOKEN=$SESSION_TOKEN" >> /home/ec2-user/.env
echo "JWT_SECRET=$JWT_ACTUAL" >> /home/ec2-user/.env
echo "SYNC_TOKEN=$SYNC_ACTUAL" >> /home/ec2-user/.env
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ACTUAL" >> /home/ec2-user/.env
echo "AWS_REGION=us-east-1" >> /home/ec2-user/.env
echo "AWS_DEFAULT_REGION=us-east-1" >> /home/ec2-user/.env
echo "AWS_S3_BUCKET=$S3_BUCKET" >> /home/ec2-user/.env

echo -e "\n Recreando contenedor de la API con imagen actualizada..."
cd /home/ec2-user
docker compose pull api
docker compose up -d --no-deps --force-recreate api

echo -e "\n Reiniciando Grafana para aplicar aprovisionamiento SCP..."
docker restart incendios-grafana

echo "=========================================================="
echo " Refresh completado de forma segura vía CI/CD."
echo "=========================================================="

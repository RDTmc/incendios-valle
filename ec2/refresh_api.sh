echo "=========================================================="
echo "REFRESH API - Modo Lambda Proxy (LabRole)"
echo "=========================================================="

JWT_ACTUAL=$(grep JWT_SECRET /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
SYNC_ACTUAL=$(grep SYNC_TOKEN /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
GRAFANA_ACTUAL=$(grep GRAFANA_ADMIN_PASSWORD /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=$(grep AWS_S3_BUCKET /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=${S3_BUCKET:-incendios-valle-sol}

echo -e "\n Actualizando archivo .env (sin credenciales AWS - usando LabRole)..."
echo "JWT_SECRET=$JWT_ACTUAL" > /home/ec2-user/.env
echo "SYNC_TOKEN=$SYNC_ACTUAL" >> /home/ec2-user/.env
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ACTUAL" >> /home/ec2-user/.env
echo "AWS_S3_BUCKET=$S3_BUCKET" >> /home/ec2-user/.env

echo -e "\n Descargando nueva imagen de API desde Docker Hub..."
docker-compose pull api

echo -e "\n Recreando ÚNICAMENTE el contenedor de la API..."
docker-compose up -d --no-deps --force-recreate api

echo -e "\n=========================================================="
echo " Refresh completado vía CI/CD — imagen inmutable."
echo "=========================================================="

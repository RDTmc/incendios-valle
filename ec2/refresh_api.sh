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

echo -e "\n--- Backup SQLite a S3 ---"
aws s3 cp /home/ec2-user/incendios-data/api/incendios.db \
  s3://$S3_BUCKET/backups/incendios-latest.db 2>/dev/null || true
aws s3 cp /home/ec2-user/incendios-data/api/incendios.db \
  s3://$S3_BUCKET/backups/incendios-$(date +%Y%m%d-%H%M%S).db 2>/dev/null || true

echo -e "\n--- Backup Grafana interno a S3 ---"
aws s3 cp /home/ec2-user/incendios-data/grafana/grafana.db \
  s3://$S3_BUCKET/backups/grafana-latest.db 2>/dev/null || true

echo -e "\n Descargando nueva imagen de API desde Docker Hub..."
docker-compose pull api

echo -e "\n--- Restore SQLite desde S3 (si existe backup) ---"
aws s3 cp s3://$S3_BUCKET/backups/incendios-latest.db \
  /home/ec2-user/incendios-data/api/incendios.db 2>/dev/null || true
aws s3 cp s3://$S3_BUCKET/backups/grafana-latest.db \
  /home/ec2-user/incendios-data/grafana/grafana.db 2>/dev/null || true

echo -e "\n Recreando el contenedor de la API..."
docker-compose up -d --no-deps --force-recreate api

echo -e "\n=========================================================="
echo " Refresh completado vía CI/CD — imagen inmutable."
echo "=========================================================="

echo "=========================================================="
echo "REFRESH API - Modo Lambda Proxy (LabRole)"
echo "=========================================================="

# Sanitizar .env: eliminar lineas corruptas sin KEY=VALUE
sed -ni '/^[A-Za-z_][A-Za-z0-9_]*=/p' /home/ec2-user/.env 2>/dev/null || true

JWT_ACTUAL=$(grep "^JWT_SECRET=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
SYNC_ACTUAL=$(grep "^SYNC_TOKEN=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
GRAFANA_ACTUAL=$(grep "^GRAFANA_ADMIN_PASSWORD=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
GRAFANA_TOKEN_ACTUAL=$(grep "^GRAFANA_TOKEN=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
MAILTRAP_ACTUAL=$(grep "^MAILTRAP_TOKEN=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
MAILTRAP_SENDER_ACTUAL=$(grep "^MAILTRAP_SENDER=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
MAILTRAP_SENDER_NAME_ACTUAL=$(grep "^MAILTRAP_SENDER_NAME=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
FIRMS_ACTUAL=$(grep "^FIRMS_API_KEY=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
OWM_ACTUAL=$(grep "^OWM_API_KEY=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=$(grep "^AWS_S3_BUCKET=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=${S3_BUCKET:-incendios-valle-sol}

echo -e "\nSanitizando y reescribiendo .env completo..."

cat > /home/ec2-user/.env << ENVEOF
JWT_SECRET=$JWT_ACTUAL
SYNC_TOKEN=$SYNC_ACTUAL
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ACTUAL
GRAFANA_TOKEN=$GRAFANA_TOKEN_ACTUAL
MAILTRAP_TOKEN=$MAILTRAP_ACTUAL
MAILTRAP_SENDER=$MAILTRAP_SENDER_ACTUAL
MAILTRAP_SENDER_NAME=$MAILTRAP_SENDER_NAME_ACTUAL
AWS_S3_BUCKET=$S3_BUCKET
FIRMS_API_KEY=$FIRMS_ACTUAL
OWM_API_KEY=$OWM_ACTUAL
ENVEOF

echo -e "\n--- Backup SQLite a S3 ---"
aws s3 cp /home/ec2-user/incendios-data/api/incendios.db \
  s3://$S3_BUCKET/backups/incendios-latest.db 2>/dev/null || true
aws s3 cp /home/ec2-user/incendios-data/api/incendios.db \
  s3://$S3_BUCKET/backups/incendios-$(date +%Y%m%d-%H%M%S).db 2>/dev/null || true

echo -e "\n--- Backup Grafana interno a S3 (solo backup, no restore) ---"
aws s3 cp /home/ec2-user/incendios-data/grafana/grafana.db \
  s3://$S3_BUCKET/backups/grafana-latest.db 2>/dev/null || true

echo -e "\n Descargando nueva imagen de API desde Docker Hub..."
docker-compose pull api

echo -e "\n--- Restore SQLite desde S3 (solo API, NO sobrescribir grafana.db) ---"
aws s3 cp s3://$S3_BUCKET/backups/incendios-latest.db \
  /home/ec2-user/incendios-data/api/incendios.db 2>/dev/null || true
echo -e "\n--- Fijando ownership para que Grafana (uid 472) pueda escribir ---"
# Datos de Grafana (internos)
sudo chown 472:472 /home/ec2-user/incendios-data/grafana/grafana.db 2>/dev/null || true
sudo chown 472:472 /home/ec2-user/incendios-data/grafana 2>/dev/null || true
# BD compartida SQLite (API escribe, Grafana lee — ambos como uid 472)
sudo chown -R 472:472 /home/ec2-user/incendios-data/api 2>/dev/null || true
sudo chmod 775 /home/ec2-user/incendios-data/api 2>/dev/null || true

echo -e "\n--- Preparando directorios para Prometheus ---"
sudo mkdir -p /home/ec2-user/prometheus
sudo mkdir -p /home/ec2-user/incendios-data/prometheus
# Prometheus corre como usuario por defecto (nobody:65534 en la imagen)
# Se da permisos universales porque el UID varía según distro
sudo chmod 777 /home/ec2-user/incendios-data/prometheus 2>/dev/null || true

echo -e "\n Recreando el contenedor de la API..."
docker-compose up -d --no-deps --force-recreate api

echo -e "\n--- Levantando servicios de monitoreo (Prometheus + node-exporter) ---"
docker-compose up -d prometheus node-exporter

echo -e "\n=========================================================="
echo " Refresh completado vía CI/CD — imagen inmutable."
echo "=========================================================="

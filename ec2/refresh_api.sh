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
PG_HOST_ACTUAL=$(grep "^PG_HOST=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
PG_PORT_ACTUAL=$(grep "^PG_PORT=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
PG_USER_ACTUAL=$(grep "^PG_USER=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
PG_PASSWORD_ACTUAL=$(grep "^PG_PASSWORD=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
PG_DATABASE_ACTUAL=$(grep "^PG_DATABASE=" /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)

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
PG_HOST=${PG_HOST_ACTUAL}
PG_PORT=${PG_PORT_ACTUAL:-5432}
PG_USER=${PG_USER_ACTUAL}
PG_PASSWORD=${PG_PASSWORD_ACTUAL}
PG_DATABASE=${PG_DATABASE_ACTUAL}
ENVEOF

echo -e "\n--- Generando datasource PostgreSQL para Grafana ---"
sed "s|__PG_HOST__|$PG_HOST_ACTUAL|g; s|__PG_PORT__|${PG_PORT_ACTUAL:-5432}|g; s|__PG_USER__|$PG_USER_ACTUAL|g; s|__PG_PASSWORD__|$PG_PASSWORD_ACTUAL|g; s|__PG_DATABASE__|$PG_DATABASE_ACTUAL|g" \
  /home/ec2-user/grafana-provisioning/datasources/datasource-postgres.yml.template \
  > /home/ec2-user/grafana-provisioning/datasources/datasource-postgres.yml && \
  echo "Datasource PostgreSQL generado OK" || echo "WARN: No se pudo generar datasource PostgreSQL"

echo -e "\n--- Backup PostgreSQL a S3 (pg_dump) ---"
PGPASSWORD=$PG_PASSWORD_ACTUAL pg_dump -h $PG_HOST_ACTUAL -U $PG_USER_ACTUAL -d $PG_DATABASE_ACTUAL \
  --no-owner --no-acl | gzip | aws s3 cp - s3://$S3_BUCKET/backups/incendios-pg-$(date +%Y%m%d).sql.gz 2>/dev/null || true

echo -e "\n--- Backup Grafana interno a S3 (solo backup, no restore) ---"
aws s3 cp /home/ec2-user/incendios-data/grafana/grafana.db \
  s3://$S3_BUCKET/backups/grafana-latest.db 2>/dev/null || true

echo -e "\n Descargando nueva imagen de API desde Docker Hub..."
docker-compose pull api

echo -e "\n--- Fijando permisos ---"
sudo chown 472:472 /home/ec2-user/incendios-data/grafana 2>/dev/null || true
sudo chown -R 472:472 /home/ec2-user/incendios-data/api 2>/dev/null || true
sudo chmod 775 /home/ec2-user/incendios-data/api 2>/dev/null || true

echo -e "\n--- Preparando directorios para Prometheus ---"
sudo mkdir -p /home/ec2-user/prometheus
sudo mkdir -p /home/ec2-user/incendios-data/prometheus
# Limpiar TSDB corrupto de ejecuciones previas con configuracion rota
# (no habia datos utiles — scrape targets apuntaban mal)
sudo rm -rf /home/ec2-user/incendios-data/prometheus/* 2>/dev/null || true
sudo chown 472:472 /home/ec2-user/incendios-data/prometheus 2>/dev/null || true
sudo chmod 777 /home/ec2-user/incendios-data/prometheus 2>/dev/null || true

echo -e "\n Recreando el contenedor de la API..."
docker-compose up -d --no-deps --force-recreate api

# Nginx cachea DNS del upstream al arrancar. Al recrear la API cambia la IP,
# asi que nginx debe recargar config para resolver la nueva IP del container.
echo -e "\n--- Recargando nginx para refrescar cache DNS del upstream ---"
docker-compose exec -T nginx nginx -s reload 2>/dev/null || echo "WARN: No se pudo recargar nginx via exec (puede estar detenido). Se reintentara con force-recreate."
# Fallback: recrear nginx si el exec falla (container nunca existio o murio)
docker-compose up -d --no-deps --force-recreate nginx 2>/dev/null || echo "WARN: Fallback de nginx no disponible (API aun en start_period). Se recuperara en el proximo deploy."

echo -e "\n--- Levantando servicios de monitoreo (Prometheus + node-exporter) ---"
docker-compose up -d prometheus node-exporter

echo -e "\n=========================================================="
echo " Refresh completado vía CI/CD — imagen inmutable."
echo "=========================================================="

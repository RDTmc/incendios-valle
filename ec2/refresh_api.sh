echo "=========================================================="
echo "REFRESH API - Modo Lambda Proxy"
echo "=========================================================="

read -p " Ingresa el AWS_ACCESS_KEY_ID: " ACCESS_KEY
read -p " Ingresa el AWS_SECRET_ACCESS_KEY: " SECRET_KEY
read -p " Ingresa el AWS_SESSION_TOKEN: " SESSION_TOKEN

JWT_ACTUAL=$(grep JWT_SECRET /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
SYNC_ACTUAL=$(grep SYNC_TOKEN /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
GRAFANA_ACTUAL=$(grep GRAFANA_ADMIN_PASSWORD /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=$(grep AWS_S3_BUCKET /home/ec2-user/.env 2>/dev/null | cut -d'=' -f2)
S3_BUCKET=${S3_BUCKET:-incendios-valle-sol}

echo -e "\n Actualizando archivo .env..."
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY" > /home/ec2-user/.env
echo "AWS_SECRET_ACCESS_KEY=$SECRET_KEY" >> /home/ec2-user/.env
echo "AWS_SESSION_TOKEN=$SESSION_TOKEN" >> /home/ec2-user/.env
echo "JWT_SECRET=$JWT_ACTUAL" >> /home/ec2-user/.env
echo "SYNC_TOKEN=$SYNC_ACTUAL" >> /home/ec2-user/.env
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ACTUAL" >> /home/ec2-user/.env
echo "AWS_S3_BUCKET=$S3_BUCKET" >> /home/ec2-user/.env

echo -e "\n Recreando ÚNICAMENTE el contenedor de la API..."
docker-compose up -d --no-deps --force-recreate api

sleep 10

echo -e "\n Aplicando parches en caliente (main.py + lambda_service)..."
if docker inspect incendios-api --format "{{.State.Status}}" | grep -q running; then
    docker cp /home/ec2-user/main_fixed_v2.py incendios-api:/app/main.py
    docker cp /home/ec2-user/lambda_service.py incendios-api:/app/lambda_service.py
    docker restart incendios-api
    sleep 5
    echo -e "\n Parches aplicados correctamente."
else
    echo "Error: contenedor api no está en estado running"
fi

echo -e "\n=========================================================="
echo " Refresh completado. API invoca Lambda para uploads."
echo "=========================================================="

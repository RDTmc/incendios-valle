echo "=========================================================="
echo "REFRESH API - Modo Quirúrgico (Solo API)"
echo "=========================================================="

read -p " Ingresa el AWS_ACCESS_KEY_ID: " ACCESS_KEY
read -p " Ingresa el AWS_SECRET_ACCESS_KEY: " SECRET_KEY
read -p " Ingresa el AWS_SESSION_TOKEN: " SESSION_TOKEN

JWT_ACTUAL=$(grep JWT_SECRET /home/ec2-user/.env | cut -d'=' -f2)
SYNC_ACTUAL=$(grep SYNC_TOKEN /home/ec2-user/.env | cut -d'=' -f2)
GRAFANA_ACTUAL=$(grep GRAFANA_ADMIN_PASSWORD /home/ec2-user/.env | cut -d'=' -f2)

echo -e "\n Actualizando archivo .env con credenciales vigentes..."
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY" > /home/ec2-user/.env
echo "AWS_SECRET_ACCESS_KEY=$SECRET_KEY" >> /home/ec2-user/.env
echo "AWS_SESSION_TOKEN=$SESSION_TOKEN" >> /home/ec2-user/.env
echo "JWT_SECRET=$JWT_ACTUAL" >> /home/ec2-user/.env
echo "SYNC_TOKEN=$SYNC_ACTUAL" >> /home/ec2-user/.env
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ACTUAL" >> /home/ec2-user/.env
export AWS_ACCESS_KEY_ID="$ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SECRET_KEY"
export AWS_SESSION_TOKEN="$SESSION_TOKEN"

echo -e "\n Recreando ÚNICAMENTE el contenedor de la API..."
docker-compose up -d --no-deps --force-recreate api

sleep 10

echo -e "\n Aplicando parches en caliente (main.py completo + s3_service)..."
# El --force-recreate crea un contenedor NUEVO desde la imagen (Mayo 20).
# Inyectamos el main.py completo con todos los endpoints modernos.
if docker inspect incendios-api --format "{{.State.Status}}" | grep -q running; then
    docker cp /home/ec2-user/main_fixed_v2.py incendios-api:/app/main.py
    docker cp /home/ec2-user/s3_service.py incendios-api:/app/s3_service.py
    docker restart incendios-api
    sleep 5
    echo -e "\n Parches aplicados correctamente."
else
    echo "Error: contenedor api no está en estado running"
fi

echo -e "\n=========================================================="
echo " Refresh completado. API y parches activos."
echo "=========================================================="

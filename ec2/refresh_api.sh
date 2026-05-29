echo "=========================================================="
echo "REFRESH API - Modo Lambda Proxy"
echo "=========================================================="

if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
  ACCESS_KEY="$AWS_ACCESS_KEY_ID"
  SECRET_KEY="$AWS_SECRET_ACCESS_KEY"
  SESSION_TOKEN="${AWS_SESSION_TOKEN:-}"
  echo " Usando credenciales desde variables de entorno"
else
  read -p " Ingresa el AWS_ACCESS_KEY_ID: " ACCESS_KEY
  read -p " Ingresa el AWS_SECRET_ACCESS_KEY: " SECRET_KEY
  read -p " Ingresa el AWS_SESSION_TOKEN: " SESSION_TOKEN
fi

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

echo -e "\n=========================================================="
echo " Refresh completado vía CI/CD — imagen inmutable."
echo "=========================================================="

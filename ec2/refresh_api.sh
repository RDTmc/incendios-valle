
echo "=========================================================="
echo "REFRESH API - Credenciales AWS Academy (Modo Compose)"
echo "=========================================================="

# 1. Solicitar las credenciales de AWS de forma interactiva
read -p "🔑 Ingresa el AWS_ACCESS_KEY_ID: " ACCESS_KEY
read -p "🔑 Ingresa el AWS_SECRET_ACCESS_KEY: " SECRET_KEY
read -p "🔑 Ingresa el AWS_SESSION_TOKEN: " SESSION_TOKEN

# 2. Mantener los secrets dinámicos actuales que ya validamos en el .env
JWT_ACTUAL=$(grep JWT_SECRET /home/ec2-user/.env | cut -d'=' -f2)
SYNC_ACTUAL=$(grep SYNC_TOKEN /home/ec2-user/.env | cut -d'=' -f2)
GRAFANA_ACTUAL=$(grep GRAFANA_ADMIN_PASSWORD /home/ec2-user/.env | cut -d'=' -f2)

echo -e "\n Actualizando archivo .env con credenciales vigentes..."

# 3. Reescribir el .env ordenadamente con los nuevos tokens de AWS y los secrets preservados
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY" > /home/ec2-user/.env
echo "AWS_SECRET_ACCESS_KEY=$SECRET_KEY" >> /home/ec2-user/.env
echo "AWS_SESSION_TOKEN=$SESSION_TOKEN" >> /home/ec2-user/.env
echo "JWT_SECRET=$JWT_ACTUAL" >> /home/ec2-user/.env
echo "SYNC_TOKEN=$SYNC_ACTUAL" >> /home/ec2-user/.env
echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ACTUAL" >> /home/ec2-user/.env
export AWS_ACCESS_KEY_ID="$ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SECRET_KEY"
export AWS_SESSION_TOKEN="$SESSION_TOKEN"

echo " Recreando el contenedor de la API con la nueva sesión..."
cd /home/ec2-user
docker-compose down
docker-compose up -d --force-recreate
sleep 15

echo " Instalando dependencia bcrypt en caliente..."
docker exec incendios-api pip install bcrypt

echo " Inyectando código de la API (main_fixed.py)..."
docker cp /home/ec2-user/main_fixed.py incendios-api:/app/main.py

echo " Inyectando y ejecutando el script de siembra (seed_fixed.py)..."
docker cp /home/ec2-user/seed_fixed.py incendios-api:/app/seed_fixed.py

echo " Reiniciando API para aplicar el código y la librería..."
docker restart incendios-api
sleep 10

echo " Ejecutando la semilla en DynamoDB..."
docker exec -it incendios-api python3 /app/seed_fixed.py

echo -e "\n Realizando prueba de fuego (Login Auth vía Nginx)..."
# Probamos a través del puerto 8000 directo para validar la API internamente
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@valledelsol.cl","password":"admin123"}'

echo -e "\n\n=========================================================="
echo " ¡Todo listo! API sincronizada mediante Compose por las próximas 4 horas."
echo "=========================================================="

#!/bin/bash
# Healthcheck para monitoreo de la API
# Uso: ./healthcheck.sh [--slack] [--email]

API_URL="http://localhost:8000/api/health"
GRAFANA_URL="http://localhost:3000/api/health"
TIMEOUT=10

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_endpoint() {
    local name=$1
    local url=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ $name: OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: FAIL (HTTP $response)${NC}"
        return 1
    fi
}

echo "========================================"
echo " Healthcheck - Incendios Valle del Sol"
echo " Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

FAILURES=0

check_endpoint "API FastAPI" "$API_URL" || ((FAILURES++))
check_endpoint "Grafana" "$GRAFANA_URL" || ((FAILURES++))

# Verificar contenedores Docker
echo ""
echo "--- Contenedores Docker ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker no disponible"

# Verificar uso de disco
echo ""
echo "--- Disco ---"
df -h / | tail -1 | awk '{print "Uso: " $5 " de " $2}'

# Verificar memoria
echo ""
echo "--- Memoria ---"
free -h | grep Mem | awk '{print "Usado: " $3 " / " $2}'

echo ""
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ Todos los servicios operativos${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILURES servicio(s) con fallos${NC}"
    exit 1
fi

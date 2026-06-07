#!/bin/bash
echo "=== Register test user ==="
cat > /tmp/payload.json << 'EOF'
{"httpMethod":"POST","path":"/register","body":"{\"email\":\"api-test@test.com\",\"password\":\"test123\",\"nombre\":\"API Test\"}"}
EOF
aws lambda invoke --function-name ms-usuarios \
  --payload fileb:///tmp/payload.json \
  --region us-east-1 /tmp/response.json 2>&1
echo "Respuesta:"
cat /tmp/response.json
echo ""

echo "=== Login with created user ==="
cat > /tmp/payload2.json << 'EOF'
{"httpMethod":"POST","path":"/login","body":"{\"email\":\"api-test@test.com\",\"password\":\"test123\"}"}
EOF
aws lambda invoke --function-name ms-usuarios \
  --payload fileb:///tmp/payload2.json \
  --region us-east-1 /tmp/response2.json 2>&1
echo "Respuesta:"
cat /tmp/response2.json
echo ""

echo "=== Test via API Gateway ==="
curl -s -X POST "https://jywf027zj3.execute-api.us-east-1.amazonaws.com/prod/auth" \
  -H "Content-Type: application/json" \
  -d '{"email":"api-test@test.com","password":"test123"}' 2>&1

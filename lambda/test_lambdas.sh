#!/bin/bash
echo "=== Test ms-usuarios ==="
cat > /tmp/payload.json << 'EOF'
{"httpMethod":"POST","path":"/login","body":"{\"email\":\"test@test.com\",\"password\":\"test\"}"}
EOF

aws lambda invoke --function-name ms-usuarios \
  --payload fileb:///tmp/payload.json \
  --region us-east-1 /tmp/response.json 2>&1

echo "Respuesta:"
cat /tmp/response.json
echo ""

echo "=== Test ms-incidencias ==="
cat > /tmp/payload2.json << 'EOF'
{"httpMethod":"GET","path":"/reports","queryStringParameters":{"user_id":"test"}}
EOF

aws lambda invoke --function-name ms-incidencias \
  --payload fileb:///tmp/payload2.json \
  --region us-east-1 /tmp/response2.json 2>&1

echo "Respuesta:"
cat /tmp/response2.json

echo "=== Done ==="

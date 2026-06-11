#!/bin/bash
set -euo pipefail

echo "=== Grafana DB permissions fix ==="
ls -la /home/ec2-user/incendios-data/grafana/grafana.db

echo "=== Setting ownership ==="
sudo chown 472:472 /home/ec2-user/incendios-data/grafana/grafana.db 2>/dev/null || true
sudo chown 472:472 /home/ec2-user/incendios-data/grafana 2>/dev/null || true

echo "=== Setting permissions ==="
chmod 664 /home/ec2-user/incendios-data/grafana/grafana.db 2>/dev/null || true

echo "=== All grafana dir files ==="
ls -la /home/ec2-user/incendios-data/grafana/

echo "=== Test sqlite write ==="
sqlite3 /home/ec2-user/incendios-data/grafana/grafana.db \
  "INSERT INTO session VALUES('test_write_perm','data',9999999999);" 2>&1
sqlite3 /home/ec2-user/incendios-data/grafana/grafana.db \
  "DELETE FROM session WHERE key='test_write_perm';" 2>&1
echo "write test ok"

echo "=== Restart Grafana ==="
docker-compose -f /home/ec2-user/docker-compose.yml restart grafana
sleep 5

echo "=== Verify login ==="
curl -s -o /dev/null -w "Login HTTP %{http_code}\n" \
  -X POST http://localhost/dashboard/login \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"ValleSol2026!Secure"}'

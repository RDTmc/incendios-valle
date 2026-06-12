#!/usr/bin/env python3
"""Debug: fetch dashboard JSON and show raw response."""
import json, subprocess

def run_in_container(cmd):
    full = ["docker", "exec", "incendios-grafana", "sh", "-c", cmd]
    r = subprocess.run(full, capture_output=True, text=True)
    return r.stdout, r.stderr, r.returncode

out, err, rc = run_in_container(
    'curl -s -c /tmp/c -X POST http://localhost:3000/login '
    '-H "Content-Type: application/json" '
    '-d \'{"user":"admin","password":"ValleSol2026!Secure"}\''
)
print("Login response:", out[:200])
print("Login err:", err[:200])

# Verify cookie file exists
out2, err2, rc2 = run_in_container('cat /tmp/c')
print("Cookie file:", out2[:300] if out2 else "EMPTY")
if not out2:
    print("No cookie file!")
    # Maybe we need to try different endpoints
    out3, err3, rc3 = run_in_container('curl -s -v http://localhost:3000/login 2>&1')
    print("Login page:", out3[:500])

out4, err4, rc4 = run_in_container(
    'curl -s -b /tmp/c http://localhost:3000/api/dashboards/uid/incendios-valle-main'
)
print("Dashboard response:", out4[:500])

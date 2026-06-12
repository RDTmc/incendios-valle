#!/usr/bin/env python3
"""Debug Grafana login."""
import subprocess

def run(cmd):
    full = ["docker", "exec", "incendios-grafana", "sh", "-c", cmd]
    r = subprocess.run(full, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip()

# Try login with verbose output
cmd1 = 'curl -s -v -c /tmp/c2 -X POST http://localhost:3000/login -H "Content-Type: application/json" -d \'{"user":"admin","password":"ValleSol2026!Secure"}\' 2>&1'
out, err = run(cmd1)
print("=== Login verbose ===")
print(out[:500])

# Check cookie after login
out2, err2 = run('cat /tmp/c2')
print("=== Cookie file ===")
print(out2[:500])

# What about the /api/login endpoint?
out3, err3 = run('curl -s -v -c /tmp/c3 -X POST http://localhost:3000/api/login -H "Content-Type: application/json" -d \'{"user":"admin","password":"ValleSol2026!Secure"}\' 2>&1')
print("=== API Login ===")
print(out3[:500])

out4, err4 = run('cat /tmp/c3')
print("=== Cookie 3 ===")
print(out4[:500])

# Try basic auth
out5, err5 = run('curl -s -u admin:ValleSol2026!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main')
print("=== Basic auth dashboard ===")
print(out5[:500])

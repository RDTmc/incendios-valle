#!/usr/bin/env python3
"""Check current panel 5 options."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)
p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)
print("cellHeight:", repr(p5['options']['cellHeight']))
print("targets refIds:", [t.get('refId') for t in p5.get('targets', [])])
print()
print("Full options:", json.dumps(p5['options'], indent=2))

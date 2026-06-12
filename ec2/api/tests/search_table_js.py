#!/usr/bin/env python3
"""Search for image cell rendering code in Grafana's table plugin JS."""
import subprocess, re

subprocess.run([
    "docker", "cp", "incendios-grafana:/usr/share/grafana/public/build/tableOldPlugin.8c72b8399d197aeebe16.js",
    "/tmp/tableOldPlugin.js"
])

with open("/tmp/tableOldPlugin.js", "r", errors="replace") as f:
    content = f.read()

# Search specific patterns
searches = [
    "objectFit", "object-fit", "ImageCell", "imageCell",
    "imagen", "img src", "value.src", "cellType",
    "cellHeight", "width:100%", "height:100%"
]

for s in searches:
    idx = content.find(s)
    if idx >= 0:
        start = max(0, idx - 80)
        end = min(len(content), idx + 200)
        context = content[start:end]
        print(f"\n=== '{s}' at offset {idx} ===")
        print(context)

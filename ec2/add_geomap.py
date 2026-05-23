import json

path = '/home/ec2-user/grafana-provisioning/dashboards/dashboard_incendios.json'
with open(path) as f:
    d = json.load(f)

# Add a 4th panel: Geomap Heatmap
geomap_panel = {
    "id": 4,
    "title": "Mapa de Calor - Focos de Incendio",
    "type": "geomap",
    "gridPos": {"h": 16, "w": 24, "x": 0, "y": 8},
    "datasource": {"type": "marcusolsson-json-datasource", "uid": "incendios-api"},
    "fieldConfig": {
        "defaults": {},
        "overrides": []
    },
    "options": {
        "view": {
            "lat": -33.45,
            "lng": -70.66,
            "zoom": 10
        },
        "controls": {
            "showZoom": True,
            "showAttribution": False
        },
        "layers": [
            {
                "name": "Heatmap",
                "type": "heatmap",
                "location": {
                    "mode": "auto"
                }
            }
        ]
    },
    "targets": [
        {
            "datasource": {"type": "marcusolsson-json-datasource", "uid": "incendios-api"},
            "refId": "A",
            "method": "GET",
            "urlPath": "/public/map-coordinates",
            "fields": [
                {"name": "lat", "jsonPath": "$[*].lat", "type": "number"},
                {"name": "lng", "jsonPath": "$[*].lng", "type": "number"},
                {"name": "intensidad", "jsonPath": "$[*].intensidad", "type": "number"},
                {"name": "estado", "jsonPath": "$[*].estado", "type": "string"},
                {"name": "tipo", "jsonPath": "$[*].tipo", "type": "string"}
            ]
        }
    ]
}

d['panels'].append(geomap_panel)

with open(path, 'w') as f:
    json.dump(d, f, indent=2)
print('GEOMAP PANEL ADDED')
print(f'Total panels: {len(d["panels"])}')

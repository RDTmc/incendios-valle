import json, os

ds_uid = 'incendios-api'
api_url_path = '/public/dashboard-stats'

dashboard = {
    "id": None,
    "uid": "incendios-valle-main",
    "title": "Incendios Valle del Sol",
    "tags": ["incendios", "valle-del-sol", "produccion"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "30s",
    "editable": True,
    "panels": [
        {
            "id": 1,
            "title": "Focos Críticos Activos",
            "type": "stat",
            "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
            "datasource": {"type": "marcusolsson-json-datasource", "uid": ds_uid},
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "orange", "value": 1},
                            {"color": "red", "value": 5}
                        ]
                    },
                    "mappings": [],
                    "unit": "none"
                },
                "overrides": []
            },
            "options": {
                "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "auto"
            },
            "targets": [{
                "refId": "A",
                "urlPath": api_url_path,
                "method": "GET",
                "params": [],
                "headers": [],
                "fields": [
                    {"name": "focos_activos", "type": "number", "source": "$.focos_activos"}
                ]
            }]
        },
        {
            "id": 2,
            "title": "Distribución por Tipo de Incendio",
            "type": "stat",
            "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
            "datasource": {"type": "marcusolsson-json-datasource", "uid": ds_uid},
            "fieldConfig": {
                "defaults": {"mappings": [], "unit": "none"},
                "overrides": []
            },
            "options": {
                "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value",
                "graphMode": "none",
                "justifyMode": "auto"
            },
            "targets": [{
                "refId": "A",
                "urlPath": api_url_path,
                "method": "GET",
                "params": [],
                "headers": [],
                "fields": [
                    {"name": "tipo_forestal", "type": "number", "source": "$.tipo_forestal"},
                    {"name": "tipo_urbano", "type": "number", "source": "$.tipo_urbano"}
                ]
            }]
        },
        {
            "id": 3,
            "title": "Estatus Global de Reportes",
            "type": "stat",
            "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
            "datasource": {"type": "marcusolsson-json-datasource", "uid": ds_uid},
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "orange", "value": 3},
                            {"color": "red", "value": 5}
                        ]
                    },
                    "mappings": [],
                    "unit": "none",
                    "min": 0
                },
                "overrides": []
            },
            "options": {
                "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""},
                "orientation": "auto",
                "textMode": "auto",
                "colorMode": "value",
                "graphMode": "none",
                "justifyMode": "auto"
            },
            "targets": [{
                "refId": "A",
                "urlPath": api_url_path,
                "method": "GET",
                "params": [],
                "headers": [],
                "fields": [
                    {"name": "estado_pendiente", "type": "number", "source": "$.estado_pendiente"},
                    {"name": "estado_activo", "type": "number", "source": "$.estado_activo"},
                    {"name": "estado_controlado", "type": "number", "source": "$.estado_controlado"}
                ]
            }]
        }
    ]
}

out = '/home/ec2-user/grafana-provisioning/dashboards/dashboard_incendios.json'
with open(out, 'w') as f:
    json.dump(dashboard, f, indent=2)
print('DASHBOARD JSON CREATED')

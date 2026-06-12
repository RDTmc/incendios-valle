import json

with open(r'C:\Users\rdmun\Videos\a-react-pwa\incendios-valle\ec2\api\tests\dash_raw.json') as f:
    dash = json.load(f)
print('Dashboard:', dash.get('dashboard',{}).get('title'))
panels = dash['dashboard']['panels']
p5 = next((p for p in panels if p.get('id') == 5), None)
if p5:
    print('Panel 5:', p5.get('title'))
    print('Targets:', len(p5.get('targets',[])))
    ds = p5['targets'][0].get('datasource',{}) if p5.get('targets') else {}
    print('Datasource:', json.dumps(ds))
    
    # Add test image target
    p5.setdefault('targets',[]).append({
        'rawQueryText': "SELECT 'https://picsum.photos/200/300' AS \"Imagen\", 'TEST' AS \"Reporte\"",
        'refId': 'B',
        'datasource': ds,
        'format': 'table'
    })
    
    with open(r'C:\Users\rdmun\Videos\a-react-pwa\incendios-valle\ec2\api\tests\dash_patched.json', 'w') as f:
        json.dump(dash, f)
    print('Patched dashboard saved')
else:
    print('Panel 5 not found!')
    for p in panels:
        print(f"Panel id={p.get('id')} title={p.get('title')}")

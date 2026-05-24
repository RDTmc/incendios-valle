import json, sys
d = json.load(open(sys.argv[1]))
print('Panels:', len(d.get('panels', [])))
for p in d.get('panels', []):
    print(' ', p['id'], p['title'], '(', p['type'], ')')

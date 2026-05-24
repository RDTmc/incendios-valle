path = '/home/ec2-user/nginx/nginx.conf'
with open(path) as f:
    c = f.read()

old_block = """        location /dashboard/ {
            proxy_pass http://grafana;  # SIN barra diagonal al final para mantener la URI intacta
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Encabezados vitales para que Grafana no rompa el sub-path
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port $server_port;
            proxy_set_header Upgrade ;
            proxy_set_header Connection  upgrade;
        }"""

new_block = """        location /dashboard/ {
            proxy_pass http://grafana;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port $server_port;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }"""

if old_block in c:
    c = c.replace(old_block, new_block)
    with open(path, 'w') as f:
        f.write(c)
    print('NGINX PATCHED')
else:
    print('BLOCK NOT FOUND - checking current state...')
    import re
    m = re.search(r'location /dashboard/ \{.*?\}', c, re.DOTALL)
    if m:
        print('Current block:')
        print(m.group())
    else:
        print('No /dashboard/ location block found')

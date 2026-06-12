#!/usr/bin/env python3
"""Update dashboard to use the test JPEG from S3 to verify display."""
import subprocess, json

def rc(cmd):
    r = subprocess.run(
        ["docker", "exec", "incendios-grafana", "sh", "-c", cmd],
        capture_output=True, text=True
    )
    return r.stdout, r.stderr, r.returncode

# The test image URL (from the upload above)
test_key = "reportes/test_8b0fc37d0cdc42ccb2f00249e77f5d85.jpg"
test_url = "https://incendios-valle-sol.s3.amazonaws.com/reportes/test_8b0fc37d0cdc42ccb2f00249e77f5d85.jpg?AWSAccessKeyId=ASIA45I7OK4TTY6EU5OS&Signature=BZBsDhbEt%2BTt2XMyNpv%2BmaalJbg%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEEMaCXVzLWVhc3QtMSJGMEQCIBq%2B5PVI%2BPDzR1sDy2ZVkmb1xK%2F5nUsrA4Q9r0ZSDOpuAiA4GUzKIAznMKypa%2B3qVp7m8e5H7JM6E8wuM3iG6DOmayrdAwgMEAIaDDg4NzUxMzU2OTA2MyIMiyPxSxe0%2FW39drw%2BKroDHkxAryAlokeLnAkVVHUya4OC1nj4AxCGl7eL8Le6aI8h0yJniIoNVw6cHP%2BihAVPibrrCaoxkKukr0pi0ibNwuMN5ayDq4nryO%2BzEv1ee%2F3p7%2By67Y%2BPqYJCfotT5jSFRsF%2F7Y4bSdCd3SvBKwdqn8sNOKLbbNIQ0XrBLaCyzYpx%2FFBB%2FPAULEOnSmQaww4U0jCW1cwW5W4nxiVN6AAWLirryqUk%2Ft9Cj2E9cs%2F6txRdDnFiV9pVQUCjchxTsPjkWXO7FjdyDLVY07s%2FIe7wRfj6kEX5M3sAlsUxQau4wRR%2F4c%2BRxLFPs3OvNAUI%2FUDi2rsNOvdsIJ6FPh3UHhIPnnPGY0aeelz3cvvg4vQ6s7MmeJd0wAUzqv%2Fus%2F8jxQyyNmr8pPuDouIov5HCv1jJtaCm2KvBaiy2PrwM2Kt%2FOR%2FSamfb8%2FbvQAzI2gbtRbxdnOV4zvYc9b4%2B3gxTn%2BxmEQjciN1%2F8Lb9UFI2dcBdXSp8N0iqmjZPXwzELZ%2Bm2WlR8SNoEu%2FibFxwmr5fUOt8sFb9cyikgJDBSX1trqbCKld519hM7PIQ9VJ%2BhUJjT6X%2F6GZbU%2BTRPoys7DDq363RBjqiAa9KQ%2BFcjzwIFkboev2xMOn44nISk%2BBiw61iC0flfjNvXAJBjw1G7QD0C%2F3ntLclLsNFJMULSkCUH%2BLs6YVBD20LQv%2Fy%2Bj8kNrLXaXCi%2FUltyrvm7gHPzJCch69WE60M7%2Bwlw8DtMXrsUUbK6VvKCuBIO91J%2FdNsgulMnCaOa2gnA54xtr026q1YthEmhNBRNiVym263rm7KnRlJ0ziubZticw%3D%3D&Expires=1781836395"

# No - I need to generate a FRESH presigned URL since the one above uses an old signature
# Let me generate a new one from the API container
r = subprocess.run(
    ["docker", "exec", "incendios-api", "python3", "-c",
     'import boto3; s3=boto3.client("s3", region_name="us-east-1"); '
     'url=s3.generate_presigned_url("get_object", Params={"Bucket":"incendios-valle-sol","Key":"reportes/test_8b0fc37d0cdc42ccb2f00249e77f5d85.jpg"}, ExpiresIn=604800); '
     'print(url)'],
    capture_output=True, text=True, timeout=15
)
test_url = r.stdout.strip()
print("Fresh URL:", test_url[:80])

# Fetch dashboard
out, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure http://localhost:3000/api/dashboards/uid/incendios-valle-main")
dash = json.loads(out)
p5 = next(p for p in dash['dashboard']['panels'] if p.get('id') == 5)

# Escape single quotes in URL for SQL
escaped_url = test_url.replace("'", "''")

# Update SQL to show test image
for t in p5['targets']:
    if t.get('refId') == 'A':
        t['rawQueryText'] = (
            "SELECT report_id AS \"ID\", foto_url AS \"Imagen\", descripcion AS \"Descripcion\", "
            "tipo AS \"Tipo\", estado AS \"Estado\", created_at AS \"Fecha\" "
            "FROM reports WHERE foto_url IS NOT NULL AND foto_url != ''\n"
            "UNION ALL\n"
            f"SELECT '99' AS \"ID\", '{escaped_url}' AS \"Imagen\", "
            "'TEST S3 JPEG' AS \"Descripcion\", 'test' AS \"Tipo\", 'activo' AS \"Estado\", "
            "datetime('now') AS \"Fecha\"\n"
            "ORDER BY \"Fecha\" DESC LIMIT 15"
        )

# Ensure image cell type
overrides = p5['fieldConfig']['overrides']
for o in overrides:
    if o.get('matcher', {}).get('options') == 'Imagen':
        for prop in o['properties']:
            if prop['id'] == 'custom.cellOptions':
                prop['value'] = {'type': 'image'}

p5['options']['cellHeight'] = 300
p5['options']['footer']['enablePagination'] = False

patched = json.dumps(dash)
subprocess.run(
    ["docker", "exec", "-i", "incendios-grafana", "sh", "-c", "cat > /tmp/dash_s3_test2.json"],
    input=patched, text=True
)

out2, _, _ = rc("curl -s -u admin:ValleSol2026\\!Secure -X POST http://localhost:3000/api/dashboards/db -H 'Content-Type: application/json' -d @/tmp/dash_s3_test2.json")
print("Update:", out2[:200])

import httpx

r = httpx.post("http://localhost:8000/login",
    json={"email": "admin@valledelsol.cl", "password": "admin123"})

if r.status_code != 200:
    print(f"Login failed: {r.status_code} - {r.json()}")
    exit()

data = r.json()
token = data.get("token") or data.get("temp_token", "")
print(f"Login OK")

headers = {"Authorization": f"Bearer {token}"}

for path, key in [
    ("/admin/users", "users"),
    ("/admin/audit-log", None),
    ("/admin/reports", "reports"),
    ("/admin/notifications", None),
]:
    r = httpx.get(f"http://localhost:8000{path}", headers=headers)
    count = len(r.json()) if key is None else len(r.json().get(key, []))
    print(f"GET {path}: {r.status_code}, count={count}")

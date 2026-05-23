import re

path = '/app/main.py'
with open(path) as f:
    c = f.read()

patches = [
    # 1. Import UploadFile + s3_service
    ("from fastapi import FastAPI, HTTPException, Depends, Header",
     "from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File"),
    ("import sqlite3",
     "import sqlite3\nfrom s3_service import upload_image"),

    # 2. ALLOWED_MIME + MAX_FILE_SIZE before ENDPOINTS
]

# Add upload endpoint before @app.post("/login")
login_marker = "@app.post(\"/login\")"
upload_endpoint = """ALLOWED_MIME = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


@app.post("/reports/upload")
def upload_report_image(file: UploadFile = File(...)):
    try:
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Solo se permiten imágenes JPEG o PNG")

        contents = file.file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="La imagen no debe superar los 2MB")

        url = upload_image(contents, file.content_type)
        return {"foto_url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")
"""

if '/reports/upload"' not in c:
    c = c.replace(login_marker, upload_endpoint + '\n' + login_marker)
    print("UPLOAD ENDPOINT ADDED")
else:
    print("UPLOAD ENDPOINT ALREADY EXISTS")

# 3. Update ReportRequest
c = c.replace(
    "descripcion: str = \"\"",
    "descripcion: str = \"\"\n    foto_url: str = \"\""
)

# 4. Update create_report item
c = c.replace(
    "'descripcion': req.descripcion,",
    "'descripcion': req.descripcion,\n            'foto_url': req.foto_url,"
)

# 5. Update SQLite reports schema
c = c.replace(
    "descripcion TEXT,",
    "descripcion TEXT,\n            foto_url TEXT DEFAULT '',"
)

# 6. Update sync_to_sqlite INSERT
c = c.replace(
    "INSERT OR REPLACE INTO reports\n                    (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, estado, created_at, updated_at)\n                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    "INSERT OR REPLACE INTO reports\n                    (report_id, user_id, tipo, latitud, longitud, geohash, descripcion, foto_url, estado, created_at, updated_at)\n                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
c = c.replace(
    "data.get('descripcion'), data.get('estado'),",
    "data.get('descripcion'), data.get('foto_url', ''),\n                      data.get('estado'),"
)

# 7. Add migration in init_db
init_db_end = "    conn.commit()\n    conn.close()\n\ninit_db()"
migration = """    # Migracion: agregar columna foto_url si no existe (BD existentes)
    try:
        cursor.execute("ALTER TABLE reports ADD COLUMN foto_url TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Ya existe

    conn.commit()
    conn.close()

init_db()"""

c = c.replace(init_db_end, migration)

with open(path, 'w') as f:
    f.write(c)

print("ALL PATCHES APPLIED")

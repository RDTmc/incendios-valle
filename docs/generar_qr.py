"""Genera el código QR oficial único para Incendios Valle del Sol.
Sintaxis estricta: URL limpia sin parámetros para máxima compatibilidad con escáneres."""
import qrcode
from pathlib import Path

URL_QR = "https://incendios-valle.pages.dev/qr/"

DOCS = Path(__file__).parent
RUTA = DOCS / "qr-pwa-incendios.png"

img = qrcode.make(URL_QR)
img.save(RUTA)
print(f"  {RUTA.name} — {RUTA.stat().st_size} bytes")
print(f"  Texto exacto en QR: '{URL_QR}'")
print(f"  Longitud: {len(URL_QR)} caracteres — sin UTM, sin saltos de línea")

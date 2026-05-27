"""Genera el código QR oficial único para Incendios Valle del Sol."""
import qrcode
from pathlib import Path

URL_QR = "https://incendios-valle.pages.dev/qr?utm_source=afiche_municipal&utm_medium=qr"

DOCS = Path(__file__).parent
RUTA_SALIDA = DOCS / "qr-pwa-incendios.png"

# Eliminar variante intent si existe
ruta_intent = DOCS / "qr-pwa-android-intent.png"
if ruta_intent.exists():
    ruta_intent.unlink()
    print(f"  Eliminado: {ruta_intent.name}")

img = qrcode.make(URL_QR)
img.save(RUTA_SALIDA)
print(f"  {RUTA_SALIDA.name} — {RUTA_SALIDA.stat().st_size} bytes")
print(f"  Destino: {URL_QR}")
print("  Listo — QR único y universal.")

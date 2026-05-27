"""Genera códigos QR para la campaña municipal de Incendios Valle del Sol."""
import qrcode
from pathlib import Path

BASE = "https://incendios-valle.pages.dev"
URL_CAMPANNA = f"{BASE}/?utm_source=afiche_municipal&utm_medium=qr"
INTENT_ANDROID = (
    "intent://incendios-valle.pages.dev/"
    "?utm_source=afiche_municipal&utm_medium=qr"
    "#Intent;scheme=https;package=com.android.chrome;end"
)

DOCS = Path(__file__).parent

pares = [
    ("qr-pwa-incendios.png", URL_CAMPANNA, "URL canónica con UTM"),
    ("qr-pwa-android-intent.png", INTENT_ANDROID, "Intent Android (abre en Chrome)"),
]

for nombre, url, desc in pares:
    ruta = DOCS / nombre
    img = qrcode.make(url)
    img.save(ruta)
    print(f"  {nombre} — {ruta.stat().st_size} bytes | {desc}")

print("\nListo — ambos QR generados.")

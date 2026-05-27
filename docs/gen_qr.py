import qrcode
from pathlib import Path

url = "https://incendios-valle.pages.dev"
out = Path(__file__).parent / "qr-pwa-incendios.png"

img = qrcode.make(url)
img.save(out)
print(f"QR generado: {out} ({out.stat().st_size} bytes)")
print(f"URL: {url}")

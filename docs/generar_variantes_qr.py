"""Genera variantes de código QR para pruebas de compatibilidad Android.
Cada variante codifica la misma URL con un formato distinto.
https://incendios-valle.pages.dev/qr/"""
import qrcode
from pathlib import Path

DESTINO = Path(__file__).parent / "test-qr"
DESTINO.mkdir(parents=True, exist_ok=True)

URL = "https://incendios-valle.pages.dev/qr/"
TITULO = "Incendios Valle"

variantes = [
    {
        "archivo": "qr-control.png",
        "texto": URL,
        "desc": "CONTROL - URL plana (misma que produccion)",
    },
    {
        "archivo": "qr-urlto.png",
        "texto": f"URLTO:{URL}",
        "desc": "URLTO - formato estandar ISO/IEC 18004 para URLs en QR",
    },
    {
        "archivo": "qr-mebkm.png",
        "texto": f"MEBKM:TITLE:{TITULO};URL:{URL};;",
        "desc": "MEBKM - Mobile ESR Bookmark, algunos lectores lo interpretan como marcador web",
    },
    {
        "archivo": "qr-html.png",
        "texto": f'<a href="{URL}">Reportar incendio</a>',
        "desc": "HTML - ancla html, algunos lectores extraen el href",
    },
]

for v in variantes:
    ruta = DESTINO / v["archivo"]
    qrcode.make(v["texto"]).save(ruta)
    kb = ruta.stat().st_size
    print(f"  {v['archivo']:25s} {kb:5d} bytes  | {v['desc']}")

print(f"\n{len(variantes)} variantes generadas en: {DESTINO}")

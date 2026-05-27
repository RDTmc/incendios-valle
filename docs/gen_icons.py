"""Generate PWA icons for Incendios Valle del Sol.
Uses the official municipal logo instead of the old red ellipse."""
from PIL import Image
from pathlib import Path

PUBLIC = Path(__file__).parent.parent / "frontend" / "public"
LOGO = Path(__file__).parent / "logo-muni-valle-del-sol.png"
PUBLIC.mkdir(parents=True, exist_ok=True)

SIZES = {
    "pwa-192x192.png": 192,
    "pwa-512x512.png": 512,
    "apple-touch-icon.png": 180,
}

logo = Image.open(LOGO).convert("RGBA")

for name, sz in SIZES.items():
    resized = logo.resize((sz, sz), Image.LANCZOS)
    path = PUBLIC / name
    resized.save(path)
    print(f"  {path.name} ({sz}x{sz}) — {path.stat().st_size} bytes")

# Generate multi-resolution favicon.ico (16, 32, 48)
ico_sizes = [16, 32, 48]
ico_images = []
for sz in ico_sizes:
    ico_images.append(logo.resize((sz, sz), Image.LANCZOS))
ico_path = PUBLIC / "favicon.ico"
ico_images[0].save(ico_path, format="ICO", sizes=[(s, s) for s in ico_sizes])
print(f"  favicon.ico ({', '.join(str(s) for s in ico_sizes)} px) — {ico_path.stat().st_size} bytes")

print("Done — all icons regenerated from municipal logo.")

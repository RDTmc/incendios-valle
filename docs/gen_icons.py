"""Generate PWA icons for Incendios Valle del Sol."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PUBLIC = Path(__file__).parent.parent / "frontend" / "public"
PUBLIC.mkdir(parents=True, exist_ok=True)

SIZES = {
    "pwa-192x192.png": 192,
    "pwa-512x512.png": 512,
    "apple-touch-icon.png": 180,
}


def make_icon(size):
    img = Image.new("RGBA", (size, size), (239, 68, 68, 255))
    draw = ImageDraw.Draw(img)
    # White circle in center
    margin = size // 6
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(255, 255, 255, 240),
    )
    # Simple flame shape using text
    try:
        font = ImageFont.truetype("segoeui.ttf", size // 2)
    except Exception:
        font = ImageFont.load_default()
    # Center the fire emoji / text
    text = "🔥"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=(200, 50, 50, 255))
    return img


for name, sz in SIZES.items():
    path = PUBLIC / name
    make_icon(sz).save(path)
    print(f"  {path.name} ({sz}x{sz}) — {path.stat().st_size} bytes")

print("Done — all icons generated.")

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
OUT_PATH = SITE_DIR / "social-preview.jpg"
PUBLISHER_LOGO_PATH = SITE_DIR / "publisher-logo.png"
IMAGE_URL = "https://homekeepinglab.com/social-preview.jpg"
PUBLISHER_LOGO_URL = "https://homekeepinglab.com/publisher-logo.png"
SITE_URL = "https://homekeepinglab.com/"
ABOUT_URL = "https://homekeepinglab.com/about/"
W, H = 1200, 630

GREEN = "#17663f"
DARK = "#123d2f"
MID = "#2d7a50"
PALE = "#eff7ef"
CREAM = "#f5efe4"
WHITE = "#ffffff"
TEXT = "#15352b"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_brand_icon(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0, color: str = GREEN) -> None:
    def p(px: float, py: float) -> tuple[int, int]:
        return (int(x + px * scale), int(y + py * scale))

    lw = max(2, int(5 * scale))
    draw.line([p(3, 25), p(28, 4), p(53, 25)], fill=color, width=lw, joint="curve")
    draw.line([p(10, 22), p(10, 50), p(46, 50), p(46, 22)], fill=color, width=lw)
    draw.line([p(23, 50), p(23, 34), p(33, 34), p(33, 50)], fill=color, width=max(2, int(4 * scale)))
    draw.ellipse([p(25, 19), p(39, 33)], outline=color, width=max(2, int(3 * scale)))
    draw.line([p(27, 31), p(37, 21)], fill=color, width=max(2, int(2.5 * scale)))
    sx, sy = p(50, 6)
    r = max(3, int(5 * scale))
    draw.line([(sx - r, sy), (sx + r, sy)], fill=color, width=max(1, int(2 * scale)))
    draw.line([(sx, sy - r), (sx, sy + r)], fill=color, width=max(1, int(2 * scale)))


def make_preview() -> None:
    im = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(im)

    for x in range(W):
        if x < 720:
            t = x / 720
            c1 = (247, 250, 247)
            c2 = (237, 247, 239)
        else:
            t = (x - 720) / (W - 720)
            c1 = (246, 241, 230)
            c2 = (233, 228, 208)
        rgb = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
        draw.line([(x, 0), (x, H)], fill=rgb)

    draw_brand_icon(draw, 72, 52, 0.85)
    draw.text((135, 60), "Homekeeping Lab", fill=DARK, font=font(34, True))
    draw.text((137, 101), "Practical home care, laundry & cleaning guides", fill=MID, font=font(17))

    rounded(draw, (72, 165, 315, 207), 21, PALE)
    draw.text((94, 176), "PRACTICAL TIPS, REAL RESULTS", fill=GREEN, font=font(14, True))

    draw.multiline_text((72, 238), "Simple solutions for\na cleaner home", fill=DARK, font=font(57, True), spacing=2)
    draw.line([(76, 393), (458, 393)], fill="#39a35e", width=6)
    draw.multiline_text(
        (74, 426),
        "Clear, safety-first guides that help you\nclean smarter and care for what you own.",
        fill=TEXT,
        font=font(22),
        spacing=8,
    )

    draw.line([(930, 170), (995, 360)], fill="#477b43", width=8)
    for box in [(865, 145, 955, 215), (935, 125, 1020, 195), (970, 205, 1060, 275), (850, 235, 940, 305)]:
        draw.ellipse(box, fill="#4c8b45")
    towel_boxes = [
        (930, 402, 1138, 474, "#7a9d72"),
        (920, 354, 1148, 422, "#f8f5ec"),
        (936, 309, 1155, 372, "#d5c29c"),
    ]
    for x1, y1, x2, y2, color in towel_boxes:
        rounded(draw, (x1, y1, x2, y2), 16, color)
        draw.line([(x1 + 15, y1 + 16), (x2 - 15, y1 + 16)], fill="#ffffff", width=2)
    rounded(draw, (760, 280, 890, 480), 24, "#f8fbf7", outline="#c8d3c9", width=3)
    rounded(draw, (792, 239, 855, 304), 12, "#ffffff", outline="#c8d3c9", width=3)
    draw.polygon([(810, 242), (895, 228), (919, 248), (853, 271)], fill="#ffffff", outline="#c8d3c9")
    rounded(draw, (779, 352, 871, 420), 12, PALE)
    draw_brand_icon(draw, 797, 360, 0.65, GREEN)

    rounded(draw, (72, 548, 1128, 592), 22, "#e5f2e6")
    draw.text((316, 559), "A cleaner home. A fresher space. A simpler life.", fill=GREEN, font=font(18, True))

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    im.save(OUT_PATH, "JPEG", quality=88, optimize=True, progressive=True)


def make_publisher_logo() -> None:
    size = 512
    im = Image.new("RGB", (size, size), WHITE)
    draw = ImageDraw.Draw(im)
    rounded(draw, (28, 28, size - 28, size - 28), 96, PALE)
    draw_brand_icon(draw, 125, 112, 4.7, GREEN)
    im.save(PUBLISHER_LOGO_PATH, "PNG", optimize=True)


def extract(pattern: str, text: str, default: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1).strip()) if match else default


def inject_meta() -> None:
    for path in SITE_DIR.rglob("*.html"):
        text = path.read_text(encoding="utf-8")

        if path.name == "404.html":
            text = text.replace(
                '<meta name="robots" content="index,follow,max-image-preview:large">',
                '<meta name="robots" content="noindex,follow">',
                1,
            )

        if 'property="og:image"' in text:
            path.write_text(text, encoding="utf-8")
            continue

        title = extract(r"<title>(.*?)</title>", text, "Homekeeping Lab")
        description = extract(r'<meta\s+name="description"\s+content="([^"]*)"', text, "Practical, safety-first home care guides.")
        canonical = extract(r'<link\s+rel="canonical"\s+href="([^"]*)"', text, SITE_URL)
        og_type = "article" if "/guides/" in canonical else "website"

        def esc(value: str) -> str:
            return html.escape(value, quote=True)

        tags = f'''\n<meta property="og:site_name" content="Homekeeping Lab">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{IMAGE_URL}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Homekeeping Lab — practical home care guides">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{IMAGE_URL}">'''

        if "</head>" in text:
            text = text.replace("</head>", tags + "\n</head>", 1)
            path.write_text(text, encoding="utf-8")


def enhance_structured_data() -> None:
    pattern = re.compile(r'(<script\s+type="application/ld\+json">)(.*?)(</script>)', re.IGNORECASE | re.DOTALL)

    for path in SITE_DIR.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        canonical = extract(r'<link\s+rel="canonical"\s+href="([^"]*)"', text, "")
        if "/guides/" not in canonical:
            continue

        def replace_schema(match: re.Match[str]) -> str:
            try:
                data = json.loads(match.group(2))
            except json.JSONDecodeError:
                return match.group(0)

            nodes = data.get("@graph", []) if isinstance(data, dict) else []
            changed = False
            for node in nodes:
                if not isinstance(node, dict) or node.get("@type") != "Article":
                    continue

                node["mainEntityOfPage"] = {"@type": "WebPage", "@id": canonical}
                node["image"] = {
                    "@type": "ImageObject",
                    "url": IMAGE_URL,
                    "width": 1200,
                    "height": 630,
                }
                node["author"] = {
                    "@type": "Organization",
                    "name": "Homekeeping Lab",
                    "url": ABOUT_URL,
                }
                node["publisher"] = {
                    "@type": "Organization",
                    "name": "Homekeeping Lab",
                    "url": SITE_URL,
                    "logo": {
                        "@type": "ImageObject",
                        "url": PUBLISHER_LOGO_URL,
                        "width": 512,
                        "height": 512,
                    },
                }
                changed = True

            if not changed:
                return match.group(0)

            encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
            return match.group(1) + encoded + match.group(3)

        updated = pattern.sub(replace_schema, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    make_preview()
    make_publisher_logo()
    inject_meta()
    enhance_structured_data()
    print(f"Wrote {OUT_PATH}, {PUBLISHER_LOGO_PATH}, and enhanced social/Article metadata.")

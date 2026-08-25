from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"

MAX_HTML_BYTES = 80 * 1024
MAX_TOTAL_CSS_BYTES = 50 * 1024
MAX_SOCIAL_IMAGE_BYTES = 400 * 1024
MAX_PUBLISHER_LOGO_BYTES = 120 * 1024
MAX_FAVICON_BYTES = 20 * 1024
MAX_HOMEPAGE_PLUS_CSS_BYTES = 50 * 1024


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.external_scripts: list[dict[str, str | None]] = []
        self.images: list[dict[str, str | None]] = []
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): value for key, value in attrs}
        lower = tag.lower()
        if lower == "meta" and (data.get("name") or "").lower() == "viewport":
            self.has_viewport = True
        elif lower == "script" and data.get("src"):
            src = data.get("src") or ""
            if src.startswith(("http://", "https://", "//")):
                self.external_scripts.append(data)
        elif lower == "img":
            self.images.append(data)


def size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def main() -> None:
    problems: list[str] = []
    html_files = list(SITE_DIR.rglob("*.html"))
    css_files = list(SITE_DIR.rglob("*.css"))

    if not html_files:
        raise SystemExit("Performance/mobile audit FAILED: no generated HTML files")

    for html_path in html_files:
        relative = html_path.relative_to(SITE_DIR)
        html_size = size(html_path)
        if html_size > MAX_HTML_BYTES:
            problems.append(f"HTML too large ({html_size} bytes): {relative}")

        text = html_path.read_text(encoding="utf-8")
        parser = ResourceParser()
        parser.feed(text)

        if not parser.has_viewport:
            problems.append(f"missing mobile viewport meta: {relative}")

        for script in parser.external_scripts:
            # External JS must not block first paint.
            if "async" not in script and "defer" not in script:
                problems.append(f"render-blocking external script in {relative}: {script.get('src')}")

        for image in parser.images:
            src = image.get("src") or "[unknown]"
            if not image.get("width") or not image.get("height"):
                problems.append(f"image missing width/height in {relative}: {src}")
            # Below-the-fold content images should normally be lazy-loaded. Hero/logo images are exempt.
            classes = image.get("class") or ""
            if "hero" not in classes and "logo" not in classes and image.get("loading") not in {"lazy", "eager"}:
                problems.append(f"image missing explicit loading policy in {relative}: {src}")

        if 'id="hl-mobile-style"' not in text:
            problems.append(f"mobile navigation/touch override missing: {relative}")
        if 'name="viewport"' in text and "width=device-width" not in text:
            problems.append(f"viewport does not use device width: {relative}")

    total_css = sum(size(path) for path in css_files)
    if total_css > MAX_TOTAL_CSS_BYTES:
        problems.append(f"CSS budget exceeded: {total_css} bytes")

    homepage = SITE_DIR / "index.html"
    if homepage.exists() and size(homepage) + total_css > MAX_HOMEPAGE_PLUS_CSS_BYTES:
        problems.append(
            f"homepage + CSS budget exceeded: {size(homepage) + total_css} bytes"
        )

    assets = {
        SITE_DIR / "social-preview.jpg": MAX_SOCIAL_IMAGE_BYTES,
        SITE_DIR / "publisher-logo.png": MAX_PUBLISHER_LOGO_BYTES,
        SITE_DIR / "favicon.svg": MAX_FAVICON_BYTES,
    }
    for path, limit in assets.items():
        if not path.exists():
            problems.append(f"expected asset missing: {path.name}")
        elif size(path) > limit:
            problems.append(f"asset too large ({size(path)} bytes): {path.name}")

    # The generated mobile override must keep navigation reachable and touch targets usable.
    common = (ROOT / "scripts" / "common.py").read_text(encoding="utf-8")
    if "hl-mobile-style" not in common:
        problems.append("central mobile override is not defined in scripts/common.py")
    if not re.search(r"min-height\s*:\s*44px", common):
        problems.append("44px mobile touch-target minimum is not defined")

    if problems:
        print("Performance/mobile audit FAILED:")
        for problem in problems:
            print(f" - {problem}")
        raise SystemExit(1)

    print(
        "Performance/mobile audit PASS: "
        f"{len(html_files)} HTML pages, {total_css} CSS bytes, "
        f"homepage {size(homepage)} bytes, social preview {size(SITE_DIR / 'social-preview.jpg')} bytes."
    )


if __name__ == "__main__":
    main()

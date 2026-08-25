from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
CONFIG_PATH = ROOT / "config" / "site.json"
SITEMAP_PATH = SITE_DIR / "sitemap.xml"
ROBOTS_PATH = SITE_DIR / "robots.txt"


def extract(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else default


def html_for_url(site_url: str, domain: str) -> Path | None:
    parts = urlsplit(site_url)
    base = urlsplit(domain)
    if parts.scheme != base.scheme or parts.netloc != base.netloc:
        return None
    if parts.query or parts.fragment:
        return None

    path = parts.path or "/"
    if path == "/":
        return SITE_DIR / "index.html"
    relative = path.lstrip("/")
    if path.endswith("/"):
        return SITE_DIR / relative / "index.html"
    return SITE_DIR / relative


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    domain = config["domain"].rstrip("/")
    sitemap_url = f"{domain}/sitemap.xml"
    problems: list[str] = []

    if not SITEMAP_PATH.exists():
        raise SystemExit("Indexability audit FAILED: sitemap.xml is missing")
    if not ROBOTS_PATH.exists():
        raise SystemExit("Indexability audit FAILED: robots.txt is missing")

    # Parse sitemap URLs.
    try:
        root = ET.parse(SITEMAP_PATH).getroot()
    except ET.ParseError as exc:
        raise SystemExit(f"Indexability audit FAILED: invalid sitemap XML: {exc}") from exc

    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = [
        (node.text or "").strip()
        for node in root.findall("sm:url/sm:loc", namespace)
        if (node.text or "").strip()
    ]
    sitemap_set = set(sitemap_urls)
    if len(sitemap_urls) != len(sitemap_set):
        problems.append("sitemap contains duplicate URLs")

    # Robots must advertise the canonical sitemap and must not block the whole site.
    robots = ROBOTS_PATH.read_text(encoding="utf-8")
    if f"Sitemap: {sitemap_url}" not in robots:
        problems.append("robots.txt does not advertise the canonical sitemap URL")
    if re.search(r"(?im)^\s*Disallow:\s*/\s*$", robots):
        problems.append("robots.txt blocks the entire site with Disallow: /")

    canonical_to_file: dict[str, Path] = {}
    indexable_urls: set[str] = set()
    html_files = list(SITE_DIR.rglob("*.html"))

    # Every generated HTML page must clearly declare whether it is indexable.
    for html_path in html_files:
        text = html_path.read_text(encoding="utf-8")
        relative = html_path.relative_to(SITE_DIR)
        robots_meta = extract(r'<meta\s+name="robots"\s+content="([^"]*)"', text)
        canonical = extract(r'<link\s+rel="canonical"\s+href="([^"]*)"', text)

        is_noindex = "noindex" in robots_meta.lower()
        if relative.as_posix() == "404.html" and not is_noindex:
            problems.append("404.html must be noindex")

        if not canonical:
            problems.append(f"missing canonical: {relative}")
            continue

        parts = urlsplit(canonical)
        base = urlsplit(domain)
        if parts.scheme != "https":
            problems.append(f"canonical is not HTTPS: {canonical}")
        if parts.scheme != base.scheme or parts.netloc != base.netloc:
            problems.append(f"canonical uses the wrong origin: {canonical}")
        if parts.query or parts.fragment:
            problems.append(f"canonical contains query or fragment: {canonical}")

        if is_noindex:
            if canonical in sitemap_set:
                problems.append(f"noindex page appears in sitemap: {canonical}")
            continue

        if canonical in canonical_to_file:
            problems.append(
                f"duplicate canonical {canonical}: {canonical_to_file[canonical].relative_to(SITE_DIR)} and {relative}"
            )
        else:
            canonical_to_file[canonical] = html_path

        indexable_urls.add(canonical)
        if canonical not in sitemap_set:
            problems.append(f"indexable page missing from sitemap: {canonical}")

    # Every sitemap URL must resolve to a generated, indexable page whose canonical matches it.
    for sitemap_entry in sitemap_urls:
        target = html_for_url(sitemap_entry, domain)
        if target is None:
            problems.append(f"sitemap URL has invalid origin/query/fragment: {sitemap_entry}")
            continue
        if not target.exists():
            problems.append(f"sitemap URL has no generated page: {sitemap_entry}")
            continue

        text = target.read_text(encoding="utf-8")
        robots_meta = extract(r'<meta\s+name="robots"\s+content="([^"]*)"', text)
        canonical = extract(r'<link\s+rel="canonical"\s+href="([^"]*)"', text)
        if "noindex" in robots_meta.lower():
            problems.append(f"sitemap points to noindex page: {sitemap_entry}")
        if canonical != sitemap_entry:
            problems.append(
                f"sitemap/canonical mismatch: sitemap={sitemap_entry}, canonical={canonical or '[missing]'}"
            )

    extra_sitemap = sitemap_set - indexable_urls
    if extra_sitemap:
        for item in sorted(extra_sitemap):
            problems.append(f"sitemap contains non-indexable or unknown URL: {item}")

    if problems:
        print("Sitemap/indexability audit FAILED:")
        for problem in problems:
            print(f" - {problem}")
        raise SystemExit(1)

    print(
        f"Sitemap/indexability audit PASS: {len(indexable_urls)} indexable pages, "
        f"{len(sitemap_urls)} sitemap URLs, {len(html_files)} HTML files checked."
    )


if __name__ == "__main__":
    main()

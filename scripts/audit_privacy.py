from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"


def require(text: str, needle: str, label: str, problems: list[str]) -> None:
    if needle not in text:
        problems.append(f"missing {label}")


def main() -> None:
    problems: list[str] = []
    privacy_path = SITE_DIR / "privacy-policy" / "index.html"
    cookie_path = SITE_DIR / "cookie-policy" / "index.html"
    home_path = SITE_DIR / "index.html"
    sitemap_path = SITE_DIR / "sitemap.xml"

    for path, label in ((privacy_path, "privacy policy"), (cookie_path, "cookie policy"), (home_path, "homepage"), (sitemap_path, "sitemap")):
        if not path.exists():
            problems.append(f"missing {label}: {path.relative_to(ROOT)}")

    if problems:
        print("Privacy/consent audit FAILED:")
        for problem in problems:
            print(f" - {problem}")
        raise SystemExit(1)

    privacy = privacy_path.read_text(encoding="utf-8")
    cookie = cookie_path.read_text(encoding="utf-8")
    home = home_path.read_text(encoding="utf-8")
    sitemap = sitemap_path.read_text(encoding="utf-8")

    require(privacy, "Google Analytics", "Google Analytics disclosure in privacy policy", problems)
    require(privacy, "Cloudflare", "Cloudflare disclosure in privacy policy", problems)
    require(privacy, "homekeepinglab_analytics_consent_v1", "consent storage disclosure in privacy policy", problems)
    require(cookie, "analytics_storage", "analytics consent-mode disclosure in cookie policy", problems)
    require(cookie, "ad_storage", "advertising consent-mode disclosure in cookie policy", problems)
    require(cookie, "_ga", "Google Analytics cookie example in cookie policy", problems)
    require(home, 'href="/privacy-policy/"', "privacy-policy footer link", problems)
    require(home, 'href="/cookie-policy/"', "cookie-policy footer link", problems)
    require(home, 'id="hl-cookie-settings"', "cookie-settings control", problems)
    require(home, 'id="hl-consent"', "consent dialog", problems)
    require(home, "'analytics_storage': savedAnalyticsConsent === 'granted' ? 'granted' : 'denied'", "default-denied analytics consent", problems)
    require(home, "'ad_storage': 'denied'", "default-denied ad storage", problems)
    require(home, "'ad_user_data': 'denied'", "default-denied ad user data", problems)
    require(home, "'ad_personalization': 'denied'", "default-denied ad personalization", problems)
    require(sitemap, "/privacy-policy/", "privacy policy in sitemap", problems)
    require(sitemap, "/cookie-policy/", "cookie policy in sitemap", problems)

    html_files = list(SITE_DIR.rglob("*.html"))
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(SITE_DIR)
        if 'id="hl-consent"' not in text:
            problems.append(f"consent dialog missing from {rel}")
        if 'id="hl-cookie-settings"' not in text:
            problems.append(f"cookie settings control missing from {rel}")

    if problems:
        print("Privacy/consent audit FAILED:")
        for problem in problems:
            print(f" - {problem}")
        raise SystemExit(1)

    print(f"Privacy/consent audit PASS: {len(html_files)} HTML pages checked.")


if __name__ == "__main__":
    main()

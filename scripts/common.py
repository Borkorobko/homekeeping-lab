from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "content_plan.csv"
CONFIG_PATH = ROOT / "config" / "site.json"
ARTICLES_DIR = ROOT / "content" / "articles"
QA_DIR = ROOT / "qa"
SOURCES_DIR = ROOT / "sources"
SITE_DIR = ROOT / "site"

ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
QA_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)

GA_MEASUREMENT_ID = "G-6L050GSVSB"
CONSENT_KEY = "homekeepinglab_analytics_consent_v1"
FAVICON_LINK = '<link rel="icon" type="image/svg+xml" href="/favicon.svg">'
FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="16" fill="#2e6b58"/>
  <text x="32" y="40" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="25" font-weight="700" fill="#ffffff">HL</text>
</svg>'''
BRAND_MARK_HTML = '''<span class="brand-mark hl-logo" aria-hidden="true"><svg viewBox="0 0 36 36"><path d="M8.5 17.5 18 9.5l9.5 8v10H22v-6.5h-8v6.5H8.5z" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linejoin="round" stroke-linecap="round"/><path d="M27.5 5.5v5M25 8h5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg></span>'''
BRAND_MARK_STYLE = '''<style id="hl-brand-mark-style">.brand-mark.hl-logo{display:grid;place-items:center;background:linear-gradient(145deg,#347863,#245747);color:#fff;box-shadow:0 5px 14px rgba(35,86,71,.16);transition:.16s ease}.brand-mark.hl-logo svg{width:27px;height:27px;display:block}.brand:hover .brand-mark.hl-logo{transform:translateY(-1px);box-shadow:0 7px 18px rgba(35,86,71,.22)}</style>'''
MOBILE_STYLE = '''<style id="hl-mobile-style">@media(max-width:760px){.site-header .nav-wrap{min-height:auto;display:block;padding:10px 0}.site-header .brand{width:max-content}.site-header .nav-wrap nav{display:flex;gap:6px;flex-wrap:nowrap;overflow-x:auto;white-space:nowrap;padding:7px 0 2px;scrollbar-width:thin;-webkit-overflow-scrolling:touch}.site-header .nav-wrap nav a{display:inline-flex;align-items:center;min-height:44px;padding:0 8px}#hl-consent button{min-height:44px}}</style>'''

GA_SNIPPET = f'''<!-- Google tag (gtag.js) -->
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  var savedAnalyticsConsent = null;
  try {{ savedAnalyticsConsent = localStorage.getItem('{CONSENT_KEY}'); }} catch (e) {{}}
  gtag('consent', 'default', {{
    'analytics_storage': savedAnalyticsConsent === 'granted' ? 'granted' : 'denied',
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied',
    'wait_for_update': 500
  }});
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>'''

CONSENT_BANNER = f'''<style>
#hl-consent{{position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:760px;margin:0 auto;background:#fff;border:1px solid #dfe6e2;border-radius:16px;box-shadow:0 12px 36px rgba(20,48,43,.18);padding:18px 20px;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#18302b;display:none}}
#hl-consent p{{margin:0 0 14px;line-height:1.5;font-size:.95rem}}
#hl-consent-actions{{display:flex;gap:10px;flex-wrap:wrap}}
#hl-consent button{{border:1px solid #2e6b58;border-radius:10px;padding:10px 14px;font-weight:700;cursor:pointer;font:inherit}}
#hl-consent-accept{{background:#2e6b58;color:#fff}}
#hl-consent-reject{{background:#fff;color:#2e6b58}}
</style>
<div id="hl-consent" role="dialog" aria-live="polite" aria-label="Analytics cookie preferences">
  <p><strong>Analytics cookies</strong><br>We use optional Google Analytics cookies to understand how visitors use Homekeeping Lab. You can accept or reject analytics cookies. Essential site functions do not depend on them.</p>
  <div id="hl-consent-actions">
    <button id="hl-consent-accept" type="button">Accept analytics</button>
    <button id="hl-consent-reject" type="button">Reject</button>
  </div>
</div>
<script>
(function(){{
  var key = '{CONSENT_KEY}';
  var banner = document.getElementById('hl-consent');
  var saved = null;
  try {{ saved = localStorage.getItem(key); }} catch (e) {{}}

  function setConsent(value) {{
    try {{ localStorage.setItem(key, value); }} catch (e) {{}}
    gtag('consent', 'update', {{'analytics_storage': value}});
    if (value === 'granted') {{
      gtag('event', 'page_view', {{page_location: window.location.href, page_title: document.title}});
    }}
    banner.style.display = 'none';
  }}

  if (!saved) {{ banner.style.display = 'block'; }}
  document.getElementById('hl-consent-accept').addEventListener('click', function(){{ setConsent('granted'); }});
  document.getElementById('hl-consent-reject').addEventListener('click', function(){{ setConsent('denied'); }});
}})();
</script>'''

# Build output is generated from several call sites in build_site.py. Inject the
# analytics tag, favicon, mobile behavior and consent controls centrally into every
# generated HTML file so future articles and hub pages inherit them automatically.
_ORIGINAL_WRITE_TEXT = Path.write_text


def _write_text_with_analytics(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
    try:
        is_site_html = self.suffix.lower() == ".html" and (self == SITE_DIR or SITE_DIR in self.parents)
    except Exception:
        is_site_html = False

    if is_site_html:
        if GA_MEASUREMENT_ID not in data and "<head>" in data:
            data = data.replace("<head>", "<head>\n" + GA_SNIPPET, 1)
        if "/favicon.svg" not in data and "<head>" in data:
            data = data.replace("<head>", "<head>\n" + FAVICON_LINK, 1)
        if 'id="hl-brand-mark-style"' not in data and "<head>" in data:
            data = data.replace("<head>", "<head>\n" + BRAND_MARK_STYLE, 1)
        if 'id="hl-mobile-style"' not in data and "<head>" in data:
            data = data.replace("<head>", "<head>\n" + MOBILE_STYLE, 1)
        data = data.replace('<span class="brand-mark">HL</span>', BRAND_MARK_HTML)
        if "id=\"hl-consent\"" not in data and "</body>" in data:
            data = data.replace("</body>", CONSENT_BANNER + "\n</body>", 1)

    result = _ORIGINAL_WRITE_TEXT(self, data, *args, **kwargs)

    # build_site.py recreates SITE_DIR on each build, so create the favicon again
    # during the first HTML write instead of relying on a hand-maintained output file.
    if is_site_html:
        favicon_path = SITE_DIR / "favicon.svg"
        if not favicon_path.exists() or favicon_path.read_text(encoding="utf-8") != FAVICON_SVG:
            _ORIGINAL_WRITE_TEXT(favicon_path, FAVICON_SVG, encoding="utf-8")

    return result


Path.write_text = _write_text_with_analytics


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_plan() -> list[dict[str, str]]:
    with PLAN_PATH.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def save_plan(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError("content_plan.csv cannot be empty")
    fieldnames = list(rows[0].keys())
    with PLAN_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plan_by_id(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    return {int(row["ID"]): row for row in rows}


def article_path(row: dict[str, str]) -> Path:
    return ARTICLES_DIR / f'{row["Slug"]}.json'


def qa_path(row: dict[str, str]) -> Path:
    return QA_DIR / f'{row["Slug"]}.json'


def source_path(row: dict[str, str]) -> Path:
    return SOURCES_DIR / f'{row["ID"]}.json'


def load_source_packet(row: dict[str, str]) -> dict[str, Any] | None:
    path = source_path(row)
    if not path.exists():
        return None
    packet = json.loads(path.read_text(encoding="utf-8"))
    sources = packet.get("sources", [])
    if not isinstance(sources, list) or not sources:
        return None
    return packet


def normalize_source_required(value: str) -> bool:
    return value.strip().lower() in {"yes", "true", "1"}


def article_text(article: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "summary", "quick_answer"):
        value = article.get(key)
        if isinstance(value, str):
            parts.append(value)
    for key in ("items_needed", "steps", "mistakes", "safety_notes"):
        value = article.get(key, [])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if isinstance(v, (str, int, float)))
    for section in article.get("sections", []):
        if isinstance(section, dict):
            parts.extend(str(v) for v in section.values() if isinstance(v, str))
            bullets = section.get("bullets", [])
            if isinstance(bullets, list):
                parts.extend(str(v) for v in bullets)
    for item in article.get("faq", []):
        if isinstance(item, dict):
            parts.extend(str(v) for v in item.values() if isinstance(v, str))
    return "\n".join(parts)

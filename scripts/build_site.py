from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from common import (
    SITE_DIR,
    article_path,
    load_config,
    load_plan,
    load_source_packet,
    plan_by_id,
    save_plan,
)

config = load_config()
rows = load_plan()
by_id = plan_by_id(rows)
DOMAIN = config["domain"].rstrip("/")
SITE_NAME = config["site_name"]
TODAY = datetime.now(timezone.utc).date().isoformat()


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def url(path: str = "") -> str:
    if not path:
        return f"{DOMAIN}/"
    return f"{DOMAIN}/{path.lstrip('/')}"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def nav() -> str:
    return '''<header class="site-header"><div class="wrap nav-wrap">
<a class="brand" href="/"><span class="brand-mark">HL</span><span>Homekeeping Lab</span></a>
<nav aria-label="Primary"><a href="/laundry/">Laundry</a><a href="/stain-removal/">Stains</a><a href="/bathroom/">Bathroom</a><a href="/kitchen/">Kitchen</a><a href="/about/">About</a></nav>
</div></header>'''


def footer() -> str:
    return f'''<footer class="site-footer"><div class="wrap footer-grid">
<div><strong>{e(SITE_NAME)}</strong><p>Practical home cleaning, laundry and fabric-care guides with safety-first publishing rules.</p></div>
<div><strong>Explore</strong><a href="/laundry/">Laundry</a><a href="/stain-removal/">Stain removal</a><a href="/home-cleaning/">Home cleaning</a></div>
<div><strong>Policies</strong><a href="/editorial-policy/">Editorial policy</a><a href="/safety/">Safety</a><a href="/privacy-policy/">Privacy policy</a><a href="/cookie-policy/">Cookie policy</a><button class="footer-cookie-settings" id="hl-cookie-settings" type="button">Cookie settings</button><a href="/about/">About</a></div>
</div><div class="wrap footer-bottom">© {TODAY[:4]} {e(SITE_NAME)}</div></footer>'''


def page(title: str, description: str, canonical: str, body: str, schema: dict | None = None) -> str:
    schema_html = ""
    if schema:
        schema_html = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    return f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(description[:160])}">
<meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{e(canonical)}">
<link rel="stylesheet" href="/assets/style.css">{schema_html}</head><body>{nav()}<main>{body}</main>{footer()}</body></html>'''


def article_card(row: dict[str, str], article: dict) -> str:
    return f'''<article class="card"><span class="tag">{e(row['Category'])}</span>
<h3><a href="/guides/{e(row['Slug'])}/">{e(row['Title'])}</a></h3>
<p>{e(article.get('summary', ''))}</p><a class="text-link" href="/guides/{e(row['Slug'])}/">Read guide →</a></article>'''


def published_rows() -> list[dict[str, str]]:
    return [row for row in rows if row["Status"] in {"SafetyPassed", "Published"} and article_path(row).exists()]


def render_article(row: dict[str, str], article: dict, published: dict[int, dict[str, str]]) -> str:
    meta = article.get("meta", {})
    parts: list[str] = []
    parts.append(f'''<section class="article-hero"><div class="article-wrap"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>›</span><a href="{e(row['ParentHub'])}">{e(row['Category'])}</a></nav>
<span class="tag">{e(row['Category'])}</span><h1>{e(row['Title'])}</h1><p class="lede">{e(article.get('summary',''))}</p>
<div class="article-meta">Updated {e(row['PublishedDate'] or TODAY)} · Risk level {e(row['RiskLevel'])}</div></div></section>''')
    parts.append(f'''<article class="article-wrap article-body"><section class="quick-answer"><h2>Quick answer</h2><p>{e(article.get('quick_answer',''))}</p></section>''')

    items = article.get("items_needed", [])
    if items:
        parts.append('<section><h2>What you need</h2><ul>')
        parts.extend(f"<li>{e(item)}</li>" for item in items)
        parts.append("</ul></section>")

    steps = article.get("steps", [])
    if steps:
        parts.append('<section><h2>Step-by-step</h2><ol class="steps">')
        for step in steps:
            parts.append(f"<li><h3>{e(step.get('title',''))}</h3><p>{e(step.get('body',''))}</p></li>")
        parts.append("</ol></section>")

    for section in article.get("sections", []):
        parts.append(f"<section><h2>{e(section.get('heading',''))}</h2><p>{e(section.get('body',''))}</p>")
        bullets = section.get("bullets", [])
        if bullets:
            parts.append("<ul>")
            parts.extend(f"<li>{e(item)}</li>" for item in bullets)
            parts.append("</ul>")
        parts.append("</section>")

    mistakes = article.get("mistakes", [])
    if mistakes:
        parts.append('<section class="warning-box"><h2>What not to do</h2><ul>')
        parts.extend(f"<li>{e(item)}</li>" for item in mistakes)
        parts.append("</ul></section>")

    safety_notes = article.get("safety_notes", [])
    if safety_notes:
        parts.append('<section class="safety-box"><h2>Safety notes</h2><ul>')
        parts.extend(f"<li>{e(item)}</li>" for item in safety_notes)
        parts.append("</ul></section>")

    faq = article.get("faq", [])
    if faq:
        parts.append('<section><h2>Frequently asked questions</h2>')
        for item in faq:
            parts.append(f"<h3>{e(item.get('question',''))}</h3><p>{e(item.get('answer',''))}</p>")
        parts.append("</section>")

    packet = load_source_packet(row)
    if packet:
        parts.append('<section class="sources"><h2>Sources & safety references</h2><ul>')
        for source in packet.get("sources", []):
            href = source.get("url", "")
            host = urlparse(href).netloc
            parts.append(f'''<li><a href="{e(href)}" rel="nofollow noopener">{e(source.get('title','Source'))}</a> — {e(source.get('authority', host))}</li>''')
        parts.append("</ul></section>")

    related = [published[rid] for rid in meta.get("related_ids", []) if rid in published][: config["seo"]["max_related_articles"]]
    if related:
        parts.append('<section><h2>Related guides</h2><div class="related-grid">')
        for rel in related:
            parts.append(f'''<a class="related-card" href="/guides/{e(rel['Slug'])}/"><span>{e(rel['Category'])}</span><strong>{e(rel['Title'])}</strong></a>''')
        parts.append("</div></section>")

    parts.append('</article>')
    return "".join(parts)


# Rebuild generated output from scratch so stale pages cannot linger.
if SITE_DIR.exists():
    shutil.rmtree(SITE_DIR)
SITE_DIR.mkdir(parents=True, exist_ok=True)

# Promote SafetyPassed drafts only during a successful build.
for row in rows:
    if row["Status"] == "SafetyPassed" and article_path(row).exists():
        row["Status"] = "Published"
        if not row["PublishedDate"]:
            row["PublishedDate"] = TODAY

published = {int(row["ID"]): row for row in published_rows()}
articles: dict[int, dict] = {}
for rid, row in published.items():
    articles[rid] = json.loads(article_path(row).read_text(encoding="utf-8"))

STYLE = r'''
:root{--ink:#18302b;--muted:#60716d;--bg:#f5f7f4;--card:#fff;--line:#dfe6e2;--accent:#2e6b58;--accent2:#dceadf;--warn:#fff4db;--safe:#e6f4ed;--wrap:1120px}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.65}.wrap{width:min(var(--wrap),calc(100% - 32px));margin:auto}.site-header{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}.nav-wrap{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{display:flex;gap:10px;align-items:center;color:var(--ink);font-weight:800;text-decoration:none}.brand-mark{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--accent);color:#fff}.site-header nav{display:flex;gap:18px;flex-wrap:wrap}.site-header nav a,.site-footer a{color:var(--ink);text-decoration:none}.hero{padding:72px 0 44px;background:linear-gradient(145deg,#edf4ef,#f9faf8)}.hero h1{font-size:clamp(2.3rem,6vw,4.8rem);line-height:1.02;max-width:850px;margin:.2em 0}.hero p{max-width:720px;font-size:1.15rem;color:var(--muted)}.section{padding:48px 0}.section h2{font-size:2rem}.grid,.category-grid,.related-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.card,.category-card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:24px}.card h3,.category-card h3{margin:.5rem 0}.card a,.category-card a,.text-link{color:var(--accent);text-decoration:none}.tag{display:inline-block;border-radius:999px;background:var(--accent2);padding:5px 10px;font-size:.78rem;font-weight:800;text-transform:uppercase;letter-spacing:.04em}.article-hero{background:#edf4ef;padding:42px 0}.article-wrap{width:min(760px,calc(100% - 32px));margin:auto}.article-hero h1{font-size:clamp(2.2rem,5vw,4rem);line-height:1.08;margin:.35em 0}.lede{font-size:1.2rem;color:var(--muted)}.article-meta,.breadcrumbs{color:var(--muted);font-size:.9rem}.breadcrumbs{display:flex;gap:8px;margin-bottom:22px}.breadcrumbs a{color:inherit}.article-body{background:#fff;margin-top:28px;margin-bottom:48px;padding:34px;border:1px solid var(--line);border-radius:20px}.article-body h2{font-size:1.65rem;margin-top:2rem}.article-body h3{font-size:1.12rem}.quick-answer,.warning-box,.safety-box{padding:20px 22px;border-radius:14px;margin:22px 0}.quick-answer{background:#eef5f1}.warning-box{background:var(--warn)}.safety-box{background:var(--safe)}.steps li{padding-left:6px;margin:18px 0}.sources{border-top:1px solid var(--line);padding-top:10px}.related-grid{grid-template-columns:repeat(2,1fr)}.related-card{display:flex;flex-direction:column;padding:16px;border:1px solid var(--line);border-radius:12px;text-decoration:none;color:var(--ink)}.related-card span{color:var(--muted);font-size:.82rem}.site-footer{background:#16332b;color:#e9f1ee;padding:44px 0 22px}.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:28px}.site-footer a{display:block;color:#e9f1ee;margin:7px 0}.footer-cookie-settings{display:block;background:none;border:0;color:#e9f1ee;padding:0;margin:7px 0;font:inherit;cursor:pointer;text-align:left}.footer-cookie-settings:hover,.footer-cookie-settings:focus{text-decoration:underline}.footer-bottom{border-top:1px solid #345249;margin-top:28px;padding-top:18px;color:#bfcfca}@media(max-width:760px){.site-header nav{display:none}.grid,.category-grid,.related-grid,.footer-grid{grid-template-columns:1fr}.article-body{padding:22px}.hero{padding-top:48px}.footer-cookie-settings{min-height:44px}}
'''
write(SITE_DIR / "assets" / "style.css", STYLE)

# Article pages and structured data.
for rid, row in published.items():
    article = articles[rid]
    canonical = url(f"guides/{row['Slug']}/")
    faq_entities = [
        {"@type": "Question", "name": item.get("question", ""), "acceptedAnswer": {"@type": "Answer", "text": item.get("answer", "")}}
        for item in article.get("faq", [])
    ]
    graph = [
        {
            "@type": "Article",
            "headline": row["Title"],
            "description": article.get("summary", ""),
            "datePublished": row["PublishedDate"] or TODAY,
            "dateModified": row["PublishedDate"] or TODAY,
            "mainEntityOfPage": canonical,
            "publisher": {"@type": "Organization", "name": SITE_NAME, "url": url()},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": url()},
                {"@type": "ListItem", "position": 2, "name": row["Category"], "item": url(row["ParentHub"])},
                {"@type": "ListItem", "position": 3, "name": row["Title"], "item": canonical},
            ],
        },
    ]
    if faq_entities:
        graph.append({"@type": "FAQPage", "mainEntity": faq_entities})
    schema = {"@context": "https://schema.org", "@graph": graph}
    body = render_article(row, article, published)
    write(SITE_DIR / "guides" / row["Slug"] / "index.html", page(f"{row['Title']} | {SITE_NAME}", article.get("summary", ""), canonical, body, schema))

# Category hubs.
for category in config["categories"]:
    matching = [row for row in published.values() if row["Category"] == category["name"]]
    cards = "".join(article_card(row, articles[int(row["ID"])]) for row in matching)
    if not cards:
        cards = '<div class="card"><h3>Guides are being prepared</h3><p>This section will grow as safety and quality checks are completed.</p></div>'
    body = f'''<section class="hero"><div class="wrap"><span class="tag">Topic hub</span><h1>{e(category['name'])}</h1><p>Practical {e(category['name'].lower())} guides from Homekeeping Lab.</p></div></section><section class="section"><div class="wrap"><div class="grid">{cards}</div></div></section>'''
    write(SITE_DIR / category["slug"] / "index.html", page(f"{category['name']} Guides | {SITE_NAME}", f"Practical {category['name'].lower()} guides for everyday home care.", url(f"{category['slug']}/"), body))

# Home page.
latest = sorted(published.values(), key=lambda r: (r["PublishedDate"], int(r["ID"])), reverse=True)[:9]
latest_cards = "".join(article_card(row, articles[int(row["ID"])]) for row in latest)
if not latest_cards:
    latest_cards = '<div class="card"><h3>Launch guides are in preparation</h3><p>The publishing pipeline is active, but only articles that pass both quality and safety gates are shown here.</p></div>'
category_cards = "".join(f'''<article class="category-card"><h3><a href="/{e(cat['slug'])}/">{e(cat['name'])}</a></h3><p>Browse practical {e(cat['name'].lower())} guides.</p></article>''' for cat in config["categories"])
home_body = f'''<section class="hero"><div class="wrap"><span class="tag">Practical home care</span><h1>Clean smarter. Care for what you own.</h1><p>Homekeeping Lab publishes clear, evergreen guides for laundry, stains, fabrics, kitchens, bathrooms, odors and everyday home maintenance—with safety gates for chemical advice.</p></div></section>
<section class="section"><div class="wrap"><h2>Explore by topic</h2><div class="category-grid">{category_cards}</div></div></section>
<section class="section"><div class="wrap"><h2>Latest guides</h2><div class="grid">{latest_cards}</div></div></section>'''
org_schema = {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": url()}
write(SITE_DIR / "index.html", page(f"{SITE_NAME} | Practical Cleaning, Laundry & Home Care", "Practical, safety-first guides for laundry, stain removal, fabric care, cleaning, odors and everyday home maintenance.", url(), home_body, org_schema))

# Trust and transparency pages.
about_body = '''<section class="hero"><div class="wrap"><h1>About Homekeeping Lab</h1><p>Homekeeping Lab is an independent practical-reference site focused on solving everyday cleaning, laundry, fabric-care and home-maintenance problems clearly.</p></div></section><section class="section"><div class="article-wrap"><h2>How the site is built</h2><p>Articles may be produced with automated assistance. Publication is controlled by structured content plans plus deterministic quality and safety checks. Safety-sensitive topics require verified source packets before they can move through the automated pipeline.</p><h2>What we optimize for</h2><p>We prioritize a direct answer, material compatibility, clear steps, useful warnings and durable evergreen guidance over filler or dramatic cleaning hacks.</p></div></section>'''
write(SITE_DIR / "about" / "index.html", page(f"About | {SITE_NAME}", "About Homekeeping Lab and how its practical home-care guides are produced.", url("about/"), about_body))

editorial_body = '''<section class="hero"><div class="wrap"><h1>Editorial policy</h1><p>Our publishing system separates content generation from publication approval.</p></div></section><section class="section"><div class="article-wrap"><h2>Structured publishing</h2><p>Each planned guide has a category, search intent, priority, risk level, source requirement and explicit related-guide relationships. A generated draft must pass a quality gate and a safety gate before it can be published.</p><h2>Automation disclosure</h2><p>Homekeeping Lab may use automated tools to draft, structure and maintain content. We do not present automated output as personal testing or first-hand experience.</p><h2>Corrections and updates</h2><p>Guides are intended to be evergreen. When manufacturer guidance or safety evidence changes, source-sensitive guidance should be rechecked before being updated.</p></div></section>'''
write(SITE_DIR / "editorial-policy" / "index.html", page(f"Editorial Policy | {SITE_NAME}", "How Homekeeping Lab creates, checks and publishes practical home-care guides.", url("editorial-policy/"), editorial_body))

safety_body = '''<section class="hero"><div class="wrap"><h1>Safety policy</h1><p>SEO and automation never override household safety.</p></div></section><section class="section"><div class="article-wrap"><h2>Chemical mixing</h2><p>Our system blocks instructions that recommend dangerous combinations such as bleach with ammonia or acids, and it blocks unknown cleaner combinations.</p><h2>Source-sensitive advice</h2><p>Higher-risk guides cannot proceed automatically without a verified source packet. Product labels and manufacturer instructions take priority over generic cleaning advice.</p><h2>Material compatibility</h2><p>Where compatibility is uncertain, our guides should direct readers to manufacturer guidance or an inconspicuous patch test rather than claim universal safety.</p></div></section>'''
write(SITE_DIR / "safety" / "index.html", page(f"Safety Policy | {SITE_NAME}", "Homekeeping Lab safety rules for household cleaning and chemical advice.", url("safety/"), safety_body))

privacy_body = f'''<section class="hero"><div class="wrap"><h1>Privacy policy</h1><p>This policy explains the current data practices of Homekeeping Lab.</p></div></section><section class="section"><div class="article-wrap"><p><strong>Last updated:</strong> {e(TODAY)}</p><h2>Data you provide</h2><p>Homekeeping Lab currently does not offer user accounts, comments, a newsletter signup or a contact form, so the site does not intentionally ask visitors to submit personal information through those features.</p><h2>Technical and hosting data</h2><p>When you request a page, hosting and security infrastructure may process technical request data needed to deliver and protect the site, such as IP address, browser or device information, requested URL and request timing. Homekeeping Lab is hosted on Cloudflare Pages, so Cloudflare may process this technical data as part of hosting, performance and security operations.</p><h2>Optional Google Analytics</h2><p>Google Analytics is used only as optional audience measurement. Analytics storage is denied by default. If you accept analytics, Google Analytics may process information such as pages viewed, approximate location derived from network information, device and browser characteristics, and interaction or timing data. Google processes this information under its own terms and privacy documentation.</p><h2>Consent preference</h2><p>Your analytics choice is stored locally in your browser under the key <code>homekeepinglab_analytics_consent_v1</code>. You can change your choice at any time by using <strong>Cookie settings</strong> in the site footer. Rejecting analytics updates consent to denied and the site attempts to remove first-party Google Analytics cookies created for this site.</p><h2>Why data is processed</h2><p>Technical hosting and security processing is used to operate, secure and deliver the site. Optional analytics is used only after consent to understand aggregated site usage and improve content and navigation.</p><h2>Retention and third parties</h2><p>Homekeeping Lab does not maintain a separate visitor profile database. Retention of technical hosting data and analytics data is governed by the applicable provider settings and policies. Current third-party services include Cloudflare for hosting and Google Analytics for optional measurement.</p><h2>Your choices and rights</h2><p>You can refuse or withdraw analytics consent without losing access to the site's essential content. You may also use browser controls to remove cookies or site storage. Depending on your location, privacy law may give you additional rights concerning personal data processed by service providers.</p><h2>Future features</h2><p>If Homekeeping Lab later adds advertising, newsletters, accounts, forms or other features that change how personal data is handled, this policy and the consent controls should be updated before those features are enabled.</p><h2>Operator information</h2><p>Homekeeping Lab is currently an independently operated informational site. Operator contact details will be published here before any feature that directly collects user-submitted personal data is enabled. At present, the site has no account system or contact form.</p></div></section>'''
write(SITE_DIR / "privacy-policy" / "index.html", page(f"Privacy Policy | {SITE_NAME}", "Privacy information for Homekeeping Lab, including hosting, analytics and consent choices.", url("privacy-policy/"), privacy_body))

cookie_body = f'''<section class="hero"><div class="wrap"><h1>Cookie policy</h1><p>Homekeeping Lab keeps optional analytics separate from essential site access.</p></div></section><section class="section"><div class="article-wrap"><p><strong>Last updated:</strong> {e(TODAY)}</p><h2>What cookies are used for</h2><p>The site itself does not require analytics cookies for its core content. The current optional cookie use is Google Analytics, which helps measure how visitors use the site after consent is granted.</p><h2>Analytics consent is off by default</h2><p>Google Consent Mode is initialized with <code>analytics_storage</code>, <code>ad_storage</code>, <code>ad_user_data</code> and <code>ad_personalization</code> denied. Analytics storage is changed to granted only when you choose <strong>Accept analytics</strong>. Advertising-related consent remains denied in the current site setup.</p><h2>Google Analytics cookies</h2><p>After analytics consent is granted, Google Analytics may set first-party cookies such as <code>_ga</code> and <code>_ga_*</code>. These are used to distinguish browser instances and support audience measurement. Exact cookie duration can depend on Google Analytics configuration, browser behavior and later product changes.</p><h2>Consent preference storage</h2><p>Your choice is saved in browser local storage using <code>homekeepinglab_analytics_consent_v1</code>. This preference is not used for advertising; it exists so the site can remember whether analytics was accepted or rejected.</p><h2>Change or withdraw your choice</h2><p>Use the <strong>Cookie settings</strong> button in the footer on any page. Choosing <strong>Reject analytics</strong> changes analytics storage to denied and the site attempts to delete first-party Google Analytics cookies for this domain. You can also clear cookies and site storage through your browser.</p><h2>Advertising cookies</h2><p>Homekeeping Lab does not currently enable advertising storage or personalized-ad consent. If advertising such as Google AdSense is added later, this policy and the consent interface should be reviewed and updated before ad-related storage is enabled.</p><h2>Related information</h2><p>For broader information about technical request data, hosting and optional analytics, read the <a href="/privacy-policy/">Privacy Policy</a>.</p></div></section>'''
write(SITE_DIR / "cookie-policy" / "index.html", page(f"Cookie Policy | {SITE_NAME}", "How Homekeeping Lab uses optional analytics cookies and how visitors can change consent.", url("cookie-policy/"), cookie_body))

# Crawling files.
urls = [url(), url("about/"), url("editorial-policy/"), url("safety/"), url("privacy-policy/"), url("cookie-policy/")]
urls.extend(url(f"{cat['slug']}/") for cat in config["categories"])
urls.extend(url(f"guides/{row['Slug']}/") for row in published.values())
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += "".join(f"  <url><loc>{e(item)}</loc></url>\n" for item in urls)
sitemap += "</urlset>\n"
write(SITE_DIR / "sitemap.xml", sitemap)
write(SITE_DIR / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
write(SITE_DIR / "404.html", page(f"Page not found | {SITE_NAME}", "Page not found.", url("404.html"), '<section class="hero"><div class="wrap"><h1>Page not found</h1><p><a href="/">Return to Homekeeping Lab</a></p></div></section>'))
write(SITE_DIR / ".nojekyll", "\n")

save_plan(rows)
print(f"Built site with {len(published)} published guides into {SITE_DIR}.")

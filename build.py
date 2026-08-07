#!/usr/bin/env python3
"""
Halo static site build.

Reads pages/<slug>.html (body content only) and writes <slug>.html at the root
with the shared shell around it. No runtime dependency: the output is plain
static HTML you can drop on any host.

    python3 build.py            # build all pages
    python3 -m http.server 8000 # then open http://localhost:8000
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(ROOT, "pages")

SITE = "https://halo.app"

# slug: (title, meta description, nav section this page belongs to)
PAGE_META = {
    "index":     ("Appreciation, beautifully delivered.",
                  "Halo is the employee appreciation platform. Recognition cards that become a permanent record of a person's career.", ""),
    "product":   ("Product",
                  "Workspaces, departments, recognition and points. The whole of Halo in one place.", "product"),
    "cards":     ("Appreciation cards",
                  "The card is the product. Write one, sign it together, and it stays on a profile for as long as they work with you.", "product"),
    "templates": ("Templates",
                  "Considered card designs for every moment that matters, from a two-line thank you to a five year anniversary.", "product"),
    "ai":        ("Halo AI",
                  "AI helps you say it. It never says it for you. Wording, tone and translation inside the composer.", "product"),
    "pricing":   ("Pricing",
                  "Free under ten people. Per-user pricing after that, with a full feature comparison and no seat commitment.", "pricing"),
    "security":  ("Security",
                  "How Halo stores recognition, who can see it, and what happens to a card when someone leaves.", "company"),
}

# The full information architecture. Pages not yet built render as
# aria-disabled with a "soon" marker rather than as broken links.
BUILT = set(PAGE_META)

NAV = [
    ("Product", "product", 3, [
        ("Overview", [
            ("product",   "Product overview", "Everything Halo does, in order"),
            ("cards",     "Appreciation cards", "The object at the centre"),
            ("templates", "Templates", "Designs for every moment"),
        ]),
        ("Capabilities", [
            ("ai",        "Halo AI", "Wording, tone, translation"),
            ("features",  "All features", "Every capability in detail"),
            ("addons",    "Add-ons", "Packs, themes, integrations"),
        ]),
        ("Trust", [
            ("security",  "Security", "Privacy, permissions, compliance"),
            ("downloads", "Downloads", "iOS, Android, web"),
            ("resources", "Resources", "Guides, docs, changelog"),
        ]),
    ]),
    ("Company", "company", 2, [
        ("Halo", [
            ("about",     "About", "Why we built this"),
            ("customers", "Customers", "Stories and case studies"),
        ]),
        ("Talk to us", [
            ("contact",   "Contact", "Sales, support, general"),
            ("resources", "Help centre", "Answers and guides"),
        ]),
    ]),
]

FOOT = [
    ("Product",  [("product","Overview"), ("cards","Appreciation cards"),
                  ("templates","Templates"), ("ai","Halo AI"), ("addons","Add-ons")]),
    ("Company",  [("about","About"), ("customers","Customers"),
                  ("contact","Contact"), ("pricing","Pricing")]),
    ("Resources",[("resources","Guides"), ("resources","Changelog"),
                  ("downloads","Downloads"), ("security","Security")]),
    ("Legal",    [("privacy","Privacy"), ("terms","Terms"), ("cookies","Cookies")]),
]

RING = ('<svg viewBox="0 0 100 100" aria-hidden="true">'
        '<circle class="ring" cx="50" cy="50" r="33.5"/></svg>')


def link(slug, label, extra=""):
    """Emit a link, or a disabled placeholder when the page is not built yet."""
    if slug in BUILT:
        return '<a href="%s.html"%s>%s</a>' % (slug, extra, label)
    return '<a href="#" aria-disabled="true" tabindex="-1"%s>%s</a>' % (extra, label)


def nav_html(active):
    out = ['<header class="nav" id="nav"><div class="wrap nav-in">',
           '<a class="brand" href="index.html" aria-label="Halo, home">%s Halo</a>' % RING,
           '<ul class="nav-links">']
    for label, key, cols, groups in NAV:
        out.append('<li><button class="nav-item" type="button" data-mega aria-expanded="false"'
                   '%s>%s<svg class="caret" viewBox="0 0 10 10" aria-hidden="true">'
                   '<path d="M1 3.5 5 7l4-3.5" fill="none" stroke="currentColor" stroke-width="1.4"'
                   ' stroke-linecap="round"/></svg></button>'
                   % (' aria-current="page"' if key == active else '', label))
        out.append('<div class="mega" style="--cols:%d">' % cols)
        for heading, items in groups:
            out.append('<div><h4>%s</h4>' % heading)
            for slug, name, desc in items:
                body = '<b>%s</b><span>%s</span>' % (name, desc)
                out.append(link(slug, body))
            out.append('</div>')
        out.append('</div></li>')
    out.append('<li><a class="nav-item" href="pricing.html"%s>Pricing</a></li>'
               % (' aria-current="page"' if active == 'pricing' else ''))
    out.append('</ul>')
    out.append('<div class="nav-act"><a class="login" href="#">Log in</a>'
               '<a class="btn" href="pricing.html">Get Halo free</a>'
               '<button class="nav-toggle" id="navToggle" aria-expanded="false" '
               'aria-controls="sheet" aria-label="Menu"><span></span><span></span></button></div>')
    out.append('</div></header>')

    # mobile sheet: the same IA, flattened
    out.append('<div class="sheet" id="sheet">')
    seen = set()
    for label, key, cols, groups in NAV:
        out.append('<h4>%s</h4>' % label)
        for heading, items in groups:
            for slug, name, desc in items:
                if slug in seen:
                    continue
                seen.add(slug)
                out.append(link(slug, name))
    out.append('<h4>Plans</h4><a href="pricing.html">Pricing</a>')
    out.append('<a class="btn btn--lit" href="pricing.html">Get Halo free</a></div>')
    return "\n".join(out)


def foot_html():
    out = ['<footer class="foot"><div class="wrap"><div class="foot-grid">',
           '<div class="foot-brand"><a class="brand" href="index.html" aria-label="Halo, home">'
           '%s Halo</a><p>The employee appreciation platform.</p></div>' % RING]
    for heading, items in FOOT:
        out.append('<div><h4>%s</h4><ul>' % heading)
        for slug, name in items:
            out.append('<li>%s</li>' % link(slug, name))
        out.append('</ul></div>')
    out.append('</div><div class="foot-base"><span>&copy; 2026 Halo</span>'
               '<span>Built for teams that care how things feel.</span></div></div></footer>')
    return "\n".join(out)


CLOSE = """
<section class="close grain">
  <div class="close-glow" aria-hidden="true"></div>
  <div class="close-light" aria-hidden="true">
    <svg viewBox="0 0 100 100">
      <circle class="ring-path ring-halo" cx="50" cy="50" r="33.5"/>
      <circle class="ring-path ring-mid"  cx="50" cy="50" r="33.5"/>
      <circle class="ring-path ring-core" cx="50" cy="50" r="33.5"/>
    </svg>
  </div>
  <div class="wrap close-in">
    <h2 class="display d1" data-rise>{headline}</h2>
    <p class="lede" data-rise>{sub}</p>
    <div class="close-cta" data-rise>
      <a class="btn btn--lit" href="pricing.html" data-magnet>Get Halo free</a>
      <a class="btn btn--ghost" href="cards.html">See a card <span class="arw">&rarr;</span></a>
    </div>
    <small data-rise>No credit card required</small>
  </div>
</section>
"""

SHELL = """<!DOCTYPE html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0A0C10">
<meta name="color-scheme" content="dark light">
<link rel="canonical" href="{site}/{slug}">

<link rel="icon" href="brand/favicon.ico" sizes="any">
<link rel="icon" href="brand/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="brand/apple-touch-icon.png">
<link rel="mask-icon" href="brand/safari-pinned-tab.svg" color="#0A0C10">
<link rel="manifest" href="brand/site.webmanifest">

<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}/brand/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{site}/brand/twitter-image.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..600;1,6..72,200..500&family=Instrument+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/halo.css">
<link rel="stylesheet" href="assets/pages.css">
<script>document.documentElement.className='js';</script>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

<div id="loader" role="status" aria-live="polite">
  <div class="loader-in">
    <svg class="loader-ring" viewBox="0 0 100 100" aria-hidden="true" style="--c:210.5">
      <circle cx="50" cy="50" r="33.5" transform="rotate(113 50 50)"/>
    </svg>
    <p class="loader-msg" id="loaderMsg">Preparing appreciation</p>
  </div>
</div>

<div class="fade-top" aria-hidden="true"></div>
{nav}

<main id="main">
{content}
{close}
</main>

{foot}
<script src="assets/halo.js"></script>
</body>
</html>
"""


def build():
    if not os.path.isdir(PAGES):
        sys.exit("missing pages/ directory")
    written = []
    for slug, (title, desc, section) in PAGE_META.items():
        src = os.path.join(PAGES, slug + ".html")
        if not os.path.exists(src):
            print("  skip %-12s (no pages/%s.html)" % (slug, slug))
            continue
        raw = open(src, encoding="utf-8").read()

        # A page may override the closing CTA with an HTML comment directive:
        #   <!--close: Headline text | Sub text -->
        close = CLOSE.format(headline="Say the thing.",
                             sub="Set up a workspace in a few minutes. The first ten people are free, permanently.")
        m = re.search(r"<!--close:(.+?)\|(.+?)-->", raw, re.S)
        if m:
            close = CLOSE.format(headline=m.group(1).strip(), sub=m.group(2).strip())
            raw = raw.replace(m.group(0), "")
        if "<!--noclose-->" in raw:
            close = ""
            raw = raw.replace("<!--noclose-->", "")

        full_title = "Halo" if slug == "index" else "Halo · " + title
        if slug == "index":
            full_title = "Halo · " + title

        html = SHELL.format(
            title=full_title, desc=desc, site=SITE,
            slug="" if slug == "index" else slug + ".html",
            nav=nav_html(section), foot=foot_html(),
            content=raw.strip(), close=close,
        )
        out = os.path.join(ROOT, slug + ".html")
        open(out, "w", encoding="utf-8").write(html)
        written.append(slug + ".html")
        print("  built %-16s %6d bytes" % (slug + ".html", len(html)))

    unbuilt = sorted({s for _, _, _, gs in NAV for _, its in gs for s, _, _ in its} - BUILT)
    print("\n%d pages built. Not yet built (shown as 'soon' in the nav): %s"
          % (len(written), ", ".join(unbuilt) or "none"))


if __name__ == "__main__":
    build()

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

# Artboards with a dark field behind the navigation.
DARK_PAGES = {"pricing"}

NAV_BLURB = {
    "product":   "Everything Halo does, and the one thing it is for.",
    "solutions": "Halo adapts to your organisation, whatever its size.",
    "resources": "Guides, answers and everything we have shipped.",
    "company":   "Why this exists, and how to reach us.",
}

NAV = [
    ("Product", "product", 3, [
        ("Core", [
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
            ("product",   "Integrations", "Slack, Teams, Google, Outlook"),
        ]),
    ]),
    ("Solutions", "solutions", 2, [
        ("By size", [
            ("product",   "Startups", "Build strong cultures early"),
            ("product",   "Growing teams", "Scale recognition as you grow"),
            ("security",  "Enterprises", "Advanced controls and security"),
        ]),
        ("By team", [
            ("product",   "People and HR", "Run recognition without running it"),
            ("product",   "Managers", "Recognise without spending points"),
            ("cards",     "Everyone else", "Say the thing in ninety seconds"),
        ]),
    ]),
    ("Resources", "resources", 2, [
        ("Learn", [
            ("resources", "Guides", "How good recognition actually works"),
            ("resources", "Help centre", "Answers and walkthroughs"),
            ("resources", "Changelog", "Everything we have shipped"),
        ]),
        ("Get it", [
            ("downloads", "Downloads", "iOS, Android and the web app"),
            ("security",  "Security", "How your data is handled"),
            ("contact",   "Contact support", "Talk to a person"),
        ]),
    ]),
    ("Company", "company", 2, [
        ("Halo", [
            ("about",     "About", "Why we built this"),
            ("customers", "Customers", "Stories and case studies"),
        ]),
        ("Talk to us", [
            ("contact",   "Contact", "Sales, support, general"),
            ("pricing",   "Pricing", "Plans and what is in them"),
        ]),
    ]),
]

FOOT = [
    ("Product", [("product","Overview"), ("cards","Appreciation Cards"), ("features","Features"),
                 ("ai","AI Assistant"), ("templates","Templates"), ("product","Integrations"),
                 ("pricing","Pricing")]),
    ("Solutions", [("product","By Role"), ("product","By Department"), ("product","Startups"),
                   ("product","Small Business"), ("security","Enterprise"), ("product","Remote Teams")]),
    ("Resources", [("resources","Blog"), ("resources","Guides"), ("resources","Help Center"),
                   ("customers","Case Studies"), ("resources","Webinars"), ("resources","Changelog")]),
    ("Company", [("about","About Us"), ("about","Careers"), ("about","Press Kit"),
                 ("customers","Partners"), ("contact","Contact Us")]),
]

SOCIALS = [
    ("LinkedIn", '<path d="M4.5 3.5a2 2 0 11-.001 4.001A2 2 0 014.5 3.5zM3 9h3v12H3zm6 0h2.9v1.6h.04c.4-.76 1.4-1.6 2.9-1.6 3.1 0 3.7 2 3.7 4.7V21h-3v-5.6c0-1.3 0-3-1.9-3s-2.1 1.4-2.1 2.9V21H9z"/>'),
    ("Instagram", '<path d="M12 2.2c3.2 0 3.6 0 4.9.07 3.3.15 4.8 1.7 5 5 .06 1.3.07 1.7.07 4.9s0 3.6-.07 4.9c-.15 3.3-1.7 4.8-5 5-1.3.06-1.7.07-4.9.07s-3.6 0-4.9-.07c-3.3-.15-4.8-1.7-5-5C2.04 15.6 2 15.2 2 12s0-3.6.07-4.9c.15-3.3 1.7-4.8 5-5C8.4 2.2 8.8 2.2 12 2.2zm0 3.8a6 6 0 100 12 6 6 0 000-12zm0 2a4 4 0 110 8 4 4 0 010-8zm6.2-3.5a1.4 1.4 0 100 2.8 1.4 1.4 0 000-2.8z"/>'),
    ("X", '<path d="M17.5 3h3.2l-7 8 8.2 10h-6.4l-5-6.1L4.7 21H1.5l7.5-8.6L1.2 3h6.6l4.5 5.6zm-1.1 16h1.8L7.7 4.9H5.8z"/>'),
    ("YouTube", '<path d="M21.6 7.2a2.5 2.5 0 00-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 002.4 7.2C2 8.8 2 12 2 12s0 3.2.4 4.8a2.5 2.5 0 001.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 001.8-1.8c.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15.1V8.9l5.2 3.1z"/>'),
]

LEGAL = [("privacy","Privacy"), ("terms","Terms"), ("cookies","Cookies"), ("security","Security")]

RING = ('<svg class="brand-grad" viewBox="0 0 100 100" aria-hidden="true">'
        '<circle class="ring" cx="50" cy="50" r="33.5"/></svg>')

# One gradient definition per document, referenced by every brand mark.
BRAND_DEFS = (
    '<svg width="0" height="0" aria-hidden="true" focusable="false" '
    'style="position:absolute">'
    '<defs><linearGradient id="brandGrad" x1="12%" y1="4%" x2="88%" y2="96%">'
    '<stop offset="0%" stop-color="#AFC6E9"/>'
    '<stop offset="38%" stop-color="#C6BEE4"/>'
    '<stop offset="72%" stop-color="#EBC9A8"/>'
    '<stop offset="100%" stop-color="#F2D9A6"/>'
    '</linearGradient></defs></svg>')


# --------------------------------------------------------------- cards ----
# {{card finish|moment|Title|Body|From|Date|Label}}   Label is optional.
SEAL_TEXT = {
    "appreciation": "THANK YOU \u00b7 WELL DONE \u00b7 ",
    "birthday":     "CELEBRATE \u00b7 ME \u00b7 YOU \u00b7 ",
    "milestone":    "GREAT WORK \u00b7 KEEP IT UP \u00b7 ",
    "welcome":      "WELCOME \u00b7 GLAD YOU ARE HERE \u00b7 ",
}
MARKS = {
    "appreciation": '<path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/>',
    "milestone":    '<path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/>',
    "welcome":      '<path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/>',
    "birthday":     ('<path d="M12 2c.9.9 1.4 1.7 1.4 2.4A1.4 1.4 0 0112 5.8a1.4 1.4 0 01-1.4-1.4'
                     'c0-.7.5-1.5 1.4-2.4zM7 7h10v3H7zm-3 4h16v3.2c-1.4 0-1.4 1.2-2.7 1.2s-1.3-1.2-2.6-1.2'
                     '-1.3 1.2-2.7 1.2-1.3-1.2-2.6-1.2S8 15.4 6.7 15.4 5.4 14.2 4 14.2zm0 5.4'
                     'c1.4 0 1.4 1.2 2.7 1.2s1.3-1.2 2.6-1.2 1.3 1.2 2.7 1.2 1.3-1.2 2.6-1.2 1.4 1.2 2.7 1.2'
                     'V22H4z"/>'),
}
SEAL_ICON = {
    "birthday": '<path d="M0-7c.8.8 1.2 1.5 1.2 2.1A1.2 1.2 0 010-3.7 1.2 1.2 0 01-1.2-5c0-.6.4-1.3 1.2-2.1zM-4-2h8v2.6h-8zm-2.4 3.6h12.8v2.7c-1.1 0-1.1 1-2.1 1S3.2 4.3 2.2 4.3s-1 1-2.2 1-1-1-2.1-1-1 1-2.1 1-1-1-2.2-1z"/>',
}
_seal_n = [0]


def seal(moment):
    _seal_n[0] += 1
    sid = "seal%d" % _seal_n[0]
    text = SEAL_TEXT.get(moment, SEAL_TEXT["appreciation"])
    icon = SEAL_ICON.get(moment,
        '<path d="M0-8l1.7 5.6L7 0 1.7 2.4 0 8l-1.7-5.6L-7 0l5.3-2.4z"/>')
    return (
      '<span class="hcard-seal" aria-hidden="true"><svg viewBox="0 0 100 100">'
      '<defs><path id="%s" fill="none" d="M50,50 m-37,0 a37,37 0 1,1 74,0 a37,37 0 1,1 -74,0"/></defs>'
      '<text><textPath href="#%s" startOffset="0">%s%s</textPath></text>'
      '<circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" stroke-width=".8" opacity=".3"/>'
      '<g transform="translate(50,50)" fill="currentColor">%s</g>'
      '</svg></span>' % (sid, sid, text, text, icon))


def card(m):
    parts = [p.strip() for p in m.group(1).split("|")]
    while len(parts) < 7:
        parts.append("")
    finish, moment, title, body, who, date, label = parts[:7]
    initials = "".join(w[0] for w in who.split()[:2]).upper() or "H"
    kicker = {"appreciation": "Appreciation", "birthday": "Happy birthday",
              "milestone": "Great work", "welcome": "Welcome"}.get(moment, moment.title())
    html = (
      '<article class="hcard hcard--%s hcard--moment">'
      '<div class="hcard-top">'
        '<span class="hcard-brand">%s Halo</span>'
        '<svg class="hcard-mark" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">%s</svg>'
      '</div>'
      '<p class="hcard-kicker">%s</p>'
      '<h3 class="hcard-title">%s</h3>'
      '<hr class="hcard-rule">'
      '<p class="hcard-body">%s</p>'
      '<div class="hcard-foot">'
        '<span class="hcard-from"><span class="avatar">%s</span>'
        '<span><b>%s</b><span>%s</span></span></span>%s'
      '</div></article>'
      % (finish, RING.replace(' class="brand-grad"', ''),
         MARKS.get(moment, MARKS["appreciation"]),
         kicker, title, body, initials, who, date, seal(moment)))
    if label:
        n, name = (label.split(".", 1) + [""])[:2] if "." in label else ("", label)
        html = ('<figure style="margin:0">%s<figcaption class="hcard-label">'
                '<i>%s</i>%s</figcaption></figure>'
                % (html, n.strip(), name.strip()))
    return html


def link(slug, label, extra=""):
    """Emit a link, or a disabled placeholder when the page is not built yet."""
    if slug in BUILT:
        return '<a href="%s.html"%s>%s</a>' % (slug, extra, label)
    return '<a href="#" aria-disabled="true" tabindex="-1"%s>%s</a>' % (extra, label)


def nav_html(active, dark=False):
    out = ['<header class="nav %s" id="nav">' % ("nav--dark" if dark else "nav--light") + '<div class="wrap nav-in">',
           '<a class="brand" href="index.html" aria-label="Halo, home">%s Halo</a>' % RING,
           '<ul class="nav-links">']
    for label, key, cols, groups in NAV:
        blurb = NAV_BLURB.get(key, "")
        out.append('<li><button class="nav-item" type="button" data-mega aria-expanded="false"'
                   '%s>%s<svg class="caret" viewBox="0 0 10 10" aria-hidden="true">'
                   '<path d="M1 3.5 5 7l4-3.5" fill="none" stroke="currentColor" stroke-width="1.4"'
                   ' stroke-linecap="round"/></svg></button>'
                   % (' aria-current="page"' if key == active else '', label))
        out.append('<div class="mega mega--cards" style="--cols:%d">' % cols)
        for heading, items in groups:
            out.append('<div><h4>%s</h4>' % heading)
            for slug, name, desc in items:
                body = '<b>%s</b><span>%s</span>' % (name, desc)
                out.append(link(slug, body))
            out.append('</div>')
        out.append('<div class="mega-foot"><span>%s</span>'
                   '<a class="btn btn--spec" href="pricing.html">Get Halo free</a></div>' % blurb)
        out.append('</div></li>')
        if key == "resources":
            out.append('<li><a class="nav-item" href="pricing.html"%s>Pricing</a></li>'
                       % (' aria-current="page"' if active == 'pricing' else ''))
    out.append('</ul>')
    out.append('<div class="nav-act"><a class="btn btn--paper login" href="#">Log in</a>'
               '<a class="btn btn--spec" href="pricing.html">Get Halo free</a>'
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


def foot_html(headline, sub):
    out = ['<footer class="pfoot">',
           '<div class="pfoot-glow" aria-hidden="true"></div>',
           '<div class="pfoot-halo" aria-hidden="true">'
           '<svg viewBox="0 0 470 200" preserveAspectRatio="none">'
           '<ellipse class="ph-wide" cx="235" cy="100" rx="222" ry="88"/>'
           '<ellipse class="ph-mid"  cx="235" cy="100" rx="222" ry="88"/>'
           '<ellipse class="ph-core" cx="235" cy="100" rx="222" ry="88"/>'
           '</svg></div>',
           '<div class="wrap pfoot-cta">',
           '<h2 data-rise>%s</h2>' % headline,
           '<p data-rise style="--rise-delay:80ms">%s</p>' % sub,
           '<div class="row" data-rise style="--rise-delay:150ms">'
           '<a class="pbtn pbtn--paper pbtn--pill" href="pricing.html">Get Halo free</a>'
           '<a class="pbtn pbtn--onDark pbtn--pill" href="cards.html">Book a demo</a></div>',
           '<small data-rise style="--rise-delay:210ms">No credit card required</small>',
           '</div>',
           '<div class="wrap"><div class="pfoot-main">']

    out.append('<div class="pfoot-brand">'
               '<a class="brand" href="index.html" aria-label="Halo, home">%s Halo</a>'
               '<p class="tag">Appreciation,<br><em>beautifully</em> delivered.</p>'
               '<p>Halo helps teams recognize each other with meaningful cards, '
               'celebrations, and a culture that grows stronger every day.</p>'
               '<div class="socials">' % RING)
    for name, path in SOCIALS:
        out.append('<a href="#" aria-label="%s"><svg viewBox="0 0 24 24" fill="currentColor" '
                   'aria-hidden="true">%s</svg></a>' % (name, path))
    out.append('</div></div>')

    for heading, items in FOOT:
        out.append('<div class="pfoot-col"><h4>%s</h4><ul>' % heading)
        for slug, name in items:
            out.append('<li>%s</li>' % link(slug, name))
        out.append('</ul></div>')

    out.append('<div class="newsletter">'
               '<h4><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
               '<path d="M12 2.4l1.55 6.05L19.6 10l-6.05 1.55L12 17.6l-1.55-6.05L4.4 10l6.05-1.55z"/>'
               '</svg> Stay in the loop</h4>'
               '<p>Subscribe to get product updates, culture insights, and Halo news.</p>'
               '<form onsubmit="return false">'
               '<label class="vh" for="nl">Email address</label>'
               '<input id="nl" type="email" name="email" placeholder="Enter your email" autocomplete="email">'
               '<button class="pbtn pbtn--paper" type="submit">Subscribe <span class="arw">&rarr;</span></button>'
               '</form>'
               '<p class="privacy"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
               '<path d="M12 1.5a4.5 4.5 0 014.5 4.5v3H18a1.5 1.5 0 011.5 1.5v10A1.5 1.5 0 0118 22H6a1.5 1.5 0 01-1.5-1.5v-10A1.5 1.5 0 016 9h1.5V6A4.5 4.5 0 0112 1.5zm0 2A2.5 2.5 0 009.5 6v3h5V6A2.5 2.5 0 0012 3.5z"/>'
               '</svg> We respect your privacy. Unsubscribe anytime.</p>'
               '</div>')

    out.append('</div></div>')
    out.append('<div class="wrap pfoot-base"><span>&copy; 2026 Halo</span><ul>')
    for slug, name in LEGAL:
        out.append('<li>%s</li>' % link(slug, name))
    out.append('</ul></div></footer>')
    return "\n".join(out)


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
<link rel="stylesheet" href="assets/cards.css">
<link rel="stylesheet" href="assets/rb.css">
<link rel="stylesheet" href="assets/pdf.css">
<link rel="stylesheet" href="assets/pdf2.css">
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

{brand_defs}
<div class="fade-top" aria-hidden="true"></div>
{nav}

<nav class="linebar" data-linebar></nav>

<main id="main">
{content}
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
        headline = "Ready to build a culture of appreciation?"
        sub = ("Join thousands of teams already using Halo "
               "to recognize what matters most.")
        m = re.search(r"<!--close:(.+?)\|(.+?)-->", raw, re.S)
        if m:
            headline, sub = m.group(1).strip(), m.group(2).strip()
            raw = raw.replace(m.group(0), "")
        raw = raw.replace("<!--noclose-->", "")

        full_title = "Halo" if slug == "index" else "Halo · " + title
        if slug == "index":
            full_title = "Halo · " + title

        raw = re.sub(r"\{\{card (.+?)\}\}", card, raw, flags=re.S)

        html = SHELL.format(
            title=full_title, desc=desc, site=SITE, brand_defs=BRAND_DEFS,
            slug="" if slug == "index" else slug + ".html",
            nav=nav_html(section, slug in DARK_PAGES), foot=foot_html(headline, sub),
            content=raw.strip(),
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

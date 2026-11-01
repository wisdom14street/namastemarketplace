#!/usr/bin/env python3
"""Build namastemarketplace.com: wholesale-only site for Namaste Bookshop's B2B program.
Product data comes from the public namastebookshop.com product JSON for the handles in the Shopify
"Namaste Wholesale" catalog (site/catalog_seed.json). No cart, no checkout on this site."""
import json, os, re, shutil, sys, time, html, urllib.request, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(f'{R}/site/config.json')); SEED = json.load(open(f'{R}/site/catalog_seed.json'))
SITE = 'https://' + CFG['domain']; SHOP = CFG['shop']; BRAND = CFG['brand']
OUT = f'{R}/dist'; CACHE = f'{R}/data/products.json'
E = lambda s: html.escape(str(s), quote=True)
GA = CFG.get('GA_MEASUREMENT_ID', '').strip()
TODAY = datetime.date.today().isoformat()

def fetch():
    old = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    out = {}
    for h in SEED['handles']:
        for i in range(4):
            try:
                req = urllib.request.Request(f'{SHOP}/products/{h}.js', headers={'User-Agent': 'namastemarketplace-build'})
                out[h] = json.load(urllib.request.urlopen(req, timeout=30)); break
            except Exception as e:
                if getattr(e, 'code', 0) == 404: break
                time.sleep(2 + 3 * i)
        if h not in out and h in old: out[h] = old[h]
        time.sleep(0.35)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True); json.dump(out, open(CACHE, 'w'))
    return out

CATS = [
 ('waters', 'Spiritual and cleansing waters', 'Florida Water and herbal cleansing waters in 7.5 oz bottles. A steady, low-cost add-on for counters and ritual shelves.', {'Cleansing Water'}),
 ('candles', 'Ritual and Reiki candles', 'Herbal pillar candles with a named intention on each label, plus small 4-inch ritual candles sold by color.', {'Reiki Herbal Pillar Candle', 'Ritual Candle'}),
 ('smudge', 'Sage, palo santo and cleansing kits', 'California white sage bundles, Peruvian palo santo and a ready-made Florida Water cleansing kit.', {'Sage', 'Palo Santo', 'Energy Cleansing Kit'}),
 ('incense', 'Incense', 'Hand-rolled Satya Nag Champa in three sizes and resin-rolled sticks in palo santo, frankincense, myrrh and dragon\'s blood.', {'Incense Sticks'}),
 ('crystals', 'Crystals, bracelets and tokens', 'Beaded stone bracelets, tumbled gallets, raw selenite sticks and small talismans picked by the bookshop\'s crystal team.', {'Crystal Bead Bracelets', 'Crystal Gallet', 'Crystal Specimen', 'Worry Stone', 'Crystal'}),
 ('tarot', 'Tarot', 'The Rider-Waite deck and the three-card Gift of Tarot set. Tarot carries a smaller discount than the rest of the line.', {'Tarot Deck'}),
]

def items(P):
    rows = []
    for h in SEED['handles']:
        p = P.get(h)
        if not p: continue
        retail = min(v['price'] for v in p['variants']) / 100
        fx = SEED['fixed'].get(h)
        pct = round(100 * (1 - float(fx) / retail)) if fx else 50
        mins = SEED['mins'].get(h, [1]); mn = min(mins)
        per = ' per color' if len(p['variants']) > 1 else ''
        img = p.get('featured_image') or ''
        if img.startswith('//'): img = 'https:' + img
        cat = next((c[0] for c in CATS if p.get('type') in c[3]), 'crystals')
        avail = any(v.get('available') for v in p['variants'])
        rows.append(dict(h=h, t=p['title'], retail=retail, pct=pct, min=mn, per=per, img=img, cat=cat, avail=avail, vendor=p.get('vendor', '')))
    return rows

NAV = [('/', 'Home'), ('/line/', 'The line'), ('/how-it-works/', 'How it works'), ('/events-and-gifts/', 'Events & gifts'), ('/faq/', 'FAQ'), ('/contact/', 'Contact')]
LOGIN = f'{SHOP}/account/login'

def ga_head():
    if not GA: return ''
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>'
            f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{GA}",{json.dumps({"site_brand": BRAND})});</script>')

ORG = {"@context": "https://schema.org", "@type": "Organization", "@id": SITE + "/#org", "name": BRAND, "url": SITE + "/",
       "logo": SITE + "/assets/logo.png", "image": SITE + "/og.jpg", "email": CFG['email'], "telephone": "+1-212-645-0141",
       "description": "The wholesale program of Namaste Bookshop in Manhattan, for shops, studios, spas and gift buyers.",
       "address": {"@type": "PostalAddress", "streetAddress": "2 West 14th Street", "addressLocality": "New York", "addressRegion": "NY", "postalCode": "10011", "addressCountry": "US"},
       "contactPoint": {"@type": "ContactPoint", "contactType": "sales", "telephone": "+1-212-645-0141", "email": CFG['email'], "areaServed": "US", "availableLanguage": "en"},
       "parentOrganization": {"@type": "BookStore", "@id": "https://namastebookshop.com/#store", "name": "Namaste Bookshop", "url": "https://namastebookshop.com/"}}

def page(path, title, desc, body, extra_ld=None, noindex=False):
    canon = SITE + path
    ld = [ORG] + (extra_ld or [])
    nav = ''.join(f'<a href="{u}"{" aria-current=\"page\"" if u == path else ""}>{E(n)}</a>' for u, n in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{ga_head()}
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{canon}">'}
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{SITE}/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1e3b33"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v={TODAY}">
<script type="application/ld+json">{json.dumps(ld if len(ld) > 1 else ORG).replace("</", "<\\/")}</script></head>
<body><a class="skip" href="#main">Skip to content</a>
<div class="topline">Wholesale only &middot; for approved business accounts<span class="tl-ph"> &middot; <a href="tel:{CFG['tel']}">{CFG['phone']}</a></span></div>
<header class="hd"><div class="wrap hdin"><a class="logo" href="/"><span class="mark">NM</span><span><b>Namaste Marketplace</b><small>Wholesale from Namaste Bookshop</small></span></a>
<details class="menu"><summary aria-label="Menu">Menu</summary><nav>{nav}</nav></details>
<nav class="desk">{nav}</nav><div class="hbtn"><a class="btn sm ghost" href="{LOGIN}" data-ev="sign_in">Sign in</a><a class="btn sm" href="/apply/">Apply</a></div></div></header>
<main id="main">{body}</main>
<footer class="ft"><div class="wrap fgrid"><div><p class="fb">Namaste Marketplace</p><p>The wholesale program of Namaste Bookshop. Namaste Bookshop and Namaste Marketplace are businesses of {CFG['legal']}</p>
<p>Namaste Bookshop<br>2 West 14th Street, New York, NY 10011<br><a href="tel:{CFG['tel']}">{CFG['phone']}</a> &middot; <a href="mailto:{CFG['email']}">{CFG['email']}</a></p></div>
<div><p class="fb">Buyers</p><p><a href="/apply/">Apply for an account</a><br><a href="{LOGIN}" data-ev="sign_in">Sign in to order</a><br><a href="/line/">The wholesale line</a><br><a href="/how-it-works/">Terms and tax-exempt buying</a></p></div>
<div><p class="fb">More</p><p><a href="/events-and-gifts/">Events and gift boxes</a><br><a href="/faq/">FAQ</a><br><a href="/privacy/">Privacy</a><br><a href="https://namastebookshop.com/">Shop retail at namastebookshop.com</a></p></div></div>
<div class="wrap fine">&copy; {datetime.date.today().year} {CFG['legal']} Product names and photos are from the Namaste Bookshop catalog.</div></footer>
<script src="/assets/ga.js" defer></script><script src="/assets/site.js" defer></script></body></html>'''

def card(it):
    return f'''<article class="card"><div class="ph">{f'<img src="{E(it["img"])}&width=480" alt="{E(it["t"])}" width="480" height="480" loading="lazy" decoding="async">' if it["img"] else '<div class="noimg">Photo coming</div>'}<span class="tier">{it["pct"]}% off retail</span></div>
<div class="cb"><h3>{E(it["t"])}</h3><dl><div><dt>Retail</dt><dd>${it["retail"]:.2f}</dd></div><div><dt>Minimum</dt><dd>{it["min"]}{it["per"]}</dd></div></dl>
{'' if it['avail'] else '<p class="oos">Ask about restock</p>'}<a class="mini" href="{SHOP}/products/{it["h"]}" rel="nofollow">Approved buyers: order this item &rarr;</a></div></article>'''

def cta():
    return f'''<section class="band"><div class="wrap bandin"><div><h2>Open a wholesale account</h2><p>Tell us about your business. We review every application by hand and reply by email, usually within a few business days.</p></div>
<div class="btns"><a class="btn light" href="/apply/">Apply now</a><a class="btn outline" href="{LOGIN}" data-ev="sign_in">Already approved? Sign in</a></div></div></section>'''

def home(I):
    cats = ''
    for k, name, blurb, _ in CATS:
        its = [i for i in I if i['cat'] == k]
        if not its: continue
        im = next((i['img'] for i in its if i['img']), '')
        cats += f'''<a class="cat" href="/line/#{k}"><img src="{E(im)}&width=420" alt="{E(name)}" width="420" height="420" loading="lazy" decoding="async"><span><b>{E(name)}</b><small>{len(its)} item{'s' if len(its) != 1 else ''} &middot; {'20' if k == 'tarot' else '50'}% off retail</small></span></a>'''
    who = ''.join(f'<li>{w}</li>' for w in ['Gift shops, boutiques and bookstores', 'Metaphysical and crystal shops', 'Yoga and meditation studios', 'Spas, salons and wellness practices', 'Reiki practitioners and healers', 'Boutique hotels and retreat hosts', 'Event planners and party hosts', 'Companies buying client or staff gifts'])
    faq = [('Is this a store I can buy from today?', 'Not without an account. Namaste Marketplace sells only to approved businesses. Personal shoppers can buy at namastebookshop.com.'),
           ('Who reviews my application?', 'The owner of Namaste Bookshop reviews each one. If something is missing we will email you rather than decline.'),
           ('Do I need a resale certificate?', 'To buy without sales tax in New York, yes: a completed Form ST-120. Event and gifting buyers who are not reselling can still open an account and pay sales tax.')]
    fq = ''.join(f'<details class="q"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq)
    body = f'''<section class="hero"><div class="wrap heroin"><div class="htxt"><p class="eyebrow">Wholesale &middot; Union Square, New York</p>
<h1>Stock what a 14th Street spiritual bookshop sells every day.</h1>
<p class="lede">Namaste Marketplace is the wholesale program of <a href="https://namastebookshop.com/">Namaste Bookshop</a>. Approved businesses buy our cleansing waters, candles, sage, incense, crystals and tarot at 50% off retail on most items, with small per-item minimums.</p>
<div class="btns"><a class="btn" href="/apply/">Apply for an account</a><a class="btn ghost" href="{LOGIN}" data-ev="sign_in">Sign in to order</a></div>
<ul class="facts"><li><b>50%</b><span>off retail on most of the line</span></li><li><b>4&ndash;24</b><span>units minimum per item</span></li><li><b>ST-120</b><span>tax-exempt resale in NY</span></li></ul></div>
<div class="hcol" aria-hidden="true">{''.join(f'<img src="{E(i["img"])}&width=360" alt="" width="360" height="360" decoding="async">' for i in [next(x for x in I if x['cat'] == c and x['img']) for c in ('candles', 'smudge', 'waters', 'crystals')])}</div></div></section>
<section class="sec"><div class="wrap"><p class="eyebrow">Three steps</p><h2>How buying wholesale works</h2>
<ol class="steps"><li><b>Apply</b><span>Fill in the short business form. It goes straight to the bookshop's wholesale inbox.</span></li><li><b>Get approved</b><span>We set up your company account in our store system, with wholesale pricing, minimums and, if you resell in New York, tax exemption.</span></li><li><b>Sign in and order</b><span>Sign in at namastebookshop.com with the email you applied with. Wholesale prices and minimums appear automatically at checkout.</span></li></ol>
<p><a class="link" href="/how-it-works/">Full terms, minimums and tax-exempt steps &rarr;</a></p></div></section>
<section class="sec alt"><div class="wrap"><p class="eyebrow">The line</p><h2>What you can carry</h2><p class="muted">{len(I)} products today, all items the bookshop stocks and sells on its own shelves. Photos are the real catalog photos.</p>
<div class="cats">{cats}</div><p><a class="link" href="/line/">See every item with minimums &rarr;</a></p></div></section>
<section class="sec"><div class="wrap two"><div><p class="eyebrow">Who qualifies</p><h2>Built for small businesses that sell or gift</h2><p class="muted">You need a real business: a shop, a studio, a practice, a venue or a company. A website, social page or storefront address helps us approve you faster.</p></div><ul class="who">{who}</ul></div></section>
<section class="sec alt"><div class="wrap two"><div><p class="eyebrow">Beyond the shelf</p><h2>Readers and gift boxes for events</h2><p class="muted">The bookshop also sends tarot readers to parties and corporate events and packs crystal and sage gift boxes in three tiers.</p><a class="link" href="/events-and-gifts/">Event and gift packages &rarr;</a></div>
<div><p class="eyebrow">Quick answers</p>{fq}<p><a class="link" href="/faq/">All questions &rarr;</a></p></div></div></section>{cta()}'''
    return page('/', 'Namaste Marketplace | Wholesale Crystals, Sage, Candles & Incense from Namaste Bookshop NYC',
                'Wholesale program of Namaste Bookshop in Union Square, NYC. Approved shops, studios, spas and gift buyers get 50% off retail on most items, low minimums and NY tax-exempt resale.', body)

def line(I):
    sec = ''
    for k, name, blurb, _ in CATS:
        its = [i for i in I if i['cat'] == k]
        if not its: continue
        sec += f'<section class="sec{" alt" if len(sec) % 2 else ""}" id="{k}"><div class="wrap"><h2>{E(name)}</h2><p class="muted">{E(blurb)}</p><div class="grid">{"".join(card(i) for i in its)}</div></div></section>'
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">The wholesale line</p><h1>Every item open to wholesale accounts</h1>
<p class="lede">These are the {len(I)} products in the Namaste Wholesale catalog right now. Each card shows the public retail price, the wholesale discount and the minimum per order. Your exact wholesale price is applied automatically when you sign in with an approved account.</p>
<nav class="jump">{''.join(f'<a href="#{k}">{E(n.split(",")[0])}</a>' for k, n, _, _ in CATS)}</nav></div></section>{sec}
<section class="sec"><div class="wrap narrow"><p class="muted small">Retail prices are refreshed daily from namastebookshop.com. Stock moves fast on some items, and the catalog can change; your account always shows the current line. Looking for something not listed? Ask us at <a href="mailto:{CFG['email']}?subject=Wholesale%20question">{CFG['email']}</a>.</p></div></section>{cta()}'''
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": "Namaste Wholesale line", "numberOfItems": len(I),
           "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": i['t'], "url": f"{SHOP}/products/{i['h']}"} for n, i in enumerate(I)]}]
    return page('/line/', 'Wholesale Line: Cleansing Waters, Reiki Candles, Sage, Incense & Crystals | Namaste Marketplace',
                f'The {len(I)} products in the Namaste Bookshop wholesale catalog, with retail price, wholesale discount and per-item minimums. Approved business accounts order at namastebookshop.com.', body, ld)

def how():
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">How it works</p><h1>From application to first order</h1><p class="lede">Everything runs through Namaste Bookshop's own store system, so there is one account, one catalog and one checkout.</p></div></section>
<section class="sec"><div class="wrap narrow prose">
<h2>1. Apply</h2><p>Use the <a href="/apply/">application form</a>. Tell us your business name, what kind of business it is, where you sell, and which categories interest you. The form is delivered to the bookshop's wholesale inbox; nothing is charged and no account is created yet.</p>
<h2>2. Review and approval</h2><p>We read each application ourselves. Once approved, we create a company account for your business in our Shopify store, add you as its buyer, and connect it to the Namaste Wholesale catalog and price list. We email you as soon as your account is ready to use.</p>
<h2>3. Sign in</h2><p>Go to <a href="{LOGIN}" data-ev="sign_in">namastebookshop.com/account/login</a> and enter the email address on your application. Shopify sends a one-time code to that inbox; there is no password to remember. If your login is linked to more than one location, choose the one you are ordering for.</p>
<h2>4. Order</h2><p>While signed in, wholesale prices replace retail prices on catalog items and the minimum quantity for each item is enforced in the cart. Check out as usual. You can also place orders by phone at <a href="tel:{CFG['tel']}">{CFG['phone']}</a> or in person at the shop.</p>
<h2>Pricing</h2><ul><li>Most of the line: 50% off the retail price.</li><li>Tarot decks: 20% off retail. Publisher costs on decks leave less room, so we keep this tier smaller and honest rather than inflating retail.</li><li>Prices are in US dollars. Retail prices can change; your account always shows what you will pay.</li></ul>
<h2>Minimums</h2><ul><li>Each item has its own minimum, from 4 units (Rider-Waite deck) to 24 units (small tokens, 2 oz Florida Water, Gift of Tarot). Most items are 6 or 12.</li><li>Mini ritual candles are counted per color.</li><li>Opening orders start at $150. Reorders follow the per-item minimums.</li></ul>
<h2>Tax-exempt resale in New York</h2><p>If you resell the goods and hold a New York sales tax Certificate of Authority, you can buy without sales tax:</p><ol><li>Fill in New York State Form ST-120, Resale Certificate, with your Certificate of Authority number. The form is available from the <a href="https://www.tax.ny.gov/pdf/current_forms/st/st120_fill_in.pdf" rel="noopener">NYS Department of Taxation and Finance</a>.</li><li>Email the signed form to <a href="mailto:{CFG['email']}?subject=ST-120%20for%20wholesale%20account">{CFG['email']}</a>, or bring it to the shop.</li><li>We mark your company account tax-exempt before your first order, so tax is not charged at checkout.</li></ol>
<p>Buying for events, staff or clients rather than resale? You can still have a wholesale account; sales tax is charged as normal. Based outside New York? Tell us your state in the application and we will let you know which certificate we can accept.</p>
<h2>Pickup and delivery</h2><p>Pick up at Namaste Bookshop, 2 West 14th Street. Delivery in New York City or shipping can be arranged on request. Net payment terms may be offered to established accounts on request.</p>
</div></section>{cta()}'''
    return page('/how-it-works/', 'How Wholesale Works: Apply, Approval, Minimums & NY ST-120 | Namaste Marketplace',
                'How to open a Namaste Bookshop wholesale account: apply, get approved, sign in at namastebookshop.com and order at wholesale prices. Minimums, discount tiers and NY ST-120 tax-exempt steps.', body)

def events():
    pk = [('Reader at your event', 'From $175 per hour', 'One of the bookshop\'s professional tarot readers at your party, client evening or brand activation. Two-hour minimum.'),
          ('Half-day reading lounge', 'From $1,100', 'Two readers for four hours. Suited to conferences, galas and hotel lobbies where guests come and go.'),
          ('Team tarot workshop', 'From $35 per person', 'A hands-on introduction to the cards, led by a Namaste reader, for teams and private groups of 10 or more.'),
          ('Curated gift boxes', '$25, $49 or $95 per box', 'Crystal, sage and ritual boxes in three tiers for staff, clients and guests.')]
    cards = ''.join(f'<article class="pkg"><h3>{E(a)}</h3><p class="from">{E(b)}</p><p>{E(c)}</p></article>' for a, b, c in pk)
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">Events &amp; gifts</p><h1>Tarot readers and gift boxes for your guests</h1><p class="lede">Alongside wholesale stock, Namaste Bookshop books readers for events and packs gift boxes for companies. Prices below are starting points; every event gets its own quote.</p></div></section>
<section class="sec"><div class="wrap"><div class="pkgs">{cards}</div><p class="muted">To get a quote, send your date, location, guest count and budget through the <a href="/apply/">application form</a> (choose "Event planner" or "Corporate gifting") or email <a href="mailto:{CFG['email']}?subject=Event%20or%20gift%20quote">{CFG['email']}</a>.</p></div></section>{cta()}'''
    return page('/events-and-gifts/', 'Tarot Readers for Events & Corporate Gift Boxes NYC | Namaste Marketplace',
                'Book a Namaste Bookshop tarot reader for your event, a half-day reading lounge or a team tarot workshop, or order crystal and sage gift boxes for staff and clients in NYC.', body)

FAQ = [
 ('Can I buy here without an account?', 'No. This is a wholesale-only site with no cart. Approved businesses order through their account at namastebookshop.com. If you are shopping for yourself, namastebookshop.com sells at retail.'),
 ('What kind of businesses do you approve?', 'Shops and boutiques, metaphysical and crystal stores, yoga and meditation studios, spas, salons, healers and wellness practices, boutique hotels, event planners and companies buying gifts.'),
 ('How long does approval take?', 'We aim to reply within a few business days. Applications with a website, social page or shop address are the quickest to check.'),
 ('How big is the discount?', 'Most items are 50% off retail. Tarot decks are 20% off retail.'),
 ('What are the minimums?', 'Every item has its own minimum, from 4 to 24 units, shown on each product in the line. Mini ritual candles count per color. Opening orders start at $150.'),
 ('How do I buy tax-free?', 'If you resell in New York, send us a completed Form ST-120 with your Certificate of Authority number. We mark your account tax-exempt before your first order.'),
 ('How do I sign in?', 'Go to namastebookshop.com/account/login and enter the email you applied with. You will get a one-time code by email. Once signed in, wholesale prices show automatically.'),
 ('Why do I see retail prices after signing in?', 'Your account may not be approved yet, or you signed in with a different email. Call or email us and we will check.'),
 ('Can I order by phone or in person?', 'Yes. Call 212-645-0141 or visit 2 West 14th Street. Your account pricing applies either way.'),
 ('Do you ship?', 'Pickup at the shop is standard. Delivery in New York City or shipping can be arranged on request.'),
 ('Do you offer payment terms?', 'Net terms may be offered to established accounts on request.'),
 ('Is Namaste Marketplace a separate company?', 'It is Namaste Bookshop\'s wholesale program. Both are businesses of Wealth Edge Ventures Inc., and all orders are filled by the bookshop.'),
]

def faq():
    qs = ''.join(f'<details class="q"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in FAQ)
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}]
    body = f'<section class="hero sm"><div class="wrap"><p class="eyebrow">FAQ</p><h1>Wholesale questions, answered</h1></div></section><section class="sec"><div class="wrap narrow">{qs}</div></section>{cta()}'
    return page('/faq/', 'Wholesale FAQ: Approval, Minimums, Tax-Exempt & Sign In | Namaste Marketplace',
                'Answers about Namaste Bookshop wholesale accounts: who qualifies, approval time, discounts, minimums, ST-120 tax exemption, signing in and ordering.', body, ld)

def apply():
    types = ['Gift shop or boutique', 'Bookstore', 'Metaphysical or crystal shop', 'Yoga or meditation studio', 'Spa or salon', 'Healer or wellness practice', 'Boutique hotel or retreat', 'Event planner', 'Corporate gifting', 'Other']
    cats = ['Cleansing waters', 'Candles', 'Sage and palo santo', 'Incense', 'Crystals and bracelets', 'Tarot', 'Event readers', 'Gift boxes']
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">Apply</p><h1>Wholesale account application</h1><p class="lede">This form goes to Namaste Bookshop's own inbox, the same place as the application on namastebookshop.com. We review it and reply by email.</p></div></section>
<section class="sec"><div class="wrap narrow">
<form class="apply" method="post" action="{SHOP}/contact#ContactForm" accept-charset="UTF-8" id="applyForm">
<input type="hidden" name="form_type" value="contact"><input type="hidden" name="utf8" value="&#10003;">
<input type="hidden" name="contact[Subject]" value="Wholesale application (namastemarketplace.com)">
<fieldset><legend>You</legend>
<label>Your name *<input name="contact[Name]" autocomplete="name" required></label>
<label>Email for your account *<input type="email" name="contact[email]" autocomplete="email" required><small>You will sign in with this address.</small></label>
<label>Phone<input type="tel" name="contact[Phone number]" autocomplete="tel"></label></fieldset>
<fieldset><legend>Your business</legend>
<label>Business name *<input name="contact[Business name]" autocomplete="organization" required></label>
<label>Type of business *<select name="contact[Business type]" required><option value="">Choose one</option>{''.join(f'<option>{E(t)}</option>' for t in types)}</select></label>
<label>Website or social page<input name="contact[Website or social]" inputmode="url"></label>
<label>Business address *<input name="contact[Business address]" autocomplete="street-address" required></label>
<label>Resale certificate<select name="contact[Resale certificate]"><option>NY ST-120: I will email it</option><option>Outside New York: I have my state's certificate</option><option>Not reselling (events or gifts)</option><option>Not sure yet</option></select></label>
<label>NY Certificate of Authority number (if you have one)<input name="contact[Certificate of Authority number]"></label></fieldset>
<fieldset><legend>What you need</legend><div class="checks">{''.join(f'<label class="ck"><input type="checkbox" name="contact[Interested in][]" value="{E(c)}">{E(c)}</label>' for c in cats)}</div>
<label>Estimated first order<select name="contact[Estimated first order]"><option>$150 to $300</option><option>$300 to $750</option><option>$750 to $1,500</option><option>Over $1,500</option><option>Event or gift quote</option></select></label>
<label>Anything else we should know<textarea name="contact[Comment]" rows="5" placeholder="Products you want, event date and guest count, delivery needs"></textarea></label></fieldset>
<p class="small muted">By sending this you agree that Namaste Bookshop may contact you about your application. See our <a href="/privacy/">privacy page</a>.</p>
<button class="btn" type="submit">Send application</button>
<p class="small muted">After you send it, you land on namastebookshop.com. If a quick human check appears there, complete it to finish sending.</p></form>
<div class="alt-apply"><h2>Prefer email or phone?</h2><p>Email the same details to <a href="mailto:{CFG['email']}?subject=Wholesale%20application">{CFG['email']}</a> with the subject "Wholesale application", or call <a href="tel:{CFG['tel']}">{CFG['phone']}</a>.</p><p>Already approved? <a href="{LOGIN}" data-ev="sign_in">Sign in at namastebookshop.com</a>.</p></div>
</div></section>'''
    return page('/apply/', 'Apply for a Wholesale Account | Namaste Marketplace', 'Apply for a Namaste Bookshop wholesale account for your shop, studio, spa, event or gifting business. Applications are reviewed by hand.', body)

def contact():
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">Contact</p><h1>Talk to the wholesale desk</h1></div></section>
<section class="sec"><div class="wrap two"><div class="prose"><p><b>Phone</b><br><a href="tel:{CFG['tel']}">{CFG['phone']}</a></p><p><b>Email</b><br><a href="mailto:{CFG['email']}?subject=Wholesale">{CFG['email']}</a></p>
<p><b>Visit</b><br>Namaste Bookshop<br>2 West 14th Street, New York, NY 10011<br><a href="https://www.google.com/maps/search/?api=1&query=Namaste+Bookshop+2+W+14th+St+New+York" rel="noopener">Directions</a></p></div>
<div class="prose"><p><b>Hours</b><br>Monday to Thursday, 11 am to 8 pm<br>Friday and Saturday, 11 am to 9 pm<br>Sunday, 11 am to 7 pm</p><p class="muted small">Hours are the bookshop's posted hours and can change on holidays.</p><p><a class="btn" href="/apply/">Apply for an account</a></p></div></div></section>'''
    return page('/contact/', 'Contact the Wholesale Desk | Namaste Marketplace', 'Call, email or visit Namaste Bookshop at 2 W 14th St, New York, about wholesale accounts, orders, events and gift boxes.', body)

def privacy():
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">Privacy</p><h1>Privacy on namastemarketplace.com</h1></div></section><section class="sec"><div class="wrap narrow prose">
<p>This site is run by {CFG['legal']} for Namaste Bookshop's wholesale program. It has no cart and does not take payments.</p>
<h2>Applications</h2><p>When you send the application form, your answers are delivered to Namaste Bookshop through its Shopify store's contact form at namastebookshop.com. We use them to review your application, set up your account and contact you. We do not sell them.</p>
<h2>Analytics</h2><p>This site uses Google Analytics to count visits and see which pages are viewed and which buttons are used; Google may set cookies to do this. You can block these cookies in your browser or with Google's opt-out add-on.</p>
<h2>Accounts and orders</h2><p>Signing in and ordering happen on namastebookshop.com and are covered by its <a href="https://namastebookshop.com/policies/privacy-policy">privacy policy</a>.</p>
<h2>Questions</h2><p>Email <a href="mailto:{CFG['email']}">{CFG['email']}</a>.</p></div></section>'''
    return page('/privacy/', 'Privacy | Namaste Marketplace', 'How namastemarketplace.com handles wholesale applications and analytics.', body)

def notfound():
    body = '<section class="hero"><div class="wrap"><p class="eyebrow">404</p><h1>That page is not on the shelf.</h1><p class="lede">The link may be old. Try one of these.</p><div class="btns"><a class="btn" href="/">Home</a><a class="btn ghost" href="/line/">The line</a><a class="btn ghost" href="/apply/">Apply</a></div></div></section>'
    return page('/404.html', 'Page not found | Namaste Marketplace', 'Page not found.', body, noindex=True)

def main():
    P = fetch() if '--offline' not in sys.argv else json.load(open(CACHE))
    I = items(P); assert len(I) >= 40, f'only {len(I)} products fetched'
    if os.path.exists(OUT): shutil.rmtree(OUT)
    shutil.copytree(f'{R}/static', OUT)
    pages = {'index.html': home(I), 'line/index.html': line(I), 'how-it-works/index.html': how(), 'events-and-gifts/index.html': events(),
             'faq/index.html': faq(), 'apply/index.html': apply(), 'contact/index.html': contact(), 'privacy/index.html': privacy(), '404.html': notfound()}
    for p, h in pages.items():
        os.makedirs(os.path.dirname(f'{OUT}/{p}') or OUT, exist_ok=True); open(f'{OUT}/{p}', 'w').write(h)
    urls = ['/', '/line/', '/how-it-works/', '/apply/', '/events-and-gifts/', '/faq/', '/contact/', '/privacy/']
    open(f'{OUT}/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n')
    bots = ['Googlebot', 'Bingbot', 'OAI-SearchBot', 'ChatGPT-User', 'GPTBot', 'PerplexityBot', 'Google-Extended', 'ClaudeBot']
    open(f'{OUT}/robots.txt', 'w').write(''.join(f'User-agent: {b}\nAllow: /\n\n' for b in bots) + f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    open(f'{OUT}/llms.txt', 'w').write(f'''# Namaste Marketplace

> The wholesale-only program of Namaste Bookshop (2 West 14th Street, New York, NY 10011; 212-645-0141; {CFG['email']}). Approved businesses buy at 50% off retail on most items (tarot decks 20% off), with per-item minimums of 4 to 24 units. Namaste Marketplace and Namaste Bookshop are businesses of {CFG['legal']}

- [Home]({SITE}/): what the program is and who qualifies
- [The line]({SITE}/line/): the {len(I)} products in the wholesale catalog with retail price, discount and minimums
- [How it works]({SITE}/how-it-works/): apply, approval, sign in at namastebookshop.com, minimums, NY ST-120 tax-exempt steps
- [Apply]({SITE}/apply/): application form delivered to Namaste Bookshop
- [Events and gifts]({SITE}/events-and-gifts/): tarot readers for events and corporate gift boxes
- [FAQ]({SITE}/faq/)
- [Contact]({SITE}/contact/)

There is no cart or checkout on this site. Approved buyers sign in at {LOGIN} and order at namastebookshop.com.
''')
    open(f'{OUT}/CNAME', 'w').write(CFG['domain'] + '\n')
    print('built', len(pages), 'pages,', len(I), 'products')

if __name__ == '__main__': main()

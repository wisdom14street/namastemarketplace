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
 ('tarot', 'Tarot', 'The Rider-Waite deck and the three-card Gift of Tarot set. Decks carry a 1.25x markup rather than keystone.', {'Tarot Deck'}),
]

PL = json.load(open(f'{R}/site/pricelist.json'))
from decimal import Decimal, ROUND_HALF_UP
def wprice(vid, retail_cents):
    """Wholesale unit price by the Shopify price-list rule: fixed price if set, else retail minus the % adjustment, half-up to the cent."""
    if str(vid) in PL['fixed_prices']: return float(PL['fixed_prices'][str(vid)])
    r = Decimal(retail_cents) / 100 * (1 - Decimal(PL['adjustment']['value']) / 100)
    return float(r.quantize(Decimal('0.01'), ROUND_HALF_UP))

def items(P):
    rows = []
    for h in SEED['handles']:
        p = P.get(h)
        if not p: continue
        img = p.get('featured_image') or ''
        if img.startswith('//'): img = 'https:' + img
        cat = next((c[0] for c in CATS if p.get('type') in c[3]), 'crystals')
        vs = []
        for v in p['variants']:
            vid = str(v['id']); mn = int(PL['min_qty'].get(vid, min(SEED['mins'].get(h, [1]))))
            ws = wprice(vid, v['price']); msrp = v['price'] / 100
            vs.append(dict(v=vid, vt=v.get('title') or '', sku=v.get('sku') or '', ws=ws, msrp=msrp, min=mn, avail=bool(v.get('available'))))
        if not vs: continue
        rows.append(dict(h=h, t=p['title'], img=img, cat=cat, vendor=p.get('vendor', ''), vs=vs, avail=any(x['avail'] for x in vs)))
    return rows

def money(x): return f'${x:,.2f}'
def mk(v): return v['msrp'] / v['ws'] if v['ws'] else 0

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
<div class="topline">Wholesale only &middot; <a href="{LOGIN}" data-ev="sign_in">Approved buyers: sign in</a><span class="tl-ph"> &middot; <a href="tel:{CFG['tel']}">{CFG['phone']}</a></span></div>
<header class="hd"><div class="wrap hdin"><a class="logo" href="/"><span class="mark">NM</span><span><b>Namaste Marketplace</b><small>Wholesale from Namaste Bookshop</small></span></a>
<details class="menu"><summary aria-label="Menu">Menu</summary><nav>{nav}</nav></details>
<nav class="desk">{nav}</nav><div class="hbtn"><a class="btn sm ghost" href="/apply/">Apply</a><button type="button" class="btn sm cbtn" data-cart-open aria-label="Open order">Order <span class="cnt" data-cart-count hidden>0</span></button></div></div></header>
<main id="main">{body}</main>
<footer class="ft"><div class="wrap fgrid"><div><p class="fb">Namaste Marketplace</p><p>The wholesale program of Namaste Bookshop. Namaste Bookshop and Namaste Marketplace are businesses of {CFG['legal']}</p>
<p>Namaste Bookshop<br>2 West 14th Street, New York, NY 10011<br><a href="tel:{CFG['tel']}">{CFG['phone']}</a> &middot; <a href="mailto:{CFG['email']}">{CFG['email']}</a></p></div>
<div><p class="fb">Buyers</p><p><a href="/apply/">Apply for an account</a><br><a href="{LOGIN}" data-ev="sign_in">Sign in to order</a><br><a href="/line/">The wholesale line</a><br><a href="/how-it-works/">Terms and tax-exempt buying</a></p></div>
<div><p class="fb">More</p><p><a href="/events-and-gifts/">Events and gift boxes</a><br><a href="/faq/">FAQ</a><br><a href="/privacy/">Privacy</a><br><a href="https://namastebookshop.com/">Shop retail at namastebookshop.com</a></p></div></div>
<div class="wrap fine">&copy; {datetime.date.today().year} {CFG['legal']} Product names and photos are from the Namaste Bookshop catalog.</div></footer>
<div class="cdim" data-cart-close hidden></div><aside class="drawer" id="cart" aria-label="Your wholesale order" aria-hidden="true"><div class="dh"><h2>Your wholesale order</h2><button type="button" class="x" data-cart-close aria-label="Close">&times;</button></div><div class="dbody" data-cart-body></div></aside>
<script>window.NM_CART={json.dumps({"shop": SHOP, "domain": CFG["domain"], "brand": BRAND, "min": 150, "login": LOGIN})};</script>
<script src="/assets/ga.js" defer></script><script src="/assets/cart.js?v={TODAY}" defer></script><script src="/assets/site.js?v={TODAY}" defer></script></body></html>'''

def vdata(it, v):
    vt = v['vt'] if v['vt'] != 'Default Title' else ''
    return (f'data-v="{v["v"]}" data-h="{E(it["h"])}" data-t="{E(it["t"])}" data-vt="{E(vt)}" data-sku="{E(v["sku"])}" data-p="{v["ws"]:.2f}" '
            f'data-msrp="{v["msrp"]:.2f}" data-min="{v["min"]}" data-i="{E(it["img"])}" data-c="{E(it["cat"])}"')

def stepper(it, v):
    return (f'<div class="buy" {vdata(it, v)}><div class="step"><button type="button" data-dn aria-label="One case fewer">&minus;</button>'
            f'<span class="qv"><b data-cases>1</b> case<span data-pl></span><small data-units>{v["min"]} units</small></span>'
            f'<button type="button" data-up aria-label="One case more">+</button></div>'
            f'<button type="button" class="btn sm addb" data-add{"" if v["avail"] else " disabled"}>{"Add to order" if v["avail"] else "Restocking"}</button></div>')

def vselect(it):
    if len(it['vs']) < 2: return ''
    return '<label class="vsel">Color <select data-vsel>' + ''.join(f'<option value="{n}"{"" if v["avail"] else " disabled"}>{E(v["vt"])}{"" if v["avail"] else " (restocking)"}</option>' for n, v in enumerate(it['vs'])) + '</select></label>'

def vjson(it):
    return E(json.dumps([{k: v[k] for k in ('v', 'vt', 'sku', 'ws', 'msrp', 'min', 'avail')} for v in it['vs']]))

def first_v(it): return next((x for x in it['vs'] if x['avail']), it['vs'][0])
def sku_of(it, v): return v['sku'] if len(it['vs']) == 1 else f'{len(it["vs"])} colors'

def card(it):
    v = first_v(it); earn = v['msrp'] - v['ws']; per = ' per color' if len(it['vs']) > 1 else ''
    ph = f'<img src="{E(it["img"])}&width=480" alt="{E(it["t"])}" width="480" height="480" loading="lazy" decoding="async">' if it['img'] else '<span class="noimg">Photo coming</span>'
    return f'''<article class="card" data-cat="{it["cat"]}" data-vs="{vjson(it)}">
<button type="button" class="ph" data-detail aria-label="Details for {E(it["t"])}">{ph}</button>
<div class="cb"><p class="sku">Item <span data-sku>{E(sku_of(it, v))}</span></p><h3>{E(it["t"])}</h3>
<p class="wp"><b data-ws>{money(v["ws"])}</b> <span>/ unit wholesale</span></p>
<p class="cs">Case of <span data-pack>{v["min"]}</span>{per} &middot; <span data-casep>{money(v["ws"] * v["min"])}</span> / case</p>
<dl class="mg"><div><dt>MSRP</dt><dd data-msrp>{money(v["msrp"])}</dd></div><div><dt>Markup</dt><dd data-mk>{mk(v):.2f}x</dd></div><div><dt>You earn</dt><dd><span data-earn>{money(earn)}</span> per unit</dd></div></dl>
{vselect(it)}{stepper(it, v)}</div></article>'''

def trow(it):
    v = first_v(it); earn = v['msrp'] - v['ws']
    ph = f'<img src="{E(it["img"])}&width=120" alt="" width="56" height="56" loading="lazy">' if it['img'] else ''
    return f'''<tr class="card" data-cat="{it["cat"]}" data-vs="{vjson(it)}"><td class="ti"><div class="tiw"><button type="button" class="tph" data-detail aria-label="Details for {E(it["t"])}">{ph}</button><span><b>{E(it["t"])}</b>{vselect(it)}</span></div></td>
<td data-sku>{E(sku_of(it, v))}</td><td class="n"><b data-ws>{money(v["ws"])}</b></td><td class="n" data-pack>{v["min"]}</td><td class="n" data-casep>{money(v["ws"] * v["min"])}</td><td class="n" data-msrp>{money(v["msrp"])}</td><td class="n"><span data-earn>{money(earn)}</span> <small data-mk>{mk(v):.2f}x</small></td><td>{stepper(it, v)}</td></tr>'''

def cta():
    return f'''<section class="band"><div class="wrap bandin"><div><h2>Open a wholesale account</h2><p>Tell us about your business. We review every application by hand and reply by email, usually within a few business days.</p></div>
<div class="btns"><a class="btn light" href="/apply/">Apply now</a><a class="btn outline" href="{LOGIN}" data-ev="sign_in">Already approved? Sign in</a></div></div></section>'''

def sample_rows(I):
    picks = []
    for c in ('candles', 'smudge', 'waters', 'incense', 'crystals', 'tarot'):
        x = next((i for i in I if i['cat'] == c and i['avail']), None)
        if x: picks.append(x)
    r = ''
    for it in picks:
        v = first_v(it)
        r += f'<tr><td>{E(it["t"])}</td><td class="n"><b>{money(v["ws"])}</b></td><td class="n">{v["min"]}</td><td class="n">{money(v["msrp"])}</td><td class="n">{mk(v):.2f}x</td></tr>'
    return f'<div class="tblwrap"><table class="ls mini"><thead><tr><th>Item</th><th class="n">Wholesale</th><th class="n">Case</th><th class="n">MSRP</th><th class="n">Markup</th></tr></thead><tbody>{r}</tbody></table></div>'

def home(I):
    keystone = sum(1 for i in I if abs(mk(first_v(i)) - 2) < 0.02)
    lo_case = min(first_v(i)['ws'] * first_v(i)['min'] for i in I)
    cats = ''
    for k, name, blurb, _ in CATS:
        its = [i for i in I if i['cat'] == k]
        if not its: continue
        im = next((i['img'] for i in its if i['img']), '')
        lo = min(first_v(i)['ws'] for i in its)
        cats += f'''<a class="cat" href="/line/#{k}"><img src="{E(im)}&width=420" alt="{E(name)}" width="420" height="420" loading="lazy" decoding="async"><span><b>{E(name)}</b><small>{len(its)} item{'s' if len(its) != 1 else ''} &middot; from {money(lo)}/unit</small></span></a>'''
    who = ''.join(f'<li>{w}</li>' for w in ['Gift shops, boutiques and bookstores', 'Metaphysical and crystal shops', 'Yoga and meditation studios', 'Spas, salons and wellness practices', 'Reiki practitioners and healers', 'Boutique hotels and retreat hosts', 'Event planners and party hosts', 'Companies buying client or staff gifts'])
    faq = [('Is this a store I can buy from today?', 'You can build an order here, but only approved business accounts can check out at wholesale prices. Personal shoppers can buy at namastebookshop.com.'),
           ('Who reviews my application?', 'The owner of Namaste Bookshop reviews each one. If something is missing we will email you rather than decline.'),
           ('Do I need a resale certificate?', 'To buy without sales tax in New York, yes: a completed Form ST-120. Event and gifting buyers who are not reselling can still open an account and pay sales tax.')]
    fq = ''.join(f'<details class="q"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq)
    hero_imgs = ''.join(f'<img src="{E(i["img"])}&width=360" alt="" width="360" height="360" decoding="async">' for i in [next(x for x in I if x['cat'] == c and x['img']) for c in ('candles', 'smudge', 'waters', 'crystals')])
    body = f'''<section class="hero"><div class="wrap heroin"><div class="htxt"><p class="eyebrow">Wholesale line &middot; Namaste Bookshop, Union Square NYC</p>
<h1>Keystone margins on the spiritual goods a Manhattan bookshop sells every day.</h1>
<p class="lede">Namaste Marketplace is the wholesale program of <a href="https://namastebookshop.com/">Namaste Bookshop</a>. Buy cleansing waters, Reiki candles, sage, incense and crystals by the case, price them at the suggested retail, and earn about double what you paid.</p>
<div class="btns"><a class="btn" href="/line/">Build an order</a><a class="btn ghost" href="/apply/">Apply for an account</a></div>
<ul class="facts"><li><b>2x</b><span>keystone markup on {keystone} of {len(I)} items</span></li><li><b>Case of 4&ndash;24</b><span>small case packs, cases from {money(lo_case)}</span></li><li><b>$150</b><span>opening order</span></li></ul></div>
<div class="hcol" aria-hidden="true">{hero_imgs}</div></div></section>
<section class="sec"><div class="wrap"><p class="eyebrow">Line sheet preview</p><h2>What a case costs, and what it sells for</h2>
<p class="muted">Wholesale prices come from the bookshop's own Shopify wholesale price list. MSRP is the price on namastebookshop.com.</p>{sample_rows(I)}
<p><a class="link" href="/line/">Full line sheet with all {len(I)} items &rarr;</a></p></div></section>
<section class="sec alt"><div class="wrap"><p class="eyebrow">Ordering</p><h2>How wholesale ordering works</h2>
<ol class="steps"><li><b>Apply once</b><span>Send the short business form. We review it by hand and set up your company account with wholesale pricing and, for New York resellers, tax exemption.</span></li><li><b>Build your order</b><span>Add cases here. The order summary shows case count, wholesale subtotal and how close you are to the $150 opening order.</span></li><li><b>Sign in and check out</b><span>Send the order to namastebookshop.com, sign in with your approved email, and Shopify confirms your wholesale prices at checkout.</span></li></ol>
<p><a class="link" href="/how-it-works/">Terms, case packs and tax-exempt steps &rarr;</a></p></div></section>
<section class="sec"><div class="wrap"><p class="eyebrow">Categories</p><h2>The line</h2><div class="cats">{cats}</div></div></section>
<section class="sec alt"><div class="wrap two"><div><p class="eyebrow">Who qualifies</p><h2>Built for small businesses that sell or gift</h2><p class="muted">You need a real business: a shop, a studio, a practice, a venue or a company. A website, social page or storefront address helps us approve you faster.</p></div><ul class="who">{who}</ul></div></section>
<section class="sec"><div class="wrap two"><div><p class="eyebrow">Beyond the shelf</p><h2>Readers and gift boxes for events</h2><p class="muted">The bookshop also sends tarot readers to parties and corporate events and packs crystal and sage gift boxes in three tiers.</p><a class="link" href="/events-and-gifts/">Event and gift packages &rarr;</a></div>
<div><p class="eyebrow">Quick answers</p>{fq}<p><a class="link" href="/faq/">All questions &rarr;</a></p></div></div></section>{cta()}'''
    return page('/', 'Namaste Marketplace | Wholesale Sage, Candles, Incense & Crystals by the Case, NYC',
                'Wholesale line sheet from Namaste Bookshop in Union Square, NYC: case packs from 4 units, keystone (2x) margins on most items, $150 opening order and NY tax-exempt resale for approved accounts.', body)

def line(I):
    chips = '<button type="button" class="chip on" data-f="all">All</button>' + ''.join(f'<button type="button" class="chip" data-f="{k}">{E(n.split(",")[0])}</button>' for k, n, _, _ in CATS if any(i['cat'] == k for i in I))
    order = {c[0]: n for n, c in enumerate(CATS)}; I = sorted(I, key=lambda i: (order.get(i['cat'], 9), not i['avail']))
    cards = ''.join(card(i) for i in I)
    rows = ''.join(trow(i) for i in I)
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">Wholesale line sheet &middot; updated {TODAY}</p><h1>The Namaste wholesale line</h1>
<p class="lede">{len(I)} items. Unit and case prices are the Namaste Wholesale price list in Shopify; MSRP is the namastebookshop.com price. Add cases to build an order, then sign in at checkout with your approved account.</p></div></section>
<section class="sec tight"><div class="wrap"><div class="tools"><div class="chips" role="group" aria-label="Filter by category">{chips}</div><div class="views" role="group" aria-label="View"><button type="button" class="vbtn on" data-view="cards">Cards</button><button type="button" class="vbtn" data-view="sheet">Line sheet</button></div></div>
<div class="grid" data-pane="cards">{cards}</div>
<div class="tblwrap" data-pane="sheet" hidden><table class="ls"><thead><tr><th>Item</th><th>SKU</th><th class="n">Wholesale</th><th class="n">Case</th><th class="n">Case price</th><th class="n">MSRP</th><th class="n">Earn / markup</th><th>Order</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="muted small">Prices in USD. Shopify applies your account's catalog prices and case minimums at checkout, so the checkout price is the final word. Items marked restocking can't be added online right now; ask us about them at <a href="mailto:{CFG['email']}?subject=Wholesale%20question">{CFG['email']}</a>.</p></div></section>{cta()}
<dialog class="dlg" id="detail"><form method="dialog"><button class="x" aria-label="Close">&times;</button></form><div data-dbody></div></dialog>'''
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": "Namaste wholesale line sheet", "numberOfItems": len(I),
           "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": i['t'], "url": f"{SHOP}/products/{i['h']}"} for n, i in enumerate(I)]}]
    return page('/line/', 'Wholesale Line Sheet: Case Prices, MSRP & Margins | Namaste Marketplace',
                f'The Namaste Bookshop wholesale line sheet: {len(I)} items with wholesale unit price, case pack, case price, MSRP and markup. Build an order and check out with an approved account.', body, ld)

def how():
    body = f'''<section class="hero sm"><div class="wrap"><p class="eyebrow">How it works</p><h1>Terms, case packs and your first order</h1><p class="lede">Everything runs through Namaste Bookshop's own Shopify store: one account, one wholesale price list, one checkout.</p></div></section>
<section class="sec"><div class="wrap narrow prose">
<h2>1. Apply</h2><p>Send the <a href="/apply/">application form</a> with your business name, type, address and where you sell. It goes to the bookshop's wholesale inbox. Nothing is charged.</p>
<h2>2. Approval</h2><p>We read each application ourselves. Once approved, we create a company account for your business in our Shopify store and connect it to the Namaste Wholesale price list. We email you as soon as it is ready.</p>
<h2>3. Build an order</h2><p>Use the <a href="/line/">line sheet</a> to add cases. Each item is sold by the case pack shown (the item's minimum), and the steppers add whole cases. The order summary keeps a running count of cases, units, wholesale subtotal and suggested-retail value.</p>
<h2>4. Sign in and check out</h2><p>Tap <b>Continue to checkout</b> and your order moves to the namastebookshop.com cart with the same items and quantities. Sign in there with the email on your account (Shopify emails you a one-time code; there is no password). Shopify then applies your account's wholesale prices and case minimums, and you pay at checkout. If you sign in first at <a href="{LOGIN}" data-ev="sign_in">namastebookshop.com/account/login</a>, your prices show as soon as the cart opens.</p>
<h2>Pricing and margin</h2><ul><li>Most of the line is priced for a keystone (2x) markup: the wholesale price is half the MSRP shown on namastebookshop.com.</li><li>Tarot decks carry a 1.25x markup, because decks reach us at a narrower margin.</li><li>Every price on this site comes from the Shopify price list, and the checkout price is the final word.</li></ul>
<h2>Case packs and minimums</h2><ul><li>Case packs run from 4 units (Rider-Waite deck) to 24 units (small tokens, 2 oz Florida Water, Gift of Tarot). Most are 6 or 12.</li><li>Mini ritual candles are packed per color.</li><li>Opening orders start at $150. Reorders only need to meet each item's case pack.</li></ul>
<h2>Tax-exempt resale in New York</h2><p>If you resell the goods and hold a New York sales tax Certificate of Authority, you can buy without sales tax:</p><ol><li>Fill in New York State Form ST-120, Resale Certificate, with your Certificate of Authority number. The form is available from the <a href="https://www.tax.ny.gov/pdf/current_forms/st/st120_fill_in.pdf" rel="noopener">NYS Department of Taxation and Finance</a>.</li><li>Email the signed form to <a href="mailto:{CFG['email']}?subject=ST-120%20for%20wholesale%20account">{CFG['email']}</a>, or bring it to the shop.</li><li>We mark your company account tax-exempt before your first order, so tax is not charged at checkout.</li></ol>
<p>Buying for events, staff or clients rather than resale? You can still have a wholesale account; sales tax is charged as normal. Based outside New York? Tell us your state in the application and we will let you know which certificate we can accept.</p>
<h2>Shipping, pickup and payment</h2><p>Orders ship from the bookshop in Manhattan, usually within 1 to 3 business days, or you can pick up at 2 West 14th Street. Delivery within New York City can be arranged on request. Payment is by card at checkout. Invoice or net terms are not set up online; established accounts can ask us about them.</p>
</div></section>{cta()}'''
    return page('/how-it-works/', 'How Wholesale Works: Case Packs, Margins, $150 Opening Order & NY ST-120 | Namaste Marketplace',
                'How Namaste Bookshop wholesale works: apply, get approved, build an order by the case, sign in at checkout for wholesale prices. Keystone margins, case packs, $150 opening order and NY ST-120 tax-exempt steps.', body)

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
 ('Can I buy here without an account?', 'Anyone can build an order here, but checkout happens on namastebookshop.com and only approved business accounts get wholesale prices there. If you are shopping for yourself, namastebookshop.com sells at retail.'),
 ('What kind of businesses do you approve?', 'Shops and boutiques, metaphysical and crystal stores, yoga and meditation studios, spas, salons, healers and wellness practices, boutique hotels, event planners and companies buying gifts.'),
 ('How long does approval take?', 'We aim to reply within a few business days. Applications with a website, social page or shop address are the quickest to check.'),
 ('What margin can I expect?', 'Most items are priced for a keystone (2x) markup at the suggested retail price. Tarot decks carry a 1.25x markup.'),
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
                'Answers about Namaste Bookshop wholesale accounts: who qualifies, approval time, margins, case packs, ST-120 tax exemption, signing in and ordering.', body, ld)

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
<p>This site is run by {CFG['legal']} for Namaste Bookshop's wholesale program. Its order builder keeps your cart in your own browser; checkout and payment happen on namastebookshop.com.</p>
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
    chk = bad = 0
    for it in I:
        for v in it['vs']:
            vp = PL['verified_prices'].get(v['v'])
            if vp and abs(float(vp['retail']) - v['msrp']) < 0.001:
                chk += 1
                if abs(float(vp['wholesale']) - v['ws']) > 0.001: bad += 1; print('PRICE MISMATCH', v['v'], v['ws'], vp)
    assert not bad, 'wholesale prices disagree with the Shopify price-list export'
    print('price check:', chk, 'variants match the Shopify price list export')
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

> The wholesale-only program of Namaste Bookshop (2 West 14th Street, New York, NY 10011; 212-645-0141; {CFG['email']}). Approved businesses buy by the case (4 to 24 units) at wholesale prices set for a keystone (2x) markup on most items; tarot decks are 1.25x. Opening orders start at $150. Namaste Marketplace and Namaste Bookshop are businesses of {CFG['legal']}

- [Home]({SITE}/): what the program is and who qualifies
- [The line]({SITE}/line/): the {len(I)} products in the wholesale catalog with wholesale unit price, case pack, case price, MSRP and markup
- [How it works]({SITE}/how-it-works/): apply, approval, sign in at namastebookshop.com, minimums, NY ST-120 tax-exempt steps
- [Apply]({SITE}/apply/): application form delivered to Namaste Bookshop
- [Events and gifts]({SITE}/events-and-gifts/): tarot readers for events and corporate gift boxes
- [FAQ]({SITE}/faq/)
- [Contact]({SITE}/contact/)

Orders built on this site hand off to the namastebookshop.com cart; approved buyers sign in there ({LOGIN}) and Shopify applies the wholesale price list at checkout.
''')
    open(f'{OUT}/CNAME', 'w').write(CFG['domain'] + '\n')
    print('built', len(pages), 'pages,', len(I), 'products')

if __name__ == '__main__': main()

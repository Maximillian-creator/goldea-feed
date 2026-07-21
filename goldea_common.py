"""
Goldea Health — gedeelde kern
=============================
goldea-health.com is een publieke **Shopify**-winkel (geen login). We halen alles
uit twee bronnen:

  1. /products.json          → titel, body_html, product_type, tags, opties, álle
                               afbeeldingen, varianten (sku = EAN, prijs, available)
  2. de live productpagina   → de `toggle-product-specifications`-secties
                               (ingrediënten, dosering, gezondheidsclaims, bewaren…)

Bijzonderheden van deze winkel:
- De **SKU ís de EAN-barcode** (bv. 8720299061552) → barcode = sku.
- Het `vendor`-veld is een marketing-slogan ("Activeert je natuurlijke energie"),
  geen merk → we hardcoden BRAND = "Goldea Health".
- Prijs = de getoonde **consumentenprijs (incl. BTW), 1-op-1** (afgesproken model;
  geen kostprijs/marge).
- products.json geeft alleen `available` (in/uit voorraad), geen exact aantal.

Lokaal testen achter een SSL-onderscheppende proxy: INSECURE_SSL=1.
Eén product testen: TEST_HANDLE=<handle>.
"""

import os
import re
import time
from html import unescape

import requests

BASE_URL = "https://goldea-health.com"
BRAND = "Goldea Health"
REQUEST_DELAY = 0.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GFY-GoldeaFeed/1.0)",
    "Accept-Language": "nl-NL,nl;q=0.9",
}

# Alleen voor lokaal testen achter een SSL-onderscheppende bedrijfsproxy.
VERIFY_SSL = os.environ.get("INSECURE_SSL") != "1"
if not VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings()

# De uitklap-secties op de productpagina: knop (kop) + content-div.
SECTION_RE = re.compile(
    r'<button class="toggle-button-product-specifications">(.*?)<span[^>]*>.*?</button>\s*'
    r'<div class="toggle-content-product-specifications">(.*?)</div>',
    re.DOTALL,
)


def _get(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=VERIFY_SSL)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 15
                print(f"    ⚠️  Fout ({e}), opnieuw in {wait}s...")
                time.sleep(wait)
            else:
                raise


def fetch_products_json():
    products = []
    page = 1
    while True:
        resp = _get(f"{BASE_URL}/products.json?limit=250&page={page}")
        batch = resp.json().get("products", [])
        if not batch:
            break
        products.extend(batch)
        if len(batch) < 250:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    return products


def is_supplement(p):
    """Filter promotiemateriaal, accessoires, wholesale-only en €0-artikelen weg."""
    pt = (p.get("product_type") or "").lower()
    tags = [t.lower() for t in p.get("tags", [])]
    if "accessoires" in pt or "promotiemateriaal" in pt:
        return False
    if "wholesale-only" in tags:
        return False
    if all(float(v.get("price") or 0) == 0 for v in p.get("variants", [])):
        return False
    return True


def _clean(html):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html or ""))).strip()


def _barcode(sku):
    s = (sku or "").strip()
    return s if re.fullmatch(r"\d{8,14}", s) else ""


def fetch_sections(handle):
    """De toggle-secties van de live pagina als [(kop, html-content), ...]."""
    try:
        html = _get(f"{BASE_URL}/products/{handle}").text
    except Exception as e:
        print(f"    ⚠️  Live pagina faalt bij {handle}: {e}")
        return []
    out = []
    for head, content in SECTION_RE.findall(html):
        kop = _clean(head)
        if kop:
            out.append((kop, content.strip()))
    return out


def build_description(body_html, sections):
    """body_html + alle uitklap-secties tot één rijke HTML-beschrijving."""
    parts = []
    if body_html:
        parts.append(unescape(body_html))
    for head, content in sections:
        parts.append(f"<p><strong>{head}</strong></p>\n{unescape(content)}")
    return "\n".join(parts)


def normalize(p, sections):
    opts = {o.get("position"): o.get("name", "") for o in p.get("options", [])}
    variants = []
    for v in p.get("variants", []):
        sku = v.get("sku", "") or ""
        variants.append({
            "sku": sku,
            "barcode": _barcode(sku),
            "price": round(float(v.get("price") or 0), 2),
            "compare_at": round(float(v["compare_at_price"]), 2) if v.get("compare_at_price") else "",
            "available": bool(v.get("available")),
            "title": v.get("title", "") or "",
            "option1": v.get("option1", "") or "",
            "option2": v.get("option2", "") or "",
            "option3": v.get("option3", "") or "",
            "grams": v.get("grams", "") or "",
            "featured_image": (v.get("featured_image") or {}).get("src", "") if isinstance(v.get("featured_image"), dict) else "",
        })
    images = [img.get("src", "") for img in p.get("images", []) if img.get("src")]
    return {
        "handle": p.get("handle", ""),
        "title": p.get("title", ""),
        "vendor": BRAND,
        "brand": BRAND,
        "product_type": p.get("product_type", "") or "",
        "tags": ", ".join(p.get("tags", [])),
        "body_html": unescape(p.get("body_html", "") or ""),
        "description": build_description(p.get("body_html", ""), sections),
        "images": images,
        "option1_name": opts.get(1, ""),
        "option2_name": opts.get(2, ""),
        "option3_name": opts.get(3, ""),
        "variants": variants,
    }


def fetch_products():
    raw = fetch_products_json()
    supps = [p for p in raw if is_supplement(p)]
    test = os.environ.get("TEST_HANDLE")
    if test:
        supps = [p for p in supps if p.get("handle") == test]
    print(f"📦 {len(raw)} producten, {len(supps)} supplementen te verwerken "
          f"({len(raw) - len([p for p in raw if is_supplement(p)])} gefilterd)")
    out = []
    for i, p in enumerate(supps, 1):
        secs = fetch_sections(p.get("handle", ""))
        print(f"  [{i}/{len(supps)}] {p.get('title', '')[:50]:<50} — {len(secs)} secties")
        out.append(normalize(p, secs))
        time.sleep(REQUEST_DELAY)
    return out

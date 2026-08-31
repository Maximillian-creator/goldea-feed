"""
Goldea UPDATE-feed
==================
Lichte feed om BESTAANDE producten bij te werken: verkoopprijs + beschikbaarheid.
Matcht in Stock Sync op SKU (= EAN) of barcode.

  price = consumentenprijs (incl. BTW), 1-op-1
  available = in/uit voorraad bij Goldea (products.json geeft geen exact aantal)

Bron: goldea-health.com (publieke Shopify). Zie goldea_common.py.
Lokaal: INSECURE_SSL=1, TEST_HANDLE=<handle>.
"""

import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

import goldea_common as gc

OUTPUT_FILE = "goldea_feed.xml"


def build_xml(products):
    root = ET.Element("products")
    for p in products:
        for v in p["variants"]:
            item = ET.SubElement(root, "product")

            def add(tag, value):
                el = ET.SubElement(item, tag)
                el.text = "" if value is None else str(value)

            add("sku", v["sku"])
            add("barcode", v["barcode"])
            add("title", p["title"])
            add("price", f"{v['price']:.2f}")
            add("compare_at_price", f"{v['compare_at']:.2f}" if v["compare_at"] else "")
            add("available", "true" if v["available"] else "false")
            add("handle", p["handle"])
            add("description", p["description"])
    return root


def save_xml(root, filepath):
    xml_str = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n💾 XML opgeslagen: {filepath}")


def main():
    print("🚀 Goldea UPDATE-feed gestart\n")
    start = time.time()
    products = gc.fetch_products()
    root = build_xml(products)
    gc.controleer_omvang(len(root.findall("product")), OUTPUT_FILE)
    save_xml(root, OUTPUT_FILE)
    print(f"⏱️  Klaar in {time.time() - start:.0f}s — {len(products)} producten")
    print("\n📋 Feed-URL voor Stock Sync (Update):")
    print("https://raw.githubusercontent.com/Maximillian-creator/goldea-feed/main/goldea_feed.xml")


if __name__ == "__main__":
    main()

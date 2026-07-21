"""
Goldea ADD-feed
===============
Volledige productinfo om met Stock Sync NIEUWE producten aan te maken.
Bron: goldea-health.com (publieke Shopify). Zie goldea_common.py.

  price = consumentenprijs (incl. BTW), 1-op-1
  barcode = SKU (Goldea gebruikt de EAN als SKU)
  description = body_html + alle uitklap-secties (ingrediënten, dosering,
                gezondheidsclaims, bewaren, veiligheid)

Zet in Stock Sync de ADD-koppeling op "alleen nieuwe producten aanmaken".
Lokaal: INSECURE_SSL=1, TEST_HANDLE=<handle>.
"""

import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

import goldea_common as gc

OUTPUT_FILE = "goldea_add_feed.xml"


def add_child(parent, tag, value):
    el = ET.SubElement(parent, tag)
    el.text = "" if value is None else str(value)
    return el


def build_xml(products):
    root = ET.Element("products")
    for p in products:
        item = ET.SubElement(root, "product")
        add_child(item, "handle", p["handle"])
        add_child(item, "title", p["title"])
        add_child(item, "vendor", p["vendor"])
        add_child(item, "brand", p["brand"])
        add_child(item, "product_type", p["product_type"])
        add_child(item, "tags", p["tags"])
        add_child(item, "published", "true")
        add_child(item, "body_html", p["body_html"])
        add_child(item, "description", p["description"])
        add_child(item, "option1_name", p["option1_name"])
        add_child(item, "option2_name", p["option2_name"])
        add_child(item, "option3_name", p["option3_name"])

        images_el = ET.SubElement(item, "images")
        for src in p["images"]:
            img_el = ET.SubElement(images_el, "image")
            add_child(img_el, "src", src)
        add_child(item, "image_links", ",".join(p["images"]))
        first_image = p["images"][0] if p["images"] else ""

        variants_el = ET.SubElement(item, "variants")
        for v in p["variants"]:
            v_el = ET.SubElement(variants_el, "variant")
            add_child(v_el, "sku", v["sku"])
            add_child(v_el, "barcode", v["barcode"])
            add_child(v_el, "price", f"{v['price']:.2f}")
            add_child(v_el, "compare_at_price", f"{v['compare_at']:.2f}" if v["compare_at"] else "")
            add_child(v_el, "available", "true" if v["available"] else "false")
            add_child(v_el, "variant_title", v["title"])
            add_child(v_el, "option1", v["option1"])
            add_child(v_el, "option2", v["option2"])
            add_child(v_el, "option3", v["option3"])
            add_child(v_el, "weight", v["grams"])
            add_child(v_el, "weight_unit", "g")
            add_child(v_el, "image", v["featured_image"] or first_image)
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
    print("🚀 Goldea ADD-feed gestart\n")
    start = time.time()
    products = gc.fetch_products()
    root = build_xml(products)
    save_xml(root, OUTPUT_FILE)
    print(f"⏱️  Klaar in {time.time() - start:.0f}s — {len(products)} producten")
    print("\n📋 Feed-URL voor Stock Sync (Add products):")
    print("https://raw.githubusercontent.com/Maximillian-creator/goldea-feed/main/goldea_add_feed.xml")


if __name__ == "__main__":
    main()

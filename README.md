# Goldea feeds → Stock Sync

Scrapt de publieke Shopify-winkel **Goldea Health** (`goldea-health.com`) en
genereert twee XML-feeds voor [Stock Sync](https://stock-sync.com). Beide draaien
automatisch via GitHub Actions.

| Feed | Script | Output | Doel | Schema |
|---|---|---|---|---|
| **Update-feed** | `scraper.py` | `goldea_feed.xml` | Prijs + beschikbaarheid van **bestaande** producten | 2× per dag (06:00 + 18:00 UTC) |
| **Add-feed** | `add_scraper.py` | `goldea_add_feed.xml` | **Nieuwe** producten aanmaken met álle info | 1× per week (ma 04:00 UTC) |

## Feed-URL's (Stock Sync)

```
Update:  https://raw.githubusercontent.com/Maximillian-creator/goldea-feed/main/goldea_feed.xml
Add:     https://raw.githubusercontent.com/Maximillian-creator/goldea-feed/main/goldea_add_feed.xml
```

## Bronnen & bijzonderheden

- **`/products.json`** → titel, body_html, product_type, tags, opties, álle
  afbeeldingen, varianten.
- **De live productpagina** → de `toggle-product-specifications`-secties
  (ingrediënten, dosering, gezondheidsclaims, veiligheid, bewaren). Die worden
  onder de beschrijving geplakt, zodat **álle info in het `description`-veld** zit.
- **SKU = EAN-barcode** (Goldea gebruikt de EAN als SKU) → `barcode` = `sku`.
- Het `vendor`-veld is een marketing-slogan; het merk is hard op **"Goldea Health"** gezet.

## Prijs & voorraad

- `price` = de getoonde **consumentenprijs (incl. BTW), 1-op-1** — géén opslag,
  géén kostprijs. Stel in Stock Sync dus **geen extra BTW/marge** in.
- `available` = in/uit voorraad bij Goldea. products.json geeft **geen exact aantal**,
  dus er is geen quantity-veld; map `available` op beschikbaarheid.

## Filtering

Promotiemateriaal (`wholesale-only`, product_type *Promotiemateriaal*),
accessoires (pillendoos, speelkaarten) en €0-artikelen worden automatisch
overgeslagen. Blijft over: de supplementen + bundels (~15 producten).

> **Bundels** (Daily Essential / Good Mood) hebben geen EAN-SKU. De add-feed maakt
> ze aan op `handle`; de update-feed kan ze niet op SKU matchen (matchen op handle
> of handmatig).

## Stock Sync mapping (Add products)

Nieuwe koppeling, type **"Add Products"**, bronformaat XML, record-pad
`/products/product`, groepeer op **Handle**.

| Stock Sync veld | XPath |
|---|---|
| Handle | `handle` |
| Title | `title` |
| Body HTML / Description | `description` |
| Vendor | `vendor` (= Goldea Health) |
| Type | `product_type` |
| Tags | `tags` |
| Option1/2/3 Name | `option1_name` / … |
| Image Src *(meerdere)* | `images/image/src` *(of `image_links`)* |
| Variant SKU | `variants/variant/sku` |
| Variant Barcode | `variants/variant/barcode` |
| Variant Price | `variants/variant/price` *(incl. BTW)* |
| Variant Option1/2/3 | `variants/variant/option1` / … |

Zet de add-koppeling op **alleen nieuwe producten aanmaken**.

## Lokaal draaien / testen

```bash
pip install -r requirements.txt
python scraper.py                             # update-feed
python add_scraper.py                         # add-feed
TEST_HANDLE=power-5-magnesium python add_scraper.py   # één product
INSECURE_SSL=1 python scraper.py              # achter een SSL-onderscheppende proxy
```

Op Windows lokaal: `PYTHONIOENCODING=utf-8` als de console de emoji's niet aankan.

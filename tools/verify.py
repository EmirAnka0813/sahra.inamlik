#!/usr/bin/env python3
"""
SAHRA SİTESİ — DOĞRULAMA ARACI
================================
Tek giriş noktası: hem statik hem de canlı kontrolleri yapar.

    python tools/verify.py                 # statik + canlı
    python tools/verify.py --static        # sadece statik (ag gerekmez)
    python tools/verify.py --base URL      # farkli URL (yerel sunucu)

Cikis: her kontrol icin [OK]/[FAIL], sonunda ozet. Cikis kodu:
    0 = tum kontroller gecti
    1 = en az bir kontrol basarisiz
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
PHOTOS = KOK / "photos"
VARSAYILAN = "https://emiranka0813.github.io/sahra.inamlik/index.html"

GECTI, HATALAR = [], []


def kontrol(ad, kosul, detay=""):
    (GECTI if kosul else HATALAR).append(ad)
    print(f"  [{'OK' if kosul else 'FAIL'}]   {ad}" + (f"  ({detay})" if detay else ""))


def fetch(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception:
        return ""


def statik():
    """Disk uzerinden dogrulama — ag gerekmez."""
    ih = (KOK / "index.html").read_text(encoding="utf-8")
    bh = (KOK / "index.html").exists() and (KOK / "index-bday.html").read_text(encoding="utf-8")
    galeri = json.loads((PHOTOS / "_galeri.json").read_text(encoding="utf-8"))
    data = json.loads((KOK / "data" / "sahra.json").read_text(encoding="utf-8"))

    print("\n[1] SEO — robots.txt / sitemap.xml")
    rb = (KOK / "robots.txt").read_text(encoding="utf-8")
    sm = (KOK / "sitemap.xml").read_text(encoding="utf-8")
    kontrol("robots User-agent/Allow", "User-agent: *" in rb and "Allow: /" in rb)
    kontrol("robots sitemap referansi", "sitemap.xml" in rb)
    kontrol("sitemap gecerli/urlset", sm.strip().startswith("<?xml") and "<urlset" in sm)
    kontrol("sitemap ana sayfa + bday", "sahra.inamlik/</loc>" in sm
            and "index-bday.html</loc>" in sm)
    kontrol("sitemap image namespace", "image:image" in sm)

    print("\n[2] SEO — index.html meta")
    for ad, pat in (("canonical", r'rel="canonical"'), ("robots meta", r'name="robots"'),
                    ("twitter:title", r'name="twitter:title"'),
                    ("twitter:description", r'name="twitter:description"'),
                    ("twitter:card", r'name="twitter:card"'),
                    ("og:title", r'property="og:title"'), ("og:description", r'property="og:description"'),
                    ("og:image", r'property="og:image"'), ("og:url", r'property="og:url"')):
        kontrol(f"{ad} var", bool(re.search(pat, ih)))
    kontrol("H1 tam 1", len(re.findall(r"<h1[ >]", ih, re.I)) == 1)
    kontrol("H2 7", len(re.findall(r"<h2[ >]", ih, re.I)) == 7)
    kontrol("mukerrer meta yok",
            ih.count('name="twitter:title"') == 1 and ih.count('name="robots"') == 1
            and ih.count('rel="canonical"') == 1)
    kontrol("bos UTF-8 (index.html)", "\ufffd" not in ih)
    kontrol("bos UTF-8 (index-bday.html)", "\ufffd" not in bh)

    print("\n[3] Galeri / medya")
    gal = re.findall(r'\{f:"([^"]+)"', ih)
    vid = re.findall(r'\{id:"([\w-]{11})"', ih)
    kontrol(f"galeri {len(gal)} = 22", len(gal) == 22)
    kontrol(f"medya {len(vid)} = 3", len(vid) == 3)
    kontrol("her fotograf 3 formatta", all(
        (PHOTOS / f"{a}-800.webp").exists() and (PHOTOS / f"{a}-1600.webp").exists()
        and (PHOTOS / f"{a}.jpg").exists() for a in gal))
    kontrol("photos/ 22 x 800webp", len(list(PHOTOS.glob("*-800.webp"))) == 22)
    kontrol("photos/ 22 x 1600webp", len(list(PHOTOS.glob("*-1600.webp"))) == 22)
    kontrol("data galeri 22", len(galeri) == 22)
    kontrol("data video 3", len(data["videolar"]) == 3)
    kontrol("data fotoSayisi/videoSayisi",
            data.get("fotoSayisi") == 22 and data.get("videoSayisi") == 3)

    print("\n[4] Kirik referans yok")
    for sayfa, icerik in (("index.html", ih), ("index-bday.html", bh)):
        refs = set(re.findall(r"photos/([A-Za-z0-9_\-]+?\.(?:webp|jpg))", icerik))
        eksik = [r for r in refs if not (PHOTOS / r).exists()]
        kontrol(f"{sayfa}: {len(refs)} referans diskte", not eksik, str(eksik[:3]))
    bday_foto = re.findall(r"'photos/([A-Za-z0-9_\-]+)-800\.webp'", bh)
    kontrol("bday 20 fotograf", len(bday_foto) == 20, str(len(bday_foto)))
    kontrol("bday 1600px mevcut",
            all((PHOTOS / f"{a}-1600.webp").exists() for a in bday_foto))


def canli(base):
    """Canli URL uzerinden dogrulama."""
    print(f"\n[5] Canli — {base}")
    t = fetch(base)
    if len(t) < 500:
        kontrol("canli sayfa yuklendi", False, f"{len(t)} bayt")
        return
    kontrol("canli sayfa yuklendi", True, f"{len(t)} bayt")
    kontrol("canli canonical", 'rel="canonical"' in t)
    kontrol("canli robots meta", 'name="robots"' in t)
    kontrol("canli twitter:title", 'name="twitter:title"' in t)
    kontrol("canli galeri 22", t.count('{f:"') == 22, str(t.count('{f:"')))
    kontrol("canli medya 3", t.count('{id:"') == 3, str(t.count('{id:"')))
    kontrol("canli H1 1", len(re.findall(r"<h1[ >]", t, re.I)) == 1)

    base_dir = base.rsplit("/", 1)[0] if base.endswith(".html") else base.rstrip("/")
    for yol, beklenen in (("robots.txt", "User-agent"), ("sitemap.xml", "<urlset")):
        x = fetch(f"{base_dir}/{yol}")
        kontrol(f"canli {yol} erisilebilir + dogru", beklenen in x, f"{len(x)} bayt")

    bday = fetch(f"{base_dir}/index-bday.html")
    kontrol("canli bday yuklendi", len(bday) > 5000, f"{len(bday)} bayt")
    kontrol("canli bday 20 foto", bday.count("-800.webp") >= 20, str(bday.count("-800.webp")))
    kontrol("canli bday kirik ad yok", "sampiyon.jpg" not in bday)


def main():
    ap = argparse.ArgumentParser(description="Sahra sitesi dogrulama")
    ap.add_argument("--static", action="store_true", help="sadece statik kontroller")
    ap.add_argument("--base", default=VARSAYILAN, help="dogrulanacak URL")
    a = ap.parse_args()

    print("=" * 74)
    print("SAHRA SİTESİ — DOĞRULAMA")
    print("=" * 74)
    statik()
    if not a.static:
        canli(a.base)

    print("\n" + "=" * 74)
    print(f"SONUÇ: {len(GECTI)} geçti, {len(HATALAR)} kaldı")
    for h in HATALAR:
        print(f"  FAIL: {h}")
    print("=" * 74)
    return 1 if HATALAR else 0


if __name__ == "__main__":
    sys.exit(main())

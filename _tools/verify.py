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
    h1m = re.search(r"<h1[^>]*>(.*?)</h1>", ih, re.S | re.I)
    h1_txt = re.sub(r"<[^>]+>", " ", h1m.group(1)) if h1m else ""
    h1_txt = re.sub(r"\s+", " ", h1_txt).strip()
    kontrol("H1 icinde 'Sahra İnamlık' KESINTISIZ", "Sahra İnamlık" in h1_txt, h1_txt[:56])
    kontrol("H1 metin olarak 'Sahra İnamlık' iceriyor",
            "Sahra" in h1_txt and "İnamlık" in h1_txt)
    kontrol("H2 7", len(re.findall(r"<h2[ >]", ih, re.I)) == 7)
    kontrol("mukerrer meta yok",
            ih.count('name="twitter:title"') == 1 and ih.count('name="robots"') == 1
            and ih.count('rel="canonical"') == 1)
    kontrol("bos UTF-8 (index.html)", "\ufffd" not in ih)
    kontrol("bos UTF-8 (index-bday.html)", "\ufffd" not in bh)

    print("\n[2b] Yapısal veri — JSON-LD Person entity")
    ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', ih, re.S)
    kontrol("JSON-LD blogu var", len(ld) == 1, str(len(ld)))
    if ld:
        try:
            j = json.loads(ld[0])
            kontrol("JSON-LD gecerli", True)
            kontrol("@context schema.org", j.get("@context") == "https://schema.org")
            graf = j.get("@graph", [])
            turler = [n.get("@type") for n in graf]
            kontrol("Person entity VAR", "Person" in turler, str(turler))
            kontrol("WebSite entity VAR", "WebSite" in turler)
            kontrol("ProfilePage entity VAR", "ProfilePage" in turler)
            p = next((n for n in graf if n.get("@type") == "Person"), {})
            kontrol("Person name dogru", p.get("name") == "Sahra İnamlık", str(p.get("name")))
            kontrol("Person @id sabit", p.get("@id", "").endswith("#sahra"))
            kontrol("Person sameAs >= 5", len(p.get("sameAs", [])) >= 5, str(len(p.get("sameAs", []))))
            kontrol("sameAs haber kaynaklarina bagli",
                    any("gundemebakis" in s for s in p.get("sameAs", []))
                    and any("egetelgraf" in s for s in p.get("sameAs", [])))
            kontrol("Person birthDate", p.get("birthDate") == "1994-11-29", str(p.get("birthDate")))
            kontrol("Person award >= 4", len(p.get("award", [])) >= 4, str(len(p.get("award", []))))
            kontrol("Person jobTitle", p.get("jobTitle") == "Milli Dansçı")
        except json.JSONDecodeError as e:
            kontrol("JSON-LD gecerli", False, str(e)[:80])
    # bday sayfasinda da ayni @id
    ldb = re.findall(r'<script type="application/ld\+json">(.*?)</script>', bh, re.S)
    kontrol("bday JSON-LD var", len(ldb) == 1, str(len(ldb)))
    if ldb:
        try:
            jb = json.loads(ldb[0])
            kontrol("bday JSON-LD gecerli", True)
            kontrol("bday ayni @id ile bagli", jb.get("@id", "").endswith("#sahra"))
            kontrol("bday sameAs >= 4", len(jb.get("sameAs", [])) >= 4)
        except json.JSONDecodeError as e:
            kontrol("bday JSON-LD gecerli", False, str(e)[:80])

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

    print("\n[5] İsim sorgusu görünürlüğü — 'Sahra İnamlık'")
    # H1: isim kesintisiz olmali (Google metni birlikte okumali)
    h1m = re.search(r"<h1[^>]*>(.*?)</h1>", ih, re.S | re.I)
    h1_txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h1m.group(1))).strip() if h1m else ""
    kontrol("H1 icinde 'Sahra İnamlık' kesintisiz", "Sahra İnamlık" in h1_txt, h1_txt[:46])
    # title + description + og:title ayni ismi tasiyor mu
    for ad, pat in (("title", r"<title[^>]*>(.*?)</title>"),
                    ("og:title", r'property="og:title"[^>]*content="([^"]*)"')):
        m = re.search(pat, ih, re.S | re.I)
        kontrol(f"{ad} 'Sahra İnamlık' iceriyor", bool(m) and "Sahra İnamlık" in m.group(1),
                m.group(1)[:44] if m else "-")
    # entity baglantisi (sameAs) — isim sorgusunun asil kaldiraci
    ldj = re.findall(r'<script type="application/ld\+json">(.*?)</script>', ih, re.S)
    same_as = []
    if ldj:
        j = json.loads(ldj[0])
        p = next((n for n in j.get("@graph", []) if n.get("@type") == "Person"), {})
        same_as = p.get("sameAs", [])
    kontrol("JSON-LD Person sameAs >= 5", len(same_as) >= 5, str(len(same_as)))
    kontrol("sameAs haber kaynaklarina bagli",
            all(d in ih for d in ("gundemebakis", "egetelgraf", "egeyonhaber", "kanal3")))
    # ilk 1000 karakterde isim (snippet olusturma)
    body = ih[ih.find("<body"):]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                  re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S)))
    kontrol("ilk 1000 karakterde 'Sahra İnamlık'",
            "Sahra İnamlık" in text[:1000], str(text[:1000].count("Sahra İnamlık")))
    # ayni @id iki sayfada (entity birlestirme)
    def person_id(ic):
        b = re.findall(r'<script type="application/ld\+json">(.*?)</script>', ic, re.S)
        if not b:
            return None
        jj = json.loads(b[0])
        n = jj if jj.get("@type") == "Person" else next(
            (x for x in jj.get("@graph", []) if x.get("@type") == "Person"), {})
        return n.get("@id")
    kontrol("iki sayfada ayni Person @id",
            person_id(ih) == person_id(bh) is not None,
            f"{person_id(ih)} == {person_id(bh)}")


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

    # Test dosyalari internete acik olmamali
    print("\n[6] Test dosyalari gizli mi?")
    for gizli in ("_tools/verify.py", "_test_yeni.py", "_test_bday.py", "Makefile"):
        k = fetch(f"{base_dir}/{gizli}")
        kontrol(f"'{gizli}' internete acik DEGIL", len(k) < 500 or "404" in k[:200]
                or "<title>Error 404" in k, f"{len(k)} bayt")
    anahtar = fetch(f"{base_dir}/emiranka0813.github.io.txt")
    kontrol("IndexNow anahtari yayimlanmis", len(anahtar.strip()) >= 8, anahtar.strip()[:20])

    # IndexNow: URL'ler Bing/Yandex/DDG'ye bildirilsin
    import json as _json
    import urllib.request as _req
    kok = base_dir.rstrip("/") + "/"
    try:
        pl = {"host": "emiranka0813.github.io", "key": anahtar.strip(),
              "keyLocation": kok + "emiranka0813.github.io.txt",
              "urlList": [kok, kok + "index-bday.html"]}
        rq = _req.Request("https://api.indexnow.org/indexnow",
                          data=_json.dumps(pl).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        with _req.urlopen(rq, timeout=25) as rp:
            kod = rp.status
    except urllib.error.HTTPError as e:
        kod = e.code
    except Exception:
        kod = 0
    kontrol("IndexNow kabul edildi (200/202)", kod in (200, 202), f"HTTP {kod}")


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

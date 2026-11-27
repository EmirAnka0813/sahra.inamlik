"""SAHRA PROFESYONEL TANITIM — PLAYWRIGHT TESTİ
=============================================
Yeni yapı: topbar + nav + hero grid + ribbon marquee + profil kartları
+ zaman çizelgesi + alıntı grid + editorial galeri + medya + basın kiti
+ kaynaklar + footer + lightbox
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# SAHRA_URL ile yerel/canli arasinda secim yapilabilir
URL = os.environ.get("SAHRA_URL", "https://emiranka0813.github.io/sahra.inamlik/index.html")
OUT = Path.home() / "_sahra_test"
OUT.mkdir(exist_ok=True)
VIEWPORTS = [("desktop", 1440, 900), ("tablet", 820, 1180), ("mobile", 390, 844)]

res = {}
sorun = []

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in VIEWPORTS:
        ctx = b.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="networkidle", timeout=45000)
        pg.wait_for_timeout(1800)

        ov = pg.evaluate("""() => {
            const d=document.documentElement;
            const bad=[...document.querySelectorAll('*')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.right>d.clientWidth+2||r.left<-2;
            }).slice(0,6).map(e=>e.tagName+'.'+(e.className||'').toString().slice(0,32));
            return {sw:d.scrollWidth,cw:d.clientWidth,bad};
        }""")
        imgs = pg.evaluate("""() => {
            const a=[...document.querySelectorAll('img')];
            return {n:a.length,kirik:a.filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src.split('/').pop())};
        }""")
        gal = pg.evaluate("() => document.querySelectorAll('.gi').length")
        mv = pg.evaluate("() => document.querySelectorAll('.mv').length")
        rb = pg.evaluate("() => document.querySelectorAll('.rb').length")
        ic = pg.evaluate("() => document.querySelectorAll('.icard').length")
        tl = pg.evaluate("() => document.querySelectorAll('.tl-item').length")
        q = pg.evaluate("() => document.querySelectorAll('.q').length")
        spec = pg.evaluate("() => document.querySelectorAll('.spec').length")
        src = pg.evaluate("() => document.querySelectorAll('.sa').length")
        pdf = pg.evaluate("() => [...document.querySelectorAll('a[href*=\"tdsf.org.tr\"]')].length")

        # reveal — tam sayfa scroll
        pg.evaluate("""async () => {
            document.documentElement.style.scrollBehavior='auto';
            const h=document.body.scrollHeight;
            for(let y=0;y<=h;y+=300){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,80));}
            await new Promise(r=>setTimeout(r,300));window.scrollTo(0,0);
        }""")
        pg.wait_for_timeout(900)
        rev = pg.evaluate("""() => {
            const a=[...document.querySelectorAll('.rv')];
            return {t:a.length,g:a.filter(e=>e.classList.contains('in')).length};
        }""")

        # lightbox
        pg.evaluate("() => document.querySelector('.gi').click()")
        pg.wait_for_timeout(800)
        lb = pg.evaluate("""() => {
            const i=document.getElementById('lbImg');
            return {on:document.getElementById('lb').classList.contains('on'),
                    w:i.naturalWidth,src:i.src.split('/').pop(),
                    cap:document.getElementById('lbCap').textContent,
                    cnt:document.getElementById('lbC').textContent,
                    dl:document.getElementById('lbDl').getAttribute('href')};
        }""")
        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(500)
        nxt = pg.evaluate("() => document.getElementById('lbC').textContent")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        closed = not pg.evaluate("() => document.getElementById('lb').classList.contains('on')")

        # nav sticky
        pg.evaluate("() => window.scrollTo(0,400)"); pg.wait_for_timeout(400)
        stuck = pg.evaluate("() => document.getElementById('nav').classList.contains('stuck')")
        pg.evaluate("() => window.scrollTo(0,0)")

        pg.screenshot(path=str(OUT / f"pro-{name}.png"), full_page=(name == "desktop"))

        r = {"overflow": ov["sw"]-ov["cw"], "bad": ov["bad"], "img": imgs["n"],
             "kirik": imgs["kirik"], "galeri": gal, "medya": mv, "ribbon": rb,
             "icard": ic, "timeline": tl, "quote": q, "spec": spec, "kaynak": src,
             "pdf": pdf, "rev": rev, "lb": lb, "next": nxt, "closed": closed,
             "stuck": stuck, "js": errs}
        res[name] = r

        if r["overflow"] > 0: sorun.append(f"{name}: overflow {r['overflow']}px {r['bad'][:3]}")
        if r["kirik"]: sorun.append(f"{name}: kirik {len(r['kirik'])} {r['kirik'][:3]}")
        if gal != 22: sorun.append(f"{name}: galeri {gal} (22 bekleniyor)")
        if mv != 3: sorun.append(f"{name}: medya {mv} (3 bekleniyor)")
        if rb != 16: sorun.append(f"{name}: ribbon {rb} (16 bekleniyor)")
        if ic != 4: sorun.append(f"{name}: kimlik kartı {ic}")
        if tl != 6: sorun.append(f"{name}: timeline {tl}")
        if q != 6: sorun.append(f"{name}: alıntı {q}")
        if spec != 12: sorun.append(f"{name}: künye satırı {spec}")
        if src != 9: sorun.append(f"{name}: kaynak {src}")
        if pdf < 2: sorun.append(f"{name}: TDSF PDF linki {pdf}")
        if rev["g"] != rev["t"]: sorun.append(f"{name}: reveal {rev['g']}/{rev['t']}")
        if not lb["on"] or lb["w"] == 0: sorun.append(f"{name}: lightbox {lb}")
        if not closed: sorun.append(f"{name}: esc kapatmadi")
        if not stuck: sorun.append(f"{name}: nav sticky calismadi")
        if errs: sorun.append(f"{name}: {len(errs)} JS hatasi {errs[:2]}")
        ctx.close()
    b.close()

print("=" * 74)
print("SAHRA PROFESYONEL TANITIM — TEST")
print("=" * 74)
for n, r in res.items():
    print(f"\n--- {n.upper()} ---")
    print(f"  overflow   : {r['overflow']}px")
    print(f"  görsel     : {r['img']} (kirik {len(r['kirik'])})")
    print(f"  galeri     : {r['galeri']}/22")
    print(f"  medya      : {r['medya']}/3")
    print(f"  ribbon     : {r['ribbon']}/16")
    print(f"  kimlik kart: {r['icard']}/4")
    print(f"  timeline   : {r['timeline']}/6")
    print(f"  alıntı     : {r['quote']}/6")
    print(f"  künye      : {r['spec']}/12")
    print(f"  kaynak     : {r['kaynak']}/9  (TDSF PDF {r['pdf']})")
    print(f"  reveal     : {r['rev']['g']}/{r['rev']['t']}")
    print(f"  lightbox   : {r['lb']['on']} w={r['lb']['w']} '{r['lb']['cnt']}' dl={r['lb']['dl']}")
    print(f"  ok sonraki  : {r['next']}")
    print(f"  esc kapat  : {r['closed']}")
    print(f"  nav sticky : {r['stuck']}")
    print(f"  JS hata    : {len(r['js'])}")

print("\n" + "=" * 74)
if sorun:
    print(f"SONUC: {len(sorun)} SORUN")
    for s in sorun: print("  -", s)
else:
    print("SONUC: TUM TESTLER BASARILI (3 viewport)")
print("=" * 74)
sys.exit(1 if sorun else 0)

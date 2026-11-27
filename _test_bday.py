"""SAHRA DOĞUM GÜNÜ SAYFASI — PLAYWRIGHT TESTİ
==========================================
Yeni galeri (20 fotograf, 800px + 1600px lightbox) + canonical/robots.
3 viewport: desktop / tablet / mobile
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get("SAHRA_BDAY_URL",
                      "https://emiranka0813.github.io/sahra.inamlik/index-bday.html")
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
        pg.wait_for_timeout(1500)

        ov = pg.evaluate("""() => {
            const d=document.documentElement;
            const bad=[...document.querySelectorAll('*')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.right>d.clientWidth+2||r.left<-2;
            }).slice(0,6).map(e=>e.tagName+'.'+(e.className||'').toString().slice(0,30));
            return {sw:d.scrollWidth,cw:d.clientWidth,bad};
        }""")
        imgs = pg.evaluate("""() => {
            const a=[...document.querySelectorAll('img')];
            return {n:a.length,kirik:a.filter(i=>i.complete&&i.naturalWidth===0)
                    .map(i=>i.src.split('/').pop())};
        }""")
        foto = pg.evaluate("() => document.querySelectorAll('.foto').length")
        bal = pg.evaluate("() => document.querySelectorAll('.balon,.confeti,.bal,.c') .length")

        # lightbox: buyuk (1600px) gorsel yukleniyor mu
        pg.evaluate("() => document.querySelector('.foto').click()")
        pg.wait_for_timeout(700)
        lb = pg.evaluate("""() => {
            const i=document.getElementById('lbImg');
            return {on:document.getElementById('lb').classList.contains('on'),
                    src:(i.src||'').split('/').pop(),w:i.naturalWidth,
                    cap:document.getElementById('lbCap').textContent};
        }""")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
        closed = not pg.evaluate("() => document.getElementById('lb').classList.contains('on')")

        # geri sayim
        cd = pg.evaluate("""() => {
            const e=document.querySelector('[id*=say],[class*=say],[id*=cd],[class*=cd]');
            return e?e.textContent.trim().slice(0,40):'';
        }""")

        pg.screenshot(path=str(OUT / f"bday-{name}.png"), full_page=(name == "desktop"))

        r = {"overflow": ov["sw"]-ov["cw"], "bad": ov["bad"], "img": imgs["n"],
             "kirik": imgs["kirik"], "foto": foto, "lb": lb, "closed": closed,
             "cd": cd, "js": errs}
        res[name] = r

        if r["overflow"] > 0:
            sorun.append(f"{name}: overflow {r['overflow']}px {r['bad'][:3]}")
        if r["kirik"]:
            sorun.append(f"{name}: kirik {len(r['kirik'])} {r['kirik'][:4]}")
        if foto != 20:
            sorun.append(f"{name}: foto {foto} (20 bekleniyor)")
        if not lb["on"] or lb["w"] == 0:
            sorun.append(f"{name}: lightbox {lb}")
        if "1600" not in lb["src"]:
            sorun.append(f"{name}: lightbox buyuk gorsel degil ({lb['src']})")
        if not closed:
            sorun.append(f"{name}: esc kapatmadi")
        if errs:
            sorun.append(f"{name}: {len(errs)} JS hatasi {errs[:2]}")
        ctx.close()
    b.close()

print("=" * 74)
print("DOĞUM GÜNÜ SAYFASI TESTİ —", URL)
print("=" * 74)
for n, r in res.items():
    print(f"\n--- {n.upper()} ---")
    print(f"  overflow : {r['overflow']}px")
    print(f"  görsel   : {r['img']} (kirik {len(r['kirik'])}) {r['kirik'][:3]}")
    print(f"  foto     : {r['foto']}/20")
    print(f"  lightbox : acik={r['lb']['on']} src={r['lb']['src']} w={r['lb']['w']}")
    print(f"  esc      : {r['closed']}")
    print(f"  JS hata  : {len(r['js'])}")

print("\n" + "=" * 74)
if sorun:
    print(f"SONUC: {len(sorun)} SORUN")
    for s in sorun:
        print("  -", s)
else:
    print("SONUC: TUM TESTLER BASARILI (3 viewport)")
print("=" * 74)
sys.exit(1 if sorun else 0)

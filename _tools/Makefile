# SAHRA SİTESİ — KANONİK KOMUTLAR
#
#   make -f _tools/Makefile test     → tüm doğrulama (statik + Playwright + canlı)
#   make verify   → sadece statik kontroller (ağ gerekmez)
#   serve         → yerel sunucu (http://127.0.0.1:8090)
#   deploy        → git push (GitHub Pages)
#
# NOT: _tools/ altındaki dosyalar GitHub Pages tarafından serve edilmez
#      (alt dizin publish edilmez) — testler internete açık değildir.
.PHONY: test verify serve deploy

test:
	@bash _tools/run_tests.sh

verify:
	@python _tools/verify.py --static

serve:
	@python -m http.server 8090

deploy:
	@git add -A && git commit -m "deploy" || true
	@git push origin master

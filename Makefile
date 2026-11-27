# SAHRA SİTESİ — KANONİK KOMUTLAR
#
#   make test     → tüm doğrulama (statik + Playwright + canlı)
#   make verify   → sadece statik kontroller (ağ gerekmez)
#   serve         → yerel sunucu (http://127.0.0.1:8090)
#   deploy        → git push (GitHub Pages)
#
.PHONY: test verify serve deploy

test:
	@bash tools/run_tests.sh

verify:
	@python tools/verify.py --static

serve:
	@python -m http.server 8090

deploy:
	@git add -A && git commit -m "deploy" || true
	@git push origin master

#!/usr/bin/env bash
# SAHRA SİTESİ — KANONİK DOĞRULAMA KOMUTU
#
#   bash run.sh          → tüm doğrulama (statik + Playwright + canlı)
#   bash run.sh verify   → sadece statik kontroller (ağ gerekmez)
#   bash run.sh serve    → yerel sunucu (http://127.0.0.1:8090)
#
# Gerçek uygulama _tools/ altındadır: GitHub Pages alt dizinleri
# serve etmez, böylece test dosyaları internete açılmaz.
set -e
cd "$(dirname "$0")"

case "${1:-test}" in
  verify) exec python _tools/verify.py --static ;;
  serve)  exec python -m http.server 8090 ;;
  test)   exec bash _tools/run_tests.sh ;;
  *)      echo "kullanım: bash run.sh [test|verify|serve]" >&2; exit 2 ;;
esac

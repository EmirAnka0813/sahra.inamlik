#!/usr/bin/env bash
# SAHRA SİTESİ — TEK KOMUT DOĞRULAMA
#
#   bash tools/run_tests.sh
#
# Yapar:
#   1) Statik kontroller (tools/verify.py --static)
#   2) Playwright: yerel sunucu + canli, iki sayfa x 3 viewport
#   3) Canli kontroller (tools/verify.py)
#
# Cikis kodu: 0 = hepsi gecti, 1 = hata var
set -u
cd "$(dirname "$0")/.."
KOK="$(pwd)"
PORT="${PORT:-8090}"
LOG="$(mktemp)"
BASARI=0

echo "======================================================================"
echo "SAHRA SİTESİ — DOĞRULAMA"
echo "======================================================================"

# ── 1) STATİK ─────────────────────────────────────────────────────────
echo ""
echo "[1/4] Statik kontroller"
python tools/verify.py --static || BASARI=1

# ── 2) YEREL SUNUCU ───────────────────────────────────────────────────
echo ""
echo "[2/4] Yerel sunucu baslatiliyor (port $PORT)"
python -m http.server "$PORT" >/dev/null 2>&1 &
SRV=$!
sleep 3

# ── 3) PLAYWRIGHT ────────────────────────────────────────────────────
echo ""
echo "[3/4] Playwright — profil + dogum gunu (yerel & canli)"
for sayfa in "_test_yeni.py:SAHRA_URL:index.html" "_test_bday.py:SAHRA_BDAY_URL:index-bday.html"; do
  IFS=":" read -r SCRIPT ENV DOSYA <<< "$sayfa"
  for hedef in "yerel" "canli"; do
    if [ "$hedef" = "yerel" ]; then
      export "$ENV=http://127.0.0.1:$PORT/$DOSYA"
    else
      unset "$ENV"
    fi
    printf "  %-22s %-7s " "$SCRIPT" "$hedef"
    if python "$SCRIPT" >"$LOG" 2>&1; then
      echo "OK"
    else
      echo "FAIL"
      grep -E "^  - |SONUC:" "$LOG" | head -8 | sed 's/^/      /'
      BASARI=1
    fi
  done
done
kill $SRV 2>/dev/null

# ── 4) CANLI ──────────────────────────────────────────────────────────
echo ""
echo "[4/4] Canli kontroller"
python tools/verify.py || BASARI=1

echo ""
echo "======================================================================"
if [ "$BASARI" -eq 0 ]; then
  echo "GENEL SONUÇ: TÜM TESTLER GEÇTİ"
else
  echo "GENEL SONUÇ: HATA VAR"
fi
echo "======================================================================"
rm -f "$LOG"
exit $BASARI

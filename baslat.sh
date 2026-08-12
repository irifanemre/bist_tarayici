#!/bin/bash
# BIST Tarayıcı arayüzünü başlatır. Çift tıkla veya: ./baslat.sh
cd "$(dirname "$0")"
PY=$(command -v python3 || echo /usr/bin/python3)
exec "$PY" -m streamlit run app.py

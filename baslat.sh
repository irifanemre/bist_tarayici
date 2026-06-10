#!/bin/bash
# BIST Tarayıcı'yı başlatır. Çift tıkla veya: ./baslat.sh
cd "$(dirname "$0")"
exec /opt/anaconda3/bin/python3 -m streamlit run app.py

#!/bin/bash
# Script di avvio per la dashboard ETF

echo "🚀 Avvio Dashboard ETF Portfolio..."

# Attiva l'ambiente virtuale
source .venv/bin/activate

# Installa watchdog per migliori performance
echo "📦 Installazione watchdog per migliori performance..."
pip install watchdog

# Avvia l'applicazione Streamlit
echo "🌐 Avvio applicazione Streamlit..."
streamlit run app.py

echo "✅ Dashboard avviata! Apri http://localhost:8501 nel browser"

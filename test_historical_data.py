#!/usr/bin/env python3
"""
Test per vedere la disponibilità storica di ogni ETF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import ETFDataLoader
from src.config import get_etf_symbols
import yfinance as yf

def test_historical_availability():
    """Testa la disponibilità storica di ogni ETF"""
    print("📊 Test Disponibilità Storica ETF")
    print("=" * 60)
    
    etf_symbols = get_etf_symbols()
    data_loader = ETFDataLoader()
    
    print("🔍 Testando disponibilità per ogni ETF...")
    print()
    
    etf_history = []
    
    for symbol, name in etf_symbols.items():
        try:
            print(f"📈 {symbol} - {name[:40]}...")
            
            # Prova con periodo massimo
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="max")
            
            if not hist.empty:
                start_date = hist.index.min()
                end_date = hist.index.max()
                total_days = len(hist)
                years = (end_date - start_date).days / 365.25
                
                etf_history.append({
                    'symbol': symbol,
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_days': total_days,
                    'years': years
                })
                
                print(f"   ✅ Dal {start_date.strftime('%Y-%m-%d')} al {end_date.strftime('%Y-%m-%d')}")
                print(f"   📊 {total_days} osservazioni ({years:.1f} anni)")
            else:
                print(f"   ❌ Nessun dato disponibile")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        print()
    
    # Ordina per data di inizio
    etf_history.sort(key=lambda x: x['start_date'])
    
    print("📊 RIEPILOGO STORICO (ordinato per data di lancio):")
    print("=" * 80)
    print(f"{'ETF':<12} {'Nome':<30} {'Inizio':<12} {'Fine':<12} {'Anni':<6}")
    print("-" * 80)
    
    for etf in etf_history:
        print(f"{etf['symbol']:<12} {etf['name'][:25]:<30} {etf['start_date'].strftime('%Y-%m-%d'):<12} {etf['end_date'].strftime('%Y-%m-%d'):<12} {etf['years']:<6.1f}")
    
    if etf_history:
        # Data più antica disponibile
        oldest_etf = etf_history[0]
        newest_etf = etf_history[-1]
        
        print(f"\n🎯 ANALISI:")
        print(f"📅 ETF più vecchio: {oldest_etf['symbol']} (dal {oldest_etf['start_date'].strftime('%Y-%m-%d')})")
        print(f"📅 ETF più nuovo: {newest_etf['symbol']} (dal {newest_etf['start_date'].strftime('%Y-%m-%d')})")
        
        # Calcola il periodo comune
        latest_start = max([etf['start_date'] for etf in etf_history])
        print(f"📊 Periodo comune a tutti: dal {latest_start.strftime('%Y-%m-%d')} ad oggi")
        print(f"⏰ Anni di dati comuni: {((etf_history[0]['end_date'] - latest_start).days / 365.25):.1f}")
        
        # Suggerimenti
        print(f"\n💡 SUGGERIMENTI:")
        if latest_start.year >= 2020:
            print(f"⚠️  Il periodo comune inizia solo nel {latest_start.year}")
            print(f"📋 Considera di rimuovere gli ETF più recenti per analisi storiche lunghe")
            
            # Identifica ETF recenti
            cutoff_year = 2015
            recent_etfs = [etf for etf in etf_history if etf['start_date'].year >= cutoff_year]
            old_etfs = [etf for etf in etf_history if etf['start_date'].year < cutoff_year]
            
            if old_etfs:
                print(f"\n📈 ETF disponibili da prima del {cutoff_year}:")
                for etf in old_etfs:
                    print(f"   • {etf['symbol']}: dal {etf['start_date'].strftime('%Y-%m-%d')}")
                    
            if recent_etfs:
                print(f"\n🆕 ETF recenti (dopo {cutoff_year-1}):")
                for etf in recent_etfs:
                    print(f"   • {etf['symbol']}: dal {etf['start_date'].strftime('%Y-%m-%d')}")
        else:
            print(f"✅ Buona disponibilità storica dal {latest_start.year}")

if __name__ == "__main__":
    test_historical_availability()

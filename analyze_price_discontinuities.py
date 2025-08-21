#!/usr/bin/env python3
"""
Analisi delle discontinuità nei prezzi degli ETF - Focus su febbraio-marzo 2019
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
import numpy as np
from src.config import get_etf_symbols

def analyze_price_discontinuities():
    """Analizza le discontinuità nei prezzi degli ETF"""
    print("🔍 Analisi Discontinuità Prezzi ETF - Febbraio-Marzo 2019")
    print("=" * 70)
    
    etf_symbols = get_etf_symbols()
    
    # Periodo specifico da analizzare (gennaio 2019 - aprile 2019)
    start_date = "2019-01-01"
    end_date = "2019-04-30"
    
    print(f"📅 Periodo di analisi: {start_date} - {end_date}")
    print()
    
    problematic_etfs = []
    
    for symbol, name in etf_symbols.items():
        print(f"📊 Analizzando {symbol} - {name[:50]}...")
        
        try:
            # Scarica dati per il periodo specifico
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"   ❌ Nessun dato disponibile per il periodo")
                continue
                
            if len(hist) < 10:
                print(f"   ⚠️  Dati insufficienti ({len(hist)} osservazioni)")
                continue
            
            # Calcola i rendimenti giornalieri
            returns = hist['Close'].pct_change().dropna()
            
            if returns.empty:
                print(f"   ❌ Impossibile calcolare i rendimenti")
                continue
            
            # Identifica discontinuità (rendimenti > 20% o < -20% in un giorno)
            extreme_returns = returns[(returns > 0.20) | (returns < -0.20)]
            
            if not extreme_returns.empty:
                print(f"   🚨 DISCONTINUITÀ TROVATE:")
                for date, ret in extreme_returns.items():
                    price_before = hist['Close'].loc[:date].iloc[-2] if len(hist['Close'].loc[:date]) > 1 else None
                    price_after = hist['Close'].loc[date]
                    
                    print(f"      📅 {date.strftime('%Y-%m-%d')}: {ret*100:+.1f}%")
                    if price_before:
                        print(f"         Prezzo: {price_before:.4f} → {price_after:.4f}")
                
                problematic_etfs.append({
                    'symbol': symbol,
                    'name': name,
                    'extreme_dates': extreme_returns.index.tolist(),
                    'extreme_returns': extreme_returns.values.tolist()
                })
            
            # Analisi specifica febbraio-marzo 2019
            feb_march = hist[(hist.index >= '2019-02-01') & (hist.index <= '2019-03-31')]
            
            if not feb_march.empty and len(feb_march) > 1:
                feb_start = feb_march['Close'].iloc[0]
                march_end = feb_march['Close'].iloc[-1]
                change = (march_end - feb_start) / feb_start
                
                print(f"   📈 Feb-Mar 2019: {feb_start:.4f} → {march_end:.4f} ({change*100:+.1f}%)")
                
                # Controlla se c'è un salto anomalo
                if abs(change) > 0.50:  # >50% di cambio in 2 mesi
                    print(f"   🚨 CAMBIO ANOMALO RILEVATO!")
                    problematic_etfs.append({
                        'symbol': symbol,
                        'name': name,
                        'period_change': change,
                        'type': 'feb_march_anomaly'
                    })
            
            # Analisi volatilità
            volatility = returns.std() * np.sqrt(252)  # Annualizzata
            max_daily_move = max(abs(returns.min()), abs(returns.max()))
            
            print(f"   📊 Volatilità annua: {volatility*100:.1f}%")
            print(f"   📊 Max movimento giornaliero: {max_daily_move*100:.1f}%")
            
            if max_daily_move > 0.15:  # >15% in un giorno
                print(f"   ⚠️  Movimento giornaliero elevato rilevato")
            
        except Exception as e:
            print(f"   ❌ Errore nell'analisi: {e}")
        
        print()
    
    # Riepilogo problemi
    if problematic_etfs:
        print("🚨 RIEPILOGO ETF PROBLEMATICI:")
        print("=" * 50)
        
        for etf in problematic_etfs:
            print(f"• {etf['symbol']} - {etf['name']}")
            
            if 'extreme_dates' in etf:
                print(f"  📅 Date con discontinuità: {len(etf['extreme_dates'])}")
                for i, date in enumerate(etf['extreme_dates']):
                    ret = etf['extreme_returns'][i]
                    print(f"     {date.strftime('%Y-%m-%d')}: {ret*100:+.1f}%")
            
            if 'period_change' in etf:
                print(f"  📈 Cambio Feb-Mar 2019: {etf['period_change']*100:+.1f}%")
            
            print()
        
        print("💡 POSSIBILI CAUSE:")
        print("• Split/Reverse split non aggiustato correttamente")
        print("• Cambio di ticker o ISIN")
        print("• Cambio di metodologia dell'indice sottostante")
        print("• Errori di data quality in yfinance")
        print("• Eventi societari (spin-off, merger)")
        
        print("\n🔧 SOLUZIONI CONSIGLIATE:")
        print("• Verificare dati su altre fonti (Bloomberg, Refinitiv)")
        print("• Utilizzare dati adjusted/split-adjusted")
        print("• Escludere periodi problematici dall'analisi")
        print("• Contattare il fornitore dati per correzioni")
    
    else:
        print("✅ Nessuna discontinuità significativa rilevata nel periodo analizzato")

if __name__ == "__main__":
    analyze_price_discontinuities()

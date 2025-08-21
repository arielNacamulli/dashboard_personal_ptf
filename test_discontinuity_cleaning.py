#!/usr/bin/env python3
"""
Test della pulizia delle discontinuità sui dati JPNA.MI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import ETFDataLoader
import pandas as pd

def test_discontinuity_cleaning():
    """Testa la pulizia delle discontinuità"""
    print("🧪 Test Pulizia Discontinuità - JPNA.MI")
    print("=" * 50)
    
    data_loader = ETFDataLoader()
    
    # Testa solo JPNA.MI con dati dal 2019
    symbol = 'JPNA.MI'
    
    print(f"📊 Scaricamento dati per {symbol}...")
    
    try:
        # Scarica dati con periodo massimo
        prices = data_loader.download_etf_data([symbol], period='max')
        
        if prices.empty:
            print("❌ Nessun dato scaricato")
            return
        
        print(f"📈 Dati scaricati: {len(prices)} osservazioni")
        print(f"📅 Periodo: {prices.index.min().date()} - {prices.index.max().date()}")
        
        # Controlla il periodo problematico (febbraio-marzo 2019)
        problem_period = prices[(prices.index >= '2019-02-01') & (prices.index <= '2019-03-31')]
        
        if not problem_period.empty:
            print(f"\n📊 PERIODO PROBLEMATICO (Feb-Mar 2019):")
            print(f"Numero di osservazioni: {len(problem_period)}")
            
            # Mostra alcuni prezzi chiave
            key_dates = ['2019-03-01', '2019-03-04', '2019-03-05', '2019-03-08']
            
            for date_str in key_dates:
                try:
                    date = pd.to_datetime(date_str)
                    if date in problem_period.index:
                        price = problem_period.loc[date, symbol]
                        print(f"  {date_str}: {price:.4f}")
                except:
                    continue
            
            # Calcola i rendimenti giornalieri nel periodo
            returns = problem_period[symbol].pct_change().dropna()
            
            if not returns.empty:
                print(f"\n📊 RENDIMENTI GIORNALIERI:")
                extreme_returns = returns[(returns > 0.20) | (returns < -0.20)]
                
                if not extreme_returns.empty:
                    print("🚨 Rendimenti estremi rilevati:")
                    for date, ret in extreme_returns.items():
                        print(f"  {date.date()}: {ret*100:+.1f}%")
                else:
                    print("✅ Nessun rendimento estremo rilevato (pulizia funzionante!)")
            
        # Test sui dati completi
        print(f"\n📊 ANALISI DATI COMPLETI:")
        all_returns = prices[symbol].pct_change().dropna()
        
        extreme_returns = all_returns[(all_returns > 0.50) | (all_returns < -0.50)]
        
        print(f"Rendimenti estremi (>50%): {len(extreme_returns)}")
        
        if not extreme_returns.empty:
            print("🚨 Rendimenti estremi ancora presenti:")
            for date, ret in extreme_returns.head(5).items():
                print(f"  {date.date()}: {ret*100:+.1f}%")
        else:
            print("✅ Nessun rendimento estremo rilevato")
        
        # Statistiche finali
        volatility = all_returns.std() * (252**0.5)
        max_return = all_returns.max()
        min_return = all_returns.min()
        
        print(f"\n📊 STATISTICHE FINALI:")
        print(f"Volatilità annualizzata: {volatility*100:.1f}%")
        print(f"Rendimento massimo giornaliero: {max_return*100:+.1f}%")
        print(f"Rendimento minimo giornaliero: {min_return*100:+.1f}%")
        
    except Exception as e:
        print(f"❌ Errore nel test: {e}")

if __name__ == "__main__":
    test_discontinuity_cleaning()

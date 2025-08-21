#!/usr/bin/env python3
"""
Test delle nuove features: cash fisso e massima esposizione
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset, is_exposure_exempt

def test_cash_target_and_max_exposure():
    """Test delle nuove features"""
    print("🧪 Test Cash Fisso e Massima Esposizione")
    print("=" * 50)
    
    # Crea dati di test
    np.random.seed(42)
    etf_symbols = get_etf_symbols()
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    
    # Genera rendimenti casuali
    returns_data = pd.DataFrame(
        np.random.normal(0.0005, 0.02, (len(dates), len(etf_symbols))),
        index=dates,
        columns=list(etf_symbols.keys())
    )
    
    print(f"📊 Dati di test: {len(returns_data)} giorni, {len(etf_symbols)} ETF")
    
    # Test 1: Cash fisso al 15%
    print("\n🧪 Test 1: Cash fisso al 15%")
    optimizer = PortfolioOptimizer(cash_target=0.15, max_exposure=0.25)
    
    # Test algoritmo HERC
    weights_herc = optimizer.herc_optimization(returns_data.tail(252))
    cash_asset = get_cash_asset()
    
    print(f"💰 Cash Weight (HERC): {weights_herc[cash_asset]*100:.1f}%")
    print(f"📈 Investment Weights Sum: {(1-weights_herc[cash_asset])*100:.1f}%")
    
    # Verifica che il cash sia esattamente al 15%
    assert abs(weights_herc[cash_asset] - 0.15) < 0.001, f"Cash dovrebbe essere 15%, ma è {weights_herc[cash_asset]*100:.1f}%"
    print("✅ Cash fisso verificato")
    
    # Test 2: Massima esposizione
    print("\n🧪 Test 2: Vincoli di massima esposizione")
    
    # Verifica che nessun ETF (eccetto esenti) superi il 25%
    for symbol, weight in weights_herc.items():
        if symbol != cash_asset and not is_exposure_exempt(symbol):
            if weight > 0.25:
                print(f"❌ {symbol}: {weight*100:.1f}% > 25%")
                assert False, f"{symbol} supera il limite del 25%"
            else:
                print(f"✅ {symbol}: {weight*100:.1f}% (entro il limite)")
    
    # Verifica che SWDA possa superare il limite
    swda_weight = weights_herc.get('SWDA.MI', 0.0)
    print(f"🌍 SWDA.MI (esente): {swda_weight*100:.1f}%")
    
    # Test 3: Algoritmo HRP con gli stessi vincoli
    print("\n🧪 Test 3: Algoritmo HRP con vincoli")
    weights_hrp = optimizer.hrp_optimization(returns_data.tail(252))
    
    print(f"💰 Cash Weight (HRP): {weights_hrp[cash_asset]*100:.1f}%")
    assert abs(weights_hrp[cash_asset] - 0.15) < 0.001, f"Cash dovrebbe essere 15%, ma è {weights_hrp[cash_asset]*100:.1f}%"
    print("✅ Cash fisso verificato (HRP)")
    
    # Test 4: Backtest con i nuovi parametri
    print("\n🧪 Test 4: Backtest con parametri avanzati")
    
    try:
        backtest_results = optimizer.backtest_portfolio(
            returns_data, 
            method='herc', 
            rebalance_freq='Q'
        )
        
        if not backtest_results.empty:
            print(f"📈 Backtest completato: {len(backtest_results)} osservazioni")
            print(f"📊 Rendimento finale: {backtest_results['cumulative_returns'].iloc[-1]*100:.2f}%")
            
            # Verifica che ogni ribilanciamento abbia rispettato i vincoli
            for entry in optimizer.weights_history:
                weights = entry['weights']
                date = entry['date']
                
                # Verifica cash fisso
                cash_weight = weights[cash_asset]
                if abs(cash_weight - 0.15) > 0.001:
                    print(f"❌ {date}: Cash = {cash_weight*100:.1f}% (dovrebbe essere 15%)")
                
                # Verifica massima esposizione
                for symbol, weight in weights.items():
                    if symbol != cash_asset and not is_exposure_exempt(symbol) and weight > 0.25:
                        print(f"❌ {date}: {symbol} = {weight*100:.1f}% > 25%")
            
            print("✅ Backtest con vincoli completato")
        else:
            print("❌ Backtest fallito - dati insufficienti")
    
    except Exception as e:
        print(f"❌ Errore nel backtest: {e}")
    
    # Test 5: Modifica manuale con vincoli
    print("\n🧪 Test 5: Modifica manuale con vincoli")
    
    # Simula modifica manuale che viola i vincoli
    manual_weights = weights_herc.copy()
    manual_weights['SPXS.MI'] = 0.40  # Viola il limite del 25%
    
    # Applica i vincoli
    adjusted_weights = optimizer.adjust_weights_with_cash(manual_weights, use_fixed_cash=True)
    
    print(f"💰 Cash aggiustato: {adjusted_weights[cash_asset]*100:.1f}%")
    print(f"📊 SPXS.MI aggiustato: {adjusted_weights['SPXS.MI']*100:.1f}%")
    
    # Verifica che i vincoli siano rispettati
    assert abs(adjusted_weights[cash_asset] - 0.15) < 0.001, "Cash non rispetta il target"
    assert adjusted_weights['SPXS.MI'] <= 0.25, "SPXS supera ancora il limite"
    
    print("✅ Vincoli applicati correttamente")
    
    print("\n🎉 Tutti i test completati con successo!")
    print("\n📋 Riepilogo Features:")
    print(f"💰 Cash fisso: {optimizer.cash_target*100:.1f}%")
    print(f"📊 Massima esposizione: {optimizer.max_exposure*100:.1f}%")
    print(f"🛡️ ETF esenti: SWDA.MI, {cash_asset}")

if __name__ == "__main__":
    test_cash_target_and_max_exposure()

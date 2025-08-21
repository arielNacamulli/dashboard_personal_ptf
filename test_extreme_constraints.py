#!/usr/bin/env python3
"""
Test avanzato per verificare i vincoli in scenari estremi
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset

def test_extreme_constraints():
    """Test con vincoli estremi"""
    print("🧪 Test Vincoli Estremi")
    print("=" * 40)
    
    # Test con cash molto alto (40%) e massima esposizione bassa (15%)
    optimizer = PortfolioOptimizer(cash_target=0.40, max_exposure=0.15)
    
    print(f"💰 Cash target: 40%")
    print(f"📊 Max exposure: 15%")
    print(f"🔢 Spazio per investimenti: 60%")
    print(f"📈 Max ETF count teorico: {0.60/0.15:.1f}")
    
    # Crea dati di test
    np.random.seed(42)
    etf_symbols = get_etf_symbols()
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    
    returns_data = pd.DataFrame(
        np.random.normal(0.0005, 0.02, (len(dates), len(etf_symbols))),
        index=dates,
        columns=list(etf_symbols.keys())
    )
    
    # Test ottimizzazione
    weights = optimizer.herc_optimization(returns_data.tail(252))
    cash_asset = get_cash_asset()
    
    print(f"\n💰 Cash Weight: {weights[cash_asset]*100:.1f}%")
    
    active_investments = 0
    total_investment = 0.0
    
    print("\n📊 Allocazione per ETF:")
    for symbol, weight in weights.items():
        if symbol != cash_asset and weight > 0:
            active_investments += 1
            total_investment += weight
            print(f"  {symbol}: {weight*100:.1f}%")
    
    print(f"\n📈 ETF attivi: {active_investments}")
    print(f"💵 Totale investimenti: {total_investment*100:.1f}%")
    print(f"💰 Cash finale: {weights[cash_asset]*100:.1f}%")
    
    # Verifica vincoli
    assert abs(weights[cash_asset] - 0.40) < 0.001, f"Cash non è 40%: {weights[cash_asset]*100:.1f}%"
    
    max_weight = max([w for s, w in weights.items() if s != cash_asset and s != 'SWDA.MI'])
    print(f"📊 Peso massimo (esclusi esenti): {max_weight*100:.1f}%")
    assert max_weight <= 0.15, f"Qualche ETF supera il 15%: {max_weight*100:.1f}%"
    
    print("✅ Vincoli estremi rispettati!")

if __name__ == "__main__":
    test_extreme_constraints()

#!/usr/bin/env python3
"""
Test per verificare l'applicazione dei vincoli e del peso minimo SWDA
"""

import pandas as pd
import numpy as np
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset

def test_constraints_with_swda_minimum():
    """Testa l'applicazione dei vincoli con peso minimo per SWDA"""
    
    print("🔧 Test Vincoli con Peso Minimo SWDA")
    print("=" * 50)
    
    # Carica dati
    data_loader = ETFDataLoader()
    etf_symbols = list(get_etf_symbols().keys())
    prices_data = data_loader.download_etf_data(etf_symbols, "2y")
    returns_data = data_loader.calculate_returns(prices_data)
    
    optimizer = PortfolioOptimizer(cash_target=0.10, max_exposure=0.20)
    
    # Test 1: HERC + constraints
    print("📊 Test HERC + Apply Constraints:")
    herc_weights = optimizer.herc_optimization(returns_data)
    print("Pesi prima dei vincoli:")
    for asset, weight in herc_weights.items():
        if weight > 0.001:
            print(f"   {asset:12s}: {weight*100:5.2f}%")
    
    print("\nApplicazione vincoli...")
    constrained_herc = optimizer.apply_exposure_constraints(herc_weights)
    
    print("Pesi dopo i vincoli:")
    for asset, weight in constrained_herc.items():
        if weight > 0.001:
            mark = "⭐" if asset == 'SWDA.MI' else "  "
            print(f"   {asset:12s}: {weight*100:5.2f}% {mark}")
    
    print(f"\nSWDA peso finale: {constrained_herc['SWDA.MI']*100:.2f}%")
    print(f"Somma totale: {constrained_herc.sum()*100:.2f}%")
    
    # Verifica violazioni
    cash_asset = get_cash_asset()
    violations = []
    for asset, weight in constrained_herc.items():
        if asset != cash_asset and asset not in ['SWDA.MI', 'XEON.MI']:
            if weight > 0.20 + 1e-6:
                violations.append(f"{asset}: {weight*100:.2f}%")
    
    if violations:
        print(f"\n❌ Violazioni limite 20%:")
        for violation in violations:
            print(f"   - {violation}")
    else:
        print("\n✅ Tutti i vincoli rispettati")
    
    # Test 2: Backtest completo per vedere il comportamento reale
    print("\n" + "="*50)
    print("📈 Test Backtest Completo (1 ribilanciamento):")
    
    # Prendi solo gli ultimi 6 mesi per test veloce
    recent_returns = returns_data.tail(126)  # ~6 mesi
    
    backtest_results = optimizer.backtest_portfolio(recent_returns, 'HERC', rebalance_freq='quarterly')
    
    if not backtest_results.empty:
        print(f"✅ Backtest completato: {len(backtest_results)} righe")
        
        # Analizza i pesi dell'ultimo ribilanciamento
        if optimizer.weights_history:
            last_weights = optimizer.weights_history[-1]['weights']
            last_date = optimizer.weights_history[-1]['date']
            
            print(f"\n📅 Ultimo ribilanciamento ({last_date.strftime('%Y-%m-%d')}):")
            sorted_weights = last_weights.sort_values(ascending=False)
            
            for asset, weight in sorted_weights.items():
                if weight > 0.001:
                    mark = "⭐" if asset == 'SWDA.MI' else "  "
                    exempt = " (ESENTE)" if asset in ['SWDA.MI', 'XEON.MI'] else ""
                    print(f"   {asset:12s}: {weight*100:5.2f}% {mark}{exempt}")
            
            # Verifica violazioni nel backtest
            violations = []
            for asset, weight in last_weights.items():
                if asset != cash_asset and asset not in ['SWDA.MI', 'XEON.MI']:
                    if weight > 0.20 + 1e-6:
                        violations.append(f"{asset}: {weight*100:.2f}%")
            
            if violations:
                print(f"\n❌ Violazioni nel backtest:")
                for violation in violations:
                    print(f"   - {violation}")
            else:
                print(f"\n✅ Vincoli rispettati nel backtest")
            
            print(f"\nSWDA peso nel backtest: {last_weights['SWDA.MI']*100:.2f}%")
    else:
        print("❌ Backtest fallito")

if __name__ == "__main__":
    test_constraints_with_swda_minimum()

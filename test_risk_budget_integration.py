#!/usr/bin/env python3
"""
Test per verificare l'integrazione del Risk Budgeting con il dashboard
"""
import pandas as pd
import numpy as np
from src.portfolio_optimizer import PortfolioOptimizer

def test_risk_budget_integration():
    """Test dell'integrazione Risk Budgeting con ottimizzazione e backtest"""
    
    print("🧪 Test Risk Budget Integration")
    print("="*50)
    
    # Setup dati di test
    symbols = ['SWDA.MI', 'SPXS.MI', 'XDWT.MI', 'IS3K.DE', 'SJPA.MI']
    
    # Genera dati sintetici
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    
    returns_data = pd.DataFrame(
        np.random.normal(0.0005, 0.02, (252, len(symbols))),
        index=dates,
        columns=symbols
    )
    
    print(f"📊 Dataset: {len(returns_data)} giorni, {len(symbols)} asset")
    
    # Test 1: Risk Budget uniforme (default)
    print("\n🔍 Test 1: Risk Budget Default (uniforme)")
    print("-" * 40)
    
    optimizer_default = PortfolioOptimizer(
        cash_target=0.1,
        max_exposure=0.3
    )
    
    results_default = optimizer_default.herc_optimization(returns_data)
    weights_default = optimizer_default.get_latest_weights()
    
    print("Pesi con Risk Budget default:")
    for symbol, weight in weights_default.items():
        if weight > 0.001:  # Solo pesi significativi
            print(f"   {symbol}: {weight*100:.2f}%")
    
    # Test 2: Risk Budget personalizzato
    print("\n🔍 Test 2: Risk Budget Personalizzato")
    print("-" * 40)
    
    # Risk budget: SWDA ha più rischio, altri meno
    custom_risk_budgets = {
        'SWDA.MI': 2.0,    # Doppio peso
        'SPXS.MI': 1.5,    # 50% in più
        'XDWT.MI': 0.8,    # 20% in meno
        'IS3K.DE': 1.2,    # 20% in più
        'SJPA.MI': 0.7     # 30% in meno
    }
    
    optimizer_custom = PortfolioOptimizer(
        cash_target=0.1,
        max_exposure=0.3,
        risk_budgets=custom_risk_budgets
    )
    
    results_custom = optimizer_custom.herc_optimization(returns_data)
    weights_custom = optimizer_custom.get_latest_weights()
    
    print("Pesi con Risk Budget personalizzato:")
    for symbol, weight in weights_custom.items():
        if weight > 0.001:  # Solo pesi significativi
            print(f"   {symbol}: {weight*100:.2f}%")
    
    # Test 3: Verifica backtest con Risk Budget
    print("\n🔍 Test 3: Backtest con Risk Budget")
    print("-" * 40)
    
    backtest_results = optimizer_custom.backtest_with_benchmark(
        returns_data,
        method='herc',
        rebalance_freq='monthly'
    )
    
    portfolio_returns = backtest_results['portfolio']['portfolio_returns']
    final_value = backtest_results['portfolio']['cumulative_returns'].iloc[-1]
    
    print(f"Portfolio finale: {final_value:.2f}")
    print(f"Return medio: {portfolio_returns.mean()*252*100:.2f}% annuo")
    print(f"Volatilità: {portfolio_returns.std()*np.sqrt(252)*100:.2f}% annua")
    
    # Test 4: Confronto tra default e personalizzato
    print("\n🔍 Test 4: Confronto Default vs Personalizzato")
    print("-" * 40)
    
    print("Differenze nei pesi (Personalizzato - Default):")
    for symbol in symbols:
        diff = weights_custom.get(symbol, 0) - weights_default.get(symbol, 0)
        if abs(diff) > 0.001:
            direction = "↗️" if diff > 0 else "↘️"
            print(f"   {symbol}: {diff*100:+.2f}% {direction}")
    
    # Verifiche
    print("\n✅ Verifiche:")
    
    # Verifica 1: I pesi sommano a 1
    total_default = sum(weights_default.values())
    total_custom = sum(weights_custom.values())
    print(f"   • Pesi default sommano a: {total_default:.3f}")
    print(f"   • Pesi custom sommano a: {total_custom:.3f}")
    
    # Verifica 2: SWDA ha peso maggiore con risk budget alto
    swda_default = weights_default.get('SWDA.MI', 0)
    swda_custom = weights_custom.get('SWDA.MI', 0)
    print(f"   • SWDA default: {swda_default*100:.2f}%")
    print(f"   • SWDA custom (budget 2.0): {swda_custom*100:.2f}%")
    
    if swda_custom > swda_default:
        print(f"   ✅ SWDA ha peso maggiore con risk budget alto")
    else:
        print(f"   ❌ SWDA dovrebbe avere peso maggiore")
    
    # Verifica 3: Backtest completato
    if len(portfolio_returns) > 0:
        print(f"   ✅ Backtest completato con {len(portfolio_returns)} osservazioni")
    else:
        print(f"   ❌ Backtest fallito")
    
    print("\n🎉 Test completato!")
    return True

if __name__ == "__main__":
    test_risk_budget_integration()

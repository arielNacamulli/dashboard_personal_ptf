#!/usr/bin/env python3
"""
Test per verificare che i vincoli di esposizione massima siano rispettati
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.portfolio_optimizer import PortfolioOptimizer
from src.data_loader import ETFDataLoader
from src.config import get_etf_symbols

def test_exposure_limits():
    """
    Test specifico per verificare i vincoli di esposizione massima
    """
    print("🧪 Test Vincoli di Esposizione Massima")
    print("=" * 50)
    
    # Configurazione del test
    max_exposure = 0.20  # 20% massimo per ETF
    cash_target = 0.10   # 10% cash fisso
    
    # Seleziona alcuni ETF per il test
    test_etfs = ['SWDA.MI', 'IS3K.DE', 'EIMI.MI', 'XEON.MI']
    
    print(f"ETF selezionati: {test_etfs}")
    print(f"Esposizione massima: {max_exposure*100:.0f}%")
    print(f"Cash target: {cash_target*100:.0f}%")
    print()
    
    # Carica i dati
    loader = ETFDataLoader()
    
    print("📊 Caricamento dati...")
    prices_data = loader.download_etf_data(
        symbols=test_etfs,
        period="5y"  # 5 anni di dati
    )
    
    if prices_data.empty:
        print("❌ Nessun dato caricato")
        return
    
    print(f"✅ Dati caricati: {prices_data.shape[0]} giorni, {prices_data.shape[1]} ETF")
    print(f"Periodo: {prices_data.index[0].date()} - {prices_data.index[-1].date()}")
    print()
    
    # Crea l'ottimizzatore con vincoli stretti
    optimizer = PortfolioOptimizer(
        max_exposure=max_exposure,
        cash_target=cash_target
    )
    
    # Esegui il backtest
    print("🔄 Esecuzione backtest con vincoli di esposizione...")
    backtest_data = optimizer.backtest_portfolio(
        prices_data, 
        method='HERC', 
        rebalance_freq='A'  # Annuale per vedere meglio i risultati
    )
    
    if backtest_data.empty:
        print("❌ Errore nel backtest")
        return
    
    # Accedi ai weights_history dall'ottimizzatore
    weights_history = optimizer.weights_history
    
    print(f"✅ Backtest completato: {len(weights_history)} ribilanciamenti")
    print()
    
    # Verifica i vincoli in ogni data di ribilanciamento
    print("🔍 Verifica vincoli per ogni ribilanciamento:")
    print("-" * 70)
    
    violations_count = 0
    total_rebalances = len(weights_history)
    
    for i, entry in enumerate(weights_history):
        date = entry['date']
        weights = entry['weights']
        
        # Cerca violazioni
        violations = []
        for asset, weight in weights.items():
            if asset != 'XEON.MI' and weight > max_exposure + 1e-6:
                violations.append(f"{asset}: {weight:.3f} ({weight*100:.1f}%)")
        
        if violations:
            violations_count += 1
            print(f"❌ {date.strftime('%Y-%m-%d')}: VIOLAZIONI TROVATE!")
            for violation in violations:
                print(f"   - {violation}")
        else:
            # Mostra i primi e gli ultimi ribilanciamenti anche se ok
            if i < 3 or i >= total_rebalances - 3:
                max_weight = max([w for asset, w in weights.items() if asset != 'XEON.MI'])
                max_asset = [asset for asset, w in weights.items() if w == max_weight and asset != 'XEON.MI'][0]
                print(f"✅ {date.strftime('%Y-%m-%d')}: OK (max: {max_asset} {max_weight:.3f})")
    
    print("-" * 70)
    print(f"📊 Riepilogo: {violations_count}/{total_rebalances} ribilanciamenti con violazioni")
    
    if violations_count == 0:
        print("🎉 SUCCESSO: Tutti i vincoli rispettati!")
    else:
        print(f"⚠️  ATTENZIONE: {violations_count} violazioni trovate")
    
    print()
    
    # Mostra statistiche sui pesi
    print("📈 Statistiche pesi (escludendo cash):")
    all_weights = []
    for entry in weights_history:
        weights = entry['weights']
        for asset, weight in weights.items():
            if asset != 'XEON.MI':
                all_weights.append(weight)
    
    all_weights = np.array(all_weights)
    print(f"   - Media: {all_weights.mean():.3f} ({all_weights.mean()*100:.1f}%)")
    print(f"   - Massimo: {all_weights.max():.3f} ({all_weights.max()*100:.1f}%)")
    print(f"   - Percentile 95: {np.percentile(all_weights, 95):.3f} ({np.percentile(all_weights, 95)*100:.1f}%)")
    print()
    
    # Mostra performance
    if not backtest_data.empty:
        total_return = (backtest_data['cumulative_returns'].iloc[-1] - 1) * 100
        print(f"📊 Performance totale: {total_return:.2f}%")
    
    return violations_count == 0

if __name__ == "__main__":
    success = test_exposure_limits()
    print("\n" + "="*50)
    if success:
        print("✅ TEST SUPERATO: Vincoli di esposizione rispettati")
    else:
        print("❌ TEST FALLITO: Violazioni nei vincoli di esposizione")

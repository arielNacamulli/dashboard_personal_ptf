#!/usr/bin/env python3
"""
Test per debug del problema di vincoli di esposizione in backtest reale
Verifica il comportamento con i parametri esatti dell'utente:
- 20 anni di dati (effettivamente meno quando tagliati)
- Ribilanciamento annuale 
- Massima esposizione ETF 20%
"""

import pandas as pd
import numpy as np
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset
from datetime import datetime, timedelta

def test_exposure_constraints_december_2021():
    """Test specifico per dicembre 2021 con limite 20%"""
    
    print("🔍 Test Debug Vincoli Esposizione - Dicembre 2021")
    print("=" * 60)
    
    # Parametri del test come nell'interfaccia
    period = "max"  # Usa tutti i dati disponibili
    max_exposure = 0.20  # 20%
    cash_target = 0.10   # 10%
    
    print(f"Periodo: {period}")
    print(f"Limite massimo esposizione: {max_exposure*100:.0f}%")
    print(f"Target cash: {cash_target*100:.0f}%")
    print()
    
    # Carica dati
    print("📊 Caricamento dati...")
    data_loader = ETFDataLoader()
    etf_symbols = list(get_etf_symbols().keys())
    
    try:
        prices_data = data_loader.download_etf_data(etf_symbols, period)
        returns_data = data_loader.calculate_returns(prices_data)
        
        print(f"✅ Dati caricati: {len(prices_data.columns)} ETF")
        print(f"   Periodo effettivo: {prices_data.index[0].strftime('%Y-%m-%d')} - {prices_data.index[-1].strftime('%Y-%m-%d')}")
        print(f"   Giorni di trading: {len(prices_data)}")
        print()
        
        # Inizializza optimizer
        optimizer = PortfolioOptimizer(
            cash_target=cash_target,
            max_exposure=max_exposure
        )
        
        # Esegui backtest con ribilanciamento annuale (yearly)
        print("🔄 Esecuzione backtest HERC...")
        backtest_results = optimizer.backtest_portfolio(returns_data, 'HERC', rebalance_freq='yearly')
        
        if backtest_results.empty:
            print("❌ Nessun risultato dal backtest")
            return
            
        # Analizza i pesi storici
        weights_history = optimizer.weights_history
        cash_asset = get_cash_asset()
        
        print(f"📈 Analisi pesi storici ({len(weights_history)} ribilanciamenti):")
        print()
        
        # Cerca dicembre 2021
        target_date = datetime(2021, 12, 1)
        december_2021_weights = None
        
        for i, weight_entry in enumerate(weights_history):
            rebal_date = pd.to_datetime(weight_entry['date'])
            
            # Stampa tutti i ribilanciamenti del 2021
            if rebal_date.year == 2021:
                weights = weight_entry['weights']
                max_weight_asset = weights.drop(cash_asset).idxmax()
                max_weight_value = weights[max_weight_asset]
                
                print(f"📅 {rebal_date.strftime('%Y-%m-%d')}:")
                print(f"   🏆 Asset massimo: {max_weight_asset} = {max_weight_value*100:.2f}%")
                
                # Trova violazioni
                violations = []
                for asset, weight in weights.items():
                    if asset != cash_asset and not asset in ['SWDA.MI', 'XEON.MI']:
                        if weight > max_exposure + 1e-6:
                            violations.append(f"{asset}: {weight*100:.2f}%")
                
                if violations:
                    print(f"   ⚠️  VIOLAZIONI LIMITE {max_exposure*100:.0f}%:")
                    for violation in violations:
                        print(f"      - {violation}")
                
                # Se è dicembre 2021, salva per analisi dettagliata
                if rebal_date.month == 12:
                    december_2021_weights = weights
                
                print(f"   💰 Cash: {weights[cash_asset]*100:.2f}%")
                print(f"   📊 Somma: {weights.sum()*100:.2f}%")
                print()
        
        # Analisi dettagliata dicembre 2021
        if december_2021_weights is not None:
            print("🔍 ANALISI DETTAGLIATA DICEMBRE 2021:")
            print("=" * 50)
            
            # Ordina per peso decrescente
            investment_weights = december_2021_weights.drop(cash_asset).sort_values(ascending=False)
            
            print("Top 10 posizioni:")
            for i, (asset, weight) in enumerate(investment_weights.head(10).items()):
                is_exempt = asset in ['SWDA.MI', 'XEON.MI']
                violation_mark = "⚠️" if weight > max_exposure and not is_exempt else "✅"
                exempt_mark = " (ESENTE)" if is_exempt else ""
                
                print(f"{i+1:2d}. {asset:10s}: {weight*100:6.2f}% {violation_mark}{exempt_mark}")
            
            print()
            print(f"Cash ({cash_asset}): {december_2021_weights[cash_asset]*100:.2f}%")
            print(f"Somma totale: {december_2021_weights.sum()*100:.2f}%")
            
            # Verifica constraint finale
            print()
            print("🔧 VERIFICA VINCOLI FINALI:")
            violations_found = False
            for asset, weight in investment_weights.items():
                if asset not in ['SWDA.MI', 'XEON.MI'] and weight > max_exposure + 1e-6:
                    print(f"❌ {asset}: {weight*100:.2f}% > {max_exposure*100:.0f}%")
                    violations_found = True
            
            if not violations_found:
                print("✅ Tutti i vincoli rispettati")
        
        print()
        print("📊 RIEPILOGO PERFORMANCE:")
        final_return = (backtest_results['cumulative_returns'].iloc[-1] - 1) * 100
        print(f"Rendimento totale: {final_return:.2f}%")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exposure_constraints_december_2021()

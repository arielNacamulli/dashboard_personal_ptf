#!/usr/bin/env python3
"""
Test per verificare la funzionalità di volatilità target
"""

import pandas as pd
import numpy as np
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset

def test_volatility_target():
    """Testa la funzionalità di volatilità target"""
    
    print("🎯 Test Volatilità Target")
    print("=" * 50)
    
    # Carica dati
    data_loader = ETFDataLoader()
    etf_symbols = list(get_etf_symbols().keys())
    prices_data = data_loader.download_etf_data(etf_symbols, "2y")
    returns_data = data_loader.calculate_returns(prices_data)
    
    print(f"✅ Dati caricati: {len(prices_data.columns)} ETF")
    print(f"   Periodo: {prices_data.index[0].strftime('%Y-%m-%d')} - {prices_data.index[-1].strftime('%Y-%m-%d')}")
    print()
    
    # Test 1: Cash fisso vs Volatilità target
    configs = [
        {
            "name": "Cash Fisso 10%",
            "use_volatility_target": False,
            "cash_target": 0.10,
            "target_volatility": None
        },
        {
            "name": "Volatilità Target 6%",
            "use_volatility_target": True,
            "cash_target": 0.10,  # Fallback
            "target_volatility": 0.06
        },
        {
            "name": "Volatilità Target 12%",
            "use_volatility_target": True,
            "cash_target": 0.10,  # Fallback
            "target_volatility": 0.12
        }
    ]
    
    for config in configs:
        print(f"📊 Test: {config['name']}")
        print("-" * 30)
        
        try:
            optimizer = PortfolioOptimizer(
                cash_target=config['cash_target'],
                max_exposure=0.20,
                use_volatility_target=config['use_volatility_target'],
                target_volatility=config['target_volatility']
            )
            
            # Esegui backtest breve
            recent_returns = returns_data.tail(252)  # Ultimo anno
            backtest_results = optimizer.backtest_portfolio(
                recent_returns, 
                'HERC', 
                rebalance_freq='quarterly'
            )
            
            if not backtest_results.empty:
                print(f"✅ Backtest completato: {len(backtest_results)} righe")
                
                # Analizza i pesi nel tempo
                print("\n📅 Evoluzione XEON (Cash):")
                for i, weight_entry in enumerate(optimizer.weights_history):
                    date = weight_entry['date']
                    weights = weight_entry['weights']
                    xeon_weight = weights[get_cash_asset()]
                    
                    print(f"   {date.strftime('%Y-%m-%d')}: XEON {xeon_weight*100:5.1f}%")
                
                # Calcola volatilità realizzata
                portfolio_returns = backtest_results['portfolio_returns']
                realized_volatility = portfolio_returns.std() * np.sqrt(252)
                
                print(f"\n📈 Risultati:")
                print(f"   Volatilità realizzata: {realized_volatility*100:.2f}%")
                if config['target_volatility']:
                    print(f"   Target volatilità: {config['target_volatility']*100:.2f}%")
                    diff = abs(realized_volatility - config['target_volatility'])
                    print(f"   Differenza: {diff*100:.2f}%")
                
                # Rendimento totale
                total_return = (backtest_results['cumulative_returns'].iloc[-1] - 1) * 100
                print(f"   Rendimento totale: {total_return:.2f}%")
                
            else:
                print("❌ Backtest fallito")
        
        except Exception as e:
            print(f"❌ Errore: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Test 2: Verifica del calcolo del cash target
    print("🔬 Test Calcolo Cash Target")
    print("=" * 40)
    
    optimizer = PortfolioOptimizer(
        use_volatility_target=True,
        target_volatility=0.08  # 8%
    )
    
    # Simula pesi di investimento
    investment_weights = pd.Series({
        'SWDA.MI': 0.4,
        'SPXS.MI': 0.3,
        'IS3K.DE': 0.3
    })
    
    # Test su diverse date
    test_dates = returns_data.index[-252::60]  # Ultimi 4 trimestri
    
    for test_date in test_dates:
        try:
            cash_weight = optimizer.calculate_target_cash_weight(
                returns_data, 
                investment_weights, 
                test_date
            )
            print(f"   {test_date.strftime('%Y-%m-%d')}: Cash target {cash_weight*100:.1f}%")
        except Exception as e:
            print(f"   {test_date.strftime('%Y-%m-%d')}: Errore {e}")

if __name__ == "__main__":
    test_volatility_target()

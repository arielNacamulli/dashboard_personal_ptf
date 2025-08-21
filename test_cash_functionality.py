#!/usr/bin/env python3
"""
Test delle nuove funzionalità con XEON come cash asset
"""
import pandas as pd
import numpy as np
from src.config import get_etf_symbols, get_investment_symbols, get_cash_asset
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer

def test_cash_functionality():
    """Test delle funzionalità cash"""
    print("🧪 Test delle funzionalità Cash Asset")
    print("=" * 50)
    
    # Test configurazione
    cash_asset = get_cash_asset()
    investment_symbols = get_investment_symbols()
    all_symbols = get_etf_symbols()
    
    print(f"💰 Cash Asset: {cash_asset}")
    print(f"📈 Investment Assets: {len(investment_symbols)} ETF")
    print(f"📊 Total Assets: {len(all_symbols)} ETF")
    
    # Test con dati simulati
    print("\n🔬 Test con dati simulati...")
    
    # Crea dati di ritorno simulati
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    n_assets = len(all_symbols)
    
    # Genera rendimenti casuali
    np.random.seed(42)
    returns_data = pd.DataFrame(
        np.random.normal(0.0005, 0.02, (len(dates), n_assets)),
        index=dates,
        columns=list(all_symbols.keys())
    )
    
    print(f"✅ Dati simulati: {len(returns_data)} giorni per {len(returns_data.columns)} asset")
    
    # Test ottimizzazione
    optimizer = PortfolioOptimizer()
    
    # Test HERC
    print("\n🎯 Test HERC...")
    herc_weights = optimizer.herc_optimization(returns_data)
    print(f"HERC - Pesi calcolati per {len(herc_weights)} asset")
    print(f"HERC - Somma pesi: {herc_weights.sum():.4f}")
    print(f"HERC - Peso {cash_asset}: {herc_weights.get(cash_asset, 0):.4f}")
    
    # Test HRP
    print("\n🎯 Test HRP...")
    hrp_weights = optimizer.hrp_optimization(returns_data)
    print(f"HRP - Pesi calcolati per {len(hrp_weights)} asset")
    print(f"HRP - Somma pesi: {hrp_weights.sum():.4f}")
    print(f"HRP - Peso {cash_asset}: {hrp_weights.get(cash_asset, 0):.4f}")
    
    # Test calculate_cash_weight
    print("\n💰 Test calcolo cash weight...")
    test_weights = pd.Series(0.0, index=list(all_symbols.keys()))
    test_weights['SWDA.MI'] = 0.4
    test_weights['SPXS.MI'] = 0.3
    test_weights['XDWT.MI'] = 0.2
    
    final_weights = optimizer.calculate_cash_weight(test_weights)
    print(f"Pesi test: SWDA.MI=40%, SPXS.MI=30%, XDWT.MI=20%")
    print(f"Cash automatico: {final_weights[cash_asset]:.1%}")
    print(f"Somma finale: {final_weights.sum():.4f}")
    
    # Test adjust_weights_with_cash
    print("\n🔧 Test aggiustamento pesi...")
    # Simula pesi che superano il 100%
    over_weights = pd.Series(0.0, index=list(all_symbols.keys()))
    over_weights['SWDA.MI'] = 0.6
    over_weights['SPXS.MI'] = 0.5
    over_weights['XDWT.MI'] = 0.3  # Totale = 140%
    
    adjusted_weights = optimizer.adjust_weights_with_cash(over_weights)
    print(f"Pesi originali: Totale = {over_weights.drop(cash_asset, errors='ignore').sum():.1%}")
    print(f"Pesi aggiustati: Totale = {adjusted_weights.sum():.4f}")
    print(f"Cash finale: {adjusted_weights[cash_asset]:.1%}")
    
    print("\n" + "=" * 50)
    print("✅ Test completato con successo!")
    
    return herc_weights, hrp_weights

if __name__ == "__main__":
    test_cash_functionality()

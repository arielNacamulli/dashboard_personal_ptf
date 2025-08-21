#!/usr/bin/env python3
"""
Test per verificare se SWDA.MI viene incluso correttamente nell'ottimizzazione HERC/HRP
"""

import pandas as pd
import numpy as np
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset

def test_swda_inclusion():
    """Verifica se SWDA.MI partecipa attivamente all'ottimizzazione"""
    
    print("🔍 Test Inclusione SWDA nell'Ottimizzazione")
    print("=" * 50)
    
    # Carica dati limitati per test rapido
    data_loader = ETFDataLoader()
    etf_symbols = list(get_etf_symbols().keys())
    
    print(f"ETF Symbols: {etf_symbols}")
    print()
    
    try:
        # Usa periodo più breve per test rapido
        prices_data = data_loader.download_etf_data(etf_symbols, "2y")
        returns_data = data_loader.calculate_returns(prices_data)
        
        print(f"✅ Dati caricati: {len(prices_data.columns)} ETF")
        print(f"   Periodo: {prices_data.index[0].strftime('%Y-%m-%d')} - {prices_data.index[-1].strftime('%Y-%m-%d')}")
        print(f"   Colonne returns: {list(returns_data.columns)}")
        print()
        
        # Test con diversi parametri
        test_configs = [
            {"max_exposure": 0.20, "cash_target": 0.10, "name": "20% limit"},
            {"max_exposure": 0.30, "cash_target": 0.10, "name": "30% limit"},
            {"max_exposure": 0.50, "cash_target": 0.10, "name": "50% limit"}
        ]
        
        for config in test_configs:
            print(f"📊 Test: {config['name']}")
            print("-" * 30)
            
            optimizer = PortfolioOptimizer(
                cash_target=config['cash_target'],
                max_exposure=config['max_exposure']
            )
            
            # Test HERC
            print("🔄 HERC Optimization:")
            herc_weights = optimizer.herc_optimization(returns_data)
            
            print(f"   SWDA.MI peso: {herc_weights.get('SWDA.MI', 0)*100:.2f}%")
            print(f"   XEON.MI peso: {herc_weights.get('XEON.MI', 0)*100:.2f}%")
            
            # Trova i top 3 asset (escluso cash)
            investment_weights = herc_weights.drop(get_cash_asset()).sort_values(ascending=False)
            print("   Top 3 asset:")
            for i, (asset, weight) in enumerate(investment_weights.head(3).items()):
                print(f"     {i+1}. {asset}: {weight*100:.2f}%")
            
            # Test HRP
            print("🔄 HRP Optimization:")
            hrp_weights = optimizer.hrp_optimization(returns_data)
            
            print(f"   SWDA.MI peso: {hrp_weights.get('SWDA.MI', 0)*100:.2f}%")
            print(f"   XEON.MI peso: {hrp_weights.get('XEON.MI', 0)*100:.2f}%")
            
            # Trova i top 3 asset (escluso cash)
            investment_weights = hrp_weights.drop(get_cash_asset()).sort_values(ascending=False)
            print("   Top 3 asset:")
            for i, (asset, weight) in enumerate(investment_weights.head(3).items()):
                print(f"     {i+1}. {asset}: {weight*100:.2f}%")
            
            print()
        
        # Test step-by-step per HERC per vedere dove si perde SWDA
        print("🔬 ANALISI DETTAGLIATA HERC:")
        print("=" * 40)
        
        optimizer = PortfolioOptimizer(cash_target=0.10, max_exposure=0.20)
        cash_asset = get_cash_asset()
        
        # Step 1: Preparazione dati
        print(f"Step 1 - Dati originali: {list(returns_data.columns)}")
        
        # Step 2: Filtraggio investment returns
        investment_returns = returns_data.drop(columns=[cash_asset], errors='ignore')
        print(f"Step 2 - Investment returns: {list(investment_returns.columns)}")
        print(f"         SWDA incluso: {'SWDA.MI' in investment_returns.columns}")
        
        # Step 3: Calcolo correlazione
        if not investment_returns.empty:
            correlation_matrix = investment_returns.corr().fillna(0)
            print(f"Step 3 - Correlazione shape: {correlation_matrix.shape}")
            print(f"         SWDA in correlazione: {'SWDA.MI' in correlation_matrix.index}")
            
            # Step 4: Clustering e ottimizzazione
            distance_matrix = optimizer.calculate_distance_matrix(correlation_matrix)
            linkage_matrix = optimizer.hierarchical_clustering(distance_matrix)
            covariance_matrix = investment_returns.cov()
            
            # Chiamata diretta alla ricorsione HERC
            investment_weights = optimizer._herc_recursive_allocation(
                linkage_matrix, 
                covariance_matrix, 
                investment_returns.columns.tolist()
            )
            
            print(f"Step 4 - Investment weights shape: {investment_weights.shape}")
            print(f"         Asset list: {investment_returns.columns.tolist()}")
            
            # Step 5: Mapping finale
            final_weights = pd.Series(0.0, index=returns_data.columns)
            for i, asset in enumerate(investment_returns.columns):
                final_weights[asset] = investment_weights[i]
                if asset == 'SWDA.MI':
                    print(f"         SWDA.MI mapping: position {i} -> weight {investment_weights[i]:.4f}")
            
            print("Step 5 - Pesi finali (prima di constraints):")
            for asset, weight in final_weights.items():
                if weight > 0.001:
                    print(f"         {asset}: {weight*100:.2f}%")
    
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_swda_inclusion()

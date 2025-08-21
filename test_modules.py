"""
Test per verificare il funzionamento dei moduli principali
"""
import sys
import os

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.metrics import PerformanceMetrics
from src.config import get_etf_symbols
import pandas as pd
import numpy as np

def test_data_loader():
    """Test del data loader"""
    print("Testing ETF Data Loader...")
    
    loader = ETFDataLoader()
    
    # Test simboli dai nuovi ETF
    etf_symbols = get_etf_symbols()
    test_symbols = list(etf_symbols.keys())[:2]  # Prendi i primi 2 ETF
    
    try:
        # Test download (con un periodo breve per velocità)
        data = loader.download_etf_data(test_symbols, '1y')
        
        if not data.empty:
            print(f"✅ Download successful: {len(data)} observations for {len(data.columns)} assets")
            
            # Test calcolo rendimenti
            returns = loader.calculate_returns(data)
            print(f"✅ Returns calculation: {len(returns)} return observations")
            
            # Test validazione
            is_valid, message = loader.validate_data(data)
            print(f"✅ Data validation: {is_valid} - {message}")
            
            return data, returns
        else:
            print("❌ No data downloaded")
            return None, None
            
    except Exception as e:
        print(f"❌ Error in data loader: {str(e)}")
        return None, None

def test_portfolio_optimizer(returns_data):
    """Test dell'ottimizzatore di portafoglio"""
    print("\nTesting Portfolio Optimizer...")
    
    if returns_data is None or returns_data.empty:
        print("❌ No returns data available for testing")
        return None
    
    try:
        optimizer = PortfolioOptimizer()
        
        # Test HRP
        hrp_weights = optimizer.hrp_optimization(returns_data)
        print(f"✅ HRP optimization: {len(hrp_weights)} weights, sum = {hrp_weights.sum():.4f}")
        
        # Test HERC
        herc_weights = optimizer.herc_optimization(returns_data)
        print(f"✅ HERC optimization: {len(herc_weights)} weights, sum = {herc_weights.sum():.4f}")
        
        # Test backtest breve
        backtest_results = optimizer.backtest_portfolio(returns_data, method='herc', rebalance_freq='Q')
        if not backtest_results.empty:
            print(f"✅ Backtest: {len(backtest_results)} periods simulated")
        
        return herc_weights
        
    except Exception as e:
        print(f"❌ Error in portfolio optimizer: {str(e)}")
        return None

def test_performance_metrics(returns_data):
    """Test delle metriche di performance"""
    print("\nTesting Performance Metrics...")
    
    if returns_data is None or returns_data.empty:
        print("❌ No returns data available for testing")
        return
    
    try:
        metrics_calc = PerformanceMetrics()
        
        # Test su primo asset
        first_asset_returns = returns_data.iloc[:, 0].dropna()
        
        # Test metriche individuali
        annual_return = metrics_calc.annualized_return(first_asset_returns)
        annual_vol = metrics_calc.annualized_volatility(first_asset_returns)
        sharpe = metrics_calc.sharpe_ratio(first_asset_returns)
        max_dd, _, _ = metrics_calc.maximum_drawdown(first_asset_returns)
        
        print(f"✅ Annual Return: {annual_return:.4f}")
        print(f"✅ Annual Volatility: {annual_vol:.4f}")
        print(f"✅ Sharpe Ratio: {sharpe:.4f}")
        print(f"✅ Max Drawdown: {max_dd:.4f}")
        
        # Test tutte le metriche
        all_metrics = metrics_calc.calculate_all_metrics(first_asset_returns)
        print(f"✅ All metrics calculation: {len(all_metrics)} metrics computed")
        
    except Exception as e:
        print(f"❌ Error in performance metrics: {str(e)}")

def main():
    """Funzione principale di test"""
    print("🧪 Testing ETF Portfolio Dashboard Components\n")
    print("=" * 50)
    
    # Test data loader
    price_data, returns_data = test_data_loader()
    
    # Test portfolio optimizer
    if returns_data is not None:
        weights = test_portfolio_optimizer(returns_data)
        
        # Test performance metrics
        test_performance_metrics(returns_data)
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    main()

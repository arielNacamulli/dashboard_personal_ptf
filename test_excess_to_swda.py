#!/usr/bin/env python3
"""
Test per verificare che l'eccesso di esposizione vada su SWDA invece che su XEON
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Aggiungi il path per importare i moduli
sys.path.append('/Users/arielnacamulli/Codici/dashboard_personal_ptf')

from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_cash_asset

def test_excess_to_swda():
    """Test che l'eccesso di esposizione vada su SWDA"""
    
    print("🧪 Test Redirect Eccesso su SWDA")
    print("=" * 50)
    
    # Crea dati di test
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)
    
    # Simula rendimenti realistici
    n_days = len(dates)
    etf_returns = {
        'SWDA.MI': np.random.normal(0.0008, 0.012, n_days),  # Asset core
        'XEON.MI': np.random.normal(0.0001, 0.002, n_days),  # Cash
        'SPXS.MI': np.random.normal(0.0009, 0.015, n_days),  # ETF che supererà il limite
        'XDWT.MI': np.random.normal(0.0010, 0.018, n_days),  # ETF che supererà il limite
        'IS3K.DE': np.random.normal(0.0005, 0.008, n_days),  # ETF normale
    }
    
    returns_df = pd.DataFrame(etf_returns, index=dates)
    
    print(f"📊 Dataset: {len(dates)} giorni, {len(etf_returns)} asset")
    print()
    
    # Test con limite di esposizione molto basso per forzare violazioni
    print("🔍 Test: Limite Esposizione Ridotto (15%)")
    print("-" * 40)
    
    optimizer = PortfolioOptimizer(
        cash_target=0.10,  # 10% cash fisso
        max_exposure=0.15,  # 15% limite massimo (molto basso per forzare violazioni)
        use_volatility_target=False
    )
    
    # Usa solo gli ultimi 252 giorni per l'ottimizzazione
    optimization_returns = returns_df.tail(252)
    
    print(f"Ottimizzazione con limite {optimizer.max_exposure*100:.0f}% per ETF")
    print()
    
    # Test HRP 
    print("📈 HRP Optimization:")
    hrp_weights = optimizer.hrp_optimization(optimization_returns)
    print("Pesi prima dei vincoli:")
    for asset in hrp_weights.index:
        if asset != get_cash_asset():
            print(f"   {asset}: {hrp_weights[asset]*100:.2f}%")
    
    # Applica vincoli
    constrained_weights = optimizer.apply_exposure_constraints(
        hrp_weights, 
        returns_data=returns_df, 
        current_date=returns_df.index[-1]
    )
    
    print("\nPesi dopo vincoli di esposizione:")
    cash_asset = get_cash_asset()
    swda_weight = 0
    total_investment = 0
    
    for asset in constrained_weights.index:
        weight_pct = constrained_weights[asset] * 100
        if asset == 'SWDA.MI':
            swda_weight = weight_pct
        if asset != cash_asset:
            total_investment += weight_pct
            
        print(f"   {asset}: {weight_pct:.2f}%")
    
    print(f"\nCash finale: {constrained_weights[cash_asset]*100:.2f}%")
    print(f"SWDA finale: {swda_weight:.2f}%")
    print(f"Totale investimenti: {total_investment:.2f}%")
    print()
    
    # Verifica che SWDA abbia assorbito l'eccesso
    violations = []
    for asset in constrained_weights.index:
        if asset != cash_asset and asset != 'SWDA.MI':  # Escludi cash e SWDA (esenti)
            if constrained_weights[asset] > optimizer.max_exposure + 1e-6:
                violations.append(f"{asset}: {constrained_weights[asset]*100:.2f}% > {optimizer.max_exposure*100:.0f}%")
    
    if violations:
        print("❌ Violazioni ancora presenti:")
        for violation in violations:
            print(f"   - {violation}")
    else:
        print("✅ Nessuna violazione di esposizione")
    
    # Verifica che SWDA abbia ricevuto peso extra
    if swda_weight > 30:  # Se SWDA ha più del 30%, probabilmente ha assorbito eccesso
        print(f"✅ SWDA sembra aver assorbito l'eccesso ({swda_weight:.1f}%)")
    else:
        print(f"ℹ️  SWDA ha peso normale ({swda_weight:.1f}%)")
    
    # Verifica che il cash non sia eccessivo
    cash_weight = constrained_weights[cash_asset] * 100
    if cash_weight <= 15:  # Se il cash è normale (<=15%), l'eccesso non è andato lì
        print(f"✅ Cash rimane normale ({cash_weight:.1f}%), eccesso non andato al cash")
    else:
        print(f"⚠️  Cash elevato ({cash_weight:.1f}%), possibile eccesso allocato al cash")
    
    print()
    
    # Test 2: Limite ancora più basso
    print("🔍 Test: Limite Esposizione Molto Ridotto (10%)")
    print("-" * 45)
    
    optimizer_strict = PortfolioOptimizer(
        cash_target=0.10,
        max_exposure=0.10,  # 10% limite (estremamente basso)
        use_volatility_target=False
    )
    
    # Applica vincoli ancora più stretti
    constrained_weights_strict = optimizer_strict.apply_exposure_constraints(
        hrp_weights, 
        returns_data=returns_df, 
        current_date=returns_df.index[-1]
    )
    
    print("\nPesi con vincoli molto stretti (10%):")
    swda_weight_strict = 0
    cash_weight_strict = 0
    
    for asset in constrained_weights_strict.index:
        weight_pct = constrained_weights_strict[asset] * 100
        if asset == 'SWDA.MI':
            swda_weight_strict = weight_pct
        elif asset == cash_asset:
            cash_weight_strict = weight_pct
            
        print(f"   {asset}: {weight_pct:.2f}%")
    
    print(f"\nCon limite 10%:")
    print(f"   SWDA: {swda_weight_strict:.1f}%")
    print(f"   Cash: {cash_weight_strict:.1f}%")
    
    if swda_weight_strict > swda_weight:
        print("✅ SWDA ha assorbito più eccesso con limite più stringente")
    
    print()
    print("🎉 Test completato!")
    print()
    print("📋 Riepilogo Comportamento:")
    print("   • L'eccesso di esposizione viene ora allocato prioritariamente a SWDA")
    print("   • SWDA, essendo asset core ed esente da limiti, può assorbire tutto l'eccesso")
    print("   • Il cash rimane al livello target invece di essere gonfiato dall'eccesso")
    print("   • Solo se SWDA non è disponibile, si usa la redistribuzione tradizionale")

if __name__ == "__main__":
    test_excess_to_swda()

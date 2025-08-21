#!/usr/bin/env python3
"""
Script per verificare la validità dei simboli ETF configurati
"""
import yfinance as yf
from src.config import ETF_SYMBOLS
import pandas as pd
from datetime import datetime, timedelta

def check_etf_symbol(symbol, period='1y'):
    """
    Verifica se un simbolo ETF è valido e scaricabile
    
    Args:
        symbol: Simbolo dell'ETF
        period: Periodo di test per il download
        
    Returns:
        dict: Risultato della verifica
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        
        if data.empty:
            return {
                'symbol': symbol,
                'status': 'FAILED',
                'error': 'No data available',
                'data_points': 0
            }
        
        # Ottieni info aggiuntive
        try:
            info = ticker.info
            name = info.get('longName', 'N/A')
            currency = info.get('currency', 'N/A')
            exchange = info.get('exchange', 'N/A')
        except:
            name = ETF_SYMBOLS.get(symbol, 'N/A')
            currency = 'N/A'
            exchange = 'N/A'
        
        return {
            'symbol': symbol,
            'status': 'SUCCESS',
            'name': name,
            'currency': currency,
            'exchange': exchange,
            'data_points': len(data),
            'start_date': data.index.min().strftime('%Y-%m-%d'),
            'end_date': data.index.max().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        return {
            'symbol': symbol,
            'status': 'ERROR',
            'error': str(e),
            'data_points': 0
        }

def main():
    """Funzione principale per verificare tutti gli ETF"""
    print("🔍 Verifica validità simboli ETF configurati\n")
    print("=" * 80)
    
    results = []
    
    for symbol in ETF_SYMBOLS.keys():
        print(f"Verificando {symbol}...", end=" ")
        result = check_etf_symbol(symbol)
        results.append(result)
        
        if result['status'] == 'SUCCESS':
            print(f"✅ OK ({result['data_points']} giorni)")
        elif result['status'] == 'FAILED':
            print(f"❌ FAILED: {result['error']}")
        else:
            print(f"⚠️ ERROR: {result['error']}")
    
    # Riassunto risultati
    print("\n" + "=" * 80)
    print("📊 RIASSUNTO VERIFICA")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"✅ Simboli validi: {success_count}/{total_count}")
    print(f"❌ Simboli non validi: {total_count - success_count}/{total_count}")
    
    # Dettagli simboli non validi
    failed_symbols = [r for r in results if r['status'] != 'SUCCESS']
    if failed_symbols:
        print(f"\n⚠️ SIMBOLI CON PROBLEMI:")
        for result in failed_symbols:
            print(f"  • {result['symbol']}: {result.get('error', 'Unknown error')}")
    
    # Tabella dettagliata per simboli validi
    valid_symbols = [r for r in results if r['status'] == 'SUCCESS']
    if valid_symbols:
        print(f"\n✅ SIMBOLI VALIDI:")
        df = pd.DataFrame(valid_symbols)
        print(df[['symbol', 'name', 'currency', 'exchange', 'data_points']].to_string(index=False))
    
    print(f"\n🎯 Verifica completata!")
    
    # Suggerimenti per simboli non validi
    if failed_symbols:
        print(f"\n💡 SUGGERIMENTI:")
        print("- Verifica che i simboli siano corretti per il mercato di riferimento")
        print("- Alcuni ETF potrebbero essere delisted o non disponibili su Yahoo Finance")
        print("- Controlla suffissi di mercato (.MI, .DE, .L, etc.)")

if __name__ == "__main__":
    main()

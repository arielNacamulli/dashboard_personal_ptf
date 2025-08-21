#!/usr/bin/env python3
"""
Test per analizzare la completezza dei dati ETF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import ETFDataLoader
from src.config import get_etf_symbols

def analyze_data_completeness():
    """Analizza la completezza dei dati per ogni ETF"""
    print("📊 Analisi Completezza Dati ETF")
    print("=" * 50)
    
    # Carica tutti gli ETF
    etf_symbols = list(get_etf_symbols().keys())
    data_loader = ETFDataLoader()
    
    print(f"🔍 Caricamento dati per {len(etf_symbols)} ETF...")
    
    try:
        # Download dei dati (10 anni)
        prices = data_loader.download_etf_data(etf_symbols, period='10y')
        
        if prices.empty:
            print("❌ Nessun dato scaricato")
            return
        
        # Ottieni il riassunto dettagliato
        summary = data_loader.get_data_summary(prices)
        
        print(f"\n📈 Periodo: {summary['start_date']} - {summary['end_date']}")
        print(f"📊 Osservazioni totali: {summary['num_observations']}")
        print(f"🎯 ETF analizzati: {summary['num_assets']}")
        print(f"📉 Completezza globale: {summary['completeness']}")
        print(f"❌ Valori mancanti: {summary['missing_values']}")
        
        print("\n📊 COMPLETEZZA PER ETF:")
        print("-" * 70)
        print(f"{'ETF':<12} {'Nome':<30} {'Completo':<10} {'Primo Dato':<12}")
        print("-" * 70)
        
        # Ordina per completezza
        etf_stats = []
        for etf, stats in summary['etf_completeness'].items():
            etf_name = get_etf_symbols()[etf][:25] + "..." if len(get_etf_symbols()[etf]) > 25 else get_etf_symbols()[etf]
            etf_stats.append({
                'symbol': etf,
                'name': etf_name,
                'completeness': stats['completeness'],
                'first_date': stats['first_valid_date']
            })
        
        # Ordina per completezza crescente
        etf_stats.sort(key=lambda x: x['completeness'])
        
        for etf in etf_stats:
            status = "🟢" if etf['completeness'] > 90 else "🟡" if etf['completeness'] > 50 else "🔴"
            print(f"{etf['symbol']:<12} {etf['name']:<30} {status} {etf['completeness']:<6.1f}% {etf['first_date']:<12}")
        
        # Problemi identificati
        if summary['problematic_etfs']:
            print(f"\n⚠️  ETF PROBLEMATICI (< 50% completezza):")
            print("-" * 50)
            for etf in summary['problematic_etfs']:
                print(f"• {etf['symbol']}: {etf['completeness']} - primo dato: {etf['first_date']}")
                print(f"  Nome: {etf['name']}")
                print(f"  Valori mancanti: {etf['missing']}")
                print()
        
        # Suggerimenti
        print("💡 SUGGERIMENTI:")
        if summary['problematic_etfs']:
            print("• Considera di rimuovere gli ETF con bassa completezza")
            print("• Prova un periodo più recente (es. 3y invece di 5y)")
            print("• Verifica se i simboli ETF sono corretti")
        else:
            print("• Tutti gli ETF hanno dati sufficienti per l'analisi")
        
        # Test con periodo più breve se ci sono problemi
        if float(summary['completeness'].replace('%', '')) < 80:
            print(f"\n🔍 TEST CON PERIODO PIÙ BREVE (3 anni):")
            print("-" * 40)
            
            try:
                prices_3y = data_loader.download_etf_data(etf_symbols, period='3y')
                summary_3y = data_loader.get_data_summary(prices_3y)
                
                print(f"Completezza 3y: {summary_3y['completeness']} vs 5y: {summary['completeness']}")
                
                if float(summary_3y['completeness'].replace('%', '')) > float(summary['completeness'].replace('%', '')):
                    print("✅ Miglioramento con periodo più breve!")
                else:
                    print("❌ Nessun miglioramento significativo")
                    
            except Exception as e:
                print(f"❌ Errore nel test 3y: {e}")
    
    except Exception as e:
        print(f"❌ Errore nell'analisi: {e}")

if __name__ == "__main__":
    analyze_data_completeness()

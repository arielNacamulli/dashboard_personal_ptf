"""
Dashboard ETF Portfolio Analysis con algoritmi HERC e HRP
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# Import dei moduli personalizzati
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.metrics import PerformanceMetrics
from src.config import (get_etf_symbols, get_etf_info, get_investment_symbols, get_cash_asset,
                      get_default_cash_target, get_default_max_exposure, is_exposure_exempt)
from src.utils import (
    create_performance_chart, create_weights_pie_chart, create_drawdown_chart,
    create_correlation_heatmap, create_weights_evolution_chart, create_metrics_table,
    export_to_excel, format_percentage, calculate_portfolio_summary
)

# Configurazione della pagina
st.set_page_config(
    page_title="ETF Portfolio Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato per un design minimale e professionale
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d1fae5;
        border: 1px solid #34d399;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef3c7;
        border: 1px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inizializza lo state della sessione"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'prices_data' not in st.session_state:
        st.session_state.prices_data = pd.DataFrame()
    if 'returns_data' not in st.session_state:
        st.session_state.returns_data = pd.DataFrame()
    if 'portfolio_results' not in st.session_state:
        st.session_state.portfolio_results = {}
    if 'current_weights' not in st.session_state:
        st.session_state.current_weights = pd.Series()

@st.cache_data
def load_etf_data(symbols, period):
    """Carica i dati ETF con caching"""
    data_loader = ETFDataLoader()
    return data_loader.download_etf_data(symbols, period)

def main():
    """Funzione principale dell'applicazione"""
    initialize_session_state()
    
    # Header principale
    st.markdown('<h1 class="main-header">📊 ETF Portfolio Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Analisi di portafoglio con algoritmi HERC e HRP")
    
    # Sidebar per i controlli
    with st.sidebar:
        st.header("⚙️ Configurazione")
        
        # Selezione ETF
        st.subheader("ETF Selection")
        etf_symbols = get_etf_symbols()
        
        selected_etfs = st.multiselect(
            "Seleziona ETF:",
            options=list(etf_symbols.keys()),
            default=list(etf_symbols.keys()),
            format_func=lambda x: f"{x} - {etf_symbols[x]}"
        )
        
        # Periodo di analisi
        st.subheader("Periodo di Analisi")
        period = st.selectbox(
            "Seleziona periodo:",
            options=['1y', '2y', '3y', '5y', '10y', '15y', '20y', 'max'],
            index=6,  # Default a 15y
            format_func=lambda x: {
                '1y': '1 Anno',
                '2y': '2 Anni', 
                '3y': '3 Anni',
                '5y': '5 Anni',
                '10y': '10 Anni',
                '15y': '15 Anni',
                '20y': '20 Anni',
                'max': 'Massimo disponibile (dal lancio dell\'ETF)'
            }[x]
        )
        
        # Pulsante per caricare i dati
        if st.button("🔄 Carica Dati ETF", use_container_width=True):
            if selected_etfs:
                with st.spinner("Caricamento dati in corso..."):
                    try:
                        data_loader = ETFDataLoader()
                        prices = data_loader.download_etf_data(selected_etfs, period)
                        
                        if not prices.empty:
                            # Valida i dati
                            is_valid, message = data_loader.validate_data(prices)
                            
                            if is_valid:
                                st.session_state.prices_data = prices
                                st.session_state.returns_data = data_loader.calculate_returns(prices, "log")
                                st.session_state.data_loaded = True
                                
                                st.success(f"✅ Dati caricati con successo!")
                                
                                # Mostra sommario dei dati
                                summary = data_loader.get_data_summary(prices)
                                st.write("**Sommario dati:**")
                                st.write(f"• Periodo: {summary['start_date']} - {summary['end_date']}")
                                st.write(f"• Osservazioni: {summary['num_observations']}")
                                st.write(f"• ETF: {summary['num_assets']}")
                                st.write(f"• Completezza globale: {summary['completeness']}")
                                
                                # Mostra ETF problematici se presenti
                                if summary['problematic_etfs']:
                                    st.warning("⚠️ **ETF con dati incompleti:**")
                                    for etf_info in summary['problematic_etfs']:
                                        st.write(f"• **{etf_info['symbol']}** ({etf_info['name']}): {etf_info['completeness']} completo, primo dato: {etf_info['first_date']}")
                                    
                                    st.info("💡 Suggerimento: Considera di rimuovere gli ETF con completezza molto bassa o utilizzare un periodo più recente.")
                                else:
                                    st.success("✅ Tutti gli ETF hanno dati sufficienti per l'analisi")
                            else:
                                st.error(f"❌ Errore validazione dati: {message}")
                        else:
                            st.error("❌ Nessun dato scaricato. Verifica i simboli ETF.")
                    except Exception as e:
                        st.error(f"❌ Errore nel caricamento: {str(e)}")
            else:
                st.warning("⚠️ Seleziona almeno un ETF")
        
        # Sezione ottimizzazione (solo se i dati sono caricati)
        if st.session_state.data_loaded:
            st.divider()
            st.subheader("Ottimizzazione Portfolio")
            
            # Selezione algoritmo
            algorithm = st.radio(
                "Algoritmo:",
                options=['HERC', 'HRP'],
                index=0,
                help="HERC = Hierarchical Equal Risk Contribution, HRP = Hierarchical Risk Parity"
            )
            
            # Frequenza di ribilanciamento
            rebalance_freq = st.selectbox(
                "Ribilanciamento:",
                options=['M', 'Q', 'Y'],
                index=1,
                format_func=lambda x: {
                    'M': 'Mensile',
                    'Q': 'Trimestrale', 
                    'Y': 'Annuale'
                }[x]
            )
            
            # Configurazioni avanzate
            st.subheader("⚙️ Configurazioni Avanzate")
            
            # Cash fisso
            cash_target = st.slider(
                f"Target Cash Fisso ({get_cash_asset()}):",
                min_value=0.0,
                max_value=50.0,
                value=get_default_cash_target() * 100,
                step=1.0,
                format="%.0f%%",
                help="Percentuale fissa di cash da mantenere ad ogni ribilanciamento"
            ) / 100.0
            
            # Massima esposizione
            max_exposure = st.slider(
                "Massima Esposizione per ETF:",
                min_value=10.0,
                max_value=100.0,
                value=get_default_max_exposure() * 100,
                step=1.0,
                format="%.0f%%",
                help="Limite massimo di allocazione per singolo ETF (esclude SWDA e XEON)"
            ) / 100.0
            
            # Mostra ETF esenti
            st.info(f"📋 ETF esenti dal limite: SWDA.MI, {get_cash_asset()}")
            
            # Pulsante per ottimizzare
            if st.button("🎯 Ottimizza Portfolio", use_container_width=True):
                with st.spinner("Ottimizzazione in corso..."):
                    try:
                        # Crea optimizer con i nuovi parametri
                        optimizer = PortfolioOptimizer(
                            cash_target=cash_target,
                            max_exposure=max_exposure
                        )
                        
                        # Esegui backtest con benchmark
                        backtest_results = optimizer.backtest_with_benchmark(
                            st.session_state.returns_data,
                            method=algorithm.lower(),
                            rebalance_freq=rebalance_freq
                        )
                        
                        # Ottieni i pesi più recenti con cash calcolato
                        latest_weights = optimizer.get_latest_weights()
                        
                        # Salva i risultati
                        st.session_state.portfolio_results = {
                            'backtest': backtest_results['portfolio'],
                            'benchmark': backtest_results['benchmark'],
                            'weights_history': optimizer.weights_history,
                            'rebalance_dates': optimizer.get_rebalance_dates(),
                            'algorithm': algorithm,
                            'rebalance_freq': rebalance_freq,
                            'cash_target': cash_target,
                            'max_exposure': max_exposure,
                            'benchmark_weights': backtest_results['benchmark_weights']
                        }
                        st.session_state.current_weights = latest_weights
                        st.session_state.manual_weights = latest_weights  # Inizializza pesi manuali
                        
                        st.success(f"✅ Ottimizzazione {algorithm} completata!")
                        
                    except Exception as e:
                        st.error(f"❌ Errore nell'ottimizzazione: {str(e)}")
    
    # Area principale del dashboard
    if st.session_state.data_loaded:
        
        # Tab per organizzare il contenuto
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance", "⚖️ Pesi Portfolio", "📊 Metriche", "🔍 Analisi"])
        
        with tab1:
            st.subheader("Performance del Portfolio")
            
            if st.session_state.portfolio_results:
                results = st.session_state.portfolio_results
                
                # Grafico performance principale con benchmark
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    backtest_data = results['backtest']
                    benchmark_data = results.get('benchmark', pd.DataFrame())
                    
                    if not backtest_data.empty:
                        # Crea grafico combinato portfolio + benchmark
                        fig_performance = go.Figure()
                        
                        # Linea del portfolio
                        fig_performance.add_trace(go.Scatter(
                            x=backtest_data.index,
                            y=backtest_data['cumulative_returns'] * 100,
                            mode='lines',
                            name=f'{results["algorithm"]} Portfolio',
                            line=dict(color='#2E86AB', width=2)
                        ))
                        
                        # Linea del benchmark (se disponibile)
                        if not benchmark_data.empty:
                            fig_performance.add_trace(go.Scatter(
                                x=benchmark_data.index,
                                y=benchmark_data['cumulative_returns'] * 100,
                                mode='lines',
                                name='Benchmark (SWDA + XEON)',
                                line=dict(color='#F24236', width=2, dash='dash')
                            ))
                        
                        fig_performance.update_layout(
                            title=f"Performance Cumulativa - {results['algorithm']} vs Benchmark",
                            xaxis_title="Data",
                            yaxis_title="Rendimento Cumulativo (%)",
                            template='plotly_white',
                            hovermode='x unified',
                            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                        )
                        
                        st.plotly_chart(fig_performance, use_container_width=True)
                
                with col2:
                    # Sommario performance con confronto benchmark
                    if not backtest_data.empty:
                        metrics_calc = PerformanceMetrics()
                        portfolio_metrics = metrics_calc.calculate_all_metrics(backtest_data['portfolio_returns'])
                        
                        # Calcola metriche benchmark se disponibile
                        benchmark_metrics = {}
                        if not benchmark_data.empty:
                            benchmark_metrics = metrics_calc.calculate_all_metrics(benchmark_data['benchmark_returns'])
                        
                        # Mostra metriche comparative
                        if benchmark_metrics:
                            st.write("**Portfolio vs Benchmark:**")
                            
                            # Confronti diretti
                            portfolio_return = portfolio_metrics.get('Total Return', 0)
                            benchmark_return = benchmark_metrics.get('Total Return', 0)
                            excess_return = portfolio_return - benchmark_return
                            
                            st.metric(
                                "Rendimento Totale",
                                format_percentage(portfolio_return),
                                delta=format_percentage(excess_return)
                            )
                            
                            portfolio_sharpe = portfolio_metrics.get('Sharpe Ratio', 0)
                            benchmark_sharpe = benchmark_metrics.get('Sharpe Ratio', 0)
                            sharpe_diff = portfolio_sharpe - benchmark_sharpe
                            
                            st.metric(
                                "Sharpe Ratio",
                                f"{portfolio_sharpe:.3f}",
                                delta=f"{sharpe_diff:+.3f}"
                            )
                            
                            portfolio_vol = portfolio_metrics.get('Annualized Volatility', 0)
                            benchmark_vol = benchmark_metrics.get('Annualized Volatility', 0)
                            vol_diff = portfolio_vol - benchmark_vol
                            
                            st.metric(
                                "Volatilità Annua",
                                format_percentage(portfolio_vol),
                                delta=format_percentage(vol_diff)
                            )
                            
                            # Information Ratio
                            if benchmark_metrics:
                                excess_returns = backtest_data['portfolio_returns'] - benchmark_data['benchmark_returns']
                                info_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
                                
                                st.metric(
                                    "Information Ratio",
                                    f"{info_ratio:.3f}",
                                    help="Rendimento attivo / Tracking Error"
                                )
                        else:
                            # Metriche solo portfolio se non c'è benchmark
                            st.metric(
                                "Rendimento Totale",
                                format_percentage(portfolio_metrics.get('Total Return', 0))
                            )
                            st.metric(
                                "Rendimento Annualizzato", 
                                format_percentage(portfolio_metrics.get('Annualized Return', 0))
                            )
                            st.metric(
                                "Volatilità Annualizzata",
                                format_percentage(portfolio_metrics.get('Annualized Volatility', 0))
                            )
                            st.metric(
                                "Sharpe Ratio",
                                f"{portfolio_metrics.get('Sharpe Ratio', 0):.3f}"
                            )
                
                # Grafico drawdown
                st.subheader("Analisi Drawdown")
                if not backtest_data.empty:
                    fig_drawdown = create_drawdown_chart(backtest_data['portfolio_returns'])
                    st.plotly_chart(fig_drawdown, use_container_width=True)
            else:
                st.info("🎯 Esegui l'ottimizzazione del portfolio per vedere le performance")
        
        with tab2:
            st.subheader("Allocazione Portfolio")
            
            if not st.session_state.current_weights.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Grafico a torta dei pesi
                    fig_pie = create_weights_pie_chart(
                        st.session_state.current_weights,
                        "Allocazione Corrente"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Tabella dei pesi
                    weights_df = pd.DataFrame({
                        'ETF': st.session_state.current_weights.index,
                        'Peso (%)': (st.session_state.current_weights.values * 100).round(2)
                    }).sort_values('Peso (%)', ascending=False)
                    
                    st.write("**Pesi dettagliati:**")
                    st.dataframe(weights_df, use_container_width=True)
                    
                    # Data ultimo ribilanciamento
                    if st.session_state.portfolio_results:
                        last_rebalance = st.session_state.portfolio_results['rebalance_dates'][-1]
                        cash_target = st.session_state.portfolio_results.get('cash_target', 0.0)
                        max_exposure = st.session_state.portfolio_results.get('max_exposure', 1.0)
                        
                        st.info(f"📅 Ultimo ribilanciamento: {last_rebalance.strftime('%Y-%m-%d')}")
                        st.info(f"💰 Cash fisso: {cash_target*100:.1f}% | 📊 Max esposizione: {max_exposure*100:.1f}%")
                
                # Sezione modifica manuale pesi
                st.subheader("🔧 Modifica Manuale Pesi")
                
                cash_asset = get_cash_asset()
                investment_symbols = get_investment_symbols()
                
                # Ottieni i parametri correnti dall'ottimizzazione
                current_cash_target = st.session_state.portfolio_results.get('cash_target', get_default_cash_target())
                current_max_exposure = st.session_state.portfolio_results.get('max_exposure', get_default_max_exposure())
                
                # Inizializza i pesi modificabili nello stato
                if 'manual_weights' not in st.session_state:
                    st.session_state.manual_weights = st.session_state.current_weights.copy()
                
                # Informazioni sui vincoli attivi
                st.info(f"💰 Cash fisso: {current_cash_target*100:.1f}% | 📊 Max esposizione: {current_max_exposure*100:.1f}% (eccetto SWDA e XEON)")
                
                # Colonne per gli input dei pesi
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Modifica Allocazione (%):**")
                    
                    # Input per ogni asset da investimento (esclude cash)
                    manual_weights = {}
                    total_manual = 0.0
                    available_for_investment = 1.0 - current_cash_target
                    
                    for symbol in investment_symbols.keys():
                        if symbol in st.session_state.current_weights.index:
                            current_weight = st.session_state.manual_weights.get(symbol, 0.0) * 100
                            
                            # Determina il limite massimo per questo ETF
                            if is_exposure_exempt(symbol):
                                max_weight_pct = available_for_investment * 100  # Può prendere tutto lo spazio disponibile
                                help_text = f"Peso per {symbol} (0-{max_weight_pct:.1f}% - ETF esente dal limite)"
                            else:
                                max_weight_pct = current_max_exposure * 100
                                help_text = f"Peso per {symbol} (0-{max_weight_pct:.1f}% - limite massimo applicato)"
                            
                            new_weight = st.number_input(
                                f"{symbol} - {investment_symbols[symbol]}",
                                min_value=0.0,
                                max_value=max_weight_pct,
                                value=float(min(current_weight, max_weight_pct)),
                                step=0.1,
                                key=f"weight_{symbol}",
                                help=help_text
                            )
                            
                            manual_weights[symbol] = new_weight / 100.0
                            total_manual += new_weight / 100.0
                    
                    # Mostra il peso del cash fisso (non modificabile)
                    st.number_input(
                        f"{cash_asset} - {get_etf_symbols()[cash_asset]} (Fisso)",
                        value=float(current_cash_target * 100),
                        disabled=True,
                        help=f"Peso fisso del cash impostato a {current_cash_target*100:.1f}%"
                    )
                
                with col2:
                    # Riassunto delle modifiche
                    st.write("**Riassunto Allocazione:**")
                    
                    # Verifica validità rispetto allo spazio disponibile
                    if total_manual > available_for_investment:
                        st.error(f"⚠️ Attenzione: Gli investimenti superano lo spazio disponibile ({total_manual*100:.1f}% > {available_for_investment*100:.1f}%)")
                        st.write("I pesi verranno normalizzati automaticamente.")
                    elif total_manual < available_for_investment * 0.80:  # Se usa meno dell'80% dello spazio
                        remaining_space = available_for_investment - total_manual
                        st.info(f"� Spazio rimanente: {remaining_space*100:.1f}% per altri investimenti")
                    else:
                        st.success(f"✅ Allocazione valida - Investimenti: {total_manual*100:.1f}%")
                    
                    # Mostra la ripartizione
                    summary_data = []
                    for symbol, weight in manual_weights.items():
                        if weight > 0:
                            summary_data.append({
                                'Asset': symbol,
                                'Peso (%)': f"{weight*100:.1f}%"
                            })
                    
                    # Aggiungi sempre il cash fisso
                    summary_data.append({
                        'Asset': cash_asset + " (Fisso)",
                        'Peso (%)': f"{current_cash_target*100:.1f}%"
                    })
                    
                    if summary_data:
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # Pulsanti per applicare o resettare
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Applica Modifiche", use_container_width=True):
                        # Crea la serie di pesi aggiornata
                        new_weights = pd.Series(0.0, index=st.session_state.current_weights.index)
                        
                        # Assegna i pesi manuali
                        for symbol, weight in manual_weights.items():
                            new_weights[symbol] = weight
                        
                        # Crea optimizer con i parametri correnti
                        optimizer = PortfolioOptimizer(
                            cash_target=current_cash_target,
                            max_exposure=current_max_exposure
                        )
                        
                        # Applica vincoli e normalizzazione
                        normalized_weights = optimizer.adjust_weights_with_cash(new_weights, use_fixed_cash=True)
                        
                        # Aggiorna lo stato
                        st.session_state.current_weights = normalized_weights
                        st.session_state.manual_weights = normalized_weights
                        
                        st.success("✅ Pesi aggiornati con successo!")
                        st.rerun()
                
                with col2:
                    if st.button("🔄 Reset Originali", use_container_width=True):
                        # Ripristina i pesi originali dall'ottimizzazione
                        if st.session_state.portfolio_results:
                            # Crea optimizer con i parametri originali
                            optimizer = PortfolioOptimizer(
                                cash_target=current_cash_target,
                                max_exposure=current_max_exposure
                            )
                            optimizer.weights_history = st.session_state.portfolio_results['weights_history']
                            original_weights = optimizer.get_latest_weights()
                            
                            st.session_state.current_weights = original_weights
                            st.session_state.manual_weights = original_weights
                            
                            st.success("🔄 Pesi ripristinati ai valori ottimali!")
                            st.rerun()
                
                with col3:
                    # Pulsante download con pesi modificati
                    if st.button("💾 Scarica Pesi Modificati", use_container_width=True):
                        weights_export = {
                            'Modified Weights': pd.DataFrame({
                                'ETF': st.session_state.current_weights.index,
                                'Weight': st.session_state.current_weights.values,
                                'Weight (%)': (st.session_state.current_weights.values * 100).round(2)
                            })
                        }
                        
                        excel_data = export_to_excel(weights_export, "modified_portfolio_weights.xlsx")
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name="modified_portfolio_weights.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                
                # Evoluzione pesi nel tempo
                if st.session_state.portfolio_results:
                    st.subheader("Evoluzione Pesi nel Tempo")
                    fig_weights_evolution = create_weights_evolution_chart(
                        st.session_state.portfolio_results['weights_history']
                    )
                    st.plotly_chart(fig_weights_evolution, use_container_width=True)
            else:
                st.info("🎯 Esegui l'ottimizzazione per vedere l'allocazione del portfolio")
        
        with tab3:
            st.subheader("Metriche di Performance")
            
            if st.session_state.portfolio_results:
                backtest_data = st.session_state.portfolio_results['backtest']
                
                # Determina se il benchmark è disponibile
                show_benchmark = ('benchmark' in st.session_state.portfolio_results and 
                                not st.session_state.portfolio_results['benchmark'].empty)
                
                if not backtest_data.empty:
                    metrics_calc = PerformanceMetrics()
                    portfolio_metrics = metrics_calc.calculate_all_metrics(backtest_data['portfolio_returns'])
                    
                    # Crea tabella metriche
                    metrics_df = create_metrics_table(portfolio_metrics)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Metriche Principali:**")
                        st.dataframe(metrics_df, use_container_width=True)
                    
                    with col2:
                        # Informazioni aggiuntive
                        st.write("**Informazioni Portfolio:**")
                        portfolio_summary = calculate_portfolio_summary(
                            backtest_data['portfolio_returns'],
                            st.session_state.current_weights
                        )
                        
                        for key, value in portfolio_summary.items():
                            st.write(f"• **{key}:** {value}")
                    
                    # Sezione benchmark se abilitato
                    if show_benchmark and 'benchmark' in st.session_state.portfolio_results:
                        benchmark_data = st.session_state.portfolio_results['benchmark']
                        
                        st.write("---")
                        st.subheader("Composizione Benchmark (SWDA + XEON)")
                        
                        col_bench1, col_bench2 = st.columns(2)
                        
                        with col_bench1:
                            # Pesi del benchmark
                            benchmark_weights_dict = st.session_state.portfolio_results.get('benchmark_weights', {})
                            if benchmark_weights_dict:
                                # Converti il dizionario in pandas Series
                                benchmark_weights = pd.Series(benchmark_weights_dict)
                                
                                benchmark_df = pd.DataFrame({
                                    'Asset': benchmark_weights.index,
                                    'Peso (%)': (benchmark_weights.values * 100).round(2)
                                })
                                st.dataframe(benchmark_df, use_container_width=True, hide_index=True)
                            else:
                                st.info("Nessun peso benchmark disponibile")
                        
                        with col_bench2:
                            # Grafico a torta del benchmark
                            benchmark_weights_dict = st.session_state.portfolio_results.get('benchmark_weights', {})
                            if benchmark_weights_dict:
                                # Converti il dizionario in pandas Series per il grafico
                                benchmark_weights = pd.Series(benchmark_weights_dict)
                                benchmark_fig = create_weights_pie_chart(
                                    benchmark_weights, 
                                    f"Benchmark Portfolio (Cash {cash_target:.0f}%)"
                                )
                                st.plotly_chart(benchmark_fig, use_container_width=True)
                    
                    # Distribuzione dei rendimenti
                    st.write("---")
                    st.subheader("Distribuzione Rendimenti Giornalieri")
                    
                    col_dist1, col_dist2 = st.columns(2)
                    
                    with col_dist1:
                        # Istogramma dei rendimenti
                        fig_hist = go.Figure()
                        
                        # Istogramma del portfolio
                        fig_hist.add_trace(go.Histogram(
                            x=backtest_data['portfolio_returns'] * 100,
                            nbinsx=50,
                            name='Portfolio',
                            opacity=0.7,
                            marker_color='blue'
                        ))
                        
                        # Aggiungi benchmark se disponibile
                        if show_benchmark and 'benchmark' in st.session_state.portfolio_results:
                            benchmark_data = st.session_state.portfolio_results['benchmark']
                            if not benchmark_data.empty:
                                fig_hist.add_trace(go.Histogram(
                                    x=benchmark_data['benchmark_returns'] * 100,
                                    nbinsx=50,
                                    name='Benchmark',
                                    opacity=0.7,
                                    marker_color='red'
                                ))
                        
                        fig_hist.update_layout(
                            title="Distribuzione Rendimenti (%)",
                            xaxis_title="Rendimento Giornaliero (%)",
                            yaxis_title="Frequenza",
                            barmode='overlay',
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    with col_dist2:
                        # Statistiche comparative
                        st.write("**Statistiche Rendimenti:**")
                        
                        # Calcola statistiche portfolio
                        portfolio_returns_pct = backtest_data['portfolio_returns'] * 100
                        
                        stats_data = {
                            'Portfolio': {
                                'Media (%)': f"{portfolio_returns_pct.mean():.3f}",
                                'Mediana (%)': f"{portfolio_returns_pct.median():.3f}",
                                'Std Dev (%)': f"{portfolio_returns_pct.std():.3f}",
                                'Skewness': f"{portfolio_returns_pct.skew():.3f}",
                                'Kurtosis': f"{portfolio_returns_pct.kurtosis():.3f}",
                                'Min (%)': f"{portfolio_returns_pct.min():.2f}",
                                'Max (%)': f"{portfolio_returns_pct.max():.2f}"
                            }
                        }
                        
                        # Aggiungi statistiche benchmark se disponibile
                        if show_benchmark and 'benchmark' in st.session_state.portfolio_results:
                            benchmark_data = st.session_state.portfolio_results['benchmark']
                            if not benchmark_data.empty:
                                benchmark_returns_pct = benchmark_data['benchmark_returns'] * 100
                                stats_data['Benchmark'] = {
                                    'Media (%)': f"{benchmark_returns_pct.mean():.3f}",
                                    'Mediana (%)': f"{benchmark_returns_pct.median():.3f}",
                                    'Std Dev (%)': f"{benchmark_returns_pct.std():.3f}",
                                    'Skewness': f"{benchmark_returns_pct.skew():.3f}",
                                    'Kurtosis': f"{benchmark_returns_pct.kurtosis():.3f}",
                                    'Min (%)': f"{benchmark_returns_pct.min():.2f}",
                                    'Max (%)': f"{benchmark_returns_pct.max():.2f}"
                                }
                        
                        stats_df = pd.DataFrame(stats_data)
                        st.dataframe(stats_df, use_container_width=True)
                    
                    # Metriche rolling
                    st.subheader("Metriche Rolling (1 Anno)")
                    rolling_metrics = metrics_calc.rolling_metrics(backtest_data['portfolio_returns'])
                    
                    if not rolling_metrics.empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Sharpe ratio rolling
                            fig_sharpe = go.Figure()
                            fig_sharpe.add_trace(go.Scatter(
                                x=rolling_metrics.index,
                                y=rolling_metrics['Sharpe Ratio'],
                                mode='lines',
                                name='Sharpe Ratio',
                                line=dict(color='#2E86AB', width=2)
                            ))
                            fig_sharpe.add_hline(y=1, line_dash="dash", line_color="green", opacity=0.7)
                            fig_sharpe.update_layout(
                                title="Sharpe Ratio Rolling",
                                xaxis_title="Date",
                                yaxis_title="Sharpe Ratio",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_sharpe, use_container_width=True)
                        
                        with col2:
                            # Volatilità rolling
                            fig_vol = go.Figure()
                            fig_vol.add_trace(go.Scatter(
                                x=rolling_metrics.index,
                                y=rolling_metrics['Annualized Volatility'] * 100,
                                mode='lines',
                                name='Volatilità',
                                line=dict(color='#F24236', width=2)
                            ))
                            fig_vol.update_layout(
                                title="Volatilità Rolling",
                                xaxis_title="Date",
                                yaxis_title="Volatilità (%)",
                                template='plotly_white'
                            )
                            st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.info("🎯 Esegui l'ottimizzazione per vedere le metriche")
        
        with tab4:
            st.subheader("Analisi Dettagliata")
            
            # Correlazione degli asset
            if not st.session_state.returns_data.empty:
                st.subheader("Matrice di Correlazione")
                correlation_matrix = st.session_state.returns_data.corr()
                fig_corr = create_correlation_heatmap(correlation_matrix)
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Statistiche degli asset individuali
                st.subheader("Performance Asset Individuali")
                metrics_calc = PerformanceMetrics()
                
                asset_metrics = {}
                for asset in st.session_state.returns_data.columns:
                    asset_returns = st.session_state.returns_data[asset].dropna()
                    asset_metrics[asset] = metrics_calc.calculate_all_metrics(asset_returns)
                
                # Crea DataFrame comparativo
                comparison_df = pd.DataFrame(asset_metrics).T
                comparison_df = comparison_df.round(4)
                
                st.dataframe(comparison_df, use_container_width=True)
                
                # Grafico risk-return
                st.subheader("Profilo Rischio-Rendimento")
                
                fig_scatter = go.Figure()
                
                for asset in asset_metrics.keys():
                    returns_ann = asset_metrics[asset]['Annualized Return'] * 100
                    vol_ann = asset_metrics[asset]['Annualized Volatility'] * 100
                    
                    fig_scatter.add_trace(go.Scatter(
                        x=[vol_ann],
                        y=[returns_ann],
                        mode='markers+text',
                        text=[asset],
                        textposition='top center',
                        marker=dict(size=12, opacity=0.7),
                        name=asset
                    ))
                
                fig_scatter.update_layout(
                    title="Rischio vs Rendimento - Asset Individuali",
                    xaxis_title="Volatilità Annualizzata (%)",
                    yaxis_title="Rendimento Annualizzato (%)",
                    template='plotly_white'
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
    
    else:
        # Messaggio di benvenuto
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background-color: #f8fafc; border-radius: 1rem; margin: 2rem 0;">
            <h2>🚀 Benvenuto nella Dashboard ETF</h2>
            <p style="font-size: 1.1rem; color: #6b7280;">
                Inizia selezionando gli ETF e caricando i dati storici dalla sidebar.
            </p>
            <p style="color: #9ca3af;">
                Questa dashboard implementa algoritmi avanzati di ottimizzazione del portafoglio (HERC e HRP) 
                per creare allocazioni efficienti basate sulla struttura gerarchica dei rischi.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Informazioni sugli ETF supportati
        st.subheader("📋 ETF Supportati")
        
        etf_info = get_etf_info()
        etf_df = pd.DataFrame(etf_info)
        st.dataframe(etf_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

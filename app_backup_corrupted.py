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
            
            # Modalità gestione cash
            cash_mode = st.radio(
                "Modalità Gestione Cash:",
                ["Cash Fisso", "Volatilità Target"],
                help="Cash Fisso: percentuale fissa di XEON. Volatilità Target: XEON variabile per raggiungere volatilità desiderata"
            )
            
            if cash_mode == "Cash Fisso":
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
                
                use_volatility_target = False
                target_volatility = None
            else:
                # Volatilità target
                from src.config import DEFAULT_TARGET_VOLATILITY
                
                target_volatility = st.slider(
                    "Volatilità Target Annua:",
                    min_value=1.0,
                    max_value=20.0,
                    value=DEFAULT_TARGET_VOLATILITY * 100,
                    step=0.5,
                    format="%.1f%%",
                    help="Volatilità annua target - XEON sarà usato per raggiungere questo obiettivo"
                ) / 100.0
                
                use_volatility_target = True
                cash_target = get_default_cash_target()  # Fallback value
                
                st.info(f"🎯 Con volatilità target {target_volatility*100:.1f}%, il peso di XEON varierà automaticamente ad ogni ribilanciamento")
            
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
                            max_exposure=max_exposure,
                            use_volatility_target=use_volatility_target,
                            target_volatility=target_volatility
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
                            'use_volatility_target': use_volatility_target,
                            'target_volatility': target_volatility,
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
                            # Determina l'etichetta del benchmark basata sulla modalità
                            benchmark_weights_dict = results.get('benchmark_weights', {})
                            use_vol_target = benchmark_weights_dict.get('approach') == 'volatility_target'
                            
                            if use_vol_target:
                                target_vol = benchmark_weights_dict.get('target_volatility', 0) * 100
                                benchmark_label = f'Benchmark Vol Target {target_vol:.1f}%'
                            else:
                                cash_pct = benchmark_weights_dict.get('cash_target', cash_target) * 100
                                benchmark_label = f'Benchmark Cash {cash_pct:.0f}%'
                            
                            fig_performance.add_trace(go.Scatter(
                                x=benchmark_data.index,
                                y=benchmark_data['cumulative_returns'] * 100,
                                mode='lines',
                                name=benchmark_label,
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
                            
                            # Rendimento Annualizzato 
                            portfolio_ann_return = portfolio_metrics.get('Annualized Return', 0)
                            benchmark_ann_return = benchmark_metrics.get('Annualized Return', 0)
                            ann_excess_return = portfolio_ann_return - benchmark_ann_return
                            
                            st.metric(
                                "Rendimento Annualizzato",
                                format_percentage(portfolio_ann_return),
                                delta=format_percentage(ann_excess_return)
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
                        
                        # Mostra info diverse in base alla modalità
                        use_vol_target = st.session_state.portfolio_results.get('use_volatility_target', False)
                        target_vol = st.session_state.portfolio_results.get('target_volatility', None)
                        
                        if use_vol_target and target_vol:
                            st.info(f"🎯 Volatilità target: {target_vol*100:.1f}% | 📊 Max esposizione: {max_exposure*100:.1f}%")
                        else:
                            st.info(f"💰 Cash fisso: {cash_target*100:.1f}% | 📊 Max esposizione: {max_exposure*100:.1f}%")
                
                # Sezione Risk Budgeting per HERC
                st.subheader("🎯 Risk Budgeting (HERC)")
                
                cash_asset = get_cash_asset()
                investment_symbols = get_investment_symbols()
                
                # Ottieni i parametri correnti dall'ottimizzazione
                current_cash_target = st.session_state.portfolio_results.get('cash_target', get_default_cash_target())
                current_max_exposure = st.session_state.portfolio_results.get('max_exposure', get_default_max_exposure())
                use_volatility_target = st.session_state.portfolio_results.get('use_volatility_target', False)
                target_volatility = st.session_state.portfolio_results.get('target_volatility', None)
                
                # Inizializza i risk budgets nello stato
                if 'risk_budgets' not in st.session_state:
                    # Tutti i budget iniziali sono uguali a 1.0 (budget uniforme)
                    st.session_state.risk_budgets = {symbol: 1.0 for symbol in investment_symbols.keys()}
                
                # Informazioni sui vincoli attivi
                if use_volatility_target and target_volatility:
                    st.info(f"🎯 Volatilità target: {target_volatility*100:.1f}% | 📊 Max esposizione: {current_max_exposure*100:.1f}% (eccetto SWDA e XEON)")
                else:
                    st.info(f"💰 Cash fisso: {current_cash_target*100:.1f}% | 📊 Max esposizione: {current_max_exposure*100:.1f}% (eccetto SWDA e XEON)")
                
                st.write("💡 **Risk Budget**: Controlla quanto rischio allocare ad ogni ETF. Valori più alti = maggiore peso nell'allocazione.")
                st.write("� XEON (cash) è escluso dal risk budgeting in quanto asset risk-free.")
                
                # Colonne per gli input dei risk budgets
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Risk Budget per ETF:**")
                    
                    # Input per ogni asset da investimento (esclude cash)
                    risk_budgets = {}
                    total_budget = 0.0
                    
                    for symbol in investment_symbols.keys():
                        etf_name = investment_symbols[symbol]
                        current_budget = st.session_state.risk_budgets.get(symbol, 1.0)
                        
                        # Input slider per risk budget
                        risk_budgets[symbol] = st.slider(
                            f"**{symbol}** - {etf_name}",
                            min_value=0.1,
                            max_value=3.0,
                            value=current_budget,
                            step=0.1,
                            format="%.1f",
                            help=f"Budget di rischio per {symbol}. Default: 1.0 (uniforme)"
                        )
                        total_budget += risk_budgets[symbol]
                    
                    # Aggiorna i risk budgets nello stato
                    st.session_state.risk_budgets = risk_budgets
                    
                    # Mostra il peso del cash in base alla modalità
                    st.write("**Cash (XEON):**")
                    if use_volatility_target and target_volatility:
                        # Modalità volatilità target - XEON variabile
                        current_xeon_weight = st.session_state.current_weights.get(cash_asset, 0.0)
                        st.number_input(
                            f"{cash_asset} - {get_etf_symbols()[cash_asset]} (Variabile)",
                            value=float(current_xeon_weight * 100),
                            disabled=True,
                            help=f"Peso variabile del cash per raggiungere volatilità target {target_volatility*100:.1f}%"
                        )
                        st.caption("⚡ Il peso di XEON varia automaticamente in base alla volatilità target")
                    else:
                        # Modalità cash fisso
                        st.number_input(
                            f"{cash_asset} - {get_etf_symbols()[cash_asset]} (Fisso)",
                            value=float(current_cash_target * 100),
                            disabled=True,
                            help=f"Peso fisso del cash impostato a {current_cash_target*100:.1f}%"
                        )
                
                with col2:
                    # Riassunto dei Risk Budget
                    st.write("**Riassunto Risk Budget:**")
                    
                    # Normalizza i budget per mostrare la percentuale di rischio allocata
                    normalized_budgets = {}
                    total_budget = sum(risk_budgets.values())
                    
                    if total_budget > 0:
                        for symbol, budget in risk_budgets.items():
                            normalized_budgets[symbol] = (budget / total_budget) * 100
                    
                    # Mostra la distribuzione dei risk budget
                    budget_data = []
                    for symbol, budget_pct in normalized_budgets.items():
                        budget_data.append({
                            'Asset': symbol,
                            'Risk Budget': f"{risk_budgets[symbol]:.1f}",
                            'Rischio (%)': f"{budget_pct:.1f}%"
                        })
                    
                    # Aggiungi XEON (escluso da risk budgeting)
                    budget_data.append({
                        'Asset': cash_asset,
                        'Risk Budget': "N/A",
                        'Rischio (%)': "Risk-free"
                    })
                    
                    if budget_data:
                        budget_df = pd.DataFrame(budget_data)
                        st.dataframe(budget_df, use_container_width=True, hide_index=True)
                    
                    # Informazioni sui vincoli
                    st.write("**Vincoli Attivi:**")
                    if use_volatility_target and target_volatility:
                        st.info(f"🎯 Volatilità target: {target_volatility*100:.1f}%")
                        st.caption("I pesi verranno calcolati automaticamente per raggiungere la volatilità target")
                    else:
                        st.info(f"💰 Cash fisso: {current_cash_target*100:.1f}%")
                        st.caption("Il cash ha un peso fisso, i risk budget si applicano alla parte investita")
                    
                    st.info(f"📊 Max esposizione: {current_max_exposure*100:.1f}% (eccetto SWDA e XEON)")
                    st.caption("Gli ETF con esposizione > limite allocano l'eccesso a SWDA")
                
                # Pulsanti per gestire Risk Budget
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 Ricalcola HERC", use_container_width=True,
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
                    
                    # Aggiungi il cash (fisso o variabile) al riassunto
                    if use_volatility_target and target_volatility:
                        current_xeon_weight = st.session_state.current_weights.get(cash_asset, 0.0)
                        summary_data.append({
                            'Asset': cash_asset + " (Variabile)",
                            'Peso (%)': f"{current_xeon_weight*100:.1f}%"
                        })
                    else:
                        summary_data.append({
                            'Asset': cash_asset + " (Fisso)",
                            'Peso (%)': f"{current_cash_target*100:.1f}%"
                        })
                    
                    if summary_data:
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # Pulsanti per gestire Risk Budget
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔄 Ricalcola HERC", use_container_width=True, 
                                help="Ricalcola l'ottimizzazione HERC con i nuovi Risk Budget"):
                        # Aggiorna i risk budgets nello stato
                        st.session_state.risk_budgets = risk_budgets
                        
                        # Verifica se abbiamo i dati necessari
                        if st.session_state.portfolio_results and st.session_state.portfolio_results.get('returns') is not None:
                            # Ricalcola con i nuovi risk budget
                            optimizer = PortfolioOptimizer(
                                cash_target=current_cash_target,
                                max_exposure=current_max_exposure,
                                use_volatility_target=use_volatility_target,
                                target_volatility=target_volatility,
                                risk_budgets=risk_budgets  # Passa i risk budget all'optimizer
                            )
                            
                            # Re-run HERC con i nuovi risk budget
                            returns_data = st.session_state.portfolio_results['returns']
                            results = optimizer.herc_optimization(returns_data.dropna())
                            
                            if results:
                                # Aggiorna i risultati nello stato
                                st.session_state.portfolio_results['weights_history'] = results['weights_history']
                                st.session_state.current_weights = optimizer.get_latest_weights()
                                
                                st.success("✅ HERC ricalcolato con i nuovi Risk Budget!")
                                st.rerun()
                            else:
                                st.error("❌ Errore nel ricalcolo HERC")
                        else:
                            st.error("❌ Esegui prima l'ottimizzazione HERC per poter ricalcolare")
                
                with col2:
                    if st.button("↩️ Reset Budget", use_container_width=True,
                                help="Ripristina tutti i Risk Budget a 1.0 (allocazione uniforme)"):
                        # Reset tutti i budget a 1.0
                        st.session_state.risk_budgets = {symbol: 1.0 for symbol in investment_symbols.keys()}
                        st.success("🔄 Risk Budget ripristinati!")
                        st.rerun()
                
                with col3:
                    if st.button("💾 Salva Budget", use_container_width=True,
                                help="Salva la configurazione attuale dei Risk Budget"):
                        # Esporta i risk budget attuali
                        budget_export = pd.DataFrame([
                            {
                                'ETF': symbol,
                                'Nome': investment_symbols[symbol],
                                'Risk_Budget': budget,
                                'Rischio_Pct': f"{(budget / sum(risk_budgets.values()) * 100):.1f}%"
                            }
                            for symbol, budget in risk_budgets.items()
                        ])
                        
                        csv_data = budget_export.to_csv(index=False)
                        st.download_button(
                            label="📊 Download Risk Budget CSV",
                            data=csv_data,
                            file_name="risk_budgets_configuration.csv",
                            mime="text/csv"
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
                                # Determina se stiamo usando volatilità target
                                use_vol_target = benchmark_weights_dict.get('approach') == 'volatility_target'
                                
                                if use_vol_target:
                                    # Modalità volatilità target - mostra info dinamica
                                    target_vol = benchmark_weights_dict.get('target_volatility', 0) * 100
                                    st.info(f"🎯 **Benchmark con Volatilità Target: {target_vol:.1f}%**")
                                    st.write("📊 **Pesi Dinamici (esempio medio):**")
                                    
                                    # Mostra i pesi come informazione
                                    benchmark_df = pd.DataFrame({
                                        'Asset': ['SWDA.MI', 'XEON.MI'],
                                        'Composizione': [
                                            f"Variabile (target vol {target_vol:.1f}%)",
                                            f"Variabile (target vol {target_vol:.1f}%)"
                                        ]
                                    })
                                else:
                                    # Modalità cash fisso - mostra pesi fissi
                                    cash_pct = benchmark_weights_dict.get('cash_target', cash_target) * 100
                                    st.info(f"💰 **Benchmark con Cash Fisso: {cash_pct:.1f}%**")
                                    
                                    # Rimuovi le chiavi di configurazione e mostra solo i pesi
                                    weight_keys = [k for k in benchmark_weights_dict.keys() 
                                                 if k not in ['approach', 'cash_target', 'target_volatility']]
                                    if weight_keys:
                                        benchmark_weights = pd.Series({k: benchmark_weights_dict[k] for k in weight_keys})
                                        benchmark_df = pd.DataFrame({
                                            'Asset': benchmark_weights.index,
                                            'Peso (%)': (benchmark_weights.values * 100).round(2)
                                        })
                                    else:
                                        benchmark_df = pd.DataFrame({
                                            'Asset': ['SWDA.MI', 'XEON.MI'],
                                            'Peso (%)': [100 - cash_pct, cash_pct]
                                        })
                                
                                st.dataframe(benchmark_df, use_container_width=True, hide_index=True)
                            else:
                                st.info("Nessun peso benchmark disponibile")
                        
                        with col_bench2:
                            # Grafico a torta del benchmark
                            benchmark_weights_dict = st.session_state.portfolio_results.get('benchmark_weights', {})
                            if benchmark_weights_dict:
                                use_vol_target = benchmark_weights_dict.get('approach') == 'volatility_target'
                                
                                if use_vol_target:
                                    # Per volatilità target, mostra un grafico indicativo
                                    target_vol = benchmark_weights_dict.get('target_volatility', 0) * 100
                                    # Pesi indicativi per il grafico (60% SWDA, 40% XEON come esempio)
                                    example_weights = pd.Series({'SWDA.MI': 0.6, 'XEON.MI': 0.4})
                                    benchmark_fig = create_weights_pie_chart(
                                        example_weights, 
                                        f"Benchmark (Vol Target {target_vol:.1f}% - Esempio)"
                                    )
                                else:
                                    # Cash fisso - usa i pesi reali
                                    weight_keys = [k for k in benchmark_weights_dict.keys() 
                                                 if k not in ['approach', 'cash_target', 'target_volatility']]
                                    if weight_keys:
                                        benchmark_weights = pd.Series({k: benchmark_weights_dict[k] for k in weight_keys})
                                    else:
                                        cash_pct = benchmark_weights_dict.get('cash_target', cash_target)
                                        benchmark_weights = pd.Series({'SWDA.MI': 1-cash_pct, 'XEON.MI': cash_pct})
                                    
                                    benchmark_fig = create_weights_pie_chart(
                                        benchmark_weights, 
                                        f"Benchmark (Cash {cash_target*100:.0f}%)"
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

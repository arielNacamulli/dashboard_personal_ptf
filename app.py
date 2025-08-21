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
from src.config import get_etf_symbols, get_etf_info
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
            options=['1y', '2y', '3y', '5y', 'max'],
            index=3,
            format_func=lambda x: {
                '1y': '1 Anno',
                '2y': '2 Anni', 
                '3y': '3 Anni',
                '5y': '5 Anni',
                'max': 'Massimo disponibile'
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
                                st.write(f"• Completezza: {summary['completeness']}")
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
            
            # Pulsante per ottimizzare
            if st.button("🎯 Ottimizza Portfolio", use_container_width=True):
                with st.spinner("Ottimizzazione in corso..."):
                    try:
                        optimizer = PortfolioOptimizer()
                        
                        # Esegui backtest
                        portfolio_results = optimizer.backtest_portfolio(
                            st.session_state.returns_data,
                            method=algorithm.lower(),
                            rebalance_freq=rebalance_freq
                        )
                        
                        # Ottieni i pesi più recenti
                        latest_weights = optimizer.get_latest_weights()
                        
                        # Salva i risultati
                        st.session_state.portfolio_results = {
                            'backtest': portfolio_results,
                            'weights_history': optimizer.weights_history,
                            'rebalance_dates': optimizer.get_rebalance_dates(),
                            'algorithm': algorithm,
                            'rebalance_freq': rebalance_freq
                        }
                        st.session_state.current_weights = latest_weights
                        
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
                
                # Grafico performance principale
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    backtest_data = results['backtest']
                    if not backtest_data.empty:
                        fig_performance = create_performance_chart(
                            backtest_data['portfolio_returns'],
                            title=f"Performance Cumulativa - {results['algorithm']}"
                        )
                        st.plotly_chart(fig_performance, use_container_width=True)
                
                with col2:
                    # Sommario performance
                    if not backtest_data.empty:
                        metrics_calc = PerformanceMetrics()
                        portfolio_metrics = metrics_calc.calculate_all_metrics(backtest_data['portfolio_returns'])
                        
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
                        st.info(f"📅 Ultimo ribilanciamento: {last_rebalance.strftime('%Y-%m-%d')}")
                
                # Evoluzione pesi nel tempo
                if st.session_state.portfolio_results:
                    st.subheader("Evoluzione Pesi nel Tempo")
                    fig_weights_evolution = create_weights_evolution_chart(
                        st.session_state.portfolio_results['weights_history']
                    )
                    st.plotly_chart(fig_weights_evolution, use_container_width=True)
                
                # Pulsante per scaricare i pesi
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("💾 Scarica Pesi", use_container_width=True):
                        weights_export = {
                            'Current Weights': pd.DataFrame({
                                'ETF': st.session_state.current_weights.index,
                                'Weight': st.session_state.current_weights.values
                            })
                        }
                        
                        excel_data = export_to_excel(weights_export, "portfolio_weights.xlsx")
                        st.download_button(
                            label="📊 Download Excel",
                            data=excel_data,
                            file_name="portfolio_weights.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.info("🎯 Esegui l'ottimizzazione per vedere l'allocazione del portfolio")
        
        with tab3:
            st.subheader("Metriche di Performance")
            
            if st.session_state.portfolio_results:
                backtest_data = st.session_state.portfolio_results['backtest']
                
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

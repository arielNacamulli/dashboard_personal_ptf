"""
Funzioni di utilità per l'analisi del portafoglio
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Tuple
import io
import base64

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formatta un numero come percentuale
    
    Args:
        value: Valore da formattare
        decimals: Numero di decimali
        
    Returns:
        Stringa formattata
    """
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"

def format_number(value: float, decimals: int = 4) -> str:
    """
    Formatta un numero con decimali
    
    Args:
        value: Valore da formattare
        decimals: Numero di decimali
        
    Returns:
        Stringa formattata
    """
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.{decimals}f}"

def create_performance_chart(portfolio_returns: pd.Series, 
                           benchmark_returns: pd.Series = None,
                           title: str = "Portfolio Performance") -> go.Figure:
    """
    Crea un grafico delle performance cumulative
    
    Args:
        portfolio_returns: Rendimenti del portafoglio
        benchmark_returns: Rendimenti del benchmark (opzionale)
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    fig = go.Figure()
    
    # Calcola i rendimenti cumulativi
    cumulative_returns = (1 + portfolio_returns).cumprod() - 1
    
    # Linea del portafoglio
    fig.add_trace(go.Scatter(
        x=cumulative_returns.index,
        y=cumulative_returns.values * 100,
        mode='lines',
        name='Portfolio',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Aggiungi benchmark se fornito
    if benchmark_returns is not None:
        benchmark_cumulative = (1 + benchmark_returns).cumprod() - 1
        fig.add_trace(go.Scatter(
            x=benchmark_cumulative.index,
            y=benchmark_cumulative.values * 100,
            mode='lines',
            name='Benchmark',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Cumulative Return (%)",
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_weights_pie_chart(weights: pd.Series, title: str = "Portfolio Weights") -> go.Figure:
    """
    Crea un grafico a torta dei pesi del portafoglio
    
    Args:
        weights: Serie con i pesi
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    # Filtra pesi molto piccoli per chiarezza
    significant_weights = weights[weights > 0.01]  # Mostra solo pesi > 1%
    
    # Raggruppa i pesi piccoli in "Others"
    others_weight = weights[weights <= 0.01].sum()
    if others_weight > 0:
        significant_weights = pd.concat([significant_weights, pd.Series([others_weight], index=['Others'])])
    
    fig = go.Figure(data=[go.Pie(
        labels=significant_weights.index,
        values=significant_weights.values * 100,
        hole=0.3,
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True,
        template='plotly_white'
    )
    
    return fig

def create_drawdown_chart(returns: pd.Series, title: str = "Drawdown Analysis") -> go.Figure:
    """
    Crea un grafico dei drawdown
    
    Args:
        returns: Serie dei rendimenti
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    # Calcola i drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max * 100
    
    fig = go.Figure()
    
    # Area del drawdown
    fig.add_trace(go.Scatter(
        x=drawdown.index,
        y=drawdown.values,
        fill='tonexty',
        mode='lines',
        name='Drawdown',
        line=dict(color='red', width=1),
        fillcolor='rgba(255, 0, 0, 0.3)'
    ))
    
    # Linea dello zero
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_risk_return_scatter(metrics_dict: Dict, title: str = "Risk-Return Profile") -> go.Figure:
    """
    Crea uno scatter plot rischio-rendimento
    
    Args:
        metrics_dict: Dizionario con le metriche per asset
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    assets = list(metrics_dict.keys())
    returns = [metrics_dict[asset]['Annualized Return'] * 100 for asset in assets]
    volatilities = [metrics_dict[asset]['Annualized Volatility'] * 100 for asset in assets]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=volatilities,
        y=returns,
        mode='markers+text',
        text=assets,
        textposition='top center',
        marker=dict(
            size=12,
            color='blue',
            opacity=0.7
        ),
        name='Assets'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Volatility (%)",
        yaxis_title="Return (%)",
        template='plotly_white'
    )
    
    return fig

def create_correlation_heatmap(correlation_matrix: pd.DataFrame, 
                             title: str = "Correlation Matrix") -> go.Figure:
    """
    Crea una heatmap delle correlazioni
    
    Args:
        correlation_matrix: Matrice di correlazione
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.index,
        colorscale='RdBu',
        zmid=0,
        text=correlation_matrix.round(2).values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate="<b>%{y} vs %{x}</b><br>Correlation: %{z:.3f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=title,
        template='plotly_white'
    )
    
    return fig

def create_rolling_metrics_chart(rolling_metrics: pd.DataFrame, 
                                metric: str = 'Sharpe Ratio',
                                title: str = None) -> go.Figure:
    """
    Crea un grafico delle metriche rolling
    
    Args:
        rolling_metrics: DataFrame con le metriche rolling
        metric: Metrica da visualizzare
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    if title is None:
        title = f"Rolling {metric} (1 Year Window)"
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=rolling_metrics.index,
        y=rolling_metrics[metric],
        mode='lines',
        name=metric,
        line=dict(color='#2E86AB', width=2)
    ))
    
    # Aggiungi una linea di riferimento se appropriato
    if metric == 'Sharpe Ratio':
        fig.add_hline(y=1, line_dash="dash", line_color="green", 
                     annotation_text="Good (>1)", opacity=0.7)
        fig.add_hline(y=0, line_dash="dash", line_color="red", 
                     annotation_text="Poor (<0)", opacity=0.7)
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=metric,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_weights_evolution_chart(weights_history: List[Dict], 
                                 title: str = "Portfolio Weights Evolution") -> go.Figure:
    """
    Crea un grafico dell'evoluzione dei pesi nel tempo
    
    Args:
        weights_history: Lista con la storia dei pesi
        title: Titolo del grafico
        
    Returns:
        Figura Plotly
    """
    if not weights_history:
        return go.Figure()
    
    # Estrai le date e i pesi
    dates = [entry['date'] for entry in weights_history]
    assets = weights_history[0]['weights'].index.tolist()
    
    fig = go.Figure()
    
    # Colori per gli asset
    colors = px.colors.qualitative.Set3
    
    for i, asset in enumerate(assets):
        weights = [entry['weights'][asset] * 100 for entry in weights_history]
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=weights,
            mode='lines+markers',
            name=asset,
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Rebalance Date",
        yaxis_title="Weight (%)",
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def export_to_excel(data_dict: Dict[str, pd.DataFrame], filename: str = "portfolio_analysis.xlsx") -> bytes:
    """
    Esporta i dati in un file Excel
    
    Args:
        data_dict: Dizionario con i DataFrame da esportare
        filename: Nome del file
        
    Returns:
        Bytes del file Excel
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=True)
    
    return output.getvalue()

def create_download_button(data: bytes, filename: str, label: str) -> str:
    """
    Crea un pulsante di download per Streamlit
    
    Args:
        data: Dati da scaricare
        filename: Nome del file
        label: Etichetta del pulsante
        
    Returns:
        HTML per il pulsante di download
    """
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    return href

def validate_date_range(start_date, end_date, data_index) -> Tuple[bool, str]:
    """
    Valida un range di date rispetto ai dati disponibili
    
    Args:
        start_date: Data di inizio
        end_date: Data di fine
        data_index: Indice dei dati disponibili
        
    Returns:
        Tupla (is_valid, message)
    """
    if start_date >= end_date:
        return False, "La data di inizio deve essere precedente alla data di fine"
    
    if start_date < data_index.min():
        return False, f"Data di inizio troppo antica. Prima data disponibile: {data_index.min().strftime('%Y-%m-%d')}"
    
    if end_date > data_index.max():
        return False, f"Data di fine troppo recente. Ultima data disponibile: {data_index.max().strftime('%Y-%m-%d')}"
    
    return True, "Range di date valido"

def calculate_portfolio_summary(returns: pd.Series, weights: pd.Series) -> Dict:
    """
    Calcola un riassunto del portafoglio
    
    Args:
        returns: Rendimenti del portafoglio
        weights: Pesi attuali
        
    Returns:
        Dizionario con il riassunto
    """
    if len(returns) == 0:
        return {}
    
    total_return = (1 + returns).prod() - 1
    latest_value = (1 + returns).cumprod().iloc[-1]
    
    return {
        'Total Assets': len(weights),
        'Portfolio Value': f"€{latest_value:,.2f}" if latest_value > 0 else "€1.00",
        'Total Return': format_percentage(total_return),
        'Active Positions': len(weights[weights > 0.001]),
        'Largest Position': f"{weights.max():.1%} ({weights.idxmax()})",
        'Smallest Position': f"{weights.min():.1%} ({weights.idxmin()})"
    }

def create_metrics_table(metrics: Dict) -> pd.DataFrame:
    """
    Crea una tabella formattata delle metriche
    
    Args:
        metrics: Dizionario con le metriche
        
    Returns:
        DataFrame formattato
    """
    formatted_metrics = {}
    
    for key, value in metrics.items():
        if 'Return' in key or 'Volatility' in key or 'Drawdown' in key or 'VaR' in key or 'CVaR' in key:
            formatted_metrics[key] = format_percentage(value)
        elif 'Ratio' in key or 'Beta' in key:
            formatted_metrics[key] = format_number(value, 3)
        else:
            formatted_metrics[key] = format_number(value, 4)
    
    return pd.DataFrame(list(formatted_metrics.items()), columns=['Metric', 'Value'])

def get_color_palette(n_colors: int) -> List[str]:
    """
    Ottieni una palette di colori per i grafici
    
    Args:
        n_colors: Numero di colori necessari
        
    Returns:
        Lista di colori in formato hex
    """
    if n_colors <= 10:
        return px.colors.qualitative.Set3[:n_colors]
    else:
        # Per più di 10 colori, usa una combinazione di palette
        colors = []
        palettes = [px.colors.qualitative.Set3, px.colors.qualitative.Pastel, px.colors.qualitative.Set2]
        
        for i in range(n_colors):
            palette_idx = i // 10
            color_idx = i % 10
            if palette_idx < len(palettes):
                colors.append(palettes[palette_idx][color_idx % len(palettes[palette_idx])])
            else:
                # Fallback per molti colori
                colors.append(f"hsl({(i * 137.5) % 360}, 70%, 50%)")
        
        return colors

"""
Data loader per il download e la gestione dei dati ETF
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import List, Dict, Tuple
import logging
from .config import ETF_SYMBOLS, get_etf_name

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETFDataLoader:
    """Classe per il download e la gestione dei dati ETF"""
    
    def __init__(self):
        self.etf_symbols = ETF_SYMBOLS
        self.data_cache = {}
        
    @st.cache_data(ttl=3600)  # Cache per 1 ora
    def download_etf_data(_self, symbols: List[str], period: str = "5y") -> pd.DataFrame:
        """
        Download dei dati storici ETF con caching
        
        Args:
            symbols: Lista dei simboli ETF
            period: Periodo di download (1y, 2y, 5y, 10y, max)
            
        Returns:
            DataFrame con i prezzi adjusted close
        """
        try:
            logger.info(f"Downloading data for symbols: {symbols}")
            
            # Download dati tramite yfinance
            data = yf.download(
                symbols, 
                period=period,
                progress=False,
                auto_adjust=True,  # Prezzi aggiustati automaticamente
                group_by='ticker'
            )
            
            if len(symbols) == 1:
                # Per un singolo simbolo, yfinance restituisce una struttura diversa
                prices = data['Close'].to_frame()
                prices.columns = symbols
            else:
                # Estrai solo i prezzi di chiusura aggiustati
                prices = data.xs('Close', level=1, axis=1)
                
            # Rimuovi i NaN e ordina per data
            prices = prices.dropna()
            prices.index = pd.to_datetime(prices.index)
            prices = prices.sort_index()
            
            logger.info(f"Successfully downloaded {len(prices)} days of data")
            return prices
            
        except Exception as e:
            logger.error(f"Error downloading data: {str(e)}")
            st.error(f"Errore nel download dei dati: {str(e)}")
            return pd.DataFrame()
    
    def calculate_returns(self, prices: pd.DataFrame, method: str = "log") -> pd.DataFrame:
        """
        Calcola i rendimenti dai prezzi
        
        Args:
            prices: DataFrame con i prezzi
            method: Metodo di calcolo ("log" o "simple")
            
        Returns:
            DataFrame con i rendimenti
        """
        if method == "log":
            returns = np.log(prices / prices.shift(1))
        else:
            returns = prices.pct_change()
            
        return returns.dropna()
    
    def get_etf_info(self, symbol: str) -> Dict:
        """
        Ottieni informazioni su un ETF
        
        Args:
            symbol: Simbolo dell'ETF
            
        Returns:
            Dizionario con le informazioni
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'name': info.get('longName', get_etf_name(symbol)),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'N/A'),
                'expense_ratio': info.get('annualReportExpenseRatio', 'N/A'),
                'net_assets': info.get('totalAssets', 'N/A')
            }
        except Exception as e:
            logger.warning(f"Could not get info for {symbol}: {str(e)}")
            return {
                'name': get_etf_name(symbol),
                'currency': 'USD',
                'exchange': 'N/A',
                'expense_ratio': 'N/A',
                'net_assets': 'N/A'
            }
    
    def validate_data(self, data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Valida la qualità dei dati scaricati
        
        Args:
            data: DataFrame con i dati
            
        Returns:
            Tupla (is_valid, message)
        """
        if data.empty:
            return False, "Dati vuoti"
        
        if data.isna().sum().sum() > 0:
            missing_pct = (data.isna().sum().sum() / (len(data) * len(data.columns))) * 100
            if missing_pct > 5:  # Più del 5% di dati mancanti
                return False, f"Troppi dati mancanti: {missing_pct:.1f}%"
        
        # Verifica che ci siano almeno 252 giorni di trading (1 anno)
        if len(data) < 252:
            return False, f"Dati insufficienti: solo {len(data)} giorni disponibili"
        
        return True, "Dati validi"
    
    def resample_to_monthly(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Ricampiona i dati su base mensile (fine mese)
        
        Args:
            data: DataFrame con dati giornalieri
            
        Returns:
            DataFrame con dati mensili
        """
        return data.resample('M').last()
    
    def get_data_summary(self, data: pd.DataFrame) -> Dict:
        """
        Ottieni un riassunto dei dati
        
        Args:
            data: DataFrame con i dati
            
        Returns:
            Dizionario con le statistiche
        """
        return {
            'start_date': data.index.min().strftime('%Y-%m-%d'),
            'end_date': data.index.max().strftime('%Y-%m-%d'),
            'num_observations': len(data),
            'num_assets': len(data.columns),
            'missing_values': data.isna().sum().sum(),
            'completeness': f"{((len(data) - data.isna().sum().sum()) / (len(data) * len(data.columns))) * 100:.1f}%"
        }

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
            # Pulisci le discontinuità nei prezzi
            prices = _self.clean_price_discontinuities(prices)
            
            logger.info(f"Successfully downloaded {len(prices)} days of data")
            return prices
            
        except Exception as e:
            logger.error(f"Error downloading data: {str(e)}")
            st.error(f"Errore nel download dei dati: {str(e)}")
            return pd.DataFrame()
    
    def clean_price_discontinuities(self, data: pd.DataFrame, threshold: float = 0.50) -> pd.DataFrame:
        """
        Pulisce le discontinuità nei prezzi causate da split non aggiustati
        
        Args:
            data: DataFrame con i prezzi
            threshold: Soglia per identificare discontinuità (es. 0.50 = 50%)
            
        Returns:
            DataFrame con i prezzi puliti
        """
        cleaned_data = data.copy()
        
        for column in cleaned_data.columns:
            series = cleaned_data[column].dropna()
            if len(series) < 2:
                continue
                
            # Calcola i rendimenti giornalieri
            returns = series.pct_change().dropna()
            
            # Identifica discontinuità significative
            extreme_returns = returns[(returns > threshold) | (returns < -threshold)]
            
            if not extreme_returns.empty:
                logger.warning(f"Discontinuità rilevate in {column}: {len(extreme_returns)} casi")
                
                # Per ogni discontinuità, aggiusta i prezzi precedenti
                for date in extreme_returns.index:
                    return_value = extreme_returns[date]
                    
                    # Se è un calo drastico (probabile split), aggiusta i dati precedenti
                    if return_value < -threshold:
                        # Calcola il fattore di aggiustamento
                        price_after = series[date]
                        price_before = series[:date].iloc[-2] if len(series[:date]) > 1 else None
                        
                        if price_before is not None:
                            adjustment_factor = price_after / price_before
                            
                            # Aggiusta tutti i prezzi precedenti moltiplicando per il fattore
                            mask = cleaned_data.index < date
                            cleaned_data.loc[mask, column] *= adjustment_factor
                            
                            logger.info(f"Aggiustato {column} prima del {date.date()} con fattore {adjustment_factor:.4f}")
        
        return cleaned_data
    
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
        Ottieni un riassunto dei dati con dettagli per ETF
        
        Args:
            data: DataFrame con i dati
            
        Returns:
            Dizionario con le statistiche dettagliate
        """
        # Calcola completezza per ogni ETF
        etf_completeness = {}
        total_rows = len(data)
        
        for column in data.columns:
            valid_data = data[column].dropna()
            completeness_pct = (len(valid_data) / total_rows) * 100 if total_rows > 0 else 0
            etf_completeness[column] = {
                'completeness': completeness_pct,
                'valid_observations': len(valid_data),
                'missing_observations': total_rows - len(valid_data),
                'first_valid_date': valid_data.index.min().strftime('%Y-%m-%d') if len(valid_data) > 0 else 'N/A',
                'last_valid_date': valid_data.index.max().strftime('%Y-%m-%d') if len(valid_data) > 0 else 'N/A'
            }
        
        # Trova gli ETF più problematici
        problematic_etfs = []
        for etf, stats in etf_completeness.items():
            if stats['completeness'] < 50:  # Meno del 50% di dati
                problematic_etfs.append({
                    'symbol': etf,
                    'name': get_etf_name(etf),
                    'completeness': f"{stats['completeness']:.1f}%",
                    'first_date': stats['first_valid_date'],
                    'missing': stats['missing_observations']
                })
        
        # Ordina per completezza crescente
        problematic_etfs.sort(key=lambda x: float(x['completeness'].replace('%', '')))
        
        # Completezza globale
        total_possible_values = len(data) * len(data.columns)
        total_valid_values = total_possible_values - data.isna().sum().sum()
        global_completeness = (total_valid_values / total_possible_values) * 100 if total_possible_values > 0 else 0
        
        return {
            'start_date': data.index.min().strftime('%Y-%m-%d'),
            'end_date': data.index.max().strftime('%Y-%m-%d'),
            'num_observations': len(data),
            'num_assets': len(data.columns),
            'missing_values': data.isna().sum().sum(),
            'completeness': f"{global_completeness:.1f}%",
            'etf_completeness': etf_completeness,
            'problematic_etfs': problematic_etfs
        }

"""
Calcolo delle metriche di performance per l'analisi di portafoglio
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

class PerformanceMetrics:
    """Classe per il calcolo delle metriche di performance"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Inizializza la classe con il tasso risk-free
        
        Args:
            risk_free_rate: Tasso risk-free annualizzato (default 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def annualized_return(self, returns: pd.Series) -> float:
        """
        Calcola il rendimento annualizzato
        
        Args:
            returns: Serie dei rendimenti
            
        Returns:
            Rendimento annualizzato
        """
        if len(returns) == 0:
            return 0.0
        
        # Numero di osservazioni per anno (assumendo dati giornalieri)
        periods_per_year = 252
        n_periods = len(returns)
        
        # Calcola il rendimento composto
        cumulative_return = (1 + returns).prod() - 1
        
        # Annualizza
        years = n_periods / periods_per_year
        if years > 0:
            annualized = (1 + cumulative_return) ** (1 / years) - 1
        else:
            annualized = 0.0
        
        return annualized
    
    def annualized_volatility(self, returns: pd.Series) -> float:
        """
        Calcola la volatilità annualizzata
        
        Args:
            returns: Serie dei rendimenti
            
        Returns:
            Volatilità annualizzata
        """
        if len(returns) == 0:
            return 0.0
        
        # Volatilità giornaliera
        daily_vol = returns.std()
        
        # Annualizza (assumendo 252 giorni di trading)
        annual_vol = daily_vol * np.sqrt(252)
        
        return annual_vol
    
    def sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """
        Calcola il Sharpe Ratio
        
        Args:
            returns: Serie dei rendimenti
            risk_free_rate: Tasso risk-free (se None usa quello della classe)
            
        Returns:
            Sharpe Ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0:
            return 0.0
        
        annual_return = self.annualized_return(returns)
        annual_vol = self.annualized_volatility(returns)
        
        if annual_vol == 0:
            return 0.0
        
        return (annual_return - risk_free_rate) / annual_vol
    
    def sortino_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """
        Calcola il Sortino Ratio (considera solo la volatilità negativa)
        
        Args:
            returns: Serie dei rendimenti
            risk_free_rate: Tasso risk-free
            
        Returns:
            Sortino Ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate
        
        if len(returns) == 0:
            return 0.0
        
        annual_return = self.annualized_return(returns)
        
        # Calcola la downside deviation
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return np.inf if annual_return > risk_free_rate else 0.0
        
        downside_deviation = negative_returns.std() * np.sqrt(252)
        
        if downside_deviation == 0:
            return 0.0
        
        return (annual_return - risk_free_rate) / downside_deviation
    
    def maximum_drawdown(self, returns: pd.Series) -> Tuple[float, pd.Timestamp, pd.Timestamp]:
        """
        Calcola il Maximum Drawdown
        
        Args:
            returns: Serie dei rendimenti
            
        Returns:
            Tupla (max_drawdown, start_date, end_date)
        """
        if len(returns) == 0:
            return 0.0, None, None
        
        # Calcola la curva dei valori cumulativi
        cumulative = (1 + returns).cumprod()
        
        # Calcola il running maximum
        running_max = cumulative.cummax()
        
        # Calcola il drawdown
        drawdown = (cumulative - running_max) / running_max
        
        # Trova il massimo drawdown
        max_dd = drawdown.min()
        
        # Trova le date di inizio e fine del massimo drawdown
        max_dd_date = drawdown.idxmin()
        
        # Trova la data di inizio (ultimo massimo prima del drawdown)
        start_date = running_max.loc[:max_dd_date].idxmax()
        
        return max_dd, start_date, max_dd_date
    
    def calmar_ratio(self, returns: pd.Series) -> float:
        """
        Calcola il Calmar Ratio (rendimento annualizzato / massimo drawdown)
        
        Args:
            returns: Serie dei rendimenti
            
        Returns:
            Calmar Ratio
        """
        annual_return = self.annualized_return(returns)
        max_dd, _, _ = self.maximum_drawdown(returns)
        
        if max_dd == 0:
            return np.inf if annual_return > 0 else 0.0
        
        return abs(annual_return / max_dd)
    
    def value_at_risk(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calcola il Value at Risk (VaR)
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza (default 5%)
            
        Returns:
            VaR
        """
        if len(returns) == 0:
            return 0.0
        
        return np.percentile(returns, confidence_level * 100)
    
    def conditional_var(self, returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calcola il Conditional VaR (Expected Shortfall)
        
        Args:
            returns: Serie dei rendimenti
            confidence_level: Livello di confidenza
            
        Returns:
            CVaR
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.value_at_risk(returns, confidence_level)
        return returns[returns <= var].mean()
    
    def information_ratio(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calcola l'Information Ratio rispetto ad un benchmark
        
        Args:
            portfolio_returns: Rendimenti del portafoglio
            benchmark_returns: Rendimenti del benchmark
            
        Returns:
            Information Ratio
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0
        
        # Allinea le serie temporali
        aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')
        
        if len(aligned_portfolio) == 0:
            return 0.0
        
        # Calcola l'excess return
        excess_returns = aligned_portfolio - aligned_benchmark
        
        # Information ratio = media excess return / std excess return
        if excess_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    def beta(self, portfolio_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        Calcola il Beta rispetto al mercato
        
        Args:
            portfolio_returns: Rendimenti del portafoglio
            market_returns: Rendimenti del mercato
            
        Returns:
            Beta
        """
        # Allinea le serie temporali
        aligned_portfolio, aligned_market = portfolio_returns.align(market_returns, join='inner')
        
        if len(aligned_portfolio) < 2:
            return 1.0
        
        # Calcola la covarianza e la varianza
        covariance = np.cov(aligned_portfolio, aligned_market)[0, 1]
        market_variance = np.var(aligned_market)
        
        if market_variance == 0:
            return 1.0
        
        return covariance / market_variance
    
    def tracking_error(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calcola il Tracking Error
        
        Args:
            portfolio_returns: Rendimenti del portafoglio
            benchmark_returns: Rendimenti del benchmark
            
        Returns:
            Tracking Error annualizzato
        """
        # Allinea le serie temporali
        aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')
        
        if len(aligned_portfolio) == 0:
            return 0.0
        
        # Calcola l'excess return
        excess_returns = aligned_portfolio - aligned_benchmark
        
        # Tracking error = std dell'excess return annualizzato
        return excess_returns.std() * np.sqrt(252)
    
    def calculate_all_metrics(self, returns: pd.Series, benchmark_returns: pd.Series = None) -> Dict:
        """
        Calcola tutte le metriche di performance
        
        Args:
            returns: Serie dei rendimenti del portafoglio
            benchmark_returns: Serie dei rendimenti del benchmark (opzionale)
            
        Returns:
            Dizionario con tutte le metriche
        """
        if len(returns) == 0:
            return {}
        
        metrics = {
            'Total Return': (1 + returns).prod() - 1,
            'Annualized Return': self.annualized_return(returns),
            'Annualized Volatility': self.annualized_volatility(returns),
            'Sharpe Ratio': self.sharpe_ratio(returns),
            'Sortino Ratio': self.sortino_ratio(returns),
            'Calmar Ratio': self.calmar_ratio(returns),
            'Max Drawdown': self.maximum_drawdown(returns)[0],
            'VaR (5%)': self.value_at_risk(returns),
            'CVaR (5%)': self.conditional_var(returns),
        }
        
        # Aggiungi metriche relative al benchmark se fornito
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            metrics.update({
                'Information Ratio': self.information_ratio(returns, benchmark_returns),
                'Beta': self.beta(returns, benchmark_returns),
                'Tracking Error': self.tracking_error(returns, benchmark_returns)
            })
        
        return metrics
    
    def rolling_metrics(self, returns: pd.Series, window: int = 252) -> pd.DataFrame:
        """
        Calcola le metriche su base rolling
        
        Args:
            returns: Serie dei rendimenti
            window: Finestra temporale (default 1 anno = 252 giorni)
            
        Returns:
            DataFrame con le metriche rolling
        """
        if len(returns) < window:
            return pd.DataFrame()
        
        rolling_data = []
        
        for i in range(window, len(returns) + 1):
            period_returns = returns.iloc[i-window:i]
            
            metrics = {
                'Annualized Return': self.annualized_return(period_returns),
                'Annualized Volatility': self.annualized_volatility(period_returns),
                'Sharpe Ratio': self.sharpe_ratio(period_returns),
                'Max Drawdown': self.maximum_drawdown(period_returns)[0]
            }
            
            rolling_data.append(metrics)
        
        return pd.DataFrame(rolling_data, index=returns.index[window-1:])
    
    def performance_attribution(self, portfolio_returns: pd.Series, 
                              weights: pd.DataFrame, asset_returns: pd.DataFrame) -> pd.DataFrame:
        """
        Analisi di attribuzione della performance
        
        Args:
            portfolio_returns: Rendimenti del portafoglio
            weights: DataFrame con i pesi nel tempo
            asset_returns: DataFrame con i rendimenti degli asset
            
        Returns:
            DataFrame con l'attribuzione della performance
        """
        # Allinea le date
        common_dates = portfolio_returns.index.intersection(asset_returns.index)
        
        if len(common_dates) == 0:
            return pd.DataFrame()
        
        # Calcola il contributo di ogni asset
        contribution = pd.DataFrame(index=common_dates, columns=asset_returns.columns)
        
        for date in common_dates:
            if date in weights.index:
                daily_weights = weights.loc[date]
                daily_returns = asset_returns.loc[date]
                contribution.loc[date] = daily_weights * daily_returns
        
        return contribution.fillna(0)

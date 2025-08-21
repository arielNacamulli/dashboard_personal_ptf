"""
Implementazione degli algoritmi HERC e HRP per l'ottimizzazione di portafoglio
"""
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree
from scipy.spatial.distance import squareform
from sklearn.covariance import LedoitWolf
from .config import get_cash_asset, get_default_cash_target, get_default_max_exposure, is_exposure_exempt
import warnings
warnings.filterwarnings('ignore')

class PortfolioOptimizer:
    """Classe per l'ottimizzazione del portafoglio con algoritmi gerarchici"""
    
    def __init__(self, cash_target=None, max_exposure=None):
        """
        Inizializza l'ottimizzatore con parametri opzionali
        
        Args:
            cash_target: Percentuale fissa di cash da mantenere (es. 0.10 per 10%)
            max_exposure: Massima esposizione per singolo ETF (es. 0.30 per 30%)
        """
        self.weights_history = {}
        self.rebalance_dates = []
        self.cash_target = cash_target if cash_target is not None else get_default_cash_target()
        self.max_exposure = max_exposure if max_exposure is not None else get_default_max_exposure()
        
    def calculate_distance_matrix(self, correlation_matrix: pd.DataFrame) -> np.ndarray:
        """
        Calcola la matrice delle distanze dalla correlazione
        
        Args:
            correlation_matrix: Matrice di correlazione
            
        Returns:
            Matrice delle distanze
        """
        # Converte correlazione in distanza: d = sqrt(0.5 * (1 - corr))
        distance = np.sqrt(0.5 * (1 - correlation_matrix.values))
        np.fill_diagonal(distance, 0)
        return distance
    
    def hierarchical_clustering(self, distance_matrix: np.ndarray, method: str = 'ward') -> np.ndarray:
        """
        Esegue il clustering gerarchico
        
        Args:
            distance_matrix: Matrice delle distanze
            method: Metodo di linkage ('ward', 'single', 'complete', 'average')
            
        Returns:
            Matrice di linkage
        """
        # Converte in formato condensed per scipy
        condensed_distance = squareform(distance_matrix, checks=False)
        return linkage(condensed_distance, method=method)
    
    def get_cluster_variance(self, covariance_matrix: pd.DataFrame, cluster_items: list) -> float:
        """
        Calcola la varianza di un cluster
        
        Args:
            covariance_matrix: Matrice di covarianza
            cluster_items: Lista degli asset nel cluster
            
        Returns:
            Varianza del cluster
        """
        cluster_cov = covariance_matrix.iloc[cluster_items, cluster_items]
        # Portafoglio equipesato del cluster
        weights = np.ones(len(cluster_items)) / len(cluster_items)
        return np.dot(weights, np.dot(cluster_cov.values, weights))
    
    def recursive_bisection(self, linkage_matrix: np.ndarray, covariance_matrix: pd.DataFrame, 
                          asset_indices: list = None) -> dict:
        """
        Algoritmo ricorsivo di bisezione per HRP
        
        Args:
            linkage_matrix: Matrice di linkage del clustering
            covariance_matrix: Matrice di covarianza
            asset_indices: Indici degli asset (per ricorsione)
            
        Returns:
            Dizionario con i pesi
        """
        if asset_indices is None:
            asset_indices = list(range(len(covariance_matrix)))
        
        weights = pd.Series(1.0, index=asset_indices)
        
        if len(asset_indices) == 1:
            return weights
        
        # Trova il punto di split nel dendrogramma
        clusters = self._get_clusters_from_linkage(linkage_matrix, asset_indices)
        
        if len(clusters) < 2:
            # Se non possiamo dividere ulteriormente, pesi uguali
            weights[:] = 1.0 / len(asset_indices)
            return weights
        
        # Calcola la varianza di ogni cluster
        cluster_vars = []
        for cluster in clusters:
            cluster_var = self.get_cluster_variance(covariance_matrix, cluster)
            cluster_vars.append(cluster_var)
        
        # Alloca i pesi in base alla varianza inversa
        total_inv_var = sum(1.0 / var for var in cluster_vars)
        cluster_weights = [(1.0 / var) / total_inv_var for var in cluster_vars]
        
        # Ricorsione sui sottoclusters
        final_weights = pd.Series(0.0, index=asset_indices)
        for i, (cluster, cluster_weight) in enumerate(zip(clusters, cluster_weights)):
            if len(cluster) > 1:
                sub_weights = self.recursive_bisection(linkage_matrix, covariance_matrix, cluster)
                for asset in cluster:
                    final_weights[asset] = cluster_weight * sub_weights[asset]
            else:
                final_weights[cluster[0]] = cluster_weight
                
        return final_weights
    
    def _get_clusters_from_linkage(self, linkage_matrix: np.ndarray, asset_indices: list) -> list:
        """
        Estrae i cluster dalla matrice di linkage
        
        Args:
            linkage_matrix: Matrice di linkage
            asset_indices: Indici degli asset
            
        Returns:
            Lista di cluster
        """
        if len(asset_indices) <= 1:
            return [asset_indices]
        
        # Trova il miglior numero di cluster (2 per la bisezione)
        n_clusters = min(2, len(asset_indices))
        cluster_assignments = cut_tree(linkage_matrix, n_clusters=n_clusters).flatten()
        
        clusters = []
        for cluster_id in np.unique(cluster_assignments):
            cluster_assets = [asset_indices[i] for i in range(len(asset_indices)) 
                            if cluster_assignments[i] == cluster_id]
            if cluster_assets:
                clusters.append(cluster_assets)
        
        return clusters
    
    def apply_exposure_constraints(self, weights: pd.Series) -> pd.Series:
        """
        Applica i vincoli di massima esposizione agli ETF
        
        Args:
            weights: Serie con i pesi degli asset
            
        Returns:
            Serie con i pesi aggiustati secondo i vincoli
        """
        cash_asset = get_cash_asset()
        constrained_weights = weights.copy()
        
        # Applica il vincolo di massima esposizione
        for asset in constrained_weights.index:
            if asset != cash_asset and not is_exposure_exempt(asset):
                if constrained_weights[asset] > self.max_exposure:
                    constrained_weights[asset] = self.max_exposure
        
        # Normalizza i pesi degli investimenti (escludendo cash)
        investment_weights = constrained_weights.drop(cash_asset, errors='ignore')
        investment_sum = investment_weights.sum()
        
        if investment_sum > 0:
            # Calcola lo spazio disponibile per gli investimenti (1 - cash_target)
            available_for_investment = 1.0 - self.cash_target
            
            # Normalizza i pesi degli investimenti per riempire lo spazio disponibile
            normalized_investment_weights = investment_weights * (available_for_investment / investment_sum)
            
            # Aggiorna i pesi
            for asset in normalized_investment_weights.index:
                constrained_weights[asset] = normalized_investment_weights[asset]
        
        # Imposta il cash al target fisso
        constrained_weights[cash_asset] = self.cash_target
        
        return constrained_weights
    
    def hrp_optimization(self, returns: pd.DataFrame) -> pd.Series:
        """
        Implementa l'algoritmo HRP (Hierarchical Risk Parity)
        Con cash fisso e vincoli di massima esposizione
        
        Args:
            returns: DataFrame con i rendimenti degli asset
            
        Returns:
            Serie con i pesi ottimali (incluso cash asset)
        """
        cash_asset = get_cash_asset()
        
        # Filtra solo gli asset da investire (esclude cash)
        investment_returns = returns.drop(columns=[cash_asset], errors='ignore')
        
        if investment_returns.empty:
            # Se non ci sono asset da investire, tutto in cash
            weights = pd.Series(0.0, index=returns.columns)
            weights[cash_asset] = 1.0
            return weights
        
        # Calcola la matrice di correlazione
        correlation_matrix = investment_returns.corr()
        
        # Gestisci valori NaN nella correlazione
        correlation_matrix = correlation_matrix.fillna(0)
        
        # Calcola la matrice delle distanze
        distance_matrix = self.calculate_distance_matrix(correlation_matrix)
        
        # Clustering gerarchico
        linkage_matrix = self.hierarchical_clustering(distance_matrix)
        
        # Calcola la matrice di covarianza
        covariance_matrix = investment_returns.cov()
        
        # Ottimizzazione ricorsiva solo sugli asset da investire
        investment_weights = self.recursive_bisection(linkage_matrix, covariance_matrix)
        
        # Normalizza i pesi degli investimenti
        investment_weights = investment_weights / investment_weights.sum()
        
        # Crea i pesi iniziali
        final_weights = pd.Series(0.0, index=returns.columns)
        
        # Assegna i pesi degli investimenti (senza cash)
        for asset in investment_weights.index:
            final_weights[asset] = investment_weights[asset]
        
        # Applica vincoli di esposizione e cash fisso
        final_weights = self.apply_exposure_constraints(final_weights)
        
        return final_weights
    
    def herc_optimization(self, returns: pd.DataFrame) -> pd.Series:
        """
        Implementa l'algoritmo HERC (Hierarchical Equal Risk Contribution)
        Con cash fisso e vincoli di massima esposizione
        
        Args:
            returns: DataFrame con i rendimenti degli asset
            
        Returns:
            Serie con i pesi ottimali (incluso cash asset)
        """
        cash_asset = get_cash_asset()
        
        # Filtra solo gli asset da investire (esclude cash)
        investment_returns = returns.drop(columns=[cash_asset], errors='ignore')
        
        if investment_returns.empty:
            # Se non ci sono asset da investire, tutto in cash
            weights = pd.Series(0.0, index=returns.columns)
            weights[cash_asset] = 1.0
            return weights
        
        # Calcola la matrice di correlazione e covarianza
        correlation_matrix = investment_returns.corr().fillna(0)
        covariance_matrix = investment_returns.cov()
        
        # Calcola la matrice delle distanze
        distance_matrix = self.calculate_distance_matrix(correlation_matrix)
        
        # Clustering gerarchico
        linkage_matrix = self.hierarchical_clustering(distance_matrix)
        
        # Implementa HERC con equal risk contribution
        investment_weights = self._herc_recursive_allocation(linkage_matrix, covariance_matrix, investment_returns.columns.tolist())
        
        # Normalizza i pesi degli investimenti
        investment_weights = investment_weights / investment_weights.sum()
        
        # Crea i pesi iniziali
        final_weights = pd.Series(0.0, index=returns.columns)
        
        # Assegna i pesi degli investimenti (senza cash)
        for i, asset in enumerate(investment_returns.columns):
            final_weights[asset] = investment_weights[i]
        
        # Applica vincoli di esposizione e cash fisso
        final_weights = self.apply_exposure_constraints(final_weights)
        
        return final_weights
    
    def _herc_recursive_allocation(self, linkage_matrix: np.ndarray, covariance_matrix: pd.DataFrame, 
                                 assets: list) -> np.ndarray:
        """
        Allocazione ricorsiva per HERC
        
        Args:
            linkage_matrix: Matrice di linkage
            covariance_matrix: Matrice di covarianza
            assets: Lista degli asset
            
        Returns:
            Array con i pesi
        """
        n_assets = len(assets)
        weights = np.ones(n_assets) / n_assets
        
        if n_assets <= 1:
            return weights
        
        # Trova i cluster al livello superiore
        clusters = cut_tree(linkage_matrix, n_clusters=2).flatten()
        
        # Separa gli asset in due cluster
        cluster_0 = [i for i in range(n_assets) if clusters[i] == 0]
        cluster_1 = [i for i in range(n_assets) if clusters[i] == 1]
        
        if len(cluster_0) == 0 or len(cluster_1) == 0:
            return weights
        
        # Calcola il contributo al rischio di ogni cluster
        var_0 = self.get_cluster_variance(covariance_matrix, cluster_0)
        var_1 = self.get_cluster_variance(covariance_matrix, cluster_1)
        
        # Alloca i pesi inversamente proporzionali al rischio
        total_inv_risk = (1.0 / np.sqrt(var_0)) + (1.0 / np.sqrt(var_1))
        weight_0 = (1.0 / np.sqrt(var_0)) / total_inv_risk
        weight_1 = (1.0 / np.sqrt(var_1)) / total_inv_risk
        
        # Ricorsione sui sottoclusters
        if len(cluster_0) > 1:
            sub_linkage_0 = self._extract_sublinkage(linkage_matrix, cluster_0)
            sub_cov_0 = covariance_matrix.iloc[cluster_0, cluster_0]
            sub_assets_0 = [assets[i] for i in cluster_0]
            sub_weights_0 = self._herc_recursive_allocation(sub_linkage_0, sub_cov_0, sub_assets_0)
            for i, idx in enumerate(cluster_0):
                weights[idx] = weight_0 * sub_weights_0[i]
        else:
            weights[cluster_0[0]] = weight_0
            
        if len(cluster_1) > 1:
            sub_linkage_1 = self._extract_sublinkage(linkage_matrix, cluster_1)
            sub_cov_1 = covariance_matrix.iloc[cluster_1, cluster_1]
            sub_assets_1 = [assets[i] for i in cluster_1]
            sub_weights_1 = self._herc_recursive_allocation(sub_linkage_1, sub_cov_1, sub_assets_1)
            for i, idx in enumerate(cluster_1):
                weights[idx] = weight_1 * sub_weights_1[i]
        else:
            weights[cluster_1[0]] = weight_1
            
        return weights
    
    def _extract_sublinkage(self, linkage_matrix: np.ndarray, cluster_indices: list) -> np.ndarray:
        """
        Estrae la sottomatrice di linkage per un cluster
        
        Args:
            linkage_matrix: Matrice di linkage completa
            cluster_indices: Indici del cluster
            
        Returns:
            Sottomatrice di linkage
        """
        # Implementazione semplificata - ritorna la matrice originale
        # In una implementazione completa, si dovrebbe estrarre solo la parte rilevante
        return linkage_matrix
    
    def backtest_portfolio(self, returns: pd.DataFrame, method: str = 'herc', 
                          rebalance_freq: str = 'M') -> pd.DataFrame:
        """
        Esegue il backtest del portafoglio con ribilanciamento
        
        Args:
            returns: DataFrame con i rendimenti
            method: Metodo di ottimizzazione ('herc' o 'hrp')
            rebalance_freq: Frequenza di ribilanciamento ('M' = mensile, 'Q' = trimestrale)
            
        Returns:
            DataFrame con i risultati del backtest
        """
        # Determina le date di ribilanciamento
        if rebalance_freq == 'M':
            rebalance_dates = returns.resample('M').last().index
        elif rebalance_freq == 'Q':
            rebalance_dates = returns.resample('Q').last().index
        else:
            rebalance_dates = returns.resample('Y').last().index
        
        portfolio_returns = []
        weights_history = []
        current_weights = None
        
        for i, rebalance_date in enumerate(rebalance_dates):
            # Prendi i dati fino alla data di ribilanciamento
            historical_returns = returns.loc[:rebalance_date]
            
            # Serve almeno 252 giorni di dati per l'ottimizzazione
            if len(historical_returns) < 252:
                continue
            
            # Usa solo gli ultimi 252 giorni per l'ottimizzazione
            optimization_returns = historical_returns.tail(252)
            
            # Ottimizza il portafoglio
            if method.lower() == 'herc':
                new_weights = self.herc_optimization(optimization_returns)
            else:
                new_weights = self.hrp_optimization(optimization_returns)
            
            weights_history.append({
                'date': rebalance_date,
                'weights': new_weights.copy()
            })
            
            current_weights = new_weights
            
            # Calcola i rendimenti del portafoglio fino al prossimo ribilanciamento
            if i < len(rebalance_dates) - 1:
                next_rebalance = rebalance_dates[i + 1]
                period_returns = returns.loc[rebalance_date:next_rebalance]
            else:
                period_returns = returns.loc[rebalance_date:]
            
            # Rimuovi la data di ribilanciamento corrente se presente
            if len(period_returns) > 1:
                period_returns = period_returns.iloc[1:]
            
            # Calcola i rendimenti del portafoglio
            if len(period_returns) > 0 and current_weights is not None:
                portfolio_period_returns = (period_returns * current_weights).sum(axis=1)
                portfolio_returns.extend(portfolio_period_returns.tolist())
        
        # Crea il DataFrame dei risultati
        all_dates = []
        for entry in weights_history:
            rebalance_date = entry['date']
            if len(rebalance_dates) > 1:
                idx = list(rebalance_dates).index(rebalance_date)
                if idx < len(rebalance_dates) - 1:
                    next_rebalance = rebalance_dates[idx + 1]
                    period_dates = returns.loc[rebalance_date:next_rebalance].index[1:]
                else:
                    period_dates = returns.loc[rebalance_date:].index[1:]
                all_dates.extend(period_dates)
        
        # Allinea le lunghezze
        min_length = min(len(all_dates), len(portfolio_returns))
        all_dates = all_dates[:min_length]
        portfolio_returns = portfolio_returns[:min_length]
        
        self.weights_history = weights_history
        self.rebalance_dates = rebalance_dates
        
        return pd.DataFrame({
            'portfolio_returns': portfolio_returns,
            'cumulative_returns': np.cumprod(1 + np.array(portfolio_returns)) - 1
        }, index=all_dates)
    
    def calculate_cash_weight(self, weights: pd.Series) -> pd.Series:
        """
        Calcola il peso del cash asset per completare il portafoglio al 100%
        
        Args:
            weights: Serie con i pesi degli asset
            
        Returns:
            Serie con i pesi aggiornati includendo il cash
        """
        cash_asset = get_cash_asset()
        
        # Calcola la somma dei pesi degli asset da investimento
        investment_sum = weights.drop(cash_asset, errors='ignore').sum()
        
        # Il cash prende il peso residuo per arrivare al 100%
        cash_weight = max(0.0, 1.0 - investment_sum)
        
        # Aggiorna i pesi
        final_weights = weights.copy()
        final_weights[cash_asset] = cash_weight
        
        return final_weights
    
    def adjust_weights_with_cash(self, weights: pd.Series, use_fixed_cash: bool = True) -> pd.Series:
        """
        Aggiusta i pesi considerando il cash asset
        
        Args:
            weights: Serie con i pesi modificati dall'utente
            use_fixed_cash: Se utilizzare il cash fisso o calcolare automaticamente
            
        Returns:
            Serie con i pesi normalizzati includendo il cash
        """
        cash_asset = get_cash_asset()
        
        if use_fixed_cash:
            # Utilizza il sistema di cash fisso e vincoli di esposizione
            return self.apply_exposure_constraints(weights)
        else:
            # Sistema precedente per compatibilità
            # Filtra solo gli asset da investimento (esclude cash)
            investment_weights = weights.drop(cash_asset, errors='ignore')
            
            # Se la somma degli investimenti supera il 100%, normalizza
            investment_sum = investment_weights.sum()
            if investment_sum > 1.0:
                investment_weights = investment_weights / investment_sum
            
            # Calcola il peso del cash
            cash_weight = max(0.0, 1.0 - investment_weights.sum())
            
            # Crea i pesi finali
            final_weights = weights.copy()
            final_weights[investment_weights.index] = investment_weights
            final_weights[cash_asset] = cash_weight
            
            return final_weights
    
    def get_latest_weights(self) -> pd.Series:
        """
        Ottieni i pesi più recenti del portafoglio con cash calcolato
        
        Returns:
            Serie con i pesi più recenti includendo il cash
        """
        if self.weights_history:
            weights = self.weights_history[-1]['weights']
            return self.calculate_cash_weight(weights)
        return pd.Series()
    
    def get_rebalance_dates(self) -> list:
        """
        Ottieni le date di ribilanciamento
        
        Returns:
            Lista delle date di ribilanciamento
        """
        return [entry['date'] for entry in self.weights_history]

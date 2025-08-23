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
import logging
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    """Classe per l'ottimizzazione del portafoglio con algoritmi gerarchici"""
    
    def __init__(self, cash_target=None, max_exposure=None, use_volatility_target=False, target_volatility=None):
        """
        Inizializza l'ottimizzatore con parametri opzionali
        
        Args:
            cash_target: Percentuale fissa di cash da mantenere (es. 0.10 per 10%)
            max_exposure: Massima esposizione per singolo ETF (es. 0.30 per 30%)
            use_volatility_target: Se True, usa volatilità target invece di cash fisso
            target_volatility: Volatilità target annua (es. 0.06 per 6%)
        """
        from src.config import DEFAULT_TARGET_VOLATILITY
        
        self.weights_history = {}
        self.rebalance_dates = []
        self.cash_target = cash_target if cash_target is not None else get_default_cash_target()
        self.max_exposure = max_exposure if max_exposure is not None else get_default_max_exposure()
        
        # Configurazione volatilità target
        self.use_volatility_target = use_volatility_target
        self.target_volatility = target_volatility if target_volatility is not None else DEFAULT_TARGET_VOLATILITY
        
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
        return linkage(distance_matrix, method='ward')
    
    def calculate_target_cash_weight(self, returns: pd.DataFrame, investment_weights: pd.Series, 
                                   current_date: pd.Timestamp) -> float:
        """
        Calcola il peso del cash necessario per raggiungere la volatilità target
        
        Args:
            returns: DataFrame con i rendimenti storici
            investment_weights: Pesi degli asset di investimento (normalizzati, escluso cash)
            current_date: Data corrente per il lookback
            
        Returns:
            Peso del cash (0-1) per raggiungere la volatilità target
        """
        from src.config import VOLATILITY_LOOKBACK_DAYS
        
        cash_asset = get_cash_asset()
        
        # Trova l'indice della data corrente
        available_dates = returns.index[returns.index <= current_date]
        if len(available_dates) < VOLATILITY_LOOKBACK_DAYS:
            # Se non ci sono abbastanza dati, usa tutto quello disponibile
            lookback_start = available_dates[0]
        else:
            # Usa gli ultimi 252 giorni (1 anno)
            lookback_start = available_dates[-VOLATILITY_LOOKBACK_DAYS]
        
        # Estrai dati del periodo di lookback
        lookback_returns = returns.loc[lookback_start:current_date]
        
        # Filtra solo gli asset di investimento (escluso cash)
        investment_returns = lookback_returns.drop(columns=[cash_asset], errors='ignore')
        
        # Calcola la volatilità del portfolio di investimento
        if investment_returns.empty or investment_weights.empty:
            return self.cash_target  # Fallback al cash target fisso
        
        # Assicurati che i pesi siano allineati con i rendimenti
        aligned_weights = investment_weights.reindex(investment_returns.columns, fill_value=0)
        aligned_weights = aligned_weights / aligned_weights.sum()  # Normalizza
        
        # Calcola la covarianza del portfolio di investimento
        portfolio_returns = (investment_returns * aligned_weights).sum(axis=1)
        portfolio_volatility = portfolio_returns.std() * np.sqrt(252)  # Annualizzata
        
        if portfolio_volatility <= 0:
            return self.cash_target  # Fallback se volatilità zero
        
        # Calcola il peso necessario del portfolio di investimento per raggiungere target
        # volatility_portfolio = weight_investment * volatility_investment
        # target_volatility = weight_investment * portfolio_volatility
        weight_investment = min(1.0, self.target_volatility / portfolio_volatility)
        weight_cash = 1.0 - weight_investment
        
        # Assicura che il cash non sia negativo
        weight_cash = max(0.0, weight_cash)
        
        print(f"📊 Volatilità Target Calculation ({current_date.strftime('%Y-%m-%d')}):")
        print(f"   Portfolio volatility: {portfolio_volatility*100:.2f}%")
        print(f"   Target volatility: {self.target_volatility*100:.2f}%")
        print(f"   Investment weight: {weight_investment*100:.2f}%")
        print(f"   Cash weight: {weight_cash*100:.2f}%")
        
        return weight_cash
    
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
    
    def apply_exposure_constraints(self, weights: pd.Series, returns_data: pd.DataFrame = None, 
                                 current_date: pd.Timestamp = None) -> pd.Series:
        """
        Applica i vincoli di massima esposizione agli ETF con algoritmo iterativo robusto
        Include gestione speciale per SWDA come asset core e volatilità target
        
        Args:
            weights: Serie con i pesi degli asset
            returns_data: DataFrame con i rendimenti (necessario per volatilità target)
            current_date: Data corrente (necessaria per volatilità target)
            
        Returns:
            Serie con i pesi aggiustati secondo i vincoli
        """
        cash_asset = get_cash_asset()
        constrained_weights = weights.copy()
        
        # Determina il target di cash (fisso o basato su volatilità)
        if self.use_volatility_target and returns_data is not None and current_date is not None:
            # Estrai i pesi degli investimenti (senza cash) e normalizzali
            investment_weights = constrained_weights.drop(cash_asset, errors='ignore')
            if investment_weights.sum() > 0:
                investment_weights = investment_weights / investment_weights.sum()
                
                # Calcola il peso del cash basato sulla volatilità target
                target_cash_weight = self.calculate_target_cash_weight(
                    returns_data, investment_weights, current_date
                )
            else:
                target_cash_weight = self.cash_target
        else:
            # Usa cash fisso
            target_cash_weight = self.cash_target
        
        # Peso minimo garantito per SWDA (asset core)
        from src.config import DEFAULT_SWDA_MIN_WEIGHT
        swda_min_weight = DEFAULT_SWDA_MIN_WEIGHT
        
        # Separa cash dagli altri asset
        investment_assets = [asset for asset in constrained_weights.index 
                           if asset != cash_asset]
        
        # Assicura peso minimo per SWDA se presente
        if 'SWDA.MI' in constrained_weights.index:
            current_swda_weight = constrained_weights['SWDA.MI']
            if current_swda_weight < swda_min_weight:
                print(f"🏆 Applicando peso minimo SWDA: {current_swda_weight:.3f} -> {swda_min_weight:.3f}")
                
                # Calcola quanto peso dobbiamo togliere dagli altri asset
                weight_needed = swda_min_weight - current_swda_weight
                
                # Riduci proporzionalmente gli altri asset (escluso cash e SWDA)
                other_assets = [asset for asset in investment_assets if asset != 'SWDA.MI']
                total_other_weight = sum(constrained_weights[asset] for asset in other_assets)
                
                if total_other_weight > weight_needed:
                    reduction_factor = (total_other_weight - weight_needed) / total_other_weight
                    for asset in other_assets:
                        constrained_weights[asset] *= reduction_factor
                
                # Imposta SWDA al peso minimo
                constrained_weights['SWDA.MI'] = swda_min_weight
        
        # Applica vincoli iterativamente
        max_iterations = 20
        for iteration in range(max_iterations):
            total_violation = 0.0
            violated_assets = []
            
            # Trova violazioni
            for asset in investment_assets:
                if not is_exposure_exempt(asset):
                    if constrained_weights[asset] > self.max_exposure:
                        violation = constrained_weights[asset] - self.max_exposure
                        total_violation += violation
                        violated_assets.append(asset)
                        # Taglia immediatamente al limite
                        constrained_weights[asset] = self.max_exposure
            
            # Se non ci sono violazioni, esci
            if total_violation < 1e-8:
                break
                
            print(f"Iterazione {iteration + 1}: {len(violated_assets)} asset violati, eccesso totale: {total_violation:.6f}")
            
            # Trova asset eligibili per redistribuzione
            eligible_assets = []
            total_available_space = 0.0
            
            for asset in investment_assets:
                if not is_exposure_exempt(asset):
                    available_space = max(0.0, self.max_exposure - constrained_weights[asset])
                    if available_space > 1e-8:
                        eligible_assets.append(asset)
                        total_available_space += available_space
            
            # Ridistribuisci il peso in eccesso
            if total_violation > 1e-8:
                # PRIORITÀ 1: Prova a dare l'eccesso a SWDA (asset core, esente da limiti)
                if 'SWDA.MI' in constrained_weights.index:
                    # SWDA può assorbire tutto l'eccesso (essendo esente da limiti)
                    constrained_weights['SWDA.MI'] += total_violation
                    print(f"Peso in eccesso {total_violation:.6f} allocato a SWDA (asset core)")
                    total_violation = 0.0
                
                # PRIORITÀ 2: Se SWDA non è disponibile, distribuzione tradizionale
                elif eligible_assets and total_available_space > 1e-8:
                    # Ridistribuisci proporzionalmente allo spazio disponibile
                    redistribution_ratio = min(1.0, total_violation / total_available_space)
                    
                    for asset in eligible_assets:
                        available_space = max(0.0, self.max_exposure - constrained_weights[asset])
                        additional_weight = available_space * redistribution_ratio
                        constrained_weights[asset] += additional_weight
                    
                    distributed_weight = min(total_violation, total_available_space)
                    print(f"Peso in eccesso {distributed_weight:.6f} ridistribuito tra {len(eligible_assets)} asset")
                    total_violation -= distributed_weight
                
                # PRIORITÀ 3: Solo come ultima risorsa va al cash
                if total_violation > 1e-8:
                    print(f"Peso in eccesso residuo {total_violation:.6f} allocato al cash")
                    break
            else:
                # Nessuna violazione, esci dal loop
                break
        
        if iteration >= max_iterations - 1:
            print(f"⚠️ Algoritmo di vincoli ha raggiunto il limite di iterazioni ({max_iterations})")
        
        # Calcola spazio investimenti e normalizza
        investment_sum = sum(constrained_weights[asset] for asset in investment_assets)
        available_for_investment = 1.0 - target_cash_weight
        
        if investment_sum > available_for_investment + 1e-6:
            # Se la somma degli investimenti supera lo spazio disponibile, scala proporzionalmente
            scale_factor = available_for_investment / investment_sum
            print(f"Scaling investment weights by {scale_factor:.6f}")
            
            for asset in investment_assets:
                constrained_weights[asset] *= scale_factor
        
        # Imposta il cash (fisso o calcolato dinamicamente)
        constrained_weights[cash_asset] = target_cash_weight
        
        # Verifica finale
        self._verify_constraints(constrained_weights, "apply_exposure_constraints")
        
        return constrained_weights
    
    def _verify_constraints(self, weights: pd.Series, context: str = "") -> None:
        """
        Verifica che tutti i vincoli siano rispettati
        
        Args:
            weights: Serie con i pesi da verificare
            context: Stringa per identificare il contesto della verifica
        """
        cash_asset = get_cash_asset()
        violations = []
        
        for asset in weights.index:
            if asset != cash_asset and not is_exposure_exempt(asset):
                if weights[asset] > self.max_exposure + 1e-6:  # Tolleranza numerica
                    violations.append(f"{asset}: {weights[asset]:.4f} > {self.max_exposure}")
        
        if violations:
            print(f"⚠️  VINCOLI VIOLATI in {context}:")
            for violation in violations:
                print(f"   - {violation}")
            print(f"   - Somma pesi: {weights.sum():.4f}")
            print(f"   - Cash: {weights[cash_asset]:.4f}")
            print()
    
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
        
        # Il cash verrà impostato successivamente da apply_exposure_constraints
        if cash_asset in final_weights.index:
            final_weights[cash_asset] = 0.0
        
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
        
        # Il cash verrà impostato successivamente da apply_exposure_constraints
        if cash_asset in final_weights.index:
            final_weights[cash_asset] = 0.0
        
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
            
            # Applica vincoli di esposizione e cash fisso/volatilità target ad ogni ribilanciamento
            new_weights = self.apply_exposure_constraints(
                new_weights, 
                returns_data=returns, 
                current_date=rebalance_date
            )
            
            # Verifica aggiuntiva per debug
            self._verify_constraints(new_weights, f"Backtest {rebalance_date.strftime('%Y-%m-%d')}")
            
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
    
    def create_benchmark_portfolio(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Crea un portfolio benchmark basato su SWDA + XEON
        Utilizza lo stesso approccio di liquidità del portafoglio principale
        
        Args:
            returns: DataFrame con i rendimenti degli asset
            
        Returns:
            DataFrame con i rendimenti del benchmark
        """
        cash_asset = get_cash_asset()
        swda_symbol = 'SWDA.MI'
        
        # Verifica che entrambi gli asset siano disponibili
        if cash_asset not in returns.columns or swda_symbol not in returns.columns:
            logger.warning(f"Asset mancanti per benchmark: {cash_asset} o {swda_symbol}")
            return pd.DataFrame()
        
        if self.use_volatility_target:
            # Usa volatilità target per il benchmark - calcola come il portfolio principale
            print(f"📊 Benchmark con volatilità target: {self.target_volatility*100:.1f}%")
            
            from src.config import VOLATILITY_LOOKBACK_DAYS
            min_window = VOLATILITY_LOOKBACK_DAYS
            
            benchmark_returns_list = []
            benchmark_dates = []
            
            for i, current_date in enumerate(returns.index):
                if i < min_window:
                    # Usa cash fisso per i primi giorni (come fallback)
                    cash_weight = self.cash_target
                else:
                    # Crea pesi benchmark temporanei per calcolo volatilità
                    temp_weights = pd.Series(0.0, index=returns.columns)
                    temp_weights[swda_symbol] = 1.0  # 100% SWDA temporaneamente
                    
                    # Calcola peso cash usando la stessa logica del portfolio
                    cash_weight = self.calculate_target_cash_weight(
                        returns.iloc[:i],  # Dati fino alla data corrente 
                        temp_weights.drop(cash_asset, errors='ignore'),  # Solo SWDA
                        current_date
                    )
                
                # Calcola rendimento del giorno
                swda_weight = 1.0 - cash_weight
                daily_return = (cash_weight * returns[cash_asset].iloc[i] + 
                              swda_weight * returns[swda_symbol].iloc[i])
                
                benchmark_returns_list.append(daily_return)
                benchmark_dates.append(current_date)
        
        else:
            # Usa cash fisso per il benchmark
            print(f"📊 Benchmark con cash fisso: {self.cash_target*100:.1f}%")
            benchmark_weights = pd.Series(0.0, index=returns.columns)
            benchmark_weights[cash_asset] = self.cash_target
            benchmark_weights[swda_symbol] = 1.0 - self.cash_target
            
            # Calcola rendimenti benchmark
            benchmark_returns_series = (returns * benchmark_weights).sum(axis=1)
            benchmark_returns_list = benchmark_returns_series.tolist()
            benchmark_dates = returns.index.tolist()
        
        # Crea DataFrame risultato
        benchmark_returns_series = pd.Series(benchmark_returns_list, index=benchmark_dates)
        
        return pd.DataFrame({
            'benchmark_returns': benchmark_returns_series,
            'cumulative_returns': np.cumprod(1 + benchmark_returns_series) - 1
        }, index=benchmark_dates)
    
    def backtest_with_benchmark(self, returns: pd.DataFrame, method: str = 'herc', 
                               rebalance_freq: str = 'M') -> dict:
        """
        Esegue il backtest del portafoglio includendo il benchmark
        Il benchmark utilizza lo stesso approccio di liquidità (cash fisso o volatilità target)
        
        Args:
            returns: DataFrame con i rendimenti
            method: Metodo di ottimizzazione ('herc' o 'hrp')
            rebalance_freq: Frequenza di ribilanciamento
            
        Returns:
            Dizionario con risultati portfolio e benchmark
        """
        # Backtest del portfolio principale
        portfolio_results = self.backtest_portfolio(returns, method, rebalance_freq)
        
        # Crea benchmark per lo stesso periodo
        if not portfolio_results.empty:
            benchmark_period = returns.loc[portfolio_results.index[0]:portfolio_results.index[-1]]
            benchmark_results = self.create_benchmark_portfolio(benchmark_period)
            
            # Allinea le date
            common_dates = portfolio_results.index.intersection(benchmark_results.index)
            
            if len(common_dates) > 0:
                portfolio_aligned = portfolio_results.loc[common_dates]
                benchmark_aligned = benchmark_results.loc[common_dates]
                
                # Determina i pesi del benchmark in base alla modalità
                if self.use_volatility_target:
                    benchmark_weights_info = {
                        'approach': 'volatility_target',
                        'target_volatility': self.target_volatility,
                        'SWDA.MI': f'Variabile (target vol {self.target_volatility*100:.1f}%)',
                        get_cash_asset(): f'Variabile (target vol {self.target_volatility*100:.1f}%)'
                    }
                else:
                    benchmark_weights_info = {
                        'approach': 'fixed_cash',
                        'cash_target': self.cash_target,
                        'SWDA.MI': 1.0 - self.cash_target,
                        get_cash_asset(): self.cash_target
                    }
                
                return {
                    'portfolio': portfolio_aligned,
                    'benchmark': benchmark_aligned,
                    'portfolio_weights': self.weights_history,
                    'benchmark_weights': benchmark_weights_info,
                    'use_volatility_target': self.use_volatility_target,
                    'target_volatility': self.target_volatility if self.use_volatility_target else None
                }
        
        return {
            'portfolio': portfolio_results,
            'benchmark': pd.DataFrame(),
            'portfolio_weights': self.weights_history,
            'benchmark_weights': {},
            'use_volatility_target': self.use_volatility_target,
            'target_volatility': self.target_volatility if self.use_volatility_target else None
        }

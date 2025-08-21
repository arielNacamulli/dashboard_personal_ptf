#!/usr/bin/env python3
"""
Test per capire perché SWDA riceve un peso così basso nell'ottimizzazione HERC
"""

import pandas as pd
import numpy as np
from src.data_loader import ETFDataLoader
from src.portfolio_optimizer import PortfolioOptimizer
from src.config import get_etf_symbols, get_cash_asset
from scipy.cluster.hierarchy import linkage, dendrogram, cut_tree
import matplotlib.pyplot as plt

def analyze_herc_clustering():
    """Analizza il clustering gerarchico per capire la posizione di SWDA"""
    
    print("🔬 Analisi Clustering HERC - Posizione SWDA")
    print("=" * 50)
    
    # Carica dati
    data_loader = ETFDataLoader()
    etf_symbols = list(get_etf_symbols().keys())
    
    prices_data = data_loader.download_etf_data(etf_symbols, "2y")
    returns_data = data_loader.calculate_returns(prices_data)
    
    cash_asset = get_cash_asset()
    investment_returns = returns_data.drop(columns=[cash_asset], errors='ignore')
    
    print(f"Asset analizzati: {list(investment_returns.columns)}")
    print()
    
    # Calcola correlazione
    correlation_matrix = investment_returns.corr().fillna(0)
    
    print("📊 Matrice di Correlazione con SWDA:")
    swda_correlations = correlation_matrix['SWDA.MI'].sort_values(ascending=False)
    for asset, corr in swda_correlations.items():
        print(f"   {asset:12s}: {corr:6.3f}")
    print()
    
    # Calcola distanze
    optimizer = PortfolioOptimizer()
    distance_matrix = optimizer.calculate_distance_matrix(correlation_matrix)
    
    print("📏 Distanze da SWDA:")
    swda_idx = list(investment_returns.columns).index('SWDA.MI')
    distances_from_swda = []
    for i, asset in enumerate(investment_returns.columns):
        if i != swda_idx:
            dist = distance_matrix[swda_idx, i]
            distances_from_swda.append((asset, dist))
    
    distances_from_swda.sort(key=lambda x: x[1])
    for asset, dist in distances_from_swda:
        print(f"   {asset:12s}: {dist:6.3f}")
    print()
    
    # Clustering gerarchico
    linkage_matrix = optimizer.hierarchical_clustering(distance_matrix)
    
    print("🌳 Struttura Clustering:")
    print(f"   Linkage matrix shape: {linkage_matrix.shape}")
    
    # Analizza i cluster a diversi livelli
    for n_clusters in [2, 3, 4]:
        clusters = cut_tree(linkage_matrix, n_clusters=n_clusters).flatten()
        cluster_assignment = {}
        for i, asset in enumerate(investment_returns.columns):
            cluster_id = clusters[i]
            if cluster_id not in cluster_assignment:
                cluster_assignment[cluster_id] = []
            cluster_assignment[cluster_id].append(asset)
        
        print(f"\n   Con {n_clusters} cluster:")
        for cluster_id, assets in cluster_assignment.items():
            swda_mark = "⭐" if 'SWDA.MI' in assets else "  "
            print(f"     Cluster {cluster_id} {swda_mark}: {assets}")
    
    # Analisi rischio/volatilità
    print("\n📈 Analisi Rischio:")
    volatilities = investment_returns.std() * np.sqrt(252)  # Annualizzata
    sorted_vol = volatilities.sort_values(ascending=False)
    
    for asset, vol in sorted_vol.items():
        swda_mark = "⭐" if asset == 'SWDA.MI' else "  "
        print(f"   {asset:12s} {swda_mark}: {vol*100:5.1f}%")
    
    print(f"\nSWDA posizione per volatilità: {list(sorted_vol.index).index('SWDA.MI') + 1}/{len(sorted_vol)}")
    
    # Simula allocazione HERC manuale per capire la logica
    print("\n🧮 Simulazione HERC Step-by-Step:")
    
    # Level 1: Split in 2 cluster
    clusters_2 = cut_tree(linkage_matrix, n_clusters=2).flatten()
    cluster_0_assets = [investment_returns.columns[i] for i in range(len(investment_returns.columns)) if clusters_2[i] == 0]
    cluster_1_assets = [investment_returns.columns[i] for i in range(len(investment_returns.columns)) if clusters_2[i] == 1]
    
    swda_cluster = 0 if 'SWDA.MI' in cluster_0_assets else 1
    print(f"   SWDA nel cluster {swda_cluster}")
    print(f"   Cluster 0: {cluster_0_assets}")
    print(f"   Cluster 1: {cluster_1_assets}")
    
    # Calcola risk parity tra i due cluster
    cluster_0_returns = investment_returns[cluster_0_assets]
    cluster_1_returns = investment_returns[cluster_1_assets]
    
    cluster_0_risk = np.sqrt(np.diag(cluster_0_returns.cov())).sum()
    cluster_1_risk = np.sqrt(np.diag(cluster_1_returns.cov())).sum()
    
    total_risk = cluster_0_risk + cluster_1_risk
    cluster_0_weight = cluster_1_risk / total_risk  # Inversamente proporzionale al rischio
    cluster_1_weight = cluster_0_risk / total_risk
    
    print(f"   Cluster 0 rischio: {cluster_0_risk:.4f} -> peso {cluster_0_weight:.3f}")
    print(f"   Cluster 1 rischio: {cluster_1_risk:.4f} -> peso {cluster_1_weight:.3f}")
    
    swda_cluster_weight = cluster_0_weight if swda_cluster == 0 else cluster_1_weight
    swda_cluster_size = len(cluster_0_assets) if swda_cluster == 0 else len(cluster_1_assets)
    
    # Se SWDA è in un cluster con molti asset, il suo peso sarà diluito
    estimated_swda_weight = swda_cluster_weight / swda_cluster_size
    print(f"   SWDA peso stimato: {estimated_swda_weight:.3f} ({estimated_swda_weight*100:.1f}%)")

if __name__ == "__main__":
    analyze_herc_clustering()

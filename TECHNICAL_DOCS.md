# Documentazione Tecnica - ETF Portfolio Dashboard

## Architettura dell'Applicazione

### Struttura del Progetto

```
dashboard_personal_ptf/
├── app.py                    # Applicazione principale Streamlit
├── src/                      # Moduli core dell'applicazione
│   ├── __init__.py          # Package init
│   ├── data_loader.py       # Download e gestione dati ETF
│   ├── portfolio_optimizer.py # Algoritmi HERC e HRP
│   ├── metrics.py           # Calcolo metriche di performance
│   └── utils.py             # Funzioni di utilità e grafici
├── test_modules.py          # Test di funzionamento
├── requirements.txt         # Dipendenze Python
├── start_dashboard.sh       # Script di avvio
├── .streamlit/config.toml   # Configurazione Streamlit
└── README.md               # Documentazione utente
```

## Algoritmi Implementati

### HERC (Hierarchical Equal Risk Contribution)

L'algoritmo HERC è un'evoluzione dell'approccio Equal Risk Contribution che utilizza il clustering gerarchico per allocare il rischio in modo più efficiente:

1. **Clustering Gerarchico**: Gli asset vengono raggruppati in base alla loro struttura di correlazione
2. **Allocazione del Rischio**: Il rischio viene distribuito equamente tra i cluster e poi all'interno di ogni cluster
3. **Ribilanciamento**: I pesi vengono ricalcolati periodicamente (mensile/trimestrale/annuale)

**Vantaggi:**

- Migliore diversificazione rispetto agli approcci tradizionali
- Riduzione del rischio di concentrazione
- Stabilità dei pesi nel tempo

### HRP (Hierarchical Risk Parity)

L'algoritmo HRP utilizza il clustering gerarchico per costruire portafogli diversificati senza ricorrere all'ottimizzazione tradizionale:

1. **Matrice di Distanza**: Conversione della correlazione in distanze euclidee
2. **Clustering**: Raggruppamento degli asset con algoritmi di linkage
3. **Allocazione Ricorsiva**: Distribuzione dei pesi attraverso bisezione ricorsiva

**Vantaggi:**

- Non richiede inversione di matrici (più stabile numericamente)
- Naturalmente diversificato
- Meno sensibile agli errori di stima

## Metriche di Performance Implementate

### Metriche Principali

- **Rendimento Annualizzato**: Tasso di crescita composto annuale
- **Volatilità Annualizzata**: Deviazione standard dei rendimenti annualizzata
- **Sharpe Ratio**: Eccesso di rendimento per unità di rischio
- **Sortino Ratio**: Come Sharpe ma considera solo la volatilità negativa
- **Maximum Drawdown**: Massima perdita dal picco al minimo
- **Calmar Ratio**: Rendimento annualizzato diviso per il max drawdown

### Metriche di Rischio

- **Value at Risk (VaR)**: Perdita massima attesa con un certo livello di confidenza
- **Conditional VaR (CVaR)**: Perdita media oltre il VaR
- **Beta**: Sensibilità rispetto al mercato
- **Tracking Error**: Volatilità dell'eccesso di rendimento rispetto al benchmark

## Tecnologie Utilizzate

### Frontend

- **Streamlit**: Framework per applicazioni web interattive
- **Plotly**: Libreria per grafici interattivi
- **CSS Personalizzato**: Per styling minimale e professionale

### Backend e Calcoli

- **Pandas**: Manipolazione e analisi dati
- **NumPy**: Calcoli numerici efficienti
- **SciPy**: Algoritmi scientifici (clustering, ottimizzazione)
- **Scikit-learn**: Machine learning (clustering, preprocessing)

### Dati Finanziari

- **yFinance**: Download dati storici da Yahoo Finance
- **Riskfolio-lib**: Libreria specializzata per analisi di portafoglio
- **PyPortfolioOpt**: Ottimizzazione di portafoglio

### Performance

- **Numba**: Compilazione JIT per calcoli numerici veloci
- **Joblib**: Parallelizzazione e caching

## Ottimizzazioni delle Performance

### Caching

- **Streamlit Cache**: Cache dei dati scaricati e dei calcoli pesanti
- **TTL**: Time-to-live di 1 ora per i dati di mercato

### Calcoli Efficienti

- **Numpy Vectorization**: Operazioni vettoriali per calcoli matriciali
- **Pandas Optimization**: Uso di operazioni native pandas
- **Memory Management**: Gestione efficiente della memoria per grandi dataset

### UI/UX Ottimizzazioni

- **Lazy Loading**: Caricamento dati solo quando necessario
- **Progress Indicators**: Feedback visivo durante operazioni lunghe
- **Responsive Design**: Adattamento a diverse dimensioni schermo

## Configurazione e Deployment

### Ambiente di Sviluppo

```bash
# Clona il repository
git clone <repository_url>

# Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o .venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
streamlit run app.py
```

### Configurazione Avanzata

#### File .streamlit/config.toml

- Personalizzazione tema e colori
- Configurazione server
- Ottimizzazioni browser

#### Variabili di Ambiente

```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## Estensioni Future

### Nuove Funzionalità Pianificate

1. **Analisi ESG**: Integrazione di metriche ambientali, sociali e di governance
2. **Backtesting Avanzato**: Simulazioni con costi di transazione e slippage
3. **Alert System**: Notifiche per ribilanciamenti e soglie di rischio
4. **API Integration**: Connessione con broker per trading automatico
5. **Machine Learning**: Modelli predittivi per asset allocation dinamica

### Miglioramenti Tecnici

1. **Database Integration**: Salvataggio persistente dei dati
2. **Real-time Data**: Aggiornamenti in tempo reale
3. **Multi-user Support**: Gestione portfolio multipli
4. **Cloud Deployment**: Deployment su AWS/GCP/Azure

## Troubleshooting

### Problemi Comuni

#### Errori di Download Dati

- Verificare connessione internet
- Controllare simboli ETF (alcuni potrebbero essere delisted)
- Aumentare timeout per mercati lenti

#### Errori di Calcolo

- Verificare presenza di dati sufficienti (min 252 giorni)
- Controllare presenza di NaN nei dati
- Validare range di date

#### Performance Lente

- Installare watchdog: `pip install watchdog`
- Ridurre periodo di analisi per test
- Usare meno ETF per prove iniziali

### Log e Debug

- I log sono visibili nella console dove viene avviato Streamlit
- Usare `st.write()` per debug nell'interfaccia
- Controllare browser console per errori JavaScript

## Sicurezza e Privacy

### Gestione Dati

- Nessun dato personale viene salvato permanentemente
- Cache locale pulita automaticamente
- Connessioni HTTPS per download dati

### Best Practices

- Non condividere API keys nel codice
- Usare variabili di ambiente per configurazioni sensibili
- Validazione input utente per prevenire errori

## Performance Benchmark

### Test di Carico

- **Dataset Grande**: 7 ETF x 5 anni = ~9100 osservazioni
- **Tempo Download**: ~2-5 secondi
- **Tempo Ottimizzazione**: ~1-3 secondi per algoritmo
- **Memoria RAM**: ~100-200 MB per dataset completo

### Confronto Algoritmi

- **HERC**: Generalmente più veloce, più stabile
- **HRP**: Leggermente più lento ma più robusto
- **Backtest**: Scala linearmente con lunghezza periodo

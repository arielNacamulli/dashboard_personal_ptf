# ETF Portfolio Dashboard

Una dashboard interattiva per l'analisi di portafoglio ETF con algoritmi HERC (Hierarchical Equal Risk Contribution) e HRP (Hierarchical Risk Parity).

## Caratteristiche

- Download automatico di dati storici ETF da Yahoo Finance
- Implementazione algoritmi HERC e HRP con ribilanciamento configurabile
- **XEON.MI come base monetaria**: Non incluso nell'ottimizzazione, utilizzato come cash per completare il portafoglio al 100%
- **Modifica manuale dei pesi**: Possibilità di personalizzare l'allocazione ottimale
- Calcolo automatico del peso cash per mantenere il portafoglio al 100%
- Calcolo metriche di performance (rendimenti, volatilità, Sharpe ratio, drawdown)
- Dashboard interattiva con Streamlit
- Grafici interattivi e visualizzazioni
- Export dei pesi ottimali e modificati

## ETF Supportati

- SWDA.MI (iShares Core MSCI World)
- SPXS.MI (SPDR S&P 500)
- XDWT.MI (Xtrackers MSCI World Information Technology)
- XUCD.DE (Xtrackers MSCI USA Consumer Discretionary)
- H50A.MI (HSBC EURO STOXX 50)
- JPNA.MI (UBS Core MSCI Japan)
- IS3K.DE (iShares Short Duration High Yield)
- AEME.PA (Amundi Index MSCI Emerging Markets)
- XEON.MI (Xtrackers II EUR Overnight Rate Swap) - **Base Monetaria**

## Installazione

```bash
pip install -r requirements.txt
```

## Utilizzo

```bash
streamlit run app.py
```

### Workflow Consigliato

1. **Selezione ETF**: Scegli gli ETF dalla sidebar (XEON.MI è sempre incluso come base monetaria)
2. **Download Dati**: Seleziona il periodo e carica i dati storici
3. **Ottimizzazione**: Scegli HERC o HRP e la frequenza di ribilanciamento
4. **Analisi Risultati**: Esplora performance, metriche e correlazioni
5. **Modifica Pesi** (Opzionale): Personalizza l'allocazione nel tab "Pesi Portfolio"
6. **Export**: Scarica i pesi e i risultati dell'analisi

### Gestione Base Monetaria

- **XEON.MI** viene utilizzato come asset cash e non partecipa all'ottimizzazione
- Il suo peso viene calcolato automaticamente come: `Cash = 100% - Σ(Altri Asset)`
- Nella modifica manuale, il peso di XEON si aggiorna automaticamente
- Se la somma degli altri asset supera il 100%, vengono normalizzati automaticamente

## Struttura del Progetto

```
dashboard_personal_ptf/
├── app.py                 # Dashboard principale Streamlit
├── src/
│   ├── data_loader.py     # Download e gestione dati ETF
│   ├── portfolio_optimizer.py  # Algoritmi HERC e HRP
│   ├── metrics.py         # Calcolo metriche di performance
│   └── utils.py          # Funzioni di utilità
├── requirements.txt       # Dipendenze Python
└── README.md             # Questo file
```

## Algoritmi Implementati

### HERC (Hierarchical Equal Risk Contribution)

Algoritmo di allocazione che considera la struttura gerarchica degli asset per una distribuzione ottimale del rischio.

### HRP (Hierarchical Risk Parity)

Metodo di ottimizzazione che utilizza il clustering gerarchico per costruire portafogli diversificati.

## Metriche Calcolate

- Rendimento annualizzato
- Volatilità annualizzata
- Sharpe Ratio
- Maximum Drawdown
- Calmar Ratio
- VaR (Value at Risk)

## Licenza

MIT

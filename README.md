# ETF Portfolio Dashboard

Una dashboard interattiva per l'analisi di portafoglio ETF con algoritmi HERC (Hierarchical Equal Risk Contribution) e HRP (Hierarchical Risk Parity).

## Caratteristiche

- Download automatico di dati storici ETF da Yahoo Finance
- Implementazione algoritmi HERC e HRP con ribilanciamento mensile
- Calcolo metriche di performance (rendimenti, volatilità, Sharpe ratio, drawdown)
- Dashboard interattiva con Streamlit
- Grafici interattivi e visualizzazioni
- Export dei pesi ottimali

## ETF Supportati

- SWDA.MI (iShares Core MSCI World)
- SPXS.MI (SPDR S&P 500)
- XDWT.MI (Xtrackers MSCI World Information Technology)
- XUCD.DE (Xtrackers MSCI USA Consumer Discretionary)
- H50A.MI (HSBC EURO STOXX 50)
- JPNA.MI (UBS Core MSCI Japan)
- IS3K.DE (iShares Short Duration High Yield)
- IEMB.L (iShares Core MSCI Emerging Markets)

## Installazione

```bash
pip install -r requirements.txt
```

## Utilizzo

```bash
streamlit run app.py
```

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

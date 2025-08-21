"""
Configurazione centralizzata degli ETF supportati dalla dashboard
"""

# Definizione ETF supportati con simboli e nomi completi
ETF_SYMBOLS = {
    'SWDA.MI': 'iShares Core MSCI World',
    'SPXS.MI': 'SPDR S&P 500', 
    'XDWT.MI': 'Xtrackers MSCI World Information Technology',
    'XUCD.DE': 'Xtrackers MSCI USA Consumer Discretionary',
    'CSSX5E.MI': 'iShares Core EURO STOXX 50',
    'SJPA.MI': 'iShares Core MSCI Japan',
    'IS3K.DE': 'iShares Short Duration High Yield',
    'AEME.PA': 'Amundi Index MSCI Emerging Markets',
    'XEON.MI': 'Xtrackers II EUR Overnight Rate Swap'
}

# Asset monetario di base (non da ottimizzare)
CASH_ASSET = 'XEON.MI'

# Configurazioni avanzate di portfolio
DEFAULT_CASH_TARGET = 0.10  # 10% target di cash fisso
DEFAULT_MAX_EXPOSURE = 0.30  # 30% massima esposizione per singolo ETF
DEFAULT_SWDA_MIN_WEIGHT = 0.15  # 15% peso minimo per SWDA come asset core

# ETF esenti dal limite di massima esposizione
EXPOSURE_EXEMPT_ETFS = ['SWDA.MI', 'XEON.MI']

# Informazioni dettagliate per la tabella informativa
ETF_INFO = {
    'Simbolo': list(ETF_SYMBOLS.keys()),
    'Nome': list(ETF_SYMBOLS.values()),
    'Tipo': [
        'Azionario Globale',
        'Azionario USA', 
        'Azionario Tech',
        'Azionario Consumer',
        'Azionario Europa',
        'Azionario Giappone',
        'Obbligazionario High Yield',
        'Azionario Emerging Markets',
        'Base Monetaria (Cash)'
    ]
}

def get_etf_symbols():
    """Restituisce il dizionario dei simboli ETF"""
    return ETF_SYMBOLS.copy()

def get_investment_symbols():
    """Restituisce solo gli ETF da investire (escludendo cash asset)"""
    return {k: v for k, v in ETF_SYMBOLS.items() if k != CASH_ASSET}

def get_cash_asset():
    """Restituisce il simbolo dell'asset cash"""
    return CASH_ASSET

def get_etf_info():
    """Restituisce le informazioni dettagliate degli ETF"""
    return ETF_INFO.copy()

def get_etf_name(symbol):
    """Restituisce il nome di un ETF dato il simbolo"""
    return ETF_SYMBOLS.get(symbol, symbol)

def get_default_cash_target():
    """Restituisce il target di cash di default"""
    return DEFAULT_CASH_TARGET

def get_default_max_exposure():
    """Restituisce la massima esposizione di default"""
    return DEFAULT_MAX_EXPOSURE

def get_exposure_exempt_etfs():
    """Restituisce la lista degli ETF esenti dal limite di esposizione"""
    return EXPOSURE_EXEMPT_ETFS.copy()

def is_exposure_exempt(symbol):
    """Verifica se un ETF è esente dal limite di esposizione"""
    return symbol in EXPOSURE_EXEMPT_ETFS

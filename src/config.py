"""
Configurazione centralizzata degli ETF supportati dalla dashboard
"""

# Definizione ETF supportati con simboli e nomi completi
ETF_SYMBOLS = {
    'SWDA.MI': 'iShares Core MSCI World',
    'SPXS.MI': 'SPDR S&P 500', 
    'XDWT.MI': 'Xtrackers MSCI World Information Technology',
    'XUCD.DE': 'Xtrackers MSCI USA Consumer Discretionary',
    'H50A.MI': 'HSBC EURO STOXX 50',
    'JPNA.MI': 'UBS Core MSCI Japan',
    'IS3K.DE': 'iShares Short Duration High Yield',
    'AEME.PA': 'Amundi Index MSCI Emerging Markets',
    'XEON.MI': 'Xtrackers II EUR Overnight Rate Swap'
}

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
        'Obbligazionario Euro'
    ]
}

def get_etf_symbols():
    """Restituisce il dizionario dei simboli ETF"""
    return ETF_SYMBOLS.copy()

def get_etf_info():
    """Restituisce le informazioni dettagliate degli ETF"""
    return ETF_INFO.copy()

def get_etf_name(symbol):
    """Restituisce il nome di un ETF dato il simbolo"""
    return ETF_SYMBOLS.get(symbol, symbol)

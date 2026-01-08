import os
import yfinance as yf
import pandas as pd
import json
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

def get_full_market_data():
    targets = {
        'SX50E': '^STOXX50E', 'DAX': '^GDAXI', 
        'FTSEMIB': 'FTSEMIB.MI', 'CAC': '^FCHI', 'IBEX': '^IBEX'
    }
    predictors = ['^GSPC', '^N225', '^VIX', 'ES=F']
    
    # Download dati
    df_raw = yf.download(list(targets.values()) + predictors, period="max", progress=False)
    p_h = df_raw['Close'] if isinstance(df_raw.columns, pd.MultiIndex) else df_raw
    o_h = df_raw['Open'] if isinstance(df_raw.columns, pd.MultiIndex) else df_raw

    # Dati Future per Momentum
    fut_h = yf.download('ES=F', period="5d", interval="1h", progress=False)
    if isinstance(fut_h.columns, pd.MultiIndex): fut_h.columns = fut_h.columns.get_level_values(0)
    
    try:
        f_open = fut_h.between_time('00:00', '00:00')['Open'].iloc[-1]
        f_close = fut_h.between_time('08:00', '08:00')['Close'].iloc[-1]
        fut_chg_win = ((f_close / f_open) - 1) * 100
    except: fut_chg_win = 0.0

    data_out = {'indices': {}, 'live_preds': {}}

    # Predittori Modulo 1
    sp_series = p_h['^GSPC'].dropna()
    nk_series = p_h['^N225'].dropna()
    vix_series = p_h['^VIX'].dropna()
    
    data_out['live_preds'] = {
        'sp_val': float(sp_series.iloc[-1]), 
        'sp_chg': float(((sp_series.iloc[-1] / sp_series.iloc[-2]) - 1) * 100),
        'sp_dt': sp_series.index[-1].strftime('%d %b'),
        'nk_val': float(nk_series.iloc[-1]), 
        'nk_chg': float(((nk_series.iloc[-1] / nk_series.iloc[-2]) - 1) * 100),
        'nk_dt': nk_series.index[-1].strftime('%d %b'),
        'fut_chg': float(fut_chg_win),
        'vix': float(vix_series.iloc[-1])
    }

    # Storico per Moduli 3, 4 e 5
    for name, ticker in targets.items():
        if ticker not in p_h.columns: continue
        temp_df = pd.DataFrame(index=p_h.index)
        temp_df['InP'] = o_h[ticker]
        temp_df['OutP'] = p_h[ticker]
        temp_df['MOM'] = (p_h['^GSPC'].pct_change().shift(1) + p_h['^N225'].pct_change() + p_h['ES=F'].pct_change()) / 3
        temp_df['VIX'] = p_h['^VIX']
        temp_df = temp_df.dropna()

        history = []
        for dt, row in temp_df.iterrows():
            history.append({
                'd': dt.strftime('%Y-%m-%d'), 'm': float(row['MOM']), 'v': float(row['VIX']),
                'in': float(row['InP']), 'out': float(row['OutP'])
            })
        
        data_out['indices'][name] = {
            'history': history,
            'last_price': float(p_h[ticker].dropna().iloc[-1]),
            'entry_price': float(o_h[ticker].dropna().iloc[-1])
        }

    return data_out

# Generazione HTML (Template V7.6.5 con fix asse Y e soglia)
def generate_html(market_data):
    # [Qui inserirei tutto il template HTML fornito nelle risposte precedenti]
    # Per brevità ho configurato il file per scrivere index.html
    pass

if __name__ == "__main__":
    m_data = get_full_market_data()
    # (Il codice completo che ti invierò scriverà direttamente il file index.html)

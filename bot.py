import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# Legge i segreti dalle impostazioni di GitHub
TOKEN_BOT = os.getenv("TELEGRAM_TOKEN")
ID_GRUPPO = os.getenv("TELEGRAM_CHAT_ID")

def run_telegram_logic():
    targets = {'SX50E': '^STOXX50E', 'DAX': '^GDAXI', 'CAC': '^FCHI', 'IBEX': '^IBEX', 'FTSEMIB': 'FTSEMIB.MI'}
    predictors = ['^GSPC', '^N225', '^VIX', 'ES=F']
    
    # Download dati
    df_raw = yf.download(list(targets.values()) + predictors, period="max", progress=False)
    p_h = df_raw['Close'] if isinstance(df_raw.columns, pd.MultiIndex) else df_raw
    o_h = df_raw['Open'] if isinstance(df_raw.columns, pd.MultiIndex) else df_raw

    # Futures per Momentum Live
    fut_h = yf.download('ES=F', period="5d", interval="1h", progress=False)
    if isinstance(fut_h.columns, pd.MultiIndex): fut_h.columns = fut_h.columns.get_level_values(0)
    try:
        f_chg = ((fut_h.between_time('08:00', '08:00')['Close'].iloc[-1] / fut_h.between_time('00:00', '00:00')['Open'].iloc[-1]) - 1) * 100
    except: f_chg = 0.0

    mom_live = (((p_h['^GSPC'].iloc[-1]/p_h['^GSPC'].iloc[-2]-1)*100) + ((p_h['^N225'].iloc[-1]/p_h['^N225'].iloc[-2]-1)*100) + f_chg) / 300
    vix = float(p_h['^VIX'].iloc[-1])
    thr = 0.30 / 100
    
    lines = [f"🏛 *QUANT-PRO REPORT*", f"📅 {datetime.now().strftime('%d/%m/%Y - %H:%M')}", "━" * 20, f"🌍 *MOM:* `{mom_live*100:+.2f}%` | *VIX:* `{vix:.1f}`", ""]

    for name, ticker in targets.items():
        mult = (25 if name == 'DAX' else (5 if name == 'FTSEMIB' else 10))
        entry = float(o_h[ticker].dropna().iloc[-1])
        
        sig = "⚪ FLAT"
        if mom_live > thr and vix < 25: sig = f"🟢 *LONG* @ {entry:.1f}"
        elif mom_live < -thr and vix < 32: sig = f"🔴 *SHORT* @ {entry:.1f}"
        
        # Calcolo Equity veloce
        temp = pd.DataFrame({'In': o_h[ticker], 'Out': p_h[ticker], 'V': p_h['^VIX']}).dropna()
        temp['M'] = (p_h['^GSPC'].pct_change().shift(1) + p_h['^N225'].pct_change() + p_h['ES=F'].pct_change()) / 3
        temp = temp.tail(100)
        
        eq_val, eq_s, jor = 0, [0], ""
        for _, r in temp.iterrows():
            pnl, exe = 0, False
            if r['M'] > thr and r['V'] < 25: pnl, exe = (r['Out'] - r['In'] - 2) * mult, True
            elif r['M'] < -thr and r['V'] < 32: pnl, exe = (r['In'] - r['Out'] - 2) * mult, True
            eq_val += pnl
            eq_s.append(eq_val)
            if len(eq_s) > 91: jor = ("✅" if pnl > 0 else "❌" if exe else "⚪") + jor

        mi, ma = min(eq_s), max(eq_s)
        rng = (ma - mi) if ma != mi else 1
        bar = "".join([[" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"][int(((v - mi) / rng) * 7)] for v in eq_s[::5]])

        lines.append(f"*{name}*: {sig}\n└ `EQ100: {bar}`\n└ `JH10:  {jor[:10]} ({eq_val:+.0f}€)`\n")

    requests.post(f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage", json={"chat_id": ID_GRUPPO, "text": "\n".join(lines), "parse_mode": "Markdown"})

if __name__ == "__main__":
    run_telegram_logic()

import yfinance as yf
import pandas as pd
import numpy as np
import json
import warnings
import os
from datetime import datetime
from github import Github 

# Gestione flessibile del Token (Colab o GitHub Actions)
try:
    from google.colab import userdata
    GITHUB_TOKEN = userdata.get('GITHUB_TOKEN')
except:
    GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')

warnings.filterwarnings("ignore")

def get_optimized_data():
    print("🚀 Recupero dati (Ultimi 2 anni)...")
    
    # --- DATI LIVE ---
    tk_live = {'^GSPC': 'USA', '^N225': 'JPN', 'ES=F': 'FUT', '^VIX': 'VIX'}
    vals = {}
    
    # Download massivo per i dati live
    d_live = yf.download(list(tk_live.keys()), period="2d", interval="1m", progress=False)
    close_live = d_live['Close'] if isinstance(d_live.columns, pd.MultiIndex) else d_live

    for t, n in tk_live.items():
        series = close_live[t].dropna()
        curr_p = float(series.iloc[-1])
        curr_t = series.index[-1].strftime('%d/%m %H:%M')
        
        d_prev = yf.download(t, period="5d", interval="1d", progress=False)
        if isinstance(d_prev.columns, pd.MultiIndex): d_prev.columns = d_prev.columns.get_level_values(0)
        prev_c = float(d_prev['Close'].iloc[-2])
        
        vals[n], vals[n+'_DT'], vals[n+'_P'], vals[n+'_CHG'] = curr_p, curr_t, prev_c, (curr_p/prev_c-1)*100

    vals['MOM_LIVE'] = (vals['USA_CHG'] + vals['JPN_CHG'] + vals['FUT_CHG']) / 3 / 100
    vals['UPDATE_FULL'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    vals['VIX'] = vals['VIX']

    # --- DATI STORICI (2 ANNI) ---
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df_h = yf.download(tickers, period="2y", interval="1d", auto_adjust=True, progress=False)
    
    prices, opens = df_h['Close'], df_h['Open']
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['USA_C'], df['JAP_C'] = prices['^GSPC'], prices['^N225']
    df['USA_R'], df['JAP_R'] = df['USA_C'].pct_change().shift(1), df['JAP_C'].pct_change()
    df['FUT_C_Prev'] = prices['ES=F'].shift(1)
    df['R_9'], df['VIX_Val'] = (prices['ES=F'] / df['FUT_C_Prev']) - 1, prices['^VIX']
    df = df.dropna()

    data_list = []
    mom_series = (df['USA_R'] + df['JAP_R'] + df['R_9']) / 3
    for dt, row in df.iterrows():
        data_list.append({
            'd': dt.strftime('%d/%m/%Y'), 'ts_usa': (dt - pd.Timedelta(days=1)).strftime('%d/%m 21:00'),
            'ts_jap': dt.strftime('%d/%m 07:00'), 'ts_09': dt.strftime('%d/%m 09:00'),
            'm': float(mom_series[dt]), 'v': float(row['VIX_Val']),
            'p_raw': float((row['EU_C'] - row['EU_O']) * 10),
            'usa': float(row['USA_C']), 'jap': float(row['JAP_C']), 'fut': float(row['FUT_C_Prev'])
        })
    return vals, data_list

live, data_list = get_optimized_data()

# --- GENERAZIONE HTML ---
html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background-color: #05080a; color: #ffffff; font-family: 'Inter', sans-serif; }}
        .card-pro {{ background: #0f171e; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .header-main {{ background: #111827; border-bottom: 3px solid #3b82f6; padding: 25px; border-radius: 12px; margin-bottom: 20px; }}
        .live-tile {{ background: #000000; padding: 15px; border-radius: 10px; border: 1px solid #3b82f6; min-width: 170px; text-align: center; }}
        .live-value {{ font-size: 1.5rem; font-weight: 800; color: #ffffff; display: block; }}
        .ts-label {{ font-size: 0.75rem; color: #60a5fa; font-weight: bold; display: block; }}
        .stat-card {{ background: #111827; border-radius: 8px; padding: 12px; border: 1px solid #374151; height: 100%; text-align: center; }}
        .stat-label {{ font-size: 0.65rem; color: #9ca3af; text-transform: uppercase; font-weight: bold; display: block; }}
        .stat-value {{ font-size: 1.25rem; font-weight: 700; color: #ffffff; }}
        input {{ background: #ffffff !important; color: #000000 !important; font-weight: 900; font-size: 1.2rem; text-align: center; border: 2px solid #3b82f6 !important; }}
    </style>
</head>
<body class="p-4">
    <div class="container-fluid">
        <div class="header-main shadow">
            <h2 class="mb-1 fw-bold">EUROSTOXX 50 TERMINAL (AUTOMATED)</h2>
            <h4 id="todaySignal" class="text-warning fw-bold mt-2">...</h4>
            <div class="text-secondary small mt-1">Update: <b class="text-white">{live['UPDATE_FULL']}</b></div>
            <div class="d-flex justify-content-between gap-3 mt-4 flex-wrap">
                <div class="live-tile"><span class="ts-label">USA ({live['USA_DT']})</span><span class="live-value">{live['USA']:.2f}</span></div>
                <div class="live-tile"><span class="ts-label">JPN ({live['JPN_DT']})</span><span class="live-value">{live['JPN']:.2f}</span></div>
                <div class="live-tile"><span class="ts-label">FUT ({live['FUT_DT']})</span><span class="live-value">{live['FUT']:.2f}</span></div>
                <div class="live-tile" style="border-color:#10b981"><span class="ts-label" style="color:#10b981">MOMENTUM LIVE</span><span class="live-value" style="color:#10b981">{(live['MOM_LIVE']*100):+.2f}%</span></div>
            </div>
        </div>
        <div class="row">
            <div class="col-xl-4 col-lg-5">
                <div class="card-pro">
                    <label class="fw-bold mb-3 d-block text-center text-info small">SOGLIA STRATEGIA %</label>
                    <input type="number" id="threshold" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="runAnalysis()">
                    <div class="row g-2">
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Net Profit</span><span id="resPnL" class="stat-value">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Total Trades</span><span id="resTotal" class="stat-value">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Win Rate</span><span id="resWin" class="stat-value text-success">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Profit Factor</span><span id="resPF" class="stat-value">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label text-danger">Max DD</span><span id="resMDD" class="stat-value text-danger">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Expectancy</span><span id="resExp" class="stat-value">-</span></div></div>
                    </div>
                </div>
            </div>
            <div class="col-xl-8 col-lg-7">
                <div class="card-pro"><canvas id="equityChart" style="height: 380px;"></canvas></div>
            </div>
        </div>
    </div>
    <script>
        const rawData = {json.dumps(data_list)};
        const momLive = {float(live['MOM_LIVE'])};
        const vixLive = {float(live['VIX'])};
        let myChart = null;

        function runAnalysis() {{
            const thr = parseFloat(document.getElementById('threshold').value) / 100;
            let sToday = "FLAT ⚪";
            if (momLive > thr && vixLive < 25) sToday = "LONG 🟢";
            else if (momLive < -thr && vixLive < 32) sToday = "SHORT 🔴";
            document.getElementById('todaySignal').innerText = "SEGNALE ATTUALE: " + sToday;

            let cap = 20000; let pnlSum = 0; let wins = 0; let total = 0;
            let grossP = 0; let grossL = 0; let equity = []; 
            let maxCap = 20000; let maxDD = 0;

            rawData.forEach((item) => {{
                let sig = 0;
                if (item.m > thr && item.v < 25) sig = 1;
                else if (item.m < -thr && item.v < 32) sig = -1;
                
                if (sig !== 0) {{
                    total++;
                    const tPnL = sig * item.p_raw;
                    pnlSum += tPnL; cap += tPnL;
                    if (tPnL > 0) {{ wins++; grossP += tPnL; }} else {{ grossL += Math.abs(tPnL); }}
                }}
                equity.push(cap);
                if (cap > maxCap) maxCap = cap;
                let dd = ((maxCap - cap) / maxCap) * 100;
                if (dd > maxDD) maxDD = dd;
            }});

            document.getElementById('resPnL').innerText = pnlSum.toFixed(0) + " €";
            document.getElementById('resTotal').innerText = total;
            document.getElementById('resWin').innerText = total > 0 ? ((wins/total)*100).toFixed(1) + "%" : "0%";
            document.getElementById('resPF').innerText = grossL > 0 ? (grossP/grossL).toFixed(2) : "N/A";
            document.getElementById('resMDD').innerText = "-" + maxDD.toFixed(1) + "%";
            document.getElementById('resExp').innerText = total > 0 ? (pnlSum/total).toFixed(1) + " €" : "0 €";

            const ctx = document.getElementById('equityChart').getContext('2d');
            if (myChart) myChart.destroy();
            myChart = new Chart(ctx, {{
                type: 'line',
                data: {{ labels: rawData.map(x => x.d), datasets: [{{ label: 'Equity', data: equity, borderColor: '#3b82f6', borderWidth: 2, pointRadius: 0, fill: true, backgroundColor: 'rgba(59, 130, 246, 0.05)' }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
            }});
        }}
        window.onload = runAnalysis;
    </script>
</body>
</html>
"""

# --- UPLOAD ---
repo_name = "tobiatidesca-art/dashboard"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(repo_name)

try:
    contents = repo.get_contents("index.html", ref="main")
    repo.update_file(contents.path, "Update Dashboard (2Y)", html_content, contents.sha, branch="main")
except:
    repo.create_file("index.html", "Initial Commit", html_content, branch="main")

print("✅ Operazione completata!")

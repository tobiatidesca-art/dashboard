import yfinance as yf
import pandas as pd
import numpy as np
import json
import warnings
import os
from datetime import datetime
from github import Github 

try:
    from google.colab import userdata
    GITHUB_TOKEN = userdata.get('GITHUB_TOKEN')
except:
    GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')

warnings.filterwarnings("ignore")

def get_optimized_data():
    print("🚀 Recupero dati completi...")
    # Dati LIVE
    tk_live = {'^GSPC': 'USA', '^N225': 'JPN', 'ES=F': 'FUT', '^VIX': 'VIX'}
    vals = {}
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

    # Dati STORICI
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df_h = yf.download(tickers, period="2y", interval="1d", auto_adjust=True, progress=False)
    prices, opens = df_h['Close'], df_h['Open']
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_C_Prev'] = prices['ES=F'].shift(1)
    df['R_FUT'] = (prices['ES=F'] / df['FUT_C_Prev']) - 1
    df['VIX_Val'] = prices['^VIX']
    df = df.dropna()

    data_list = []
    mom_series = (df['USA_R'] + df['JAP_R'] + df['R_FUT']) / 3
    for dt, row in df.iterrows():
        data_list.append({
            'd': dt.strftime('%d/%m/%Y'),
            'm': float(mom_series[dt]),
            'v': float(row['VIX_Val']),
            'p_raw': float((row['EU_C'] - row['EU_O']) * 10)
        })
    return vals, data_list

live, data_list = get_optimized_data()

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
        .header-main {{ background: #111827; border-bottom: 3px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
        .live-tile {{ background: #000; padding: 12px; border-radius: 10px; border: 1px solid #3b82f6; text-align: center; flex: 1; min-width: 140px; }}
        .stat-card {{ background: #111827; border-radius: 8px; padding: 10px; border: 1px solid #374151; text-align: center; }}
        .stat-label {{ font-size: 0.65rem; color: #9ca3af; text-transform: uppercase; font-weight: bold; display: block; }}
        .stat-value {{ font-size: 1.1rem; font-weight: 700; }}
        input {{ background: #fff !important; font-weight: 900; text-align: center; border: 2px solid #3b82f6 !important; font-size: 1.2rem; }}
        .table-container {{ max-height: 500px; overflow-y: auto; }}
        .text-success {{ color: #10b981 !important; }}
        .text-danger {{ color: #ef4444 !important; }}
    </style>
</head>
<body class="p-3">
    <div class="header-main">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h2 class="fw-bold m-0">EUROSTOXX 50 TERMINAL</h2>
                <h4 id="todaySignal" class="text-warning fw-bold mt-1">Calcolo...</h4>
                <div class="text-secondary small">Update: <b>{live['UPDATE_FULL']}</b></div>
            </div>
            <div class="col-md-4 text-end d-none d-md-block">
                <span class="badge bg-primary">LIVE DATA FEED</span>
            </div>
        </div>
        <div class="d-flex justify-content-between gap-2 mt-3 flex-wrap">
            <div class="live-tile"><small class="text-info d-block">USA ({live['USA_DT']})</small><b>{live['USA']:.1f}</b></div>
            <div class="live-tile"><small class="text-info d-block">JPN ({live['JPN_DT']})</small><b>{live['JPN']:.1f}</b></div>
            <div class="live-tile"><small class="text-info d-block">FUT ({live['FUT_DT']})</small><b>{live['FUT']:.1f}</b></div>
            <div class="live-tile" style="border-color:#10b981"><small style="color:#10b981" class="d-block">MOMENTUM</small><b>{(live['MOM_LIVE']*100):+.2f}%</b></div>
        </div>
    </div>

    <div class="row">
        <div class="col-xl-4">
            <div class="card-pro">
                <label class="small text-info d-block text-center mb-2">SOGLIA STRATEGIA %</label>
                <input type="number" id="threshold" class="form-control mb-3" value="0.30" step="0.05" oninput="runAnalysis()">
                <div class="row g-2">
                    <div class="col-6"><div class="stat-card"><span class="stat-label">Net Profit</span><span id="resPnL" class="stat-value">-</span></div></div>
                    <div class="col-6"><div class="stat-card"><span class="stat-label">Total Trades</span><span id="resTotal" class="stat-value">-</span></div></div>
                    <div class="col-6"><div class="stat-card"><span class="stat-label">Win Rate</span><span id="resWin" class="stat-value text-success">-</span></div></div>
                    <div class="col-6"><div class="stat-card"><span class="stat-label">Profit Factor</span><span id="resPF" class="stat-value">-</span></div></div>
                    <div class="col-6"><div class="stat-card"><span class="stat-label text-danger">Max DD</span><span id="resDD" class="stat-value text-danger">-</span></div></div>
                    <div class="col-6"><div class="stat-card"><span class="stat-label">Expectancy</span><span id="resExp" class="stat-value">-</span></div></div>
                </div>
            </div>
        </div>
        <div class="col-xl-8">
            <div class="card-pro"><canvas id="equityChart" style="height: 330px;"></canvas></div>
        </div>
    </div>

    <div class="card-pro">
        <h5 class="text-info fw-bold mb-3">REGISTRO OPERAZIONI DETTAGLIATO</h5>
        <div class="table-container">
            <table class="table table-dark table-hover">
                <thead class="sticky-top bg-dark">
                    <tr><th>DATA</th><th>SEGNALE</th><th>RISULTATO (€)</th><th>MOMENTUM</th><th>VIX</th></tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        const rawData = {json.dumps(data_list)};
        const momLive = {float(live['MOM_LIVE'])};
        const vixLive = {float(live['VIX'])};
        let myChart = null;

        function runAnalysis() {{
            const thr = parseFloat(document.getElementById('threshold').value) / 100;
            let cap = 20000; let pnl = 0; let total = 0; let wins = 0;
            let grossWin = 0; let grossLoss = 0; let maxCap = 20000; let maxDD = 0;
            let equity = []; let labels = []; let html = "";

            // Segnale Real Time
            let sToday = "FLAT ⚪";
            if (momLive > thr && vixLive < 25) sToday = "LONG 🟢";
            else if (momLive < -thr && vixLive < 32) sToday = "SHORT 🔴";
            document.getElementById('todaySignal').innerText = "SEGNALE ATTUALE: " + sToday;

            rawData.forEach(item => {{
                let s = 0;
                if (item.m > thr && item.v < 25) s = 1;
                else if (item.m < -thr && item.v < 32) s = -1;

                if (s !== 0) {{
                    total++;
                    let tradePnL = s * item.p_raw;
                    pnl += tradePnL;
                    cap += tradePnL;
                    if (tradePnL > 0) {{ wins++; grossWin += tradePnL; }}
                    else {{ grossLoss += Math.abs(tradePnL); }}
                    
                    html = `<tr>
                        <td>${{item.d}}</td>
                        <td><span class="badge ${{s===1?'bg-success':'bg-danger'}}">${{s===1?'LONG':'SHORT'}}</span></td>
                        <td class="fw-bold ${{tradePnL>0?'text-success':'text-danger'}}">${{tradePnL.toFixed(0)}} €</td>
                        <td>${{(item.m*100).toFixed(2)}}%</td>
                        <td>${{item.v.toFixed(1)}}</td>
                    </tr>` + html;
                }}
                equity.push(cap);
                labels.push(item.d);
                if (cap > maxCap) maxCap = cap;
                let dd = ((maxCap - cap) / maxCap) * 100;
                if (dd > maxDD) maxDD = dd;
            }});

            document.getElementById('resPnL').innerText = pnl.toFixed(0) + " €";
            document.getElementById('resTotal').innerText = total;
            document.getElementById('resWin').innerText = total > 0 ? ((wins/total)*100).toFixed(1) + "%" : "0%";
            document.getElementById('resPF').innerText = grossLoss > 0 ? (grossWin/grossLoss).toFixed(2) : grossWin.toFixed(0);
            document.getElementById('resDD').innerText = "-" + maxDD.toFixed(1) + "%";
            document.getElementById('resExp').innerText = total > 0 ? (pnl/total).toFixed(1) + " €" : "0 €";
            document.getElementById('tableBody').innerHTML = html;

            if (myChart) myChart.destroy();
            myChart = new Chart(document.getElementById('equityChart'), {{
                type: 'line',
                data: {{ labels: labels, datasets: [{{ label: 'Equity (€)', data: equity, borderColor: '#3b82f6', borderWidth: 2, pointRadius: 0, fill: true, backgroundColor: 'rgba(59, 130, 246, 0.05)' }}] }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
            }});
        }}
        window.onload = runAnalysis;
    </script>
</body>
</html>
"""

repo_name = "tobiatidesca-art/dashboard"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(repo_name)
contents = repo.get_contents("index.html", ref="main")
repo.update_file(contents.path, "Full Restore: All Stats & Time Labels", html_content, contents.sha, branch="main")
print("✅ Dashboard ripristinata con tutte le funzioni!")

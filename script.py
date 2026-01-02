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
    print("🚀 Recupero dati (Ultimi 2 anni)...")
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

    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df_h = yf.download(tickers, period="2y", interval="1d", auto_adjust=True, progress=False)
    
    prices, opens = df_h['Close'], df_h['Open']
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['USA_C'], df['JAP_C'] = prices['^GSPC'], prices['^N225']
    df['USA_R'] = df['USA_C'].pct_change().shift(1)
    df['JAP_R'] = df['JAP_C'].pct_change()
    df['FUT_C_Prev'] = prices['ES=F'].shift(1)
    df['R_9'] = (prices['ES=F'] / df['FUT_C_Prev']) - 1
    df['VIX_Val'] = prices['^VIX']
    df = df.dropna()

    data_list = []
    mom_series = (df['USA_R'] + df['JAP_R'] + df['R_9']) / 3
    for dt, row in df.iterrows():
        data_list.append({
            'd': dt.strftime('%d/%m/%Y'), 'm': float(mom_series[dt]), 'v': float(row['VIX_Val']),
            'p_raw': float((row['EU_C'] - row['EU_O']) * 10),
            'usa': float(row['USA_C']), 'jap': float(row['JAP_C']), 'fut': float(row['FUT_C_Prev'])
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
        .header-main {{ background: #111827; border-bottom: 3px solid #3b82f6; padding: 25px; border-radius: 12px; margin-bottom: 20px; }}
        .live-tile {{ background: #000000; padding: 15px; border-radius: 10px; border: 1px solid #3b82f6; min-width: 170px; text-align: center; }}
        .live-value {{ font-size: 1.5rem; font-weight: 800; color: #ffffff; display: block; }}
        .stat-card {{ background: #111827; border-radius: 8px; padding: 12px; border: 1px solid #374151; height: 100%; text-align: center; }}
        .stat-label {{ font-size: 0.65rem; color: #9ca3af; text-transform: uppercase; font-weight: bold; display: block; }}
        .stat-value {{ font-size: 1.25rem; font-weight: 700; color: #ffffff; }}
        input {{ background: #ffffff !important; color: #000000 !important; font-weight: 900; font-size: 1.2rem; text-align: center; border: 2px solid #3b82f6 !important; }}
        .table {{ color: #e5e7eb; }}
    </style>
</head>
<body class="p-4">
    <div class="container-fluid">
        <div class="header-main">
            <h2 class="fw-bold">EUROSTOXX 50 TERMINAL</h2>
            <h4 id="todaySignal" class="text-warning fw-bold">...</h4>
            <div class="text-secondary small">Ultimo Aggiornamento: <b>{live['UPDATE_FULL']}</b></div>
            <div class="d-flex justify-content-between gap-2 mt-4 flex-wrap">
                <div class="live-tile"><span class="small text-info">USA</span><span class="live-value">{live['USA']:.1f}</span></div>
                <div class="live-tile"><span class="small text-info">JPN</span><span class="live-value">{live['JPN']:.1f}</span></div>
                <div class="live-tile"><span class="small text-info">FUT</span><span class="live-value">{live['FUT']:.1f}</span></div>
                <div class="live-tile" style="border-color:#10b981"><span class="small" style="color:#10b981">MOMENTUM</span><span class="live-value" style="color:#10b981">{(live['MOM_LIVE']*100):+.2f}%</span></div>
            </div>
        </div>
        <div class="row">
            <div class="col-xl-4">
                <div class="card-pro">
                    <label class="small text-info d-block text-center mb-2">SOGLIA OPERATIVA %</label>
                    <input type="number" id="threshold" class="form-control mb-4" value="0.30" step="0.05" oninput="runAnalysis()">
                    <div class="row g-2">
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Net PnL</span><span id="resPnL" class="stat-value">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Trades</span><span id="resTotal" class="stat-value">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label text-success">Win Rate</span><span id="resWin" class="stat-value">-</span></div></div>
                        <div class="col-6"><div class="stat-card"><span class="stat-label">Exp.</span><span id="resExp" class="stat-value">-</span></div></div>
                    </div>
                </div>
            </div>
            <div class="col-xl-8">
                <div class="card-pro"><canvas id="equityChart" style="height: 350px;"></canvas></div>
            </div>
        </div>
        <div class="card-pro">
            <h5 class="mb-3">Registro Ultime Operazioni</h5>
            <div class="table-responsive">
                <table class="table table-dark table-hover text-center">
                    <thead>
                        <tr><th>DATA</th><th>SEGNALE</th><th>PNL (€)</th><th>MOM%</th><th>VIX</th></tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
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
            
            // Segnale Real Time
            let sToday = "FLAT ⚪";
            if (momLive > thr && vixLive < 25) sToday = "LONG 🟢";
            else if (momLive < -thr && vixLive < 32) sToday = "SHORT 🔴";
            document.getElementById('todaySignal').innerText = "SEGNALE ATTUALE: " + sToday;

            let cap = 20000; let pnlSum = 0; let wins = 0; let total = 0;
            let equity = []; let tableHTML = "";

            // Analisi Storica
            rawData.forEach((item) => {{
                let sig = 0;
                if (item.m > thr && item.v < 25) sig = 1;
                else if (item.m < -thr && item.v < 32) sig = -1;
                
                let tPnL = 0;
                if (sig !== 0) {{
                    total++;
                    tPnL = sig * item.p_raw;
                    pnlSum += tPnL; cap += tPnL;
                    if (tPnL > 0) wins++;
                }}
                equity.push(cap);

                // Aggiungi riga alla tabella solo se c'è stato un segnale
                if (sig !== 0) {{
                    tableHTML = `<tr>
                        <td>${{item.d}}</td>
                        <td><span class="badge ${{sig===1?'bg-success':'bg-danger'}}">${{sig===1?'LONG':'SHORT'}}</span></td>
                        <td class="fw-bold" style="color:${{tPnL>0?'#10b981':'#ef4444'}}">${{tPnL.toFixed(0)}} €</td>
                        <td>${{(item.m*100).toFixed(2)}}%</td>
                        <td>${{item.v.toFixed(1)}}</td>
                    </tr>` + tableHTML; // Le più recenti in alto
                }}
            }});

            // Aggiorna KPI
            document.getElementById('resPnL').innerText = pnlSum.toFixed(0) + " €";
            document.getElementById('resTotal').innerText = total;
            document.getElementById('resWin').innerText = total > 0 ? ((wins/total)*100).toFixed(1) + "%" : "0%";
            document.getElementById('resExp').innerText = total > 0 ? (pnlSum/total).toFixed(1) + " €" : "0 €";
            document.getElementById('tableBody').innerHTML = tableHTML;

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

repo_name = "tobiatidesca-art/dashboard"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(repo_name)
contents = repo.get_contents("index.html", ref="main")
repo.update_file(contents.path, "Fix Table Display", html_content, contents.sha, branch="main")
print("✅ Tabella ripristinata!")

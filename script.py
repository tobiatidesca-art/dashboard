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

def get_advanced_data():
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
    df['USA_C'], df['JAP_C'], df['FUT_C'] = prices['^GSPC'], prices['^N225'], prices['ES=F']
    df['USA_R'] = df['USA_C'].pct_change().shift(1)
    df['JAP_R'] = df['JAP_C'].pct_change()
    df['FUT_Prev'] = df['FUT_C'].shift(1)
    df['R_FUT'] = (df['FUT_C'] / df['FUT_Prev']) - 1
    df['VIX_Val'] = prices['^VIX']
    df = df.dropna()

    data_list = []
    mom_series = (df['USA_R'] + df['JAP_R'] + df['R_FUT']) / 3
    for dt, row in df.iterrows():
        d_str = dt.strftime('%d/%m')
        data_list.append({
            'date': dt.strftime('%d/%m/%Y'),
            'mom': float(mom_series[dt]),
            'vix': float(row['VIX_Val']),
            'p_raw': float((row['EU_C'] - row['EU_O']) * 10),
            'usa': f"{row['USA_C']:.2f}<br><small class='text-secondary'>{d_str} 21:00</small>",
            'jap': f"{row['JAP_C']:.2f}<br><small class='text-secondary'>{d_str} 07:00</small>",
            'fut': f"{row['FUT_C']:.2f}<br><small class='text-secondary'>{d_str} 09:00</small>"
        })
    return vals, data_list

live, data_list = get_advanced_data()

html_content = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background-color: #05080a; color: #ffffff; font-family: sans-serif; padding: 20px; }}
        .card-pro {{ background: #0f171e; border: 1px solid #1f2937; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .header-main {{ background: #111827; border-bottom: 3px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
        .live-tile {{ background: #000; padding: 10px; border-radius: 8px; border: 1px solid #3b82f6; text-align: center; flex: 1; }}
        .stat-box {{ background: #111827; border: 1px solid #374151; border-radius: 8px; padding: 10px; text-align: center; height: 100%; }}
        .stat-label {{ font-size: 0.7rem; color: #9ca3af; font-weight: bold; text-transform: uppercase; display: block; }}
        .stat-val {{ font-size: 1.15rem; font-weight: bold; color: #fff; }}
        input {{ background: #fff !important; font-weight: bold; text-align: center; border: 2px solid #3b82f6 !important; height: 45px; }}
        .table {{ font-size: 0.85rem; vertical-align: middle; }}
        .text-success {{ color: #10b981 !important; }}
        .text-danger {{ color: #ef4444 !important; }}
    </style>
</head>
<body>
    <div class="header-main">
        <h2 class="fw-bold">EUROSTOXX 50 ADVANCED TERMINAL</h2>
        <h4 id="todaySignal" class="text-warning fw-bold">...</h4>
        <div class="small text-secondary">Aggiornamento: {live['UPDATE_FULL']}</div>
        <div class="d-flex gap-2 mt-3 flex-wrap">
            <div class="live-tile"><small class="text-info d-block">USA ({live['USA_DT']})</small><b>{live['USA']:.2f}</b></div>
            <div class="live-tile"><small class="text-info d-block">JPN ({live['JPN_DT']})</small><b>{live['JPN']:.2f}</b></div>
            <div class="live-tile"><small class="text-info d-block">FUT ({live['FUT_DT']})</small><b>{live['FUT']:.2f}</b></div>
            <div class="live-tile" style="border-color:#10b981"><small style="color:#10b981" class="d-block">MOMENTUM LIVE</small><b>{(live['MOM_LIVE']*100):+.2f}%</b></div>
        </div>
    </div>

    <div class="row">
        <div class="col-xl-4 col-lg-5">
            <div class="card-pro">
                <label class="small text-info d-block text-center mb-2">SOGLIA STRATEGIA %</label>
                <input type="number" id="threshold" class="form-control mb-4" value="0.30" step="0.05" oninput="runAnalysis()">
                
                <div class="row g-2">
                    <div class="col-6"><div class="stat-box"><span class="stat-label">PnL Netto</span><div id="resPnL" class="stat-val">-</div></div></div>
                    <div class="col-6"><div class="stat-box"><span class="stat-label">Trade Totali</span><div id="resTotal" class="stat-val">-</div></div></div>
                    <div class="col-6"><div class="stat-box"><span class="stat-label">Win Rate</span><div id="resWin" class="stat-val text-success">-</div></div></div>
                    <div class="col-6"><div class="stat-box"><span class="stat-label">Profit Factor</span><div id="resPF" class="stat-val">-</div></div></div>
                    <div class="col-6"><div class="stat-box"><span class="stat-label">Max Drawdown</span><div id="resDD" class="stat-val text-danger">-</div></div></div>
                    <div class="col-6"><div class="stat-box"><span class="stat-label">Expectancy</span><div id="resExp" class="stat-val">-</div></div></div>
                </div>
            </div>
        </div>
        <div class="col-xl-8 col-lg-7">
            <div class="card-pro"><canvas id="equityChart" style="height: 320px;"></canvas></div>
        </div>
    </div>

    <div class="card-pro">
        <h5 class="text-info fw-bold mb-3">Dettaglio Operazioni con Timestamp</h5>
        <div class="table-responsive" style="max-height: 500px;">
            <table class="table table-dark table-hover">
                <thead class="sticky-top bg-dark">
                    <tr><th>DATA</th><th>AZIONE</th><th>PNL</th><th>MOM%</th><th>USA</th><th>JPN</th><th>FUT</th></tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        const rawData = {json.dumps(data_list)};
        const momLive = {float(live['MOM_LIVE'])};
        const vixLive = {float(live['VIX'])};
        let chart = null;

        function runAnalysis() {{
            const thr = parseFloat(document.getElementById('threshold').value) / 100;
            let cap = 20000; let pnl = 0; let total = 0; let wins = 0;
            let gW = 0; let gL = 0; let maxC = 20000; let mDD = 0;
            let eq = []; let html = "";

            let sigT = "FLAT ⚪";
            if (momLive > thr && vixLive < 25) sigT = "LONG 🟢";
            else if (momLive < -thr && vixLive < 32) sigT = "SHORT 🔴";
            document.getElementById('todaySignal').innerText = "SEGNALE ATTUALE: " + sigT;

            rawData.forEach(item => {{
                let s = 0;
                if (item.mom > thr && item.vix < 25) s = 1;
                else if (item.mom < -thr && item.vix < 32) s = -1;

                let r = s * item.p_raw;
                if (s !== 0) {{ 
                    total++; pnl += r; 
                    if (r > 0) {{ wins++; gW += r; }} else {{ gL += Math.abs(r); }}
                }}
                cap += r;
                eq.push(cap);
                if (cap > maxC) maxC = cap;
                let dd = ((maxC - cap) / maxC) * 100;
                if (dd > mDD) mDD = dd;

                html = `<tr>
                    <td>${{item.date}}</td>
                    <td><span class="badge ${{s===0?'bg-secondary':(s===1?'bg-success':'bg-danger')}}">${{s===0?'FLAT':(s===1?'LONG':'SHORT')}}</span></td>
                    <td class="${{r>0?'text-success':(r<0?'text-danger':'text-muted')}}">${{r===0?'--':r.toFixed(0)+' €'}}</td>
                    <td>${{(item.mom*100).toFixed(2)}}%</td>
                    <td>${{item.usa}}</td><td>${{item.jap}}</td><td>${{item.fut}}</td>
                </tr>` + html;
            }});

            document.getElementById('resPnL').innerText = pnl.toFixed(0) + " €";
            document.getElementById('resTotal').innerText = total;
            document.getElementById('resWin').innerText = total > 0 ? ((wins/total)*100).toFixed(1) + "%" : "0%";
            document.getElementById('resPF').innerText = gL > 0 ? (gW/gL).toFixed(2) : "N/A";
            document.getElementById('resDD').innerText = "-" + mDD.toFixed(1) + "%";
            document.getElementById('resExp').innerText = total > 0 ? (pnl/total).toFixed(1) + " €" : "0 €";
            document.getElementById('tableBody').innerHTML = html;

            if (chart) chart.destroy();
            chart = new Chart(document.getElementById('equityChart'), {{
                type: 'line',
                data: {{ labels: rawData.map(x=>x.date), datasets: [{{ label: 'Equity', data: eq, borderColor: '#3b82f6', pointRadius: 0, fill: true, backgroundColor: 'rgba(59, 130, 246, 0.1)' }}] }},
                options: {{ responsive: true, maintainAspectRatio: false }}
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
repo.update_file(contents.path, "Fix statistics layout and table", html_content, contents.sha, branch="main")

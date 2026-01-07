
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

def get_data():
    tk_map = {'^GSPC': 'USA', '^N225': 'JPN', 'ES=F': 'FUT', '^VIX': 'VIX'}
    live_vals = {}
    for ticker, name in tk_map.items():
        d = yf.download(ticker, period="2d", interval="1m", progress=False)
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
        h = yf.download(ticker, period="5d", interval="1d", progress=False)
        if isinstance(h.columns, pd.MultiIndex): h.columns = h.columns.get_level_values(0)
        curr_p = float(d['Close'].iloc[-1])
        prev_c = float(h['Close'].iloc[-2])
        live_vals[name] = curr_p
        live_vals[name+'_CHG'] = (curr_p / prev_c - 1) * 100
    
    live_vals['MOM_LIVE'] = (live_vals['USA_CHG'] + live_vals['JPN_CHG'] + live_vals['FUT_CHG']) / 3 / 100
    live_vals['UPDATE_TS'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    live_vals['VIX_LIVE'] = live_vals['VIX']

    df_h = yf.download(['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F'], period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df_h['Close'] if isinstance(df_h.columns, pd.MultiIndex) else df_h
    opens = df_h['Open'] if isinstance(df_h.columns, pd.MultiIndex) else df_h
    
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    # PNL reale con moltiplicatore 10 e slippage 2.0
    df['PNL_RAW'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['MOM_TOTAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    df = df.dropna()
    
    history = []
    for dt, row in df.iterrows():
        history.append({'d': dt.strftime('%d/%m/%Y'), 'm': float(row['MOM_TOTAL']), 'v': float(row['VIX']), 'p': float(row['PNL_RAW'])})
    return live_vals, history

live, history = get_data()

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background: #05080a; color: #e6edf3; font-family: sans-serif; }}
        .card-custom {{ background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .header-main {{ background: #161b22; border-bottom: 2px solid #238636; padding: 20px; margin-bottom: 20px; }}
        input {{ background: #fff !important; color: #000 !important; font-weight: bold; width: 100px; display: inline-block; }}
    </style>
</head>
<body class="p-3">
    <div class="header-main">
        <h1>EUROSTOXX 50 <span class="text-success">ULTRA-H</span></h1>
        <div>Update: {live['UPDATE_TS']} | MOM LIVE: {(live['MOM_LIVE']*100):+.2f}%</div>
        <div id="liveSignal" class="h2 fw-bold text-warning mt-2">---</div>
    </div>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-3">
                <div class="card-custom">
                    <label class="d-block mb-2">Soglia Momentum (%)</label>
                    <input type="number" id="threshold" class="form-control mb-3" value="0.30" step="0.05" oninput="run()">
                    <div id="kpiGrid" class="mt-4"></div>
                </div>
            </div>
            <div class="col-md-9">
                <div class="card-custom" style="height: 600px;"><canvas id="equityChart"></canvas></div>
            </div>
        </div>
    </div>
    <script>
        const raw = {json.dumps(history)};
        const lM = {live['MOM_LIVE']};
        const lV = {live['VIX_LIVE']};
        let chart = null;

        function run() {{
            const thr = parseFloat(document.getElementById('threshold').value) / 100;
            
            // 1. SIGNAL LIVE
            let sig = "FLAT ⚪";
            if (lM > thr && lV < 25) sig = "LONG 🟢";
            else if (lM < -thr && lV < 32) sig = "SHORT 🔴";
            document.getElementById('liveSignal').innerText = sig;

            // 2. BACKTEST ENGINE
            let cap = 20000; 
            let equity = []; 
            let labels = [];
            
            raw.forEach(item => {{
                let s = 0;
                if (item.m > thr && item.v < 25) s = 1; 
                else if (item.m < -thr && item.v < 32) s = -1;
                
                cap += (s * item.p);
                equity.push(cap); 
                labels.push(item.d);
            }});

            // 3. UPDATE UI
            document.getElementById('kpiGrid').innerHTML = `
                <div class="p-3 border rounded">
                    <small class="text-secondary">NET PROFIT</small>
                    <h2 class="${{cap >= 20000 ? 'text-success' : 'text-danger'}}">${{(cap-20000).toFixed(0)}}€</h2>
                </div>`;

            if (chart) chart.destroy();
            chart = new Chart(document.getElementById('equityChart'), {{
                type: 'line',
                data: {{ 
                    labels: labels, 
                    datasets: [{{ 
                        label: 'Equity Curve', 
                        data: equity, 
                        borderColor: '#238636', 
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: true,
                        backgroundColor: 'rgba(35, 134, 54, 0.1)'
                    }}] 
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false,
                    scales: {{ x: {{ display: false }} }}
                }}
            }});
        }}
        window.onload = run;
    </script>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

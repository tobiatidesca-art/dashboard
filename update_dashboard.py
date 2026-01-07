
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

def get_quant_data():
    trade_map = {'^STOXX50E': 'EUROSTOXX', '^GDAXI': 'DAX'}
    signal_tickers = ['^GSPC', '^N225', '^VIX', 'ES=F']
    all_data = yf.download(list(trade_map.keys()) + signal_tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    
    prices = all_data['Close'] if isinstance(all_data.columns, pd.MultiIndex) else all_data
    opens = all_data['Open'] if isinstance(all_data.columns, pd.MultiIndex) else all_data

    usa_r = prices['^GSPC'].pct_change().shift(1)
    jap_r = prices['^N225'].pct_change()
    fut_r = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    mom_total = (usa_r + jap_r + fut_r) / 3
    vix = prices['^VIX']

    payload = {}
    for code, name in trade_map.items():
        slip = 2.0 if name == 'EUROSTOXX' else 3.5 
        mult = 10 if name == 'EUROSTOXX' else 1
        df = pd.DataFrame(index=prices.index)
        df['pnl'] = ((prices[code] - opens[code]) - slip) * mult
        df['m'] = mom_total
        df['v'] = vix
        df = df.dropna()
        history = []
        for dt, row in df.iterrows():
            history.append({'d': dt.strftime('%Y-%m-%d'), 'm': float(row['m']), 'v': float(row['v']), 'p': float(row['pnl'])})
        payload[name] = {'history': history, 'l_mom': float(df['m'].iloc[-1]), 'l_vix': float(df['v'].iloc[-1])}
    return payload, datetime.now().strftime('%H:%M:%S %d/%m/%Y')

db_payload, last_update = get_quant_data()

# Qui rigeneriamo l'HTML con i nuovi dati
html_template = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --bg: #0a0e14; --card: #11171f; --neon-blue: #00d2ff; --border: #232d39; }}
        body {{ background: var(--bg); color: #afbac4; font-family: sans-serif; }}
        .quant-header {{ background: #000; border-bottom: 2px solid var(--neon-blue); padding: 20px; }}
        .stat-card {{ background: var(--card); border: 1px solid var(--border); padding: 15px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="quant-header d-flex justify-content-between">
        <h4 class="text-white">QUANT-TERM V2</h4>
        <div class="text-end text-white">Last Update: {last_update}</div>
    </div>
    <div class="container-fluid p-4">
        <div class="row">
            <div class="col-md-3">
                <div class="stat-card">
                    <label>Asset</label>
                    <select id="asset" class="form-select bg-dark text-white" onchange="update()">
                        <option value="EUROSTOXX">EUROSTOXX 50</option>
                        <option value="DAX">DAX 40</option>
                    </select>
                    <div id="signalText" class="mt-3 h3 text-center">SCANNING...</div>
                </div>
            </div>
            <div class="col-md-9">
                <div class="stat-card" style="height:500px"><canvas id="equityChart"></canvas></div>
            </div>
        </div>
    </div>
    <script>
        const db = {json.dumps(db_payload)};
        let chart = null;
        function update() {{
            const asset = document.getElementById('asset').value;
            const data = db[asset];
            let sig = "FLAT";
            if (data.l_mom > 0.003) sig = "LONG 🟢";
            else if (data.l_mom < -0.003) sig = "SHORT 🔴";
            document.getElementById('signalText').innerText = sig;
            let balance = 20000; let eq = []; let lbl = [];
            data.history.forEach(d => {{ balance += d.p; eq.push(balance); lbl.push(d.d); }});
            if (chart) chart.destroy();
            chart = new Chart(document.getElementById('equityChart'), {{
                type: 'line', data: {{ labels: lbl, datasets: [{{ label: 'Equity', data: eq, borderColor: '#00d2ff', pointRadius: 0 }}] }}
            }});
        }}
        window.onload = update;
    </script>
</body>
</html>
"""
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

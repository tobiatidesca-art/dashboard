
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# =============================================================================
# MODULO 1: DATA_INGESTION_SYSTEM
# =============================================================================
def fetch_market_data():
    # Tickers per correlazione e segnali
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# =============================================================================
# MODULO 2: QUANT_STRATEGY_CORE
# =============================================================================
def calculate_quant_logic(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    
    # Indicatori proprietari
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # PnL con Slippage incluso (-2.0 punti)
    df['PNL_UNITARIO'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['MOM_SIGNAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    
    df = df.dropna()
    
    history = []
    for dt, row in df.iterrows():
        history.append({
            'd': dt.strftime('%d/%m/%Y'), 
            'm': float(row['MOM_SIGNAL']), 
            'v': float(row['VIX']), 
            'p': float(row['PNL_UNITARIO'])
        })
    
    live_snapshot = {
        'mom': float(df['MOM_SIGNAL'].iloc[-1]),
        'vix': float(df['VIX'].iloc[-1]),
        'last_update': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    return history, live_snapshot

# =============================================================================
# MODULO 3: DASHBOARD_UI_RENDERER (Visibile in HTML)
# =============================================================================
def generate_visual_interface(history, live):
    html_code = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{ --gh-dark: #0d1117; --gh-card: #161b22; --accent: #238636; }}
            body {{ background-color: var(--gh-dark); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--accent); padding: 15px; background: var(--gh-card); }}
            .card-module {{ background: var(--gh-card); border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; }}
            .mod-label {{ position: absolute; top: -10px; right: 10px; background: var(--accent); color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px; text-transform: uppercase; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow mb-4">
            <div class="container-fluid d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="h3 m-0">EUROSTOXX 50 <span style="color:var(--accent)">QUANT-PRO V3</span></h1>
                    <small class="text-secondary">MODULO_1: DATA_SYNC | {live['last_update']}</small>
                </div>
                <div class="text-end">
                    <span class="badge bg-dark border border-secondary text-secondary">MODULO_2: CORE_LOGIC</span>
                    <div id="live-signal" class="h2 fw-bold text-warning m-0">---</div>
                </div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-3">
                <div class="col-lg-3">
                    <div class="card-module shadow">
                        <span class="mod-label">Modulo 3: UI_CONTROLS</span>
                        <label class="small fw-bold text-secondary mb-2 d-block">MOMENTUM THRESHOLD (%)</label>
                        <input type="number" id="thr-input" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="refresh()">
                        <div id="kpi-panel"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-module shadow">
                        <span class="mod-label">Modulo 3: CHART_ENGINE</span>
                        <div style="height: 500px;"><canvas id="equity-chart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const historyData = {json.dumps(history)};
            const curMom = {live['mom']};
            const curVix = {live['vix']};
            let chartInstance = null;

            function refresh() {{
                const threshold = parseFloat(document.getElementById('thr-input').value) / 100;
                
                // Segnale Real-Time
                let signalTxt = "FLAT ⚪";
                if (curMom > threshold && curVix < 25) signalTxt = "LONG 🟢";
                else if (curMom < -threshold && curVix < 32) signalTxt = "SHORT 🔴";
                document.getElementById('live-signal').innerText = signalTxt;

                // Calcolo Backtest
                let balance = 20000; let curve = []; let labels = [];
                historyData.forEach(row => {{
                    let side = 0;
                    if (row.m > threshold && row.v < 25) side = 1; 
                    else if (row.m < -threshold && row.v < 32) side = -1;
                    balance += (side * row.p);
                    curve.push(balance);
                    labels.push(row.d);
                }});

                const profit = balance - 20000;
                document.getElementById('kpi-panel').innerHTML = `
                    <div class="text-center p-3 rounded bg-black border border-secondary">
                        <span class="text-secondary small">NET PROFIT (MODULO_2)</span>
                        <h2 class="${{profit >= 0 ? 'text-success' : 'text-danger'}} mt-1">€ ${{profit.toLocaleString('it-IT', {{maximumFractionDigits: 0}})}}</h2>
                    </div>`;

                if (chartInstance) chartInstance.destroy();
                chartInstance = new Chart(document.getElementById('equity-chart'), {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            data: curve,
                            borderColor: '#238636',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: 'rgba(35, 134, 54, 0.05)'
                        }}]
                    }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ x: {{ display: false }}, y: {{ grid: {{ color: '#21262d' }} }} }}
                    }}
                }});
            }}
            window.onload = refresh;
        </script>
    </body>
    </html>
    """
    return html_code

# =============================================================================
# MODULO 4: SYSTEM_ORCHESTRATOR
# =============================================================================
p_raw, o_raw = fetch_market_data()
h_list, l_met = calculate_quant_logic(p_raw, o_raw)
final_html = generate_visual_interface(h_list, l_met)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_html)

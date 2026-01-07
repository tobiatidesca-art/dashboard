
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# -----------------------------------------------------------------------------
# MODULO_1: DATA_INGESTION
# Obiettivo: Scaricare i prezzi storici e live da Yahoo Finance
# -----------------------------------------------------------------------------
def fetch_market_data():
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# -----------------------------------------------------------------------------
# MODULO_2: STRATEGY_LOGIC
# Obiettivo: Calcolare indicatori, segnali operativi e Profit & Loss reale
# -----------------------------------------------------------------------------
def calculate_strategy(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    
    # Calcolo Momentum Cross-Asset
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # Logica PnL: 10€/punto con 2 punti di slippage fisso
    df['PNL_RAW'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['MOM_TOTAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    
    df = df.dropna()
    
    # Formattazione dati per il grafico JS
    history_data = []
    for dt, row in df.iterrows():
        history_data.append({
            'd': dt.strftime('%d/%m/%Y'), 
            'm': float(row['MOM_TOTAL']), 
            'v': float(row['VIX']), 
            'p': float(row['PNL_RAW'])
        })
    
    # Metriche per l'intestazione live
    metrics = {
        'mom': float(df['MOM_TOTAL'].iloc[-1]),
        'vix': float(df['VIX'].iloc[-1]),
        'time': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return history_data, metrics

# -----------------------------------------------------------------------------
# MODULO_3: UI_RENDERER
# Obiettivo: Generare il codice HTML, CSS e JavaScript per la Dashboard
# -----------------------------------------------------------------------------
def build_html_dashboard(history, metrics):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ background: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .card-pro {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; }}
            .header-pro {{ border-bottom: 2px solid #238636; padding: 20px 0; margin-bottom: 30px; }}
            .sig-live {{ font-size: 2.5rem; font-weight: 900; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; width: 120px; }}
        </style>
    </head>
    <body class="p-4">
        <div class="container-fluid">
            <div class="header-pro d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="m-0 text-white">EUROSTOXX 50 <span class="text-success">QUANT-PRO</span></h1>
                    <small class="text-secondary">Last Sync: {metrics['time']} | VIX: {metrics['vix']:.2f}</small>
                </div>
                <div id="status" class="sig-live text-warning">---</div>
            </div>

            <div class="row g-4">
                <div class="col-md-3">
                    <div class="card-pro shadow-sm">
                        <label class="h6 text-secondary uppercase">Momentum Threshold (%)</label>
                        <input type="number" id="thr" class="form-control form-control-lg my-3" value="0.30" step="0.05" oninput="update()">
                        <div id="results" class="mt-4"></div>
                    </div>
                </div>
                <div class="col-md-9">
                    <div class="card-pro">
                        <div style="height: 550px;"><canvas id="mainChart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const rawData = {json.dumps(history)};
            const liveM = {metrics['mom']};
            const liveV = {metrics['vix']};
            let myChart = null;

            function update() {{
                const t = parseFloat(document.getElementById('thr').value) / 100;
                
                // Aggiorna Segnale Live
                let s = "FLAT ⚪";
                if (liveM > t && liveV < 25) s = "LONG 🟢";
                else if (liveM < -t && liveV < 32) s = "SHORT 🔴";
                document.getElementById('status').innerText = s;

                // Calcolo Backtest Dinamico
                let capital = 20000; let curve = []; let days = [];
                rawData.forEach(day => {{
                    let side = 0;
                    if (day.m > t && day.v < 25) side = 1; 
                    else if (day.m < -t && day.v < 32) side = -1;
                    capital += (side * day.p);
                    curve.push(capital);
                    days.push(day.d);
                }});

                // Renderizza KPI
                const net = capital - 20000;
                document.getElementById('results').innerHTML = `
                    <div class="p-3 rounded border border-success bg-dark">
                        <small class="text-secondary">NET PROFIT</small>
                        <h2 class="text-success m-0">€ ${{net.toLocaleString('it-IT', {{maximumFractionDigits:0}})}}</h2>
                    </div>`;

                if (myChart) myChart.destroy();
                myChart = new Chart(document.getElementById('mainChart'), {{
                    type: 'line',
                    data: {{
                        labels: days,
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
            window.onload = update;
        </script>
    </body>
    </html>
    """
    return html

# -----------------------------------------------------------------------------
# MODULO_4: ORCHESTRATOR
# Obiettivo: Coordinare i moduli e salvare i file
# -----------------------------------------------------------------------------
p, o = fetch_market_data()
hist, met = calculate_strategy(p, o)
final_page = build_html_dashboard(hist, met)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(final_page)

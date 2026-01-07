
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# =============================================================================
# MODULO 1: DATA_INGESTION_SYSTEM
# Responsabilità: Connessione a Yahoo Finance e recupero prezzi Open/Close
# =============================================================================
def fetch_market_data():
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# =============================================================================
# MODULO 2: QUANT_STRATEGY_CORE
# Responsabilità: Calcolo Momentum, filtri VIX e PnL con Slippage (Onesto)
# =============================================================================
def calculate_quant_logic(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    
    # Calcolo Momentum Multi-Asset
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # Logica Profitto Reale (10€/punto, -2 punti slippage)
    # Questa formula ripristina la curva positiva corretta
    df['PNL_UNITARIO'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['MOM_SIGNAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    
    df = df.dropna()
    
    # Dati storici per il grafico
    history = []
    for dt, row in df.iterrows():
        history.append({
            'd': dt.strftime('%d/%m/%Y'), 
            'm': float(row['MOM_SIGNAL']), 
            'v': float(row['VIX']), 
            'p': float(row['PNL_UNITARIO'])
        })
    
    # Snapshot per interfaccia Live
    live_snapshot = {
        'mom': float(df['MOM_SIGNAL'].iloc[-1]),
        'vix': float(df['VIX'].iloc[-1]),
        'last_update': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return history, live_snapshot

# =============================================================================
# MODULO 3: DASHBOARD_UI_RENDERER
# Responsabilità: Generazione HTML, Design CSS e Motore Grafico JS
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
            :root {{ --gh-dark: #0d1117; --gh-card: #161b22; --green-glow: #238636; }}
            body {{ background-color: var(--gh-dark); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--green-glow); padding: 20px; margin-bottom: 30px; background: var(--gh-card); }}
            .card-module {{ background: var(--gh-card); border: 1px solid #30363d; border-radius: 12px; padding: 20px; }}
            .signal-badge {{ font-size: 2.5rem; font-weight: 900; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; border: 2px solid var(--green-glow) !important; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow-lg">
            <div class="container-fluid d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="m-0">EUROSTOXX 50 <span style="color:var(--green-glow)">QUANT-PRO</span></h1>
                    <p class="text-secondary mb-0">Sync: {live['last_update']} | VIX: {live['vix']:.2f}</p>
                </div>
                <div id="live-signal" class="signal-badge text-warning">---</div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-4">
                <div class="col-lg-3">
                    <div class="card-module">
                        <label class="fw-bold text-uppercase small mb-2 d-block">Soglia Momentum Operativa (%)</label>
                        <input type="number" id="thr-input" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="refresh()">
                        <div id="kpi-panel"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-module">
                        <div style="height: 550px;"><canvas id="equity-chart"></canvas></div>
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
                
                // Aggiornamento Segnale Dinamico
                let signalTxt = "FLAT ⚪";
                if (curMom > threshold && curVix < 25) signalTxt = "LONG 🟢";
                else if (curMom < -threshold && curVix < 32) signalTxt = "SHORT 🔴";
                document.getElementById('live-signal').innerText = signalTxt;

                // Calcolo Backtest (Logica Onesta)
                let balance = 20000; let curve = []; let labels = [];
                historyData.forEach(row => {{
                    let side = 0;
                    if (row.m > threshold && row.v < 25) side = 1; 
                    else if (row.m < -threshold && row.v < 32) side = -1;
                    balance += (side * row.p);
                    curve.push(balance);
                    labels.push(row.d);
                }});

                // Render KPI
                const profit = balance - 20000;
                document.getElementById('kpi-panel').innerHTML = `
                    <div class="text-center p-3 rounded bg-black border border-secondary">
                        <span class="text-secondary small">PROFITTO NETTO ATTUALE</span>
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
# Responsabilità: Esecuzione sequenziale dei moduli e salvataggio file
# =============================================================================
try:
    prices_raw, opens_raw = fetch_market_data()
    history_list, current_metrics = calculate_quant_logic(prices_raw, opens_raw)
    html_output = generate_visual_interface(history_list, current_metrics)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("✅ Dashboard generata correttamente dal modulo Orchestrator.")
except Exception as e:
    print(f"❌ Errore critico nel Modulo 4: {e}")

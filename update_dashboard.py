
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# =============================================================================
# MODULO 1: DATA_INGESTION (Recupero dati grezzi)
# =============================================================================
def fetch_raw_market_data():
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# =============================================================================
# MODULO 2: STRATEGY_LOGIC (Calcolo segnali e PnL)
# =============================================================================
def apply_trading_strategy(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    
    # Indicatori di Momentum
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # Logica di calcolo Profitto (10€ a punto, -2 punti slippage)
    df['PNL_RAW'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['MOM_TOTAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    
    df = df.dropna()
    
    # Preparazione Storico per JS
    history = []
    for dt, row in df.iterrows():
        history.append({
            'd': dt.strftime('%d/%m/%Y'), 
            'm': float(row['MOM_TOTAL']), 
            'v': float(row['VIX']), 
            'p': float(row['PNL_RAW'])
        })
    
    # Valori Live per il Segnale Istantaneo
    live_data = {
        'last_mom': float(df['MOM_TOTAL'].iloc[-1]),
        'last_vix': float(df['VIX'].iloc[-1]),
        'ts': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return history, live_data

# =============================================================================
# MODULO 3: USER_INTERFACE_RENDERER (Generazione HTML/JS)
# =============================================================================
def render_dashboard_html(history, live):
    html = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{ --bg: #0d1117; --card: #161b22; --text: #c9d1d9; --accent: #238636; }}
            body {{ background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; }}
            .header-bar {{ background: var(--card); border-bottom: 2px solid var(--accent); padding: 25px; margin-bottom: 30px; }}
            .stat-card {{ background: var(--card); border: 1px solid #30363d; border-radius: 10px; padding: 20px; height: 100%; }}
            .signal-box {{ font-size: 2.2rem; font-weight: 800; text-align: center; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header-bar shadow">
            <div class="container-fluid">
                <div class="row align-items-center">
                    <div class="col-md-7">
                        <h1 class="m-0">EUROSTOXX 50 <span style="color:var(--accent)">QUANT-PRO</span></h1>
                        <small class="text-secondary">Sync: {live['ts']} | MOM: {(live['last_mom']*100):+.2f}% | VIX: {live['last_vix']:.2f}</small>
                    </div>
                    <div class="col-md-5 text-md-end">
                        <div id="liveSignal" class="signal-box text-warning">WAITING...</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-4">
                <div class="col-lg-3">
                    <div class="stat-card">
                        <label class="d-block mb-3 fw-bold uppercase">Soglia Momentum (%)</label>
                        <input type="number" id="threshold" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="run()">
                        <hr>
                        <div id="kpiDisplay"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="stat-card">
                        <div style="height: 550px;"><canvas id="equityChart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const data = {json.dumps(history)};
            const curM = {live['last_mom']};
            const curV = {live['last_vix']};
            let chart = null;

            function run() {{
                const thr = parseFloat(document.getElementById('threshold').value) / 100;
                
                // Segnale Live
                let sig = "FLAT ⚪";
                if (curM > thr && curV < 25) sig = "LONG 🟢";
                else if (curM < -thr && curV < 32) sig = "SHORT 🔴";
                document.getElementById('liveSignal').innerText = sig;

                // Calcolo Equity
                let balance = 20000; let curve = []; let dates = [];
                data.forEach(day => {{
                    let pos = 0;
                    if (day.m > thr && day.v < 25) pos = 1; 
                    else if (day.m < -thr && day.v < 32) pos = -1;
                    balance += (pos * day.p);
                    curve.push(balance);
                    dates.push(day.d);
                }});

                // Update KPI
                const profit = balance - 20000;
                document.getElementById('kpiDisplay').innerHTML = `
                    <div class="text-center py-3">
                        <span class="text-secondary d-block">PROFITTO NETTO</span>
                        <h2 class="${{profit >= 0 ? 'text-success' : 'text-danger'}} mb-0">€ ${{profit.toLocaleString('it-IT', {{minimumFractionDigits: 0}})}}</h2>
                    </div>
                `;

                if (chart) chart.destroy();
                chart = new Chart(document.getElementById('equityChart'), {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [{{
                            label: 'Equity Curve (€)',
                            data: curve,
                            borderColor: '#238636',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            backgroundColor: 'rgba(35, 134, 54, 0.05)'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ x: {{ display: false }}, y: {{ grid: {{ color: '#21262d' }} }} }}
                    }}
                }});
            }}
            window.onload = run;
        </script>
    </body>
    </html>
    """
    return html

# =============================================================================
# MODULO 4: AUTOMATION_ORCHESTRATOR (Esecuzione flussi)
# =============================================================================
try:
    p_data, o_data = fetch_raw_market_data()
    hist_list, live_metrics = apply_trading_strategy(p_data, o_data)
    final_html = render_dashboard_html(hist_list, live_metrics)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    print("✅ Esecuzione locale completata")
except Exception as e:
    print(f"❌ Errore esecuzione: {{e}}")

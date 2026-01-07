
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# =============================================================================
# MODULO 1: DATA_INGESTION
# =============================================================================
def fetch_market_data():
    # Aggiunto ^GDAXI (DAX) alla lista dei ticker
    tickers = ['^STOXX50E', '^GDAXI', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# =============================================================================
# MODULO 2: STRATEGY_CORE (Multi-Asset)
# =============================================================================
def calculate_quant_logic(prices, opens):
    df = pd.DataFrame(index=prices.index)
    
    # Dati EuroStoxx50
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    # Dati DAX
    df['DAX_O'], df['DAX_C'] = opens['^GDAXI'], prices['^GDAXI']
    
    # Indicatori comuni
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # Calcolo PnL Strategia per entrambi (10€/punto, -2.0 slippage)
    df['PNL_EU'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['PNL_DAX'] = ((df['DAX_C'] - df['DAX_O']) - 2.0) * 25 # DAX moltiplicatore standard è spesso 25, teniamo 25 o 10? Usiamo 25 per realismo.
    
    df['MOM_SIGNAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    df = df.dropna()
    
    history = []
    for dt, row in df.iterrows():
        history.append({
            'd': dt.strftime('%Y-%m-%d'),
            'm': float(row['MOM_SIGNAL']), 
            'v': float(row['VIX']), 
            'p_eu': float(row['PNL_EU']),
            'p_dax': float(row['PNL_DAX']),
            'idx_eu': float(row['EU_C']),
            'idx_dax': float(row['DAX_C'])
        })
    
    live_snapshot = {
        'mom': float(df['MOM_SIGNAL'].iloc[-1]),
        'vix': float(df['VIX'].iloc[-1]),
        'last_update': datetime.now().strftime('%H:%M:%S %d/%m/%Y')
    }
    return history, live_snapshot

# =============================================================================
# MODULO 6: MULTILANGUAGE_MANAGER
# =============================================================================
def get_language_pack():
    return {
        "en": {
            "title": "QUANT-PRO V5", "sync": "Modulo 1: Data Sync", "core": "MODULO 2: CORE_LOGIC",
            "controls": "MODULO 3: UI_CONTROLS", "chart": "MODULO 4: CHART_ENGINE",
            "threshold": "MOMENTUM THRESHOLD (%)", "profit": "NET PROFIT", 
            "equity": "Equity Curve (€)", "benchmark": "Index Reference", "asset": "SELECT ASSET"
        },
        "de": {
            "title": "QUANT-PRO V5", "sync": "Modul 1: Daten", "core": "MODUL 2: KERNLOGIK",
            "controls": "MODUL 3: STEUERUNG", "chart": "MODUL 4: CHART",
            "threshold": "SCHWELLE (%)", "profit": "GEWINN", 
            "equity": "Equity (€)", "benchmark": "Index-Referenz", "asset": "ASSET WÄHLEN"
        } # ... altre lingue seguono lo stesso schema
    }

# =============================================================================
# MODULO 3 & 4: UI & CHART ENGINE
# =============================================================================
def generate_visual_interface(history, live):
    lang_pack = get_language_pack()
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{ --bg: #0d1117; --card: #161b22; --accent: #238636; --dax: #ffcc00; }}
            body {{ background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--accent); padding: 15px; background: var(--card); }}
            .card-mod {{ background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; }}
            .tag {{ position: absolute; top: -10px; right: 10px; background: var(--accent); color: white; font-size: 9px; padding: 2px 7px; border-radius: 4px; font-weight: bold; }}
            .custom-select {{ background: #1c2128; color: #fff; border: 1px solid #444c56; border-radius: 6px; padding: 8px; width: 100%; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow mb-4">
            <div class="container-fluid d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="h3 m-0 text-white" id="ui-title">QUANT-PRO V5</h1>
                    <small class="text-secondary text-uppercase" id="ui-sync">Data Sync | {live['last_update']}</small>
                </div>
                <div class="d-flex align-items-center gap-3">
                    <select class="custom-select" id="asset-select" onchange="run()">
                        <option value="eu">EUROSTOXX 50 🇪🇺</option>
                        <option value="dax">DAX 40 🇩🇪</option>
                    </select>
                    <select class="custom-select" id="lang-switch" onchange="run()">
                        <option value="en">English 🇺🇸</option>
                        <option value="de">Deutsch 🇩🇪</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-3">
                <div class="col-lg-3">
                    <div class="card-mod shadow-sm">
                        <span class="tag" id="tag-controls">CONTROLS</span>
                        <label class="small fw-bold text-secondary mb-2 d-block" id="ui-threshold-label">THRESHOLD (%)</label>
                        <input type="number" id="thr" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="run()">
                        <div id="kpi-box"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-mod shadow-sm">
                        <span class="tag" id="tag-chart">CHART ENGINE</span>
                        <div style="height: 520px;"><canvas id="main-chart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const raw = {json.dumps(history)};
            const lM = {live['mom']};
            const lV = {live['vix']};
            const langPack = {json.dumps(lang_pack)};
            let chart = null;

            function run() {{
                const lang = document.getElementById('lang-switch').value;
                const asset = document.getElementById('asset-select').value;
                const t = parseFloat(document.getElementById('thr').value) / 100;
                const tP = langPack[lang] || langPack['en'];

                // Segnale Live
                let sig = "FLAT ⚪";
                if (lM > t && lV < 25) sig = "LONG 🟢";
                else if (lM < -t && lV < 32) sig = "SHORT 🔴";
                
                // Calcolo Backtest Dinamico in base all'asset
                let cap = 20000; let curve = []; let days = []; let benchmark = [];
                raw.forEach(r => {{
                    let s = 0;
                    if (r.m > t && r.v < 25) s = 1; else if (r.m < -t && r.v < 32) s = -1;
                    
                    let pnl = (asset === 'eu') ? r.p_eu : r.p_dax;
                    let idx = (asset === 'eu') ? r.idx_eu : r.idx_dax;
                    
                    cap += (s * pnl);
                    curve.push(cap);
                    days.push(r.d);
                    benchmark.push(idx);
                }});

                document.getElementById('kpi-box').innerHTML = `
                    <div class="text-center p-3 rounded bg-black border border-secondary mt-2">
                        <span class="text-secondary small">NET PROFIT (${{asset.toUpperCase()}})</span>
                        <h2 class="${{cap >= 20000 ? 'text-success' : 'text-danger'}} mt-1">€ ${{ (cap-20000).toLocaleString('it-IT', {{maximumFractionDigits: 0}}) }}</h2>
                    </div>`;

                if (chart) chart.destroy();
                chart = new Chart(document.getElementById('main-chart'), {{
                    type: 'line',
                    data: {{
                        labels: days,
                        datasets: [
                            {{
                                label: tP.equity,
                                data: curve,
                                borderColor: '#238636',
                                backgroundColor: 'rgba(35, 134, 54, 0.1)',
                                borderWidth: 2, pointRadius: 0, fill: true, yAxisID: 'y'
                            }},
                            {{
                                label: tP.benchmark + " (" + asset.toUpperCase() + ")",
                                data: benchmark,
                                borderColor: '#58a6ff',
                                borderWidth: 1, pointRadius: 0, fill: false, yAxisID: 'y1'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        scales: {{
                            x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 12 }} }},
                            y: {{ position: 'left', title: {{ display: true, text: 'Equity (€)' }} }},
                            y1: {{ position: 'right', grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Index Points' }} }}
                        }}
                    }}
                }});
            }}
            window.onload = run;
        </script>
    </body>
    </html>
    """
    return html_code

# =============================================================================
# MODULO 5: SYSTEM_ORCHESTRATOR
# =============================================================================
p, o = fetch_market_data()
hist, metrics = calculate_quant_logic(p, o)
page = generate_visual_interface(hist, metrics)
with open("index.html", "w", encoding="utf-8") as f: f.write(page)

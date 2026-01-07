
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# --- MODULO 1: DATA_INGESTION ---
def fetch_market_data():
    tickers = ['^STOXX50E', '^GDAXI', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# --- MODULO 2: STRATEGY_CORE ---
def calculate_quant_logic(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['DAX_O'], df['DAX_C'] = opens['^GDAXI'], prices['^GDAXI']
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # PnL (10€/punto, -2.0 slippage)
    df['PNL_EU'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['PNL_DAX'] = ((df['DAX_C'] - df['DAX_O']) - 2.0) * 10
    
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

# --- MODULO 6: MULTILANGUAGE_MANAGER (Full Restore) ---
def get_language_pack():
    return {
        "en": {
            "title": "QUANT-PRO", "sync": "Modulo 1: Data Sync", "core": "MODULO 2: CORE_LOGIC",
            "controls": "MODULO 3: UI_CONTROLS", "chart": "MODULO 4: CHART_ENGINE",
            "threshold": "MOMENTUM THRESHOLD (%)", "profit": "NET PROFIT", 
            "equity": "Equity Curve (€)", "benchmark": "Index Reference", 
            "select_asset": "CHOOSE TRADING ASSET", "select_lang": "CHOOSE LANGUAGE"
        },
        "de": {
            "title": "QUANT-PRO", "sync": "Modul 1: Daten", "core": "MODUL 2: KERNLOGIK",
            "controls": "MODUL 3: STEUERUNG", "chart": "MODUL 4: CHART",
            "threshold": "SCHWELLE (%)", "profit": "GEWINN", 
            "equity": "Equity (€)", "benchmark": "Index-Referenz",
            "select_asset": "HANDELSOBJEKT WÄHLEN", "select_lang": "SPRACHE WÄHLEN"
        },
        "fr": {
            "title": "QUANT-PRO", "sync": "Module 1: Sync", "core": "MODULE 2: LOGIQUE",
            "controls": "MODULE 3: CONTRÔLES", "chart": "MODULE 4: GRAPHIQUE",
            "threshold": "SEUIL (%)", "profit": "PROFIT NET", 
            "equity": "Équité (€)", "benchmark": "Indice de Référence",
            "select_asset": "CHOISIR L'ACTIF", "select_lang": "CHOISIR LA LANGUE"
        },
        "es": {
            "title": "QUANT-PRO", "sync": "Módulo 1: Sinc", "core": "MÓDULO 2: LÓGICA",
            "controls": "MÓDULO 3: CONTROLES", "chart": "MÓDULO 4: GRÁFICO",
            "threshold": "UMBRAL (%)", "profit": "BENEFICIO NETO", 
            "equity": "Equidad (€)", "benchmark": "Índice de Referencia",
            "select_asset": "ELEGIR ACTIVO", "select_lang": "ELEGIR IDIOMA"
        },
        "zh": {
            "title": "QUANT-PRO", "sync": "模块 1: 数据", "core": "模块 2: 逻辑",
            "controls": "模块 3: 控制", "chart": "模块 4: 图表",
            "threshold": "阈值 (%)", "profit": "净利润", 
            "equity": "权益 (€)", "benchmark": "参考指数",
            "select_asset": "选择交易资产", "select_lang": "选择语言"
        }
    }

# --- MODULO 3 & 4: UI & CHART ---
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
            :root {{ --bg: #0d1117; --card: #161b22; --accent: #238636; --gold: #f1c40f; }}
            body {{ background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--accent); padding: 20px; background: var(--card); }}
            .top-control-box {{ 
                background: #1c2128; border-left: 4px solid var(--accent); border-radius: 8px; padding: 15px; margin-bottom: 15px;
            }}
            .lang-box {{ border-left: 4px solid var(--gold) !important; }}
            .card-mod {{ background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; }}
            .tag {{ position: absolute; top: -10px; right: 10px; background: var(--accent); color: white; font-size: 9px; padding: 2px 7px; border-radius: 4px; font-weight: bold; }}
            .custom-select {{ 
                background: #0d1117; color: #fff; border: 1px solid #444c56; border-radius: 8px; 
                padding: 10px; width: 100%; font-weight: bold; cursor: pointer;
            }}
            .custom-select:focus {{ border-color: var(--accent); outline: none; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow-lg mb-4">
            <div class="container-fluid d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="h2 m-0 text-white" id="ui-title">QUANT-PRO <span class="text-success">V5.2</span></h1>
                    <small class="text-secondary" id="ui-sync">MODULO 1 | {live['last_update']}</small>
                </div>
                <div id="signal-display" class="h1 fw-bold text-warning m-0">---</div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-3 mb-3">
                <div class="col-md-6">
                    <div class="top-control-box shadow-sm">
                        <label class="small fw-bold text-accent mb-2 d-block text-uppercase" id="ui-asset-label" style="color:var(--accent)">{lang_pack['en']['select_asset']}</label>
                        <select class="custom-select" id="asset-select" onchange="run()">
                            <option value="eu">EURO STOXX 50 (European Blue Chips) 🇪🇺</option>
                            <option value="dax">DAX 40 (German Stock Index) 🇩🇪</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="top-control-box lang-box shadow-sm">
                        <label class="small fw-bold mb-2 d-block text-uppercase" id="ui-lang-label" style="color:var(--gold)">{lang_pack['en']['select_lang']}</label>
                        <select class="custom-select" id="lang-switch" onchange="run()" style="border-color:var(--gold)">
                            <option value="en">English 🇺🇸</option>
                            <option value="de">Deutsch 🇩🇪</option>
                            <option value="fr">Français 🇫🇷</option>
                            <option value="es">Español 🇪🇸</option>
                            <option value="zh">中文 🇨🇳</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="row g-3">
                <div class="col-lg-3">
                    <div class="card-mod shadow-sm">
                        <span class="tag">MODULO 3</span>
                        <label class="small fw-bold text-secondary mb-2 d-block" id="ui-threshold-label">THRESHOLD (%)</label>
                        <input type="number" id="thr" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="run()">
                        <div id="kpi-box"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-mod shadow-sm">
                        <span class="tag">MODULO 4</span>
                        <div style="height: 500px;"><canvas id="main-chart"></canvas></div>
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
                const tP = langPack[lang];

                // Update UI Labels
                document.getElementById('ui-asset-label').innerText = tP.select_asset;
                document.getElementById('ui-lang-label').innerText = tP.select_lang;
                document.getElementById('ui-threshold-label').innerText = tP.threshold;

                // Calcolo Backtest
                let cap = 20000; let curve = []; let days = []; let benchmark = [];
                raw.forEach(r => {{
                    let s = 0;
                    if (r.m > t && r.v < 25) s = 1; else if (r.m < -t && r.v < 32) s = -1;
                    let pnl = (asset === 'eu') ? r.p_eu : r.p_dax;
                    let idx = (asset === 'eu') ? r.idx_eu : r.idx_dax;
                    cap += (s * pnl);
                    curve.push(cap); days.push(r.d); benchmark.push(idx);
                }});

                const profit = cap - 20000;
                document.getElementById('kpi-box').innerHTML = `
                    <div class="text-center p-3 rounded bg-black border border-secondary mt-2">
                        <span class="text-secondary small">${{tP.profit}}</span>
                        <h2 class="${{profit >= 0 ? 'text-success' : 'text-danger'}} mt-1">€ ${{ profit.toLocaleString('it-IT', {{maximumFractionDigits: 0}}) }}</h2>
                    </div>`;

                let sig = "FLAT ⚪";
                if (lM > t && lV < 25) sig = "LONG 🟢";
                else if (lM < -t && lV < 32) sig = "SHORT 🔴";
                document.getElementById('signal-display').innerText = sig;

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
                                label: asset.toUpperCase() + " Index",
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
                            x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 10 }} }},
                            y: {{ position: 'left', title: {{ display: true, text: 'Equity (€)' }} }},
                            y1: {{ position: 'right', grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Index Points' }} }}
                        }},
                        plugins: {{ legend: {{ labels: {{ color: '#c9d1d9' }} }} }}
                    }}
                }});
            }}
            window.onload = run;
        </script>
    </body>
    </html>
    """
    return html_code

# --- MODULO 5: ORCHESTRATOR ---
p, o = fetch_market_data()
h, l = calculate_quant_logic(p, o)
page = generate_visual_interface(h, l)
with open("index.html", "w", encoding="utf-8") as f: f.write(page)

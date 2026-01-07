
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# =============================================================================
# MODULO 1: DATA_INGESTION
# =============================================================================
def fetch_market_data():
    tickers = ['^STOXX50E', '^GSPC', '^N225', '^VIX', 'ES=F']
    df = yf.download(tickers, period="max", interval="1d", auto_adjust=True, progress=False)
    prices = df['Close'] if isinstance(df.columns, pd.MultiIndex) else df
    opens = df['Open'] if isinstance(df.columns, pd.MultiIndex) else df
    return prices, opens

# =============================================================================
# MODULO 2: STRATEGY_CORE
# =============================================================================
def calculate_quant_logic(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['USA_R'] = prices['^GSPC'].pct_change().shift(1)
    df['JAP_R'] = prices['^N225'].pct_change()
    df['FUT_R'] = (prices['ES=F'] / prices['ES=F'].shift(1)) - 1
    df['VIX'] = prices['^VIX']
    
    # Calcolo PnL Strategia
    df['PNL_UNITARIO'] = ((df['EU_C'] - df['EU_O']) - 2.0) * 10
    df['MOM_SIGNAL'] = (df['USA_R'] + df['JAP_R'] + df['FUT_R']) / 3
    
    df = df.dropna()
    history = []
    for dt, row in df.iterrows():
        history.append({
            'd': dt.strftime('%Y-%m-%d'), # Formato ISO per JS
            'm': float(row['MOM_SIGNAL']), 
            'v': float(row['VIX']), 
            'p': float(row['PNL_UNITARIO']),
            'idx': float(row['EU_C']) # Prezzo Indice per Modulo 4
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
            "title": "QUANT-PRO V4", "sync": "Modulo 1: Data Sync", "core": "MODULO 2: CORE_LOGIC",
            "controls": "MODULO 3: UI_CONTROLS", "chart": "MODULO 4: CHART_ENGINE",
            "threshold": "MOMENTUM THRESHOLD (%)", "profit": "NET PROFIT", 
            "equity": "Equity Curve (€)", "benchmark": "EuroStoxx 50 Index"
        },
        "de": {
            "title": "QUANT-PRO V4", "sync": "Modul 1: Daten", "core": "MODUL 2: KERNLOGIK",
            "controls": "MODUL 3: STEUERUNG", "chart": "MODUL 4: CHART",
            "threshold": "SCHWELLE (%)", "profit": "GEWINN", 
            "equity": "Equity (€)", "benchmark": "EuroStoxx 50 Index"
        },
        "fr": {
            "title": "QUANT-PRO V4", "sync": "Module 1: Données", "core": "MODULE 2: LOGIQUE",
            "controls": "MODULE 3: CONTRÔLES", "chart": "MODULE 4: GRAPHIQUE",
            "threshold": "SEUIL (%)", "profit": "PROFIT", 
            "equity": "Équité (€)", "benchmark": "EuroStoxx 50 Index"
        },
        "es": {
            "title": "QUANT-PRO V4", "sync": "Módulo 1: Datos", "core": "MÓDULO 2: LÓGICA",
            "controls": "MÓDULO 3: CONTROLES", "chart": "MÓDULO 4: GRÁFICO",
            "threshold": "UMBRAL (%)", "profit": "BENEFICIO", 
            "equity": "Equidad (€)", "benchmark": "EuroStoxx 50 Index"
        },
        "zh": {
            "title": "QUANT-PRO V4", "sync": "模块 1: 数据", "core": "模块 2: 逻辑",
            "controls": "模块 3: 控制", "chart": "模块 4: 图表",
            "threshold": "阈值 (%)", "profit": "净利润", 
            "equity": "权益 (€)", "benchmark": "欧洲斯托克50"
        }
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
            :root {{ --bg: #0d1117; --card: #161b22; --accent: #238636; }}
            body {{ background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--accent); padding: 15px; background: var(--card); }}
            .card-mod {{ background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; }}
            .tag {{ position: absolute; top: -10px; right: 10px; background: var(--accent); color: white; font-size: 9px; padding: 2px 7px; border-radius: 4px; font-weight: bold; }}
            .lang-select {{ background: #161b22; color: #fff; border: 1px solid #30363d; border-radius: 4px; padding: 5px; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow mb-4">
            <div class="container-fluid d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="h3 m-0 text-white" id="ui-title">{lang_pack['en']['title']}</h1>
                    <small class="text-secondary text-uppercase" id="ui-sync">{lang_pack['en']['sync']} | {live['last_update']}</small>
                </div>
                <div class="d-flex align-items-center">
                    <div class="me-4 text-end">
                        <span class="text-secondary small d-block" id="ui-core">{lang_pack['en']['core']}</span>
                        <div id="signal-display" class="h2 fw-bold text-warning m-0">---</div>
                    </div>
                    <select class="lang-select" id="lang-switch" onchange="run()">
                        <option value="en">English 🇺🇸</option>
                        <option value="de">Deutsch 🇩🇪</option>
                        <option value="fr">Français 🇫🇷</option>
                        <option value="es">Español 🇪🇸</option>
                        <option value="zh">中文 🇨🇳</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-3">
                <div class="col-lg-3">
                    <div class="card-mod shadow-sm">
                        <span class="tag" id="tag-controls">{lang_pack['en']['controls']}</span>
                        <label class="small fw-bold text-secondary mb-2 d-block" id="ui-threshold-label">{lang_pack['en']['threshold']}</label>
                        <input type="number" id="thr" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="run()">
                        <div id="kpi-box"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-mod shadow-sm">
                        <span class="tag" id="tag-chart">{lang_pack['en']['chart']}</span>
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
                const t = parseFloat(document.getElementById('thr').value) / 100;
                const tP = langPack[lang];

                document.getElementById('ui-title').innerText = tP.title;
                document.getElementById('ui-core').innerText = tP.core;
                document.getElementById('ui-threshold-label').innerText = tP.threshold;
                document.getElementById('tag-controls').innerText = tP.controls;
                document.getElementById('tag-chart').innerText = tP.chart;

                let sig = "FLAT ⚪";
                if (lM > t && lV < 25) sig = "LONG 🟢";
                else if (lM < -t && lV < 32) sig = "SHORT 🔴";
                document.getElementById('signal-display').innerText = sig;

                let cap = 20000; let curve = []; let days = []; let benchmark = [];
                raw.forEach(r => {{
                    let s = 0;
                    if (r.m > t && r.v < 25) s = 1; else if (r.m < -t && r.v < 32) s = -1;
                    cap += (s * r.p);
                    curve.push(cap);
                    days.push(r.d);
                    benchmark.push(r.idx);
                }});

                document.getElementById('kpi-box').innerHTML = `
                    <div class="text-center p-3 rounded bg-black border border-secondary mt-2">
                        <span class="text-secondary small">${{tP.profit}}</span>
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
                                borderWidth: 2,
                                pointRadius: 0,
                                fill: true,
                                yAxisID: 'y'
                            }},
                            {{
                                label: tP.benchmark,
                                data: benchmark,
                                borderColor: '#58a6ff',
                                borderWidth: 1,
                                pointRadius: 0,
                                fill: false,
                                yAxisID: 'y1'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        scales: {{
                            x: {{ 
                                grid: {{ display: false }},
                                ticks: {{ color: '#8b949e', maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }}
                            }},
                            y: {{ 
                                type: 'linear', display: true, position: 'left',
                                title: {{ display: true, text: 'Equity (€)', color: '#238636' }},
                                grid: {{ color: '#21262d' }}
                            }},
                            y1: {{ 
                                type: 'linear', display: true, position: 'right',
                                title: {{ display: true, text: 'Index (Points)', color: '#58a6ff' }},
                                grid: {{ drawOnChartArea: false }}
                            }}
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

# =============================================================================
# MODULO 5: SYSTEM_ORCHESTRATOR
# =============================================================================
p, o = fetch_market_data()
hist, metrics = calculate_quant_logic(p, o)
page = generate_visual_interface(hist, metrics)
with open("index.html", "w", encoding="utf-8") as f: f.write(page)


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

# --- MODULO 6: MULTILANGUAGE_MANAGER ---
def get_language_pack():
    return {
        "en": {
            "title": "QUANT-PRO V5.3", "sync": "MODULO 1: DATA_SYNC", "core": "MODULO 2: CORE_LOGIC",
            "controls": "MODULO 3: UI_CONTROLS", "chart": "MODULO 4: CHART_ENGINE", "system": "MODULO 5: ORCHESTRATOR",
            "threshold": "MOMENTUM THRESHOLD (%)", "profit": "NET PROFIT", 
            "equity": "Equity Curve (€)", "benchmark": "Index Reference", 
            "select_asset": "CHOOSE TRADING ASSET", "select_lang": "CHOOSE LANGUAGE"
        },
        "de": {
            "title": "QUANT-PRO V5.3", "sync": "MODUL 1: DATEN_SYNC", "core": "MODUL 2: KERN_LOGIK",
            "controls": "MODUL 3: STEUERUNG", "chart": "MODUL 4: GRAFIK_ENGINE", "system": "MODUL 5: SYSTEM",
            "threshold": "SCHWELLE (%)", "profit": "NETTOGEWINN", 
            "equity": "Equity (€)", "benchmark": "Index-Referenz",
            "select_asset": "HANDELSOBJEKT WÄHLEN", "select_lang": "SPRACHE WÄHLEN"
        },
        "fr": {
            "title": "QUANT-PRO V5.3", "sync": "MODULE 1: SYNC_DONNÉES", "core": "MODULE 2: LOGIQUE",
            "controls": "MODULE 3: CONTRÔLES", "chart": "MODULE 4: GRAPHIQUE", "system": "MODULE 5: SYSTÈME",
            "threshold": "SEUIL (%)", "profit": "PROFIT NET", 
            "equity": "Équité (€)", "benchmark": "Indice de Référence",
            "select_asset": "ACTIF", "select_lang": "LANGUE"
        },
        "es": {
            "title": "QUANT-PRO V5.3", "sync": "MÓDULO 1: SYNC_DATOS", "core": "MÓDULO 2: LÓGICA",
            "controls": "MÓDULO 3: CONTROLES", "chart": "MÓDULO 4: GRÁFICO", "system": "MÓDULO 5: SISTEMA",
            "threshold": "UMBRAL (%)", "profit": "BENEFICIO NETO", 
            "equity": "Equidad (€)", "benchmark": "Índice de Referencia",
            "select_asset": "ACTIVO", "select_lang": "IDIOMA"
        },
        "zh": {
            "title": "QUANT-PRO V5.3", "sync": "模块 1: 数据同步", "core": "模块 2: 逻辑核心",
            "controls": "模块 3: 界面控制", "chart": "模块 4: 图表引擎", "system": "模块 5: 系统调度",
            "threshold": "阈值 (%)", "profit": "净利润", 
            "equity": "权益 (€)", "benchmark": "参考指数",
            "select_asset": "选择资产", "select_lang": "选择语言"
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
            :root {{ --bg: #0d1117; --card: #161b22; --accent: #238636; --gold: #f1c40f; --mod: #8b949e; }}
            body {{ background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--accent); padding: 20px; background: var(--card); position: relative; }}
            .mod-tag-fixed {{ position: absolute; top: 5px; left: 20px; font-size: 10px; color: var(--mod); font-weight: bold; }}
            .core-tag {{ position: absolute; top: 5px; right: 20px; font-size: 10px; color: var(--mod); font-weight: bold; }}
            .top-control-box {{ 
                background: #1c2128; border-left: 4px solid var(--accent); border-radius: 8px; padding: 15px; position: relative;
            }}
            .card-mod {{ background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; height: 100%; }}
            .tag-mod {{ position: absolute; top: -10px; right: 10px; background: #30363d; color: #fff; font-size: 9px; padding: 2px 8px; border-radius: 4px; border: 1px solid var(--mod); }}
            .custom-select {{ background: #0d1117; color: #fff; border: 1px solid #444c56; border-radius: 8px; padding: 10px; width: 100%; font-weight: bold; }}
            input {{ background: #fff !important; color: #000 !important; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow-lg mb-4 rounded">
            <span class="mod-tag-fixed" id="ui-mod1">{lang_pack['en']['sync']}</span>
            <span class="core-tag" id="ui-mod2">{lang_pack['en']['core']}</span>
            <div class="container-fluid d-flex justify-content-between align-items-center mt-2">
                <div>
                    <h1 class="h2 m-0 text-white" id="ui-title">QUANT-PRO</h1>
                    <small class="text-secondary">Last Sync: {live['last_update']}</small>
                </div>
                <div id="signal-display" class="h1 fw-bold text-warning m-0">---</div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-3 mb-4">
                <div class="col-md-6">
                    <div class="top-control-box shadow-sm">
                        <span class="mod-tag-fixed" style="top:2px; left:10px; color:var(--accent)">MODULO 3</span>
                        <label class="small fw-bold text-accent mb-2 d-block text-uppercase mt-2" id="ui-asset-label">{lang_pack['en']['select_asset']}</label>
                        <select class="custom-select" id="asset-select" onchange="run()">
                            <option value="eu">EURO STOXX 50 (Blue Chips) 🇪🇺</option>
                            <option value="dax">DAX 40 (German Market) 🇩🇪</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="top-control-box shadow-sm" style="border-left-color: var(--gold)">
                        <span class="mod-tag-fixed" style="top:2px; left:10px; color:var(--gold)">MODULO 6</span>
                        <label class="small fw-bold mb-2 d-block text-uppercase mt-2" id="ui-lang-label" style="color:var(--gold)">{lang_pack['en']['select_lang']}</label>
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
                        <span class="tag-mod" id="ui-mod3-tag">{lang_pack['en']['controls']}</span>
                        <label class="small fw-bold text-secondary mb-2 d-block" id="ui-threshold-label">{lang_pack['en']['threshold']}</label>
                        <input type="number" id="thr" class="form-control form-control-lg mb-4" value="0.30" step="0.05" oninput="run()">
                        <div id="kpi-box"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-mod shadow-sm">
                        <span class="tag-mod" id="ui-mod4-tag">{lang_pack['en']['chart']}</span>
                        <div style="height: 500px;"><canvas id="main-chart"></canvas></div>
                    </div>
                </div>
            </div>
            <div class="text-center mt-3">
                <small class="text-muted" id="ui-mod5">{lang_pack['en']['system']} | ACTIVE</small>
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

                // Aggiornamento Etichette Moduli
                document.getElementById('ui-mod1').innerText = tP.sync;
                document.getElementById('ui-mod2').innerText = tP.core;
                document.getElementById('ui-mod3-tag').innerText = tP.controls;
                document.getElementById('ui-mod4-tag').innerText = tP.chart;
                document.getElementById('ui-mod5').innerText = tP.system + " | ACTIVE";
                document.getElementById('ui-asset-label').innerText = tP.select_asset;
                document.getElementById('ui-lang-label').innerText = tP.select_lang;
                document.getElementById('ui-threshold-label').innerText = tP.threshold;

                let cap = 20000; let curve = []; let days = []; let benchmark = [];
                raw.forEach(r => {{
                    let s = 0;
                    if (r.m > t && r.v < 25) s = 1; else if (r.m < -t && r.v < 32) s = -1;
                    let pnl = (asset === 'eu') ? r.p_eu : r.p_dax;
                    let idx = (asset === 'eu') ? r.idx_eu : r.idx_dax;
                    cap += (s * pnl);
                    curve.push(cap); days.push(r.d); benchmark.push(idx);
                }});

                document.getElementById('kpi-box').innerHTML = `
                    <div class="text-center p-3 rounded bg-black border border-secondary mt-2">
                        <span class="text-secondary small">${{tP.profit}}</span>
                        <h2 class="${{cap >= 20000 ? 'text-success' : 'text-danger'}} mt-1">€ ${{ (cap-20000).toLocaleString('it-IT', {{maximumFractionDigits: 0}}) }}</h2>
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
                                borderColor: '#238636', borderWidth: 2, pointRadius: 0, fill: true, yAxisID: 'y'
                            }},
                            {{
                                label: asset.toUpperCase() + " Index",
                                data: benchmark,
                                borderColor: '#58a6ff', borderWidth: 1, pointRadius: 0, fill: false, yAxisID: 'y1'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        scales: {{
                            x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 10 }} }},
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

# --- MODULO 5: ORCHESTRATOR ---
p, o = fetch_market_data()
h, l = calculate_quant_logic(p, o)
page = generate_visual_interface(h, l)
with open("index.html", "w", encoding="utf-8") as f: f.write(page)

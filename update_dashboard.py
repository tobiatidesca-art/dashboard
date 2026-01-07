
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

# --- MODULO 2: STRATEGY_CORE (UPDATED WITH TIMESTAMP) ---
def calculate_quant_logic(prices, opens):
    df = pd.DataFrame(index=prices.index)
    df['EU_O'], df['EU_C'] = opens['^STOXX50E'], prices['^STOXX50E']
    df['DAX_O'], df['DAX_C'] = opens['^GDAXI'], prices['^GDAXI']
    
    # Dati Indici Globali
    df['SP_C'] = prices['^GSPC']
    df['JPN_C'] = prices['^N225']
    df['USA_R'] = df['SP_C'].pct_change().shift(1)
    df['JAP_R'] = df['JPN_C'].pct_change()
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
    
    # Snapshot con Data e Ora di Rilevazione
    now = datetime.now()
    live_snapshot = {
        'mom': float(df['MOM_SIGNAL'].iloc[-1]),
        'vix': float(df['VIX'].iloc[-1]),
        'sp_price': float(df['SP_C'].iloc[-1]),
        'jpn_price': float(df['JPN_C'].iloc[-1]),
        'entry_price_eu': float(df['EU_O'].iloc[-1]),
        'entry_price_dax': float(df['DAX_O'].iloc[-1]),
        'last_sync_date': now.strftime('%d/%m/%Y'),
        'last_sync_time': now.strftime('%H:%M:%S'),
        'last_update': now.strftime('%H:%M:%S %d/%m/%Y')
    }
    return history, live_snapshot

# --- MODULO 6: MULTILANGUAGE_MANAGER ---
def get_language_pack():
    return {
        "en": {
            "title": "QUANT-PRO V5.5", "sync": "MODULO 1: DATA_SYNC", "core": "MODULO 2: CORE_LOGIC",
            "controls": "MODULO 3: UI_CONTROLS", "chart": "MODULO 4: CHART_ENGINE", "system": "MODULO 5: ORCHESTRATOR",
            "threshold": "MOMENTUM THRESHOLD (%)", "profit": "NET PROFIT", 
            "equity": "Equity Curve (€)", "benchmark": "Index Reference", 
            "select_asset": "CHOOSE TRADING ASSET", "select_lang": "CHOOSE LANGUAGE",
            "market_info": "GLOBAL MARKET STATUS", "entry": "ENTRY PRICE", "last_check": "DATA AS OF"
        },
        "de": {
            "title": "QUANT-PRO V5.5", "sync": "MODUL 1: DATEN_SYNC", "core": "MODUL 2: KERN_LOGIK",
            "controls": "MODUL 3: STEUERUNG", "chart": "MODUL 4: GRAFIK_ENGINE", "system": "MODUL 5: SYSTEM",
            "threshold": "SCHWELLE (%)", "profit": "NETTOGEWINN", 
            "equity": "Equity (€)", "benchmark": "Index-Referenz",
            "select_asset": "HANDELSOBJEKT WÄHLEN", "select_lang": "SPRACHE WÄHLEN",
            "market_info": "WELTMARKT STATUS", "entry": "EINTRITTSPREIS", "last_check": "DATEN VOM"
        },
        "fr": { "title": "QUANT-PRO V5.5", "sync": "MODULE 1: SYNC", "core": "MODULE 2: LOGIQUE", "controls": "MODULE 3: CONTRÔLES", "chart": "MODULE 4: GRAPHIQUE", "system": "MODULE 5: SYSTÈME", "threshold": "SEUIL (%)", "profit": "PROFIT NET", "equity": "Équité (€)", "benchmark": "Indice", "select_asset": "ACTIF", "select_lang": "LANGUE", "market_info": "ÉTAT DU MARCHÉ", "entry": "PRIX D'ENTRÉE", "last_check": "DONNÉES AU" },
        "es": { "title": "QUANT-PRO V5.5", "sync": "MÓDULO 1: SYNC", "core": "MÓDULO 2: LÓGICA", "controls": "MÓDULO 3: CONTROLES", "chart": "MÓDULO 4: GRÁFICO", "system": "MÓDULO 5: SISTEMA", "threshold": "UMBRAL (%)", "profit": "BENEFICIO NETO", "equity": "Equidad (€)", "benchmark": "Índice", "select_asset": "ACTIVO", "select_lang": "IDIOMA", "market_info": "ESTADO DEL MERCADO", "entry": "PRECIO ENTRADA", "last_check": "DATOS DE" },
        "zh": { "title": "QUANT-PRO V5.5", "sync": "模块 1: 同步", "core": "模块 2: 逻辑核心", "controls": "模块 3: 控制", "chart": "模块 4: 图表引擎", "system": "模块 5: 系统调度", "threshold": "阈值 (%)", "profit": "净利润", "equity": "权益 (€)", "benchmark": "参考指数", "select_asset": "选择资产", "select_lang": "选择语言", "market_info": "全球市场状态", "entry": "入场价格", "last_check": "数据时间" }
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
            :root {{ --bg: #0d1117; --card: #161b22; --accent: #238636; --gold: #f1c40f; --mod: #8b949e; --blue: #58a6ff; }}
            body {{ background-color: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }}
            .nav-header {{ border-bottom: 2px solid var(--accent); padding: 15px; background: var(--card); position: relative; }}
            .mod-label {{ font-size: 10px; color: var(--mod); font-weight: bold; text-transform: uppercase; }}
            .top-control-box {{ background: #1c2128; border-radius: 8px; padding: 12px; height: 100%; border-top: 2px solid var(--mod); }}
            .card-mod {{ background: var(--card); border: 1px solid #30363d; border-radius: 8px; padding: 20px; position: relative; height: 100%; }}
            .tag-mod {{ position: absolute; top: -10px; right: 10px; background: #30363d; color: #fff; font-size: 9px; padding: 2px 8px; border-radius: 4px; border: 1px solid var(--mod); }}
            .market-detail {{ font-size: 0.85rem; border-bottom: 1px solid #30363d; padding: 5px 0; display: flex; justify-content: space-between; }}
            .custom-select {{ background: #0d1117; color: #fff; border: 1px solid #444c56; border-radius: 6px; padding: 5px; width: 100%; font-size: 0.9rem; }}
        </style>
    </head>
    <body class="p-3">
        <div class="nav-header shadow-lg mb-3 rounded">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <span class="mod-label" id="ui-mod1">{lang_pack['en']['sync']}</span><br>
                    <h2 class="h4 m-0 text-white" id="ui-title">QUANT-PRO</h2>
                </div>
                <div class="text-end">
                    <span class="mod-label" id="ui-mod2">{lang_pack['en']['core']}</span><br>
                    <div id="signal-display" class="h2 fw-bold text-warning m-0">---</div>
                </div>
            </div>
        </div>

        <div class="container-fluid">
            <div class="row g-2 mb-3">
                <div class="col-md-4">
                    <div class="top-control-box" style="border-top-color: var(--blue)">
                        <span class="mod-label" id="ui-market-info">{lang_pack['en']['market_info']}</span>
                        <div class="market-detail mt-1"><span>S&P 500 (USA)</span><span class="text-white fw-bold">{live['sp_price']:,.2f}</span></div>
                        <div class="market-detail"><span>NIKKEI 225 (JPN)</span><span class="text-white fw-bold">{live['jpn_price']:,.2f}</span></div>
                        <div class="market-detail mt-1" style="border:none; color:var(--blue); font-size:0.75rem;">
                            <span id="ui-last-check">{lang_pack['en']['last_check']}</span>
                            <span class="fw-bold">{live['last_sync_date']} {live['last_sync_time']}</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="top-control-box" style="border-top-color: var(--accent)">
                        <span class="mod-label" id="ui-asset-label">{lang_pack['en']['select_asset']}</span>
                        <select class="custom-select mt-1" id="asset-select" onchange="run()">
                            <option value="eu">EURO STOXX 50 Index 🇪🇺</option>
                            <option value="dax">DAX 40 Performance Index 🇩🇪</option>
                        </select>
                        <div class="market-detail mt-1"><span id="ui-entry-label">{lang_pack['en']['entry']}</span><span class="text-success fw-bold" id="entry-data">---</span></div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="top-control-box" style="border-top-color: var(--gold)">
                        <span class="mod-label" id="ui-lang-label">{lang_pack['en']['select_lang']}</span>
                        <select class="custom-select mt-1" id="lang-switch" onchange="run()">
                            <option value="en">English 🇺🇸</option><option value="de">Deutsch 🇩🇪</option>
                            <option value="fr">Français 🇫🇷</option><option value="es">Español 🇪🇸</option><option value="zh">中文 🇨🇳</option>
                        </select>
                        <div class="market-detail mt-1"><span>VIX Volatility Index</span><span class="text-warning fw-bold">{live['vix']:.2f}</span></div>
                    </div>
                </div>
            </div>

            <div class="row g-3">
                <div class="col-lg-3">
                    <div class="card-mod shadow-sm">
                        <span class="tag-mod" id="ui-mod3-tag">{lang_pack['en']['controls']}</span>
                        <label class="small fw-bold text-secondary mb-2 d-block" id="ui-threshold-label">{lang_pack['en']['threshold']}</label>
                        <input type="number" id="thr" class="form-control mb-4" value="0.30" step="0.05" oninput="run()">
                        <div id="kpi-box"></div>
                    </div>
                </div>
                <div class="col-lg-9">
                    <div class="card-mod shadow-sm">
                        <span class="tag-mod" id="ui-mod4-tag">{lang_pack['en']['chart']}</span>
                        <div style="height: 400px;"><canvas id="main-chart"></canvas></div>
                    </div>
                </div>
            </div>
            <div class="text-center mt-3">
                <small class="text-muted" id="ui-mod5">{lang_pack['en']['system']} | ACTIVE SERVER SYNC</small>
            </div>
        </div>

        <script>
            const raw = {json.dumps(history)};
            const lD = {json.dumps(live)};
            const langPack = {json.dumps(lang_pack)};
            let chart = null;

            function run() {{
                const lang = document.getElementById('lang-switch').value;
                const asset = document.getElementById('asset-select').value;
                const t = parseFloat(document.getElementById('thr').value) / 100;
                const tP = langPack[lang];

                // Labels Sync
                document.getElementById('ui-mod1').innerText = tP.sync;
                document.getElementById('ui-mod2').innerText = tP.core;
                document.getElementById('ui-mod3-tag').innerText = tP.controls;
                document.getElementById('ui-mod4-tag').innerText = tP.chart;
                document.getElementById('ui-mod5').innerText = tP.system + " | " + lD.last_update;
                document.getElementById('ui-asset-label').innerText = tP.select_asset;
                document.getElementById('ui-lang-label').innerText = tP.select_lang;
                document.getElementById('ui-market-info').innerText = tP.market_info;
                document.getElementById('ui-entry-label').innerText = tP.entry;
                document.getElementById('ui-last-check').innerText = tP.last_check;

                const ep = (asset === 'eu') ? lD.entry_price_eu : lD.entry_price_dax;
                document.getElementById('entry-data').innerText = ep.toLocaleString() + " @ 09:00";

                let cap = 20000; let curve = []; let days = []; let benchmark = [];
                raw.forEach(r => {{
                    let s = 0;
                    if (r.m > t && r.v < 25) s = 1; else if (r.m < -t && r.v < 32) s = -1;
                    let pnl = (asset === 'eu') ? r.p_eu : r.p_dax;
                    let idx = (asset === 'eu') ? r.idx_eu : r.idx_dax;
                    cap += (s * pnl);
                    curve.push(cap); days.push(r.d); benchmark.push(idx);
                }});

                document.getElementById('kpi-box').innerHTML = `<div class="text-center p-3 rounded bg-black border border-secondary mt-2"><span class="text-secondary small">${{tP.profit}}</span><h2 class="${{cap >= 20000 ? 'text-success' : 'text-danger'}} mt-1">€ ${{ (cap-20000).toLocaleString('it-IT', {{maximumFractionDigits: 0}}) }}</h2></div>`;

                let sig = "FLAT ⚪";
                if (lD.mom > t && lD.vix < 25) sig = "LONG 🟢"; else if (lD.mom < -t && lD.vix < 32) sig = "SHORT 🔴";
                document.getElementById('signal-display').innerText = sig;

                if (chart) chart.destroy();
                chart = new Chart(document.getElementById('main-chart'), {{
                    type: 'line',
                    data: {{
                        labels: days,
                        datasets: [
                            {{ label: tP.equity, data: curve, borderColor: '#238636', borderWidth: 2, pointRadius: 0, fill: true, yAxisID: 'y' }},
                            {{ label: asset.toUpperCase() + " Index", data: benchmark, borderColor: '#58a6ff', borderWidth: 1, pointRadius: 0, fill: false, yAxisID: 'y1' }}
                        ]
                    }},
                    options: {{ responsive: true, maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 10 }} }}, y: {{ position: 'left' }}, y1: {{ position: 'right', grid: {{ drawOnChartArea: false }} }} }} }}
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

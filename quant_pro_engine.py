# =============================================================================
# QUANT-PRO V7.6.6 - GITHUB AUTOMATION VERSION
# =============================================================================

import os
import yfinance as yf
import pandas as pd
import json
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

def get_full_market_data():
    targets = {
        'SX50E': '^STOXX50E',
        'DAX': '^GDAXI',
        'CAC': '^FCHI',
        'IBEX': '^IBEX',
        'FTSEMIB': 'FTSEMIB.MI' 
    }
    predictors = ['^GSPC', '^N225', '^VIX', 'ES=F']
    all_tickers = list(targets.values()) + predictors

    df_raw = yf.download(all_tickers, period="max", progress=False)
    
    if isinstance(df_raw.columns, pd.MultiIndex):
        p_h = df_raw['Close']
        o_h = df_raw['Open']
    else:
        p_h = df_raw
        o_h = df_raw

    fut_h = yf.download('ES=F', period="5d", interval="1h", progress=False)
    if isinstance(fut_h.columns, pd.MultiIndex): fut_h.columns = fut_h.columns.get_level_values(0)
    
    try:
        f_open = fut_h.between_time('00:00', '00:00')['Open'].iloc[-1]
        f_close = fut_h.between_time('08:00', '08:00')['Close'].iloc[-1]
        fut_chg_win = ((f_close / f_open) - 1) * 100
    except:
        fut_chg_win = 0.0

    data_out = {'indices': {}, 'live_preds': {}}

    try:
        sp_series = p_h['^GSPC'].dropna()
        nk_series = p_h['^N225'].dropna()
        vix_series = p_h['^VIX'].dropna()
        
        data_out['live_preds'] = {
            'sp_val': float(sp_series.iloc[-1]), 
            'sp_chg': float(((sp_series.iloc[-1] / sp_series.iloc[-2]) - 1) * 100),
            'sp_dt': sp_series.index[-1].strftime('%d %b'),
            'nk_val': float(nk_series.iloc[-1]), 
            'nk_chg': float(((nk_series.iloc[-1] / nk_series.iloc[-2]) - 1) * 100),
            'nk_dt': nk_series.index[-1].strftime('%d %b'),
            'fut_chg': float(fut_chg_win),
            'vix': float(vix_series.iloc[-1])
        }
    except:
        data_out['live_preds'] = {'sp_val':0, 'sp_chg':0, 'sp_dt':'-', 'nk_val':0, 'nk_chg':0, 'nk_dt':'-', 'fut_chg':0, 'vix':20}

    for name, ticker in targets.items():
        if ticker not in p_h.columns: continue
        temp_df = pd.DataFrame(index=p_h.index)
        temp_df['InP'] = o_h[ticker]
        temp_df['OutP'] = p_h[ticker]
        temp_df['MOM'] = (p_h['^GSPC'].pct_change().shift(1) + p_h['^N225'].pct_change() + p_h['ES=F'].pct_change()) / 3
        temp_df['VIX'] = p_h['^VIX']
        temp_df = temp_df.dropna()

        history = []
        for dt, row in temp_df.iterrows():
            history.append({
                'd': dt.strftime('%Y-%m-%d'), 'm': float(row['MOM']), 'v': float(row['VIX']),
                'in': float(row['InP']), 'out': float(row['OutP'])
            })
        
        data_out['indices'][name] = {
            'history': history,
            'last_price': float(p_h[ticker].dropna().iloc[-1]),
            'entry_price': float(o_h[ticker].dropna().iloc[-1])
        }

    return data_out

market_data = get_full_market_data()

html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Roboto+Mono:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background: #05080a; color: #e6edf3; font-family: 'Inter', sans-serif; padding: 20px; }}
        .header-main {{ background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); border-bottom: 3px solid #238636; padding: 30px; border-radius: 15px; margin-bottom: 25px; }}
        .card-custom {{ background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 20px; height: 100%; }}
        .val-big-label {{ font-size: 0.85rem; color: #58a6ff; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }}
        .val-big-number {{ display: block; font-size: 2.8rem; font-family: 'Roboto Mono'; color: white; font-weight: 700; line-height: 1.1; }}
        .ts-label {{ font-size: 0.7rem; color: #8b949e; font-family: 'Roboto Mono'; text-transform: uppercase; margin-top: 5px; }}
        .section-tag {{ font-size: 0.7rem; background: #238636; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 900; text-transform: uppercase; }}
        .zoom-btn {{ background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 5px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; cursor: pointer; }}
        .zoom-btn.active {{ background: #238636; color: white; border-color: #2ea043; }}
        .signal-badge {{ font-size: 3.5rem; font-weight: 900; line-height: 1; }}
        .kpi-box {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 8px; }}
        .explainer-box {{ font-size: 0.75rem; color: #8b949e; line-height: 1.4; border-top: 1px solid #30363d; padding-top: 15px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="header-main">
        <div class="row align-items-center">
            <div class="col-md-3">
                <span class="section-tag">Mod-1 Select Asset</span>
                <select id="assetS" onchange="run()" class="form-select bg-primary text-white border-0 fw-bold mt-2 mb-2">
                    <option value="SX50E">EUROSTOXX 50</option>
                    <option value="DAX">DAX 40</option>
                    <option value="FTSEMIB">FTSE MIB 🇮🇹</option>
                    <option value="CAC">CAC 40</option>
                    <option value="IBEX">IBEX 35</option>
                </select>
                <select id="langS" onchange="run()" class="form-select bg-dark text-white border-secondary">
                    <option value="en">English 🇬🇧</option>
                    <option value="it" selected>Italiano 🇮🇹</option>
                    <option value="es">Español 🇪🇸</option>
                    <option value="zh">中文 🇨🇳</option>
                    <option value="ja">日本語 🇯🇵</option>
                    <option value="fr">Français 🇫🇷</option>
                    <option value="de">Deutsch 🇩🇪</option>
                </select>
            </div>
            <div class="col-md-7 px-4">
                <div class="row text-center">
                    <div class="col-3 border-end border-secondary">
                        <span class="val-big-label">S&P 500</span>
                        <span class="val-big-number">{market_data['live_preds']['sp_val']:.0f}</span>
                        <div class="ts-label">CLOSE: {market_data['live_preds']['sp_dt']}</div>
                    </div>
                    <div class="col-3 border-end border-secondary">
                        <span class="val-big-label">NIKKEI 225</span>
                        <span class="val-big-number">{market_data['live_preds']['nk_val']:.0f}</span>
                        <div class="ts-label">CLOSE: {market_data['live_preds']['nk_dt']}</div>
                    </div>
                    <div class="col-3 border-end border-secondary">
                        <span class="val-big-label">MOMENTUM</span>
                        <span id="mom-val" class="val-big-number" style="color:#f1c40f">0.00%</span>
                        <div class="ts-label">WIN: 00-08 CET</div>
                    </div>
                    <div class="col-3">
                        <span class="val-big-label">SERVER TIME</span>
                        <div id="market-clock" style="color: #f1c40f; font-family: 'Roboto Mono'; font-weight: 700; font-size: 1.3rem;">--:--:--</div>
                    </div>
                </div>
            </div>
            <div class="col-md-2 text-end">
                <span class="val-big-label" id="t-entry">Entry Price</span>
                <h3 id="entry-val" class="text-white fw-900 mb-0">--</h3>
                <div id="sig-time-label" class="ts-label" style="color:#f1c40f">SIGNAL AT 09:00 CET</div>
                <div id="sig-val" class="signal-badge mt-1">---</div>
            </div>
        </div>
    </div>

    <div class="row g-4">
        <div class="col-xl-3">
            <div class="card-custom">
                <h6 class="val-big-label mb-3">Parameters Mod-2</h6>
                <div class="d-flex align-items-center mb-3">
                    <label class="me-3 fw-bold">THRESHOLD:</label>
                    <input type="number" id="thr" class="form-control form-control-lg bg-dark text-white border-warning w-50" value="0.30" step="0.05" oninput="run()">
                </div>
                
                <div id="kpi-grid" class="row g-2 mb-3"></div>

                <div class="explainer-box">
                    <strong id="exp-title">A cosa serve la Soglia?</strong><br>
                    <span id="exp-desc">
                        Determina la sensibilità del segnale. 
                        <b>Aumentala (es. 0.50)</b> per filtrare il rumore e fare meno trade più sicuri. 
                        <b>Diminuila (es. 0.15)</b> per essere più aggressivo ed entrare su movimenti più piccoli.
                    </span>
                </div>
            </div>
        </div>
        <div class="col-xl-9">
            <div class="card-custom">
                <div class="d-flex justify-content-between align-items-center">
                    <span class="section-tag">Mod-4 Performance</span>
                    <div class="btn-group">
                        <button class="zoom-btn" onclick="setZoom(this, 22)">1M</button>
                        <button class="zoom-btn" onclick="setZoom(this, 66)">3M</button>
                        <button class="zoom-btn" onclick="setZoom(this, 252)">1Y</button>
                        <button class="zoom-btn" onclick="setZoom(this, 504)">2Y</button>
                        <button class="zoom-btn active" onclick="setZoom(this, 0)">MAX</button>
                    </div>
                </div>
                <div style="height: 400px;" class="mt-3"><canvas id="chart"></canvas></div>
            </div>
        </div>
    </div>

    <div class="card-custom mt-4">
        <span class="section-tag">Mod-5 Journal</span>
        <div class="table-container mt-3">
            <table class="table table-dark table-hover m-0">
                <thead class="sticky-top bg-dark border-bottom border-secondary"><tr id="table-head"></tr></thead>
                <tbody id="auditBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        const data = {json.dumps(market_data)};
        let myChart = null;
        let currentZoom = 0;

        const i18n = {{
            en: {{ 
                entry:"Entry", sigTime: "SIGNAL AT 09:00 CET", 
                expT: "What is Threshold?",
                expD: "Determines signal sensitivity. Increase it (e.g. 0.50) to filter noise for fewer, safer trades. Decrease it (e.g. 0.15) to be more aggressive on smaller moves.",
                kpi:["Profit", "Win Rate", "Trades", "Max DD", "PF"], sig:["FLAT","LONG","SHORT"], cols:["DATE","TYPE","IN","OUT","PTS","PNL"] 
            }},
            it: {{ 
                entry:"Ingresso", sigTime: "SEGNALE ORE 09:00 CET", 
                expT: "A cosa serve la Soglia?",
                expD: "Determina la sensibilità del segnale. Aumentala (es. 0.50) per filtrare il rumore e fare meno trade più sicuri. Diminuila (es. 0.15) per essere più aggressivo su movimenti piccoli.",
                kpi:["Profitto", "Win Rate", "Trade", "Max DD", "PF"], sig:["FLAT","LONG","SHORT"], cols:["DATA","TIPO","IN","OUT","PTI","PNL"] 
            }}
        }};

        function setZoom(btn, days) {{
            currentZoom = days;
            document.querySelectorAll('.zoom-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            run();
        }}

        function updateClock() {{
            const now = new Date();
            document.getElementById('market-clock').innerText = now.toLocaleString("it-IT", {{timeZone:"Europe/Berlin", hour:'2-digit', minute:'2-digit', second:'2-digit'}}) + " CET";
        }}
        setInterval(updateClock, 1000);

        function run() {{
            const asset = document.getElementById('assetS').value;
            const lang = document.getElementById('langS').value;
            const t = i18n[lang] || i18n['en'];
            const thr = parseFloat(document.getElementById('thr').value) / 100;
            const assetData = data.indices[asset];
            const preds = data.live_preds;

            document.getElementById('table-head').innerHTML = t.cols.map(c => `<th>${{c}}</th>`).join('');
            document.getElementById('t-entry').innerText = t.entry;
            document.getElementById('sig-time-label').innerText = t.sigTime;
            document.getElementById('exp-title').innerText = t.expT;
            document.getElementById('exp-desc').innerText = t.expD;
            document.getElementById('entry-val').innerText = "€ " + assetData.entry_price.toFixed(1);

            const momLive = (preds.sp_chg + preds.nk_chg + preds.fut_chg) / 300;
            document.getElementById('mom-val').innerText = (momLive*100).toFixed(2) + "%";
            
            let sig = t.sig[0] + " ⚪"; let col = "#8b949e";
            if (momLive > thr && preds.vix < 25) {{ sig = t.sig[1] + " 🟢"; col = "#238636"; }}
            else if (momLive < -thr && preds.vix < 32) {{ sig = t.sig[2] + " 🔴"; col = "#da3633"; }}
            document.getElementById('sig-val').innerText = sig; document.getElementById('sig-val').style.color = col;

            let cap = 20000, wins = 0, total = 0, mdd = 0, maxC = 20000, gP = 0, gL = 0;
            let mult = (asset === 'DAX' ? 25 : (asset === 'FTSEMIB' ? 5 : 10));

            let history = assetData.history;
            if(currentZoom > 0) history = history.slice(-currentZoom);

            let eqD = [], lbl = [], idxD = [], rows = [];
            history.forEach(h => {{
                let p = 0;
                if (h.m > thr && h.v < 25) p = 1; else if (h.m < -thr && h.v < 32) p = -1;
                if (p !== 0) {{
                    total++;
                    let pts = (p === 1) ? (h.out - h.in - 2) : (h.in - h.out - 2);
                    let pnl = pts * mult;
                    cap += pnl;
                    if (pnl > 0) {{ wins++; gP += pnl; }} else {{ gL += Math.abs(pnl); }}
                    rows.push({{ d: h.d, t: p==1?t.sig[1]:t.sig[2], in: h.in, out: h.out, pts: pts, pnl: pnl }});
                }}
                eqD.push(cap); lbl.push(h.d); idxD.push(h.out);
                if (cap > maxC) maxC = cap;
                let dd = ((maxC - cap)/maxC)*100; if(dd > mdd) mdd = dd;
            }});

            const pf = gL === 0 ? gP.toFixed(2) : (gP/gL).toFixed(2);
            document.getElementById('kpi-grid').innerHTML = `
                <div class="col-6"><div class="kpi-box"><div class="val-big-label">${{t.kpi[0]}}</div><div class="text-success fw-bold">${{(cap-20000).toLocaleString()}}€</div></div></div>
                <div class="col-6"><div class="kpi-box"><div class="val-big-label">${{t.kpi[1]}}</div><div class="text-info fw-bold">${{total?((wins/total)*100).toFixed(1):0}}%</div></div></div>
                <div class="col-12"><div class="kpi-box border-warning"><div class="val-big-label" style="color:#f1c40f">${{t.kpi[4]}}</div><div class="fw-bold" style="color:#f1c40f">${{pf}}</div></div></div>
            `;

            document.getElementById('auditBody').innerHTML = rows.reverse().map(r => `
                <tr><td>${{r.d}}</td><td class="fw-bold">${{r.t}}</td><td>${{r.in.toFixed(1)}}</td><td>${{r.out.toFixed(1)}}</td>
                <td class="${{r.pts>=0?'text-success':'text-danger'}}">${{r.pts.toFixed(1)}}</td><td class="fw-bold">${{Math.round(r.pnl)}}€</td></tr>
            `).join('');

            if (myChart) myChart.destroy();
            myChart = new Chart(document.getElementById('chart'), {{
                data: {{ labels: lbl, datasets: [
                    {{ type: 'line', label: 'Equity', data: eqD, borderColor: '#238636', borderWidth: 2.5, pointRadius: 0, yAxisID: 'y' }},
                    {{ type: 'line', label: asset, data: idxD, borderColor: 'rgba(241, 196, 15, 0.4)', borderWidth: 1.5, pointRadius: 0, yAxisID: 'y1' }}
                ]}},
                options: {{ 
                    responsive: true, maintainAspectRatio: false, animation: false,
                    scales: {{ 
                        x: {{ ticks: {{ color: '#8b949e', maxTicksLimit: 10 }}, grid: {{ color: '#161b22' }} }},
                        y: {{ position: 'left', ticks: {{ color: '#238636' }}, grid: {{ color: '#30363d' }} }},
                        y1: {{ position: 'right', ticks: {{ color: '#f1c40f' }}, grid: {{ display: false }} }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }}
        window.onload = () => {{ updateClock(); run(); }};
    </script>
</body>
</html>
"""

# SALVATAGGIO PER GITHUB (SOSTITUISCE FILES.DOWNLOAD)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

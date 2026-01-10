import os
import requests
import re
import json
from datetime import datetime

def analizza_strumenti():
    try:
        if not os.path.exists('index.html'):
            return "File index.html non trovato."
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        json_match = re.search(r'const data\s*=\s*({.*?});', content, re.DOTALL)
        if not json_match:
            return "Dati JSON non trovati."
            
        data = json.loads(json_match.group(1))
        indices = data.get('indices', {})
        
        # --- CONFIGURAZIONE SOGLIA ---
        SOGLIA = 0.7  
        # -----------------------------
        
        moltiplicatori = {"SX50E": 10, "DAX": 25, "FTSEMIB": 5, "CAC": 10, "IBEX": 10}
        nomi_strumenti = {"SX50E": "EUROSTOXX 50", "DAX": "DAX 40", "FTSEMIB": "FTSE MIB 🇮🇹", "CAC": "CAC 40", "IBEX": "IBEX 35"}

        # 1. LINK E NOTE DI CONFIGURAZIONE ALL'INIZIO
        report = "🌐 [ACCEDI ALLA DASHBOARD](https://tobiatidesca-art.github.io/dashboard/)\n"
        report += f"⚙️ *Soglia calcolo:* {SOGLIA}\n"
        report += f"⚠️ *Nota:* Per allineare i risultati sul sito, imposta la variabile `THRESHOLD` a {SOGLIA}.\n"
        report += "───────────────────\n"
        report += "🏛 *QUANT-PRO REPORT*\n"
        report += "───────────────────\n"
        
        for key, info in indices.items():
            history = info.get('history', [])
            if not history: continue
            
            mult = moltiplicatori.get(key, 1)
            
            # 2. SEGNALE LIVE CON DATA
            ultima_op = history[-1]
            data_oggi = ultima_op.get('d', datetime.now().strftime('%Y-%m-%d'))
            m_val = ultima_op['m'] * 100
            
            if m_val > SOGLIA: 
                segnale = "LONG 🟢"
            elif m_val < -SOGLIA: 
                segnale = "SHORT 🔴"
            else: 
                segnale = "FLAT ⚪"
            
            report += f"*{nomi_strumenti.get(key, key)}*\n"
            report += f"📅 Data: {data_oggi}\n"
            report += f"🎯 Segnale: {segnale}\n"
            report += f"📍 Entry: *{ultima_op.get('in', 0):,.1f}*\n\n"
            
            # 3. ULTIME 2 OPERAZIONI REALI
            trade_reali = []
            for h in reversed(history[:-1]): 
                m_h = h['m'] * 100
                if abs(m_h) > SOGLIA:
                    tipo = "LONG" if m_h > SOGLIA else "SHORT"
                    punti = (h['out'] - h['in']) if tipo == "LONG" else (h['in'] - h['out'])
                    pnl = (punti - 2) * mult # -2 punti slippage
                    trade_reali.append(f"• {h['d']} ({tipo})\n  In: {h['in']:,.1f} | Out: {h['out']:,.1f} | PnL: *{pnl:,.0f}€*")
                if len(trade_reali) == 2: break
            
            if trade_reali:
                report += "📊 *Ultime 2 Operazioni:*\n" + "\n".join(trade_reali) + "\n"

            # 4. RISULTATO ULTIME 20 OPERAZIONI
            pnl_20 = 0
            for h_20 in history[-20:]:
                m_20 = h_20['m'] * 100
                if abs(m_20) > SOGLIA:
                    tipo_20 = "LONG" if m_20 > SOGLIA else "SHORT"
                    punti_20 = (h_20['out'] - h_20['in']) if tipo_20 == "LONG" else (h_20['in'] - h_20['out'])
                    pnl_20 += (punti_20 - 2) * mult

            report += f"💰 *Risultato totale ultime 20 operazioni:* {pnl_20:,.0f}€\n"
            report += "───────────────────\n"
            
        return report
    except Exception as e:
        return f"❌ Errore: {str(e)}"

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
    testo = analizza_strumenti()
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": testo, "parse_mode": "Markdown", "disable_web_page_preview": True})

if __name__ == "__main__":
    invia_telegram()

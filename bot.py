import os
import requests
import re
import json

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
        
        moltiplicatori = {
            "SX50E": 10, "DAX": 25, "FTSEMIB": 5, "CAC": 10, "IBEX": 10
        }
        
        nomi_strumenti = {
            "SX50E": "EUROSTOXX 50", "DAX": "DAX 40", "FTSEMIB": "FTSE MIB 🇮🇹", "CAC": "CAC 40", "IBEX": "IBEX 35"
        }

        report = "🤖 *REPORT QUANT-PRO + LIVE ENTRY*\n"
        report += "───────────────────\n"
        
        for key, info in indices.items():
            history = info.get('history', [])
            if not history: continue
            
            ultime_20 = history[-20:]
            ultima_op = history[-1]
            
            # Dati segnale e prezzo
            m_val = ultima_op['m'] * 100
            prezzo_ingresso = ultima_op.get('in', 0) # Prezzo di ingresso dell'ultima operazione
            
            if m_val > 0.30: segnale = "LONG 🟢"
            elif m_val < -0.30: segnale = "SHORT 🔴"
            else: segnale = "FLAT ⚪"
            
            # Calcolo PnL Euro e Sequenza
            pnl_euro = 0
            seq = ""
            mult = moltiplicatori.get(key, 1)
            for op in ultime_20:
                punti = op.get('out', 0) - op.get('in', 0)
                pnl_euro += (punti * mult)
                seq += "✅" if punti > 0 else "❌"
            
            report += f"*{nomi_strumenti.get(key, key)}*\n"
            report += f"🎯 Segnale: {segnale}\n"
            report += f"📍 Entry Price: *{prezzo_ingresso:,.1f}*\n" # Aggiunto Prezzo Ingresso
            report += f"💰 PnL 20 op: *{pnl_euro:,.2f}€*\n"
            report += f"📜 Seq: {seq}\n"
            report += "───────────────────\n"
            
        return report
    except Exception as e:
        return f"❌ Errore: {str(e)}"

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
    
    testo = analizza_strumenti()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": testo, "parse_mode": "Markdown"})

if __name__ == "__main__":
    invia_telegram()

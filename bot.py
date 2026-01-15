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
        
        # --- CONFIGURAZIONE ---
        SOGLIA = 0.7  
        DASHBOARD_URL = "https://tobiatidesca-art.github.io/dashboard/"
        moltiplicatori = {"SX50E": 10, "DAX": 25, "FTSEMIB": 5, "CAC": 10, "IBEX": 10}
        nomi_strumenti = {"SX50E": "EUROSTOXX 50", "DAX": "DAX 40", "FTSEMIB": "FTSE MIB 🇮🇹", "CAC": "CAC 40", "IBEX": "IBEX 35"}

        # 1. LINK SEMPRE IN ALTO
        report = f"🌐 *DASHBOARD LIVE:* [ACCEDI QUI]({DASHBOARD_URL})\n"
        report += "🏛 *QUANT-PRO ANNUAL REPORT*\n"
        report += "───────────────────\n"
        
        for key, info in indices.items():
            history = info.get('history', [])
            if not history: continue
            
            mult = moltiplicatori.get(key, 1)
            ultima_op = history[-1]
            data_oggi = ultima_op.get('d', datetime.now().strftime('%Y-%m-%d'))
            m_val = ultima_op['m'] * 100
            
            # Calcolo Segnale
            if m_val > SOGLIA: segnale = "LONG 🟢"
            elif m_val < -SOGLIA: segnale = "SHORT 🔴"
            else: segnale = "FLAT ⚪"
            
            report += f"*{nomi_strumenti.get(key, key)}*\n"
            report += f"🎯 Segnale: {segnale}\n"
            report += f"📍 Entry: *{ultima_op.get('in', 0):,.1f}*\n\n"
            
            # 2. ULTIME 2 OPERAZIONI CHIUSE
            trade_reali = []
            for h in reversed(history[:-1]): 
                m_h = h['m'] * 100
                if abs(m_h) > SOGLIA:
                    tipo = "LONG" if m_h > SOGLIA else "SHORT"
                    punti = (h['out'] - h['in']) if tipo == "LONG" else (h['in'] - h['out'])
                    pnl = (punti - 2) * mult 
                    trade_reali.append(f"• {h['d']} ({tipo}): *{pnl:,.0f}€*")
                if len(trade_reali) == 2: break
            
            if trade_reali:
                report += "📊 *Ultime Operazioni:*\n" + "\n".join(trade_reali) + "\n\n"

            # 3. TABELLA PERFORMANCE ANNUALE (DOPPIA COLONNA)
            pnl_per_anno = {}
            current_year = str(datetime.now().year)
            
            for h in history:
                m_h = h['m'] * 100
                if abs(m_h) > SOGLIA:
                    anno = h['d'][:4] 
                    punti = (h['out'] - h['in']) if m_h > SOGLIA else (h['in'] - h['out'])
                    pnl = (punti - 2) * mult
                    pnl_per_anno[anno] = pnl_per_anno.get(anno, 0) + pnl

            report += "📈 *PERFORMANCE STORICA:*\n"
            anni_ordinati = sorted(pnl_per_anno.keys(), reverse=True)
            
            # Gestione Anno Corrente in riga singola
            if anni_ordinati and anni_ordinati[0] == current_year:
                val = pnl_per_anno[current_year]
                emoji = "✅" if val >= 0 else "🔻"
                report += f"`{current_year}(C): {val:+,0f}€ {emoji}`\n"
                anni_ordinati.pop(0) # Rimuoviamo il corrente per processare il resto a coppie

            # Processo il resto degli anni a coppie (2 per riga)
            for i in range(0, len(anni_ordinati), 2):
                # Primo anno della coppia
                a1 = anni_ordinati[i]
                v1 = pnl_per_anno[a1]
                e1 = "✅" if v1 >= 0 else "🔻"
                riga = f"`{a1}:{v1:+,0f}€{e1}`"
                
                # Secondo anno della coppia (se esiste)
                if i + 1 < len(anni_ordinati):
                    a2 = anni_ordinati[i+1]
                    v2 = pnl_per_anno[a2]
                    e2 = "✅" if v2 >= 0 else "🔻"
                    riga += f" | `{a2}:{v2:+,0f}€{e2}`"
                
                report += riga + "\n"
            
            report += "───────────────────\n"
            
        return report
    except Exception as e:
        return f"❌ Errore analisi: {str(e)}"

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Errore: Credenziali Telegram mancanti nei Secrets.")
        return
        
    testo = analizza_strumenti()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": testo,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Report inviato!")
    else:
        print(f"❌ Errore: {response.text}")

if __name__ == "__main__":
    invia_telegram()

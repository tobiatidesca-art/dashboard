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
        
        moltiplicatori = {"SX50E": 10, "DAX": 25, "FTSEMIB": 5, "CAC": 10, "IBEX": 10}
        nomi_strumenti = {"SX50E": "EUROSTOXX 50", "DAX": "DAX 40", "FTSEMIB": "FTSE MIB 🇮🇹", "CAC": "CAC 40", "IBEX": "IBEX 35"}

        report = "🤖 *REPORT QUANT-PRO + TRADE HISTORY*\n"
        report += "───────────────────\n"
        
        for key, info in indices.items():
            history = info.get('history', [])
            if not history: continue
            
            mult = moltiplicatori.get(key, 1)
            
            # 1. SEGNALE LIVE (Ultimo elemento della storia)
            ultima_op = history[-1]
            m_val = ultima_op['m'] * 100
            prezzo_ingresso_live = ultima_op.get('in', 0)
            
            if m_val > 0.30: segnale = "LONG 🟢"
            elif m_val < -0.30: segnale = "SHORT 🔴"
            else: segnale = "FLAT ⚪"
            
            report += f"*{nomi_strumenti.get(key, key)}*\n"
            report += f"🎯 Segnale: {segnale}\n"
            report += f"📍 Live Entry: *{prezzo_ingresso_live:,.1f}*\n\n"
            
            # 2. RICERCA ULTIME 3 OPERAZIONI REALI (NON FLAT)
            trade_reali = []
            # Scorriamo la storia al contrario
            for h in reversed(history):
                m_h = h['m'] * 100
                if abs(m_h) > 0.30:
                    tipo = "LONG" if m_h > 0.30 else "SHORT"
                    punti = (h['out'] - h['in']) if tipo == "LONG" else (h['in'] - h['out'])
                    # Sottraiamo 2 punti di slippage come nella tua dashboard
                    punti_netti = punti - 2 
                    profitto = punti_netti * mult
                    
                    trade_reali.append({
                        'data': h['d'],
                        'tipo': tipo,
                        'in': h['in'],
                        'out': h['out'],
                        'pnl': profitto
                    })
                if len(trade_reali) == 3: break # Ci fermiamo quando ne abbiamo 3

            if trade_reali:
                report += "📜 *Ultime 3 Operazioni:*\n"
                for t in trade_reali:
                    emoji = "✅" if t['pnl'] > 0 else "❌"
                    report += f"{emoji} {t['data']} ({t['tipo']})\n"
                    report += f"   In: {t['in']:,.1f} | Out: {t['out']:,.1f}\n"
                    report += f"   PnL: *{t['pnl']:,.0f}€*\n"
            
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

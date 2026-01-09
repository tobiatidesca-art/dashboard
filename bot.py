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
            return "Dati JSON non trovati nel file."
            
        data = json.loads(json_match.group(1))
        indices = data.get('indices', {})
        
        # DEFINIZIONE MOLTIPLICATORI (Puoi cambiare i numeri qui sotto)
        moltiplicatori = {
            "SX50E": 10,    # 10€ a punto
            "DAX": 25,      # 25€ a punto
            "FTSEMIB": 5,   # 5€ a punto (Mini)
            "CAC": 10,      # 10€ a punto
            "IBEX": 10      # 10€ a punto
        }
        
        nomi_strumenti = {
            "SX50E": "EUROSTOXX 50",
            "DAX": "DAX 40",
            "FTSEMIB": "FTSE MIB 🇮🇹",
            "CAC": "CAC 40",
            "IBEX": "IBEX 35"
        }

        report = "🤖 *REPORT MULTI-ASSET (Ultime 20 Op)*\n"
        report += "───────────────────\n"
        soglia = 0.30
        
        for key, info in indices.items():
            history = info.get('history', [])
            if not history: continue
            
            ultime_20 = history[-20:]
            mult = moltiplicatori.get(key, 1) # Default 1 se non specificato
            
            # 1. Calcolo Momentum e Segnale
            ultimo_m = history[-1]['m'] * 100
            if ultimo_m > soglia: segnale = "LONG 🟢"
            elif ultimo_m < -soglia: segnale = "SHORT 🔴"
            else: segnale = "FLAT ⚪"
            
            # 2. Analisi sequenza e Profitto in Euro
            profitto_euro = 0
            sequenza_emoji = ""
            
            for op in ultime_20:
                punti = op.get('out', 0) - op.get('in', 0)
                # Calcolo in base alla direzione (se m > 0 ipotizziamo operazione long)
                # Per un calcolo preciso servirebbe la direzione salvata, 
                # qui simuliamo il pnl punti * moltiplicatore
                guadagno_op = punti * mult
                profitto_euro += guadagno_op
                
                sequenza_emoji += "✅" if punti > 0 else "❌"
            
            # Composizione messaggio per lo strumento
            report += f"*{nomi_strumenti.get(key, key)}*\n"
            report += f"🎯 Segnale: {segnale} ({ultimo_m:.2f}%)\n"
            report += f"💰 PnL 20 op: *{profitto_euro:,.2f}€*\n"
            report += f"📜 Seq: {sequenza_emoji}\n"
            report += "───────────────────\n"
            
        return report

    except Exception as e:
        return f"❌ Errore: {str(e)}"

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    messaggio = analizza_strumenti()
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": messaggio, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    invia_telegram()

import os
import requests
import re
import json

def calcola_metriche_dashboard():
    try:
        if not os.path.exists('index.html'):
            return None
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        json_match = re.search(r'const data\s*=\s*({.*?});', content, re.DOTALL)
        if not json_match:
            return None
            
        data = json.loads(json_match.group(1))
        # Usiamo SX50E come riferimento
        history = data['indices']['SX50E']['history']
        
        # 1. Calcolo Momentum e Segnale
        ultimo_m_raw = history[-1]['m']
        momentum_pct = ultimo_m_raw * 100
        soglia = 0.30
        
        if momentum_pct > soglia:
            segnale = "LONG 🟢"
        elif momentum_pct < -soglia:
            segnale = "SHORT 🔴"
        else:
            segnale = "FLAT ⚪"

        # 2. Calcolo Equity ultime 20 operazioni
        # Ogni elemento in history rappresenta un'operazione con 'pnl' (in percentuale o punti)
        # Assumiamo di calcolare il PnL monetario o punti dalle ultime 20 entry
        ultime_20 = history[-20:]
        pnl_periodo = sum(op.get('out', 0) - op.get('in', 0) for op in ultime_20)
        
        # Calcolo Equity Line semplificata (somma progressiva ultimi 20)
        return {
            "momentum": f"{momentum_pct:.2f}%",
            "segnale": segnale,
            "pnl_20": f"{pnl_periodo:.2f}",
            "operazioni": len(ultime_20)
        }
    except Exception as e:
        print(f"Errore analisi: {e}")
        return None

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    metrics = calcola_metriche_dashboard()
    
    if not metrics:
        print("Impossibile recuperare le metriche")
        return

    messaggio = (
        f"🤖 *Quant-Pro Bot v2.0*\n\n"
        f"📊 Momentum: *{metrics['momentum']}*\n"
        f"🎯 Segnale: *{metrics['segnale']}*\n"
        f"💰 PnL (Ultime {metrics['operazioni']} op): *{metrics['pnl_20']} pts*\n\n"
        f"📈 _Equity delle ultime 20 operazioni calcolata._\n\n"
        f"🔗 [Dashboard](https://{os.getenv('GITHUB_REPOSITORY_OWNER', 'user')}.github.io/dashboard/)"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": messaggio, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio: {e}")

if __name__ == "__main__":
    invia_telegram()

import os
import requests
import re
import json

def estrai_valore_esatto_dal_sito():
    try:
        if not os.path.exists('index.html'):
            return "File non trovato"
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Estraiamo i dati grezzi dal JSON interno all'HTML
            json_match = re.search(r'const data\s*=\s*({.*?});', content, re.DOTALL)
            if json_match:
                data_json = json.loads(json_match.group(1))
                # Prendiamo l'ultimo momentum registrato nella history del file
                # Questo è il valore che il browser usa per mostrare lo 0.51%
                history = data_json['indices']['SX50E']['history']
                ultimo_m = history[-1]['m'] 
                return f"{ultimo_m * 100:.2f}%"
    except Exception as e:
        return f"Errore: {str(e)}"
    return "N/D"

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    valore = estrai_valore_esatto_dal_sito()
    
    messaggio = f"📊 *Aggiornamento Allineato*\n\nMomentum: *{valore}*\n(Valore identico al sito)"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": messaggio, "parse_mode": "Markdown"})

if __name__ == "__main__":
    invia_telegram()

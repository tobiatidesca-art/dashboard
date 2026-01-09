import os
import requests
import re
import json

def calcola_momentum_reale():
    """
    Estrae i dati grezzi dal file index.html e calcola il momentum
    proprio come fa il browser, evitando lo 0.00% statico.
    """
    try:
        if not os.path.exists('index.html'):
            return "File non trovato"
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 1. Estraiamo la stringa JSON contenuta nella variabile 'const data ='
            json_match = re.search(r'const data\s*=\s*({.*?});', content, re.DOTALL)
            if not json_match:
                return "Dati non trovati"
            
            data_str = json_match.group(1)
            data_json = json.loads(data_str)
            
            # 2. Accediamo alla cronologia dell'indice (usiamo EUROSTOXX 50 come default o il primo disponibile)
            # In base al tuo file, la chiave è 'SX50E'
            history = data_json['indices']['SX50E']['history']
            
            if len(history) < 1:
                return "Storico vuoto"
            
            # 3. Il momentum nel tuo script è l'ultimo valore 'm' della history
            ultimo_dato = history[-1]
            valore_m = ultimo_dato.get('m', 0)
            
            # Trasformiamo in percentuale (es: 0.0051 -> 0.51%)
            percentuale = valore_m * 100
            return f"{percentuale:.2f}%"
                
    except Exception as e:
        return f"Errore: {str(e)}"
    return "N/D"

def invia_telegram():
    # Recupera le credenziali dai Secrets di GitHub
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Errore: Credenziali mancanti nei Secrets!")
        return

    # Calcola il valore reale dai dati grezzi
    momentum_val = calcola_momentum_reale()
    
    # Sceglie l'emoji in base al valore calcolato
    if "Errore" in momentum_val or "N/D" in momentum_val:
        emoji = "⚠️"
    elif "-" in momentum_val:
        emoji = "📉"
    elif "0.00" in momentum_val:
        emoji = "⚪"
    else:
        emoji = "📈"

    messaggio = (
        f"{emoji} *Quant-Pro Intelligence*\n\n"
        f"📊 Momentum Calcolato: *{momentum_val}*\n"
        f"🕒 Stato: Dati Real-Time\n\n"
        f"🔗 [Apri Dashboard](https://{os.getenv('GITHUB_REPOSITORY_OWNER', 'user')}.github.io/dashboard/)"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": messaggio, 
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Risposta Telegram: {response.text}")
    except Exception as e:
        print(f"Errore invio: {e}")

if __name__ == "__main__":
    invia_telegram()

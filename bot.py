import os
import requests
import re

def estrai_valore_momentum():
    try:
        # Legge il file index.html appena generato
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            # Cerca il valore numerico vicino alla parola Momentum
            # Questa regex cerca un numero (es. 0.51 o -0.20) seguito da %
            match = re.search(r"Momentum:\s*([\d\.-]+)%", content)
            if match:
                return match.group(1) + "%"
    except Exception as e:
        print(f"Errore lettura file: {e}")
    return "N/D"

def invia_telegram():
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    valore = estrai_valore_momentum()
    
    # Se il valore è nan o N/D, lo segnaliamo meglio
    status = "✅ OPERATIVO" if "nan" not in valore.lower() else "⚠️ DATI INCOMPLETI"
    
    messaggio = (
        f"🚀 *Quant-Pro Update*\n"
        f"📊 Momentum: *{valore}*\n"
        f"📢 Stato: {status}\n"
        f"🌐 [Visualizza Dashboard](https://iltuonomesito.github.io/)"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": messaggio, "parse_mode": "Markdown"}
    
    response = requests.post(url, json=payload)
    print(f"Risposta Telegram: {response.text}")

if __name__ == "__main__":
    invia_telegram()

import os
import requests
import re

def estrai_valore_momentum():
    """Cerca il valore del momentum nel file index.html."""
    try:
        if not os.path.exists('index.html'):
            return "File non trovato"
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Cerca tutti i valori percentuali vicini alla parola Momentum
            pattern = r"MOMENTUM.*?([\d\.-]+)%"
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            
            # Filtra i risultati per trovare il primo valore che NON sia 0.00
            for m in matches:
                if m != "0.00":
                    return m + "%"
            
            # Se trova solo 0.00, restituisce quello
            if matches:
                return matches[0] + "%"
                
    except Exception as e:
        return f"Errore: {str(e)}"
    return "N/D"

def invia_telegram():
    """Invia il report a Telegram leggendo i Secrets di GitHub."""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Errore: Token o Chat ID mancanti!")
        return

    momentum_val = estrai_valore_momentum()
    
    # Emoji dinamica
    emoji = "📈" if "-" not in momentum_val and "0.00" not in momentum_val else "📉"
    
    messaggio = (
        f"{emoji} *Aggiornamento Quant-Pro*\n\n"
        f"📊 Momentum: *{momentum_val}*\n"
        f"🕒 Stato: Sincronizzato\n\n"
        f"🔗 [Dashboard Online](https://{os.getenv('GITHUB_REPOSITORY_OWNER', 'tuo-utente')}.github.io/dashboard/)"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": messaggio, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload)
        print(f"Risposta Telegram: {response.text}")
    except Exception as e:
        print(f"Errore invio: {e}")

# Questo blocco deve essere SEMPRE alla fine del file
if __name__ == "__main__":
    invia_telegram()

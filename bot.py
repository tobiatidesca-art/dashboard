import os
import requests
import re

def estrai_valore_momentum():
    """
    Cerca il valore del momentum nel file index.html.
    Funziona anche se il file è molto grande o contiene tag HTML complessi.
    """
    try:
        if not os.path.exists('index.html'):
            return "File non trovato"
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Cerca la stringa 'Momentum' seguita da un valore percentuale
            # Gestisce spazi, tag HTML e formattazioni varie
            match = re.search(r"Momentum.*?>\s*([\d\.-]+)%", content, re.IGNORECASE | re.DOTALL)
            
            if match:
                return match.group(1) + "%"
            
            # Tentativo di riserva: cerca qualsiasi percentuale che sembri un momentum
            # (un numero con segno +/- vicino a una parola chiave)
            backup_match = re.search(r"([\+\-]?\d+\.\d+)%", content)
            if backup_match:
                return backup_match.group(1) + "%"
                
    except Exception as e:
        return f"Errore: {str(e)}"
    
    return "Dato non trovato"

def invia_telegram():
    # Recupera le credenziali dai Secrets di GitHub
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Errore: Token o Chat ID mancanti nei Secrets!")
        return

    # Estrae il dato reale dall'HTML
    momentum_val = estrai_valore_momentum()
    
    # Determina l'emoji in base al valore
    emoji = "📈" if "-" not in momentum_val and "0.00" not in momentum_val else "📉"
    if "non trovato" in momentum_val.lower():
        emoji = "⚠️"

    messaggio = (
        f"{emoji} *Aggiornamento Quant-Pro*\n\n"
        f"📊 Momentum Rilevato: *{momentum_val}*\n"
        f"🕒 Sincronizzazione: Completata\n\n"
        f"🔗 [Apri la Dashboard](https://iltuonomerepo.github.io/)"
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

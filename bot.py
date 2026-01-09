def estrai_valore_momentum():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            # Cerca il valore numerico che segue la parola Momentum, 
            # ignorando eventuali tag HTML o spazi extra
            import re
            match = re.search(r"Momentum.*?([\d\.-]+)%", content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1) + "%"
    except Exception as e:
        print(f"Errore: {e}")
    return "N/D"

def estrai_valore_momentum():
    try:
        if not os.path.exists('index.html'):
            return "File non trovato"
            
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 1. Cerca specificamente il valore giallo/arancione del Momentum (0.51%)
            # Cerca la parola Momentum e prende il primo valore non nullo nelle vicinanze
            pattern = r"MOMENTUM.*?([\d\.-]+)%"
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            
            for m in matches:
                if m != "0.00": # Salta gli zeri iniziali di sistema
                    return m + "%"
            
            # 2. Se non trova nulla, restituisce il primo valore trovato
            if matches:
                return matches[0] + "%"
                
    except Exception as e:
        return f"Errore: {str(e)}"
    return "Dato non trovato"

if __name__ == "__main__":
    invia_telegram()

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
        
        # --- CONFIGURAZIONE ---
        SOGLIA = 0.7  
        DASHBOARD_URL = "https://tobiatidesca-art.github.io/dashboard/"
        moltiplicatori = {"SX50E": 10, "DAX": 25, "FTSEMIB": 5, "CAC": 10, "IBEX": 10}
        nomi_strumenti = {"SX50E": "EUROSTOXX 50", "DAX": "DAX 40", "FTSEMIB": "FTSE MIB 🇮🇹", "CAC": "CAC 40", "IBEX": "IBEX 35"}

        # 1. LINK SEMPRE IN ALTO
        report = f"🌐 *DASHBOARD LIVE:* [CLICCA QUI]({DASHBOARD_URL})\n"
        report += "🏛 *QUANT-PRO ANNUAL REPORT*\n"
        report += "───────────────────\n"
        
        for key, info in indices.items():
            history = info.get('history', [])
            if not history: continue
            
            mult = moltiplicatori.get(key, 1)
            ultima_op = history[-1]
            data_oggi = ultima_op.get('d', datetime.now().strftime('%Y-%m-%d'))
            m_val = ultima_op['m'] * 100
            
            # Segnale
            if m_val > SOGLIA: segnale = "LONG 🟢"
            elif m_val < -SOGLIA: segnale = "SHORT 🔴"
            else: segnale = "FLAT ⚪"
            
            report += f"*{nomi_strumenti.get(key, key)}*\n"
            report += f"🎯 Segnale: {segnale}\n"
            report += f"📍 Entry: *{ultima_op.get('in', 0):,.1f}*\n\n"
            
            # 2. ULTIME 2 OPERAZIONI CHIUSE
            trade_reali = []
            for h in reversed(history[:-1]): 
                m_h = h['m'] * 100
                if abs(m_h) > SOGLIA:
                    tipo = "LONG" if m_h > SOGLIA else "SHORT"
                    punti = (h['out'] - h['in']) if tipo == "LONG" else (h['in'] - h['out'])
                    pnl = (punti - 2) * mult 
                    trade_reali.append(f"• {h['d']} ({tipo}): *{pnl:,.0f}€*")
                if len(trade_reali) == 2: break
            
            if trade_reali:
                report += "📊 *Ultime Operazioni:*\n" + "\n".join(trade_reali) + "\n\n"

            # 3. TABELLA PERFORMANCE ANNUALE (Sostituisce gli ultimi 20 trade)
            pnl_per_anno = {}
            current_year = str(datetime.now().year)
            
            for h in history:
                m_h = h['m'] * 100
                if abs(m_h) > SOGLIA:
                    anno = h['d'][:4] 
                    punti = (h['out'] - h['in']) if m_h > SOGLIA else (h['in'] - h['out'])
                    pnl = (punti - 2) * mult
                    pnl_per_anno[anno] = pnl_per_anno.get(anno, 0) + pnl

            report += "📈 *PERFORMANCE ANNUALE:*\n"
            for anno in sorted(pnl_per_anno.keys(), reverse=True):
                val = pnl_per_anno[anno]
                status = "✅" if val >= 0 else "🔻"
                if anno == current_year:
                    report += f"🚀 *{anno} (Corrente): {val:,.0f}€ {status}*\n"
                else:
                    report += f"• {anno}: {val:,.0f}€ {status}\n"
            
            report += "───────────────────\n"
            
        return report
    except Exception as e:
        return f"❌ Errore: {str(e)}"

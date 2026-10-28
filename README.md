# GEX//CONVERTER — Web edition

Versione web responsive del convertitore MenthorQ → Pine Script.

## Avvio sul PC

1. Installa Python 3.10 o successivo.
2. Estrai lo ZIP.
3. Apri un terminale nella cartella del progetto.
4. Esegui:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Si aprirà nel browser all'indirizzo locale mostrato dal terminale.

## Pubblicarla online

Un modo semplice è Streamlit Community Cloud:

1. Crea un repository GitHub e carica `app.py` e `requirements.txt`.
2. Vai su https://share.streamlit.io/ e accedi con GitHub.
3. Crea una nuova app selezionando il repository e `app.py`.
4. Al termine riceverai un URL pubblico da aprire anche sul telefono.

Il computer non deve restare acceso quando l'app è ospitata sul cloud.

## Nota

Questa è una prima conversione web della logica presente nel codice fornito. Prima di affidarsi ai risultati, prova il parser con alcuni messaggi MenthorQ reali e confronta l'output con quello della versione desktop. Non inserire dati o credenziali riservate in un'app pubblica.

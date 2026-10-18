# 🔒 VaultPass

**VaultPass** è un gestore di password locale, moderno e sicuro, sviluppato in Python utilizzando **CustomTkinter** per un'interfaccia grafica pulita ed elegante, e la libreria **cryptography** per una protezione dei dati di livello industriale.

Nessun server cloud di terze parti: i tuoi dati rimangono esclusivamente sul tuo dispositivo all'interno della cartella protetta `%APPDATA%\MyPasswordManager`.

---

## ✨ Caratteristiche Principali

* **🔐 Sicurezza Avanzata**: Derivazione della chiave tramite **PBKDF2HMAC** (400.000 iterazioni) combinata con la cifratura simmetrica **Fernet** (AES).
* **📥 Importazione Google Chrome**: Importa facilmente le tue credenziali da un file CSV esportato da Google e **elimina automaticamente** il file originale per motivi di sicurezza.
* **⏳ Caricamento Asincrono con Barra di Progresso**: Decifrazione fluida del vault in background con aggiornamento in tempo reale (0-100%).
* **🎲 Generatore di Password Casuali**: Generatore integrato altamente personalizzabile (lunghezza, maiuscole, minuscole, numeri e simboli).
* **📋 Protezione Appunti (Clipboard)**: Copia rapida delle password con **svuotamento automatico dopo 60 secondi** per prevenire furti di dati.
* **🔍 Ricerca in Tempo Reale**: Filtra istantaneamente tra le tue credenziali salvate cercando per servizio o nome utente.
* **💻 Doppia Versione**: Trovi sia la versione moderna con interfaccia grafica (`app.py`) sia una versione leggera da terminale (`gestore_password.py`).

---

## 🛠️ Requisiti di Sistema e Librerie

Assicurati di avere Python installato sul tuo sistema. Le dipendenze necessarie sono:

```bash
pip install customtkinter cryptography
# 🔒 VaultPass

[![Download EXE](https://img.shields.io/badge/Download-.EXE%20Pronto-blue?style=for-the-badge&logo=windows)](https://narcos891.gumroad.com/l/rcvwqs)
[![Buy Me a Coffee](https://img.shields.io/badge/Sostieni-Buy%20Me%20a%20Coffee-orange?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/narcos89)

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

pip install customtkinter cryptography

🚀 Utilizzo
Clona il repository o scarica i file sorgente.

Avvia l'applicazione eseguendo:

python app.py
Alla prima apertura, ti verrà chiesto di impostare una Master Password.

📦 Compilazione dell'Esecutivo (.exe)
Se desideri compilare l'applicazione in un file eseguibile indipendente per Windows, puoi usare PyInstaller da terminale:

Bash
pyinstaller --noconsole --onefile --icon=icon.ico app.py
L'eseguibile pronto all'uso verrà generato all'interno della cartella dist/.

📜 Licenza
Questo progetto è distribuito sotto licenza aperta. Sentiti libero di forkare il codice, migliorarlo o usarlo come base per i tuoi progetti.
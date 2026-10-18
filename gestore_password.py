from cryptography.fernet import Fernet
import os

NOME_FILE_CHIAVE = "secret.key"
NOME_FILE_DATI = "passwords.dat"

def carica_o_crea_chiave():
    """Carica la chiave dal file se esiste, altrimenti ne genera una nuova e la salva."""
    if os.path.exists(NOME_FILE_CHIAVE):
        with open(NOME_FILE_CHIAVE, "rb") as key_file:
            return key_file.read()
    else:
        chiave = Fernet.generate_key()
        with open(NOME_FILE_CHIAVE, "wb") as key_file:
            key_file.write(chiave)
        print(f"Nuova chiave generata e salvata in '{NOME_FILE_CHIAVE}'.")
        return chiave

# Inizializzazione della cifratura
chiave = carica_o_crea_chiave()
fernet = Fernet(chiave)

def aggiungi_password():
    """Chiede servizio, username e password, cifra i dati e li salva su file."""
    servizio = input("Inserisci il nome del servizio (es. Google, Subito, Amazon): ").strip()
    username = input("Inserisci l'email o username: ").strip()
    password = input("Inserisci la password: ").strip()

    # Formattiamo il testo e lo convertiamo in byte
    dati_chiari = f"{servizio}|{username}|{password}".encode()
    
    # Cifriamo i dati
    dati_cifrati = fernet.encrypt(dati_chiari)

    # Salviamo i dati cifrati su file (in modalità append)
    with open(NOME_FILE_DATI, "ab") as f:
        f.write(dati_cifrati + b"\n")

    print(f"\n Credenziale per '{servizio}' salvata e cifrata con successo!")

def visualizza_password():
    """Legge il file dei dati, decifra ogni riga e mostra le credenziali."""
    if not os.path.exists(NOME_FILE_DATI):
        print("\n Nessuna password salvata al momento.")
        return

    print("\n--- CREDENZIALI SALVATE ---")
    with open(NOME_FILE_DATI, "rb") as f:
        righe = f.readlines()
        for riga in righe:
            riga = riga.strip()
            if not riga:
                continue
            try:
                # Decifriamo i dati e li riconvertiamo in testo
                dati_chiari = fernet.decrypt(riga).decode()
                servizio, username, password = dati_chiari.split("|")
                print(f"Servizio: {servizio} | User: {username} | Pass: {password}")
            except Exception as e:
                print(" Errore nella decifrazione di una riga (chiave non valida o file corrotto).")

def main():
    """Menu principale del Password Manager."""
    while True:
        print("\n=== GESTORE PASSWORD ===")
        print("1. Aggiungi nuova password")
        print("2. Visualizza password salvate")
        print("3. Esci")
        scelta = input("Seleziona un'opzione (1-3): ").strip()

        if scelta == "1":
            aggiungi_password()
        elif scelta == "2":
            visualizza_password()
        elif scelta == "3":
            print("Chiusura del gestore password. Arrivederci!")
            break
        else:
            print("Opzione non valida, riprova.")

if __name__ == "__main__":
    main()
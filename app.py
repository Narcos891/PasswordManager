import os
import sys
import csv
import base64
import random
import string
import threading
import time
import ctypes
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Imposta AppUserModelID per mostrare l'icona personalizzata sulla taskbar di Windows
try:
    myappid = "vaultpass.passwordmanager.desktop.app.v1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def get_resource_path(relative_path):
    """Ottiene il percorso della risorsa, funzionante sia in sviluppo che con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- CONFIGURAZIONE PERCORSI SICURI (AppData) ---
CARTELLA_APP = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "MyPasswordManager")
os.makedirs(CARTELLA_APP, exist_ok=True)

FILE_DATI = os.path.join(CARTELLA_APP, "passwords.dat")
FILE_SALT = os.path.join(CARTELLA_APP, "salt.bin")
FILE_VERIFICA = os.path.join(CARTELLA_APP, "master.check")

# Configurazione Grafica CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class PasswordManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VaultPass - Gestore Password Sicuro")
        self.geometry("980x720")
        self.minsize(850, 600)

        # Imposta icona della finestra
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Centra la finestra sullo schermo
        self.center_window(980, 720)

        self.fernet = None
        self.tutte_le_credenziali = []
        self.credenziali_filtrate = []
        self.max_mostrati = 50

        self.schermata_login()

    def center_window(self, width, height):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def genera_chiave_da_master(self, master_password: str) -> Fernet:
        if os.path.exists(FILE_SALT):
            with open(FILE_SALT, "rb") as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(FILE_SALT, "wb") as f:
                f.write(salt)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=400000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return Fernet(key)

    def schermata_login(self):
        self.fernet = None
        self.tutte_le_credenziali = []
        self.credenziali_filtrate = []

        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        frame = ctk.CTkFrame(container, corner_radius=18, width=420)
        frame.grid(row=0, column=0, padx=20, pady=40)
        frame.grid_columnconfigure(0, weight=1)

        icon_path = get_resource_path("icon.ico")
        self.logo_img = None
        if os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path)
                self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(72, 72))
                lbl_icon = ctk.CTkLabel(frame, text="", image=self.logo_img)
                lbl_icon.pack(pady=(28, 8))
            except Exception:
                lbl_icon = ctk.CTkLabel(frame, text="🔒", font=ctk.CTkFont(size=50))
                lbl_icon.pack(pady=(35, 5))
        else:
            lbl_icon = ctk.CTkLabel(frame, text="🔒", font=ctk.CTkFont(size=50))
            lbl_icon.pack(pady=(35, 5))

        titolo = ctk.CTkLabel(frame, text="VaultPass", font=ctk.CTkFont(size=28, weight="bold"))
        titolo.pack(pady=(0, 5))

        primo_avvio = not os.path.exists(FILE_VERIFICA)
        testo_sotto = "Crea la tua Master Password sicura" if primo_avvio else "Inserisci la Master Password per sbloccare"
        sottotitolo = ctk.CTkLabel(frame, text=testo_sotto, font=ctk.CTkFont(size=13), text_color="gray70")
        sottotitolo.pack(pady=(0, 20), padx=25)

        # Frame per entry master password + pulsante mostra/nascondi
        pass_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pass_frame.pack(pady=10, padx=35, fill="x")
        pass_frame.grid_columnconfigure(0, weight=1)

        self.entry_master = ctk.CTkEntry(
            pass_frame,
            placeholder_text="Master Password",
            show="*",
            height=42,
            font=ctk.CTkFont(size=14)
        )
        self.entry_master.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.entry_master.bind("<Return>", lambda event: self.sblocca_vault())

        self.show_master_pwd = False
        self.btn_eye_master = ctk.CTkButton(
            pass_frame,
            text="👁️",
            width=42,
            height=42,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=self.toggle_mostra_master
        )
        self.btn_eye_master.grid(row=0, column=1)

        testo_btn = "Crea Vault" if primo_avvio else "Sblocca Vault"
        btn_sblocca = ctk.CTkButton(
            frame,
            text=testo_btn,
            command=self.sblocca_vault,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144f7d"
        )
        btn_sblocca.pack(pady=(15, 20), padx=35, fill="x")

        lbl_info = ctk.CTkLabel(
            frame,
            text="🛡️ Crittografia AES-256 (PBKDF2 SHA-256)",
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        )
        lbl_info.pack(pady=(0, 25))

        self.entry_master.focus_set()

    def toggle_mostra_master(self):
        self.show_master_pwd = not self.show_master_pwd
        if self.show_master_pwd:
            self.entry_master.configure(show="")
            self.btn_eye_master.configure(text="🔒")
        else:
            self.entry_master.configure(show="*")
            self.btn_eye_master.configure(text="👁️")

    def sblocca_vault(self):
        password = self.entry_master.get().strip()
        if not password:
            messagebox.showwarning("Attenzione", "Inserisci la Master Password!")
            return

        self.fernet = self.genera_chiave_da_master(password)

        if os.path.exists(FILE_VERIFICA):
            try:
                with open(FILE_VERIFICA, "rb") as f:
                    dati_cifrati = f.read()
                dati_decifrati = self.fernet.decrypt(dati_cifrati).decode("utf-8")
                if dati_decifrati != "VAULTPASS_OK":
                    raise ValueError("Password errata")
            except Exception:
                messagebox.showerror("Errore Accesso", "Master Password errata!\nRiprova.")
                self.entry_master.delete(0, "end")
                self.entry_master.focus_set()
                return
        else:
            dati_cifrati = self.fernet.encrypt(b"VAULTPASS_OK")
            with open(FILE_VERIFICA, "wb") as f:
                f.write(dati_cifrati)
            messagebox.showinfo("Master Password Creata", "La tua Master Password è stata impostata con successo!")

        self.schermata_principale()

    def schermata_principale(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR SINISTRA ---
        sidebar = ctk.CTkFrame(self, width=230, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)

        icon_path = get_resource_path("icon.ico")
        self.sidebar_logo_img = None
        if os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path)
                self.sidebar_logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
                lbl_icon_sidebar = ctk.CTkLabel(sidebar, text="", image=self.sidebar_logo_img)
                lbl_icon_sidebar.pack(pady=(20, 4))
            except Exception:
                pass

        lbl_logo = ctk.CTkLabel(
            sidebar,
            text="VaultPass",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        lbl_logo.pack(pady=(4, 2), padx=20)

        lbl_sub = ctk.CTkLabel(
            sidebar,
            text="Sicurezza Crittografica",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        lbl_sub.pack(pady=(0, 20), padx=20)

        self.lbl_stats = ctk.CTkLabel(
            sidebar,
            text="Caricamento database...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#60a5fa"
        )
        self.lbl_stats.pack(pady=(0, 25), padx=20)

        # Pulsanti Utilità Sidebar
        btn_importa = ctk.CTkButton(
            sidebar,
            text="📥 Importa CSV Google",
            command=self.importa_csv_google,
            fg_color="#1f6aa5",
            hover_color="#144f7d",
            height=36
        )
        btn_importa.pack(pady=8, padx=16, fill="x")

        btn_esporta = ctk.CTkButton(
            sidebar,
            text="📤 Esporta Backup CSV",
            command=self.esporta_csv,
            fg_color="#374151",
            hover_color="#4b5563",
            height=36
        )
        btn_esporta.pack(pady=8, padx=16, fill="x")

        btn_logout = ctk.CTkButton(
            sidebar,
            text="🔒 Blocca Vault",
            command=self.schermata_login,
            fg_color="#b91c1c",
            hover_color="#991b1b",
            height=36
        )
        btn_logout.pack(side="bottom", pady=25, padx=16, fill="x")

        # --- CONTENUTO PRINCIPALE (TABVIEW) ---
        content = ctk.CTkTabview(self, corner_radius=12)
        content.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        tab_passwords = content.add("Le Mie Password")
        tab_generatore = content.add("Generatore Password")

        # ==========================================
        # TAB 1: GESTIONE PASSWORD
        # ==========================================
        tab_passwords.grid_columnconfigure(0, weight=1)
        tab_passwords.grid_rowconfigure(3, weight=1)

        # Barra di Ricerca
        search_frame = ctk.CTkFrame(tab_passwords, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        search_frame.grid_columnconfigure(0, weight=1)

        self.ent_ricerca = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Cerca servizio o username...",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.ent_ricerca.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_ricerca.bind("<KeyRelease>", lambda event: self.filtra_passwords())

        btn_reset_search = ctk.CTkButton(
            search_frame,
            text="✕ Reset",
            width=70,
            height=38,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self.reset_ricerca
        )
        btn_reset_search.grid(row=0, column=1)

        # Form Inserimento Nuova Credenziale
        frame_inputs = ctk.CTkFrame(tab_passwords, corner_radius=10)
        frame_inputs.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        frame_inputs.grid_columnconfigure((0, 1, 2), weight=1)

        self.ent_servizio = ctk.CTkEntry(frame_inputs, placeholder_text="Servizio (es. Google, Amazon)", height=35)
        self.ent_servizio.grid(row=0, column=0, padx=6, pady=8, sticky="ew")

        self.ent_user = ctk.CTkEntry(frame_inputs, placeholder_text="Username / Email", height=35)
        self.ent_user.grid(row=0, column=1, padx=6, pady=8, sticky="ew")

        # Password input con mini pulsante genera
        pass_input_frame = ctk.CTkFrame(frame_inputs, fg_color="transparent")
        pass_input_frame.grid(row=0, column=2, padx=6, pady=8, sticky="ew")
        pass_input_frame.grid_columnconfigure(0, weight=1)

        self.ent_pass = ctk.CTkEntry(pass_input_frame, placeholder_text="Password", show="*", height=35)
        self.ent_pass.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.show_new_pwd = False
        self.btn_toggle_new = ctk.CTkButton(
            pass_input_frame,
            text="👁️",
            width=36,
            height=35,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=self.toggle_mostra_nuova_pass
        )
        self.btn_toggle_new.grid(row=0, column=1, padx=(0, 4))

        btn_quick_gen = ctk.CTkButton(
            pass_input_frame,
            text="🎲",
            width=36,
            height=35,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=self.genera_per_input
        )
        btn_quick_gen.grid(row=0, column=2)

        btn_salva = ctk.CTkButton(
            tab_passwords,
            text="➕ Aggiungi Nuova Credenziale",
            command=self.salva_credenziale,
            fg_color="#16a34a",
            hover_color="#15803d",
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn_salva.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 8))

        # Intestazione e Contatore Lista
        list_header = ctk.CTkFrame(tab_passwords, fg_color="transparent")
        list_header.grid(row=3, column=0, sticky="nsew", padx=10, pady=0)
        list_header.grid_columnconfigure(0, weight=1)
        list_header.grid_rowconfigure(1, weight=1)

        self.lbl_risultati = ctk.CTkLabel(
            list_header,
            text="Caricamento in corso...",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            anchor="w"
        )
        self.lbl_risultati.grid(row=0, column=0, sticky="w", padx=4, pady=(0, 4))

        # Lista Scrollabile
        self.scroll_passwords = ctk.CTkScrollableFrame(list_header, corner_radius=10)
        self.scroll_passwords.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll_passwords.grid_columnconfigure(0, weight=1)

        # ==========================================
        # TAB 2: GENERATORE PASSWORD
        # ==========================================
        tab_generatore.grid_columnconfigure(0, weight=1)

        gen_container = ctk.CTkFrame(tab_generatore, corner_radius=12)
        gen_container.pack(padx=30, pady=20, fill="both", expand=True)

        lbl_gen_title = ctk.CTkLabel(
            gen_container,
            text="🛡️ Generatore Casuale Sicuro",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        lbl_gen_title.pack(pady=(25, 10))

        self.lbl_lunghezza_val = ctk.CTkLabel(
            gen_container,
            text="Lunghezza: 18 caratteri",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#60a5fa"
        )
        self.lbl_lunghezza_val.pack(pady=5)

        self.slider_lunghezza = ctk.CTkSlider(
            gen_container,
            from_=8,
            to=64,
            number_of_steps=56,
            command=self.aggiorna_etichetta_slider
        )
        self.slider_lunghezza.set(18)
        self.slider_lunghezza.pack(pady=8, padx=60, fill="x")

        # Opzioni Checkbox
        opt_frame = ctk.CTkFrame(gen_container, fg_color="transparent")
        opt_frame.pack(pady=12)

        self.chk_maiuscole = ctk.CTkCheckBox(opt_frame, text="Maiuscole (A-Z)")
        self.chk_maiuscole.select()
        self.chk_maiuscole.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.chk_minuscole = ctk.CTkCheckBox(opt_frame, text="Minuscole (a-z)")
        self.chk_minuscole.select()
        self.chk_minuscole.grid(row=0, column=1, padx=15, pady=8, sticky="w")

        self.chk_numeri = ctk.CTkCheckBox(opt_frame, text="Numeri (0-9)")
        self.chk_numeri.select()
        self.chk_numeri.grid(row=1, column=0, padx=15, pady=8, sticky="w")

        self.chk_simboli = ctk.CTkCheckBox(opt_frame, text="Caratteri Speciali (!@#$...)")
        self.chk_simboli.select()
        self.chk_simboli.grid(row=1, column=1, padx=15, pady=8, sticky="w")

        btn_genera = ctk.CTkButton(
            gen_container,
            text="⚡ Genera Nuova Password",
            command=self.genera_password_casuale,
            fg_color="#16a34a",
            hover_color="#15803d",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            width=260
        )
        btn_genera.pack(pady=15)

        self.ent_risultato_gen = ctk.CTkEntry(
            gen_container,
            placeholder_text="Password generata...",
            width=420,
            height=42,
            font=ctk.CTkFont(size=15, family="Consolas"),
            justify="center"
        )
        self.ent_risultato_gen.pack(pady=10)

        self.btn_copia_gen = ctk.CTkButton(
            gen_container,
            text="📋 Copia negli Appunti (auto-clear 60s)",
            command=lambda: self.copia_con_timer(self.ent_risultato_gen.get(), btn_widget=self.btn_copia_gen),
            height=38,
            width=320,
            font=ctk.CTkFont(size=13)
        )
        self.btn_copia_gen.pack(pady=(5, 20))

        # Genera una password iniziale nel generatore
        self.genera_password_casuale()

        # Avvio caricamento credenziali in thread separato
        threading.Thread(target=self.carica_lista_passwords, daemon=True).start()

    def toggle_mostra_nuova_pass(self):
        self.show_new_pwd = not self.show_new_pwd
        if self.show_new_pwd:
            self.ent_pass.configure(show="")
            self.btn_toggle_new.configure(text="🔒")
        else:
            self.ent_pass.configure(show="*")
            self.btn_toggle_new.configure(text="👁️")

    def genera_per_input(self):
        caratteri = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(random.choice(caratteri) for _ in range(16))
        self.ent_pass.delete(0, "end")
        self.ent_pass.insert(0, pwd)
        self.ent_pass.configure(show="")
        self.show_new_pwd = True
        self.btn_toggle_new.configure(text="🔒")

    def reset_ricerca(self):
        self.ent_ricerca.delete(0, "end")
        self.filtra_passwords()

    def aggiorna_etichetta_slider(self, val):
        self.lbl_lunghezza_val.configure(text=f"Lunghezza: {int(val)} caratteri")

    def genera_password_casuale(self):
        lunghezza = int(self.slider_lunghezza.get())
        caratteri = ""

        if self.chk_maiuscole.get():
            caratteri += string.ascii_uppercase
        if self.chk_minuscole.get():
            caratteri += string.ascii_lowercase
        if self.chk_numeri.get():
            caratteri += string.digits
        if self.chk_simboli.get():
            caratteri += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        if not caratteri:
            messagebox.showwarning("Attenzione", "Seleziona almeno un tipo di caratteri!")
            return

        pwd = "".join(random.choice(caratteri) for _ in range(lunghezza))
        self.ent_risultato_gen.delete(0, "end")
        self.ent_risultato_gen.insert(0, pwd)

    def copia_con_timer(self, testo, btn_widget=None):
        if not testo:
            messagebox.showwarning("Attenzione", "Nessun testo da copiare!")
            return

        self.clipboard_clear()
        self.clipboard_append(testo)
        self.update()

        if btn_widget:
            testo_originale = btn_widget.cget("text")
            btn_widget.configure(text="✅ Copiato!")
            self.after(2000, lambda: self._ripristina_testo_btn(btn_widget, testo_originale))

        # Cancella gli appunti dopo 60 secondi se il contenuto corrisponde ancora
        self.after(60000, lambda: self._clear_clipboard_if_matches(testo))

    def _ripristina_testo_btn(self, btn, testo_orig):
        try:
            btn.configure(text=testo_orig)
        except Exception:
            pass

    def _clear_clipboard_if_matches(self, testo):
        try:
            attuale = self.clipboard_get()
            if attuale == testo:
                self.clipboard_clear()
        except Exception:
            pass

    def carica_lista_passwords(self):
        self.tutte_le_credenziali = []
        if not os.path.exists(FILE_DATI):
            self.after(0, self.aggiorna_vista_dopo_caricamento)
            return

        try:
            with open(FILE_DATI, "rb") as f:
                righe = f.readlines()

            for riga in righe:
                riga = riga.strip()
                if not riga:
                    continue
                try:
                    dati_chiari = self.fernet.decrypt(riga).decode("utf-8", errors="replace")
                    parts = dati_chiari.split("|")
                    if len(parts) >= 3:
                        servizio = parts[0]
                        user = parts[1]
                        password = "|".join(parts[2:])
                    elif len(parts) == 2:
                        servizio = parts[0]
                        user = parts[1]
                        password = ""
                    else:
                        servizio = parts[0]
                        user = ""
                        password = ""

                    self.tutte_le_credenziali.append({
                        "servizio": servizio,
                        "user": user,
                        "password": password
                    })
                except Exception:
                    # Riga corrotta o cifrata con altra chiave, prosegui
                    pass
        except Exception as e:
            print(f"Errore lettura file dati: {e}")

        self.after(0, self.aggiorna_vista_dopo_caricamento)

    def aggiorna_vista_dopo_caricamento(self):
        totale = len(self.tutte_le_credenziali)
        self.lbl_stats.configure(text=f"📂 {totale} password salvate")
        self.filtra_passwords()

    def filtra_passwords(self):
        query = self.ent_ricerca.get().strip().lower()
        if not query:
            self.credenziali_filtrate = list(self.tutte_le_credenziali)
        else:
            self.credenziali_filtrate = [
                c for c in self.tutte_le_credenziali
                if query in c["servizio"].lower() or query in c["user"].lower()
            ]

        self.max_mostrati = 50
        self.render_cards()

    def render_cards(self):
        for widget in self.scroll_passwords.winfo_children():
            widget.destroy()

        totale_trovati = len(self.credenziali_filtrate)
        if totale_trovati == 0:
            if len(self.tutte_le_credenziali) == 0:
                self.lbl_risultati.configure(text="Nessuna password presente nel vault. Aggiungine una sopra!")
            else:
                self.lbl_risultati.configure(text="Nessun risultato per la ricerca.")
            return

        visibili = min(self.max_mostrati, totale_trovati)
        self.lbl_risultati.configure(
            text=f"Visualizzate {visibili} di {totale_trovati} credenziali (Totale vault: {len(self.tutte_le_credenziali)})"
        )

        for i in range(visibili):
            item = self.credenziali_filtrate[i]
            self.crea_card_credenziale(item)

        if totale_trovati > self.max_mostrati:
            rimanenti = totale_trovati - self.max_mostrati
            btn_mostra_altri = ctk.CTkButton(
                self.scroll_passwords,
                text=f"⬇️ Mostra altri 50 ({rimanenti} rimanenti)",
                command=self.carica_altri,
                fg_color="#374151",
                hover_color="#4b5563",
                height=36
            )
            btn_mostra_altri.pack(pady=10, fill="x", padx=15)

    def carica_altri(self):
        self.max_mostrati += 50
        self.render_cards()

    def crea_card_credenziale(self, item):
        card = ctk.CTkFrame(self.scroll_passwords, corner_radius=8, fg_color="#1e293b")
        card.pack(fill="x", pady=4, padx=5)
        card.grid_columnconfigure(0, weight=1)

        # Riga Superiore: Servizio + Pulsanti Azione
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=12, pady=(8, 2))
        top_frame.grid_columnconfigure(0, weight=1)

        lbl_servizio = ctk.CTkLabel(
            top_frame,
            text=item["servizio"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38bdf8",
            anchor="w"
        )
        lbl_servizio.grid(row=0, column=0, sticky="w")

        actions_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")

        btn_copia_user = ctk.CTkButton(
            actions_frame,
            text="👤 User",
            width=65,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self.copia_con_timer(item["user"], btn_widget=btn_copia_user)
        )
        btn_copia_user.pack(side="left", padx=3)

        btn_copia_pass = ctk.CTkButton(
            actions_frame,
            text="📋 Pass",
            width=65,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#1f6aa5",
            hover_color="#144f7d",
            command=lambda: self.copia_con_timer(item["password"], btn_widget=btn_copia_pass)
        )
        btn_copia_pass.pack(side="left", padx=3)

        btn_elimina = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            command=lambda: self.elimina_credenziale(item)
        )
        btn_elimina.pack(side="left", padx=3)

        # Riga Inferiore: Username e Password (mascherata con toggle)
        bottom_frame = ctk.CTkFrame(card, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=(2, 8))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        user_text = item["user"] if item["user"] else "(Nessun username)"
        lbl_user = ctk.CTkLabel(
            bottom_frame,
            text=f"Utente: {user_text}",
            font=ctk.CTkFont(size=12),
            text_color="gray75",
            anchor="w"
        )
        lbl_user.grid(row=0, column=0, sticky="w")

        pwd_preview_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        pwd_preview_frame.grid(row=0, column=1, sticky="e")

        lbl_pwd_val = ctk.CTkLabel(
            pwd_preview_frame,
            text="••••••••••••",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="gray80"
        )
        lbl_pwd_val.pack(side="left", padx=4)

        btn_toggle = ctk.CTkButton(
            pwd_preview_frame,
            text="👁️",
            width=28,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569"
        )
        btn_toggle.configure(
            command=lambda lbl=lbl_pwd_val, btn=btn_toggle, pwd=item["password"]: self.toggle_card_password(lbl, btn, pwd)
        )
        btn_toggle.pack(side="left")

    def toggle_card_password(self, label_widget, btn_widget, password):
        if label_widget.cget("text") == "••••••••••••":
            label_widget.configure(text=password)
            btn_widget.configure(text="🔒")
        else:
            label_widget.configure(text="••••••••••••")
            btn_widget.configure(text="👁️")

    def salva_credenziale(self):
        servizio = self.ent_servizio.get().strip()
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get().strip()

        if not servizio or not pwd:
            messagebox.showwarning("Campi Incompleti", "Inserisci almeno il Nome del Servizio e la Password!")
            return

        chiaro = f"{servizio}|{user}|{pwd}".encode("utf-8")
        cifrato = self.fernet.encrypt(chiaro)

        try:
            with open(FILE_DATI, "ab") as f:
                f.write(cifrato + b"\n")
        except Exception as e:
            messagebox.showerror("Errore Salvataggio", f"Impossibile scrivere i dati:\n{e}")
            return

        nuovo_item = {"servizio": servizio, "user": user, "password": pwd}
        self.tutte_le_credenziali.insert(0, nuovo_item)

        self.ent_servizio.delete(0, "end")
        self.ent_user.delete(0, "end")
        self.ent_pass.delete(0, "end")

        self.lbl_stats.configure(text=f"📂 {len(self.tutte_le_credenziali)} password salvate")
        self.filtra_passwords()
        messagebox.showinfo("Successo", f"Credenziale per '{servizio}' salvata con successo!")

    def elimina_credenziale(self, item):
        conferma = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare definitivamente la password per '{item['servizio']}'?"
        )
        if not conferma:
            return

        try:
            self.tutte_le_credenziali.remove(item)
            self.riscrivi_database()
            self.lbl_stats.configure(text=f"📂 {len(self.tutte_le_credenziali)} password salvate")
            self.filtra_passwords()
            messagebox.showinfo("Eliminato", f"Password per '{item['servizio']}' eliminata con successo.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile completare l'eliminazione:\n{e}")

    def riscrivi_database(self):
        file_temp = FILE_DATI + ".tmp"
        with open(file_temp, "wb") as f:
            for item in self.tutte_le_credenziali:
                chiaro = f"{item['servizio']}|{item['user']}|{item['password']}".encode("utf-8")
                f.write(self.fernet.encrypt(chiaro) + b"\n")
        if os.path.exists(FILE_DATI):
            os.remove(FILE_DATI)
        os.rename(file_temp, FILE_DATI)

    def importa_csv_google(self):
        file_path = filedialog.askopenfilename(
            title="Seleziona file CSV di Google Passwords",
            filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")]
        )
        if not file_path:
            return

        importate = 0
        try:
            with open(file_path, mode="r", encoding="utf-8", errors="replace") as csvfile:
                reader = csv.DictReader(csvfile)
                if reader.fieldnames:
                    fields = {f.strip().lower(): f for f in reader.fieldnames}
                    name_key = fields.get("name") or fields.get("nome") or fields.get("url")
                    url_key = fields.get("url")
                    user_key = fields.get("username") or fields.get("nome utente") or fields.get("user")
                    pass_key = fields.get("password") or fields.get("parola d'ordine")

                    nuove_credenziali = []
                    for row in reader:
                        servizio = (row.get(name_key) or row.get(url_key) or "Sconosciuto").strip()
                        user = (row.get(user_key) or "").strip()
                        pwd = (row.get(pass_key) or "").strip()

                        if not pwd:
                            continue

                        nuove_credenziali.append({
                            "servizio": servizio,
                            "user": user,
                            "password": pwd
                        })
                        importate += 1

                    if nuove_credenziali:
                        with open(FILE_DATI, "ab") as f:
                            for c in nuove_credenziali:
                                chiaro = f"{c['servizio']}|{c['user']}|{c['password']}".encode("utf-8")
                                f.write(self.fernet.encrypt(chiaro) + b"\n")

                        self.tutte_le_credenziali = nuove_credenziali + self.tutte_le_credenziali
                        self.lbl_stats.configure(text=f"📂 {len(self.tutte_le_credenziali)} password salvate")
                        self.filtra_passwords()

            messagebox.showinfo("Importazione Completata", f"Importate con successo {importate} credenziali nel tuo Vault!")
        except Exception as e:
            messagebox.showerror("Errore Importazione", f"Impossibile importare il file CSV:\n{e}")

    def esporta_csv(self):
        if not self.tutte_le_credenziali:
            messagebox.showwarning("Nessun Dato", "Non ci sono credenziali da esportare!")
            return

        avviso = messagebox.askyesno(
            "Attenzione Sicurezza",
            "Il file CSV esportato conterrà le tue password in CHIARO (non cifrate).\n"
            "Assicurati di conservarlo in un luogo sicuro!\n\nVuoi procedere?"
        )
        if not avviso:
            return

        file_path = filedialog.asksaveasfilename(
            title="Salva Backup Password in CSV",
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv")]
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "url", "username", "password", "note"])
                for item in self.tutte_le_credenziali:
                    writer.writerow([item["servizio"], "", item["user"], item["password"], ""])

            messagebox.showinfo("Esportazione Completata", f"Esportate {len(self.tutte_le_credenziali)} credenziali in:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Errore Esportazione", f"Impossibile salvare il file CSV:\n{e}")


if __name__ == "__main__":
    app = PasswordManagerApp()
    app.mainloop()
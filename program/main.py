import tkinter as tk
from tkinter import messagebox
import bcrypt
from auta import open_auta_window

# 🔐 Funkcje do haszowania i sprawdzania haseł
def hash_password(plain_password):
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed

def check_password(plain_password, hashed_password):
    password_bytes = plain_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password)

# 🔐 Użytkownicy - hasła są zahashowane
UZYTKOWNICY = {
    "logistik1": hash_password("haslo123"),
    "logistik2": hash_password("haslo123"),
    "logistik3": hash_password("haslo123"),
    "logistik4": hash_password("haslo123"),
    "dosia92": hash_password("haslo123"),
    "admin": hash_password("adminpass")
}

# 📦 Start głównej aplikacji po zalogowaniu
def start_aplikacji(uzytkownik):
    def open_module(name):
        if name == "Auta":
            open_auta_window(root)
        else:
            messagebox.showinfo("Moduł", f"Moduł {name} nie jest jeszcze dostępny.")

    root = tk.Tk()
    root.title("System Logistyczny")
    root.geometry("1440x810")
    root.resizable(False, False)

    header = tk.Label(root, text="📦 SYSTEM LOGISTYCZNY", font=("Segoe UI", 24, "bold"), pady=20)
    header.pack()

    frame = tk.Frame(root)
    frame.pack(pady=40)

    button_opts = {
        "width": 25, "height": 4, "font": ("Segoe UI", 12),
        "bg": "#4a90e2", "fg": "white", "activebackground": "#357ABD"
    }

    rows = [
        [("👤 Kierowcy", "Kierowcy"), ("🚚 Auta", "Auta")],
        [("💰 Kalkulator Kosztów", "Kalkulator Kosztów"), ("🧭 Planowanie Kursów", "Planowanie Kursów")],
        [("🛠️ Serwis / Naprawy", "Serwis / Naprawy"), ("📄 Raporty / Eksport", "Raporty / Eksport")]
    ]

    for r in rows:
        row_frame = tk.Frame(frame)
        row_frame.pack(pady=10)
        for text, module_name in r:
            tk.Button(row_frame, text=text, command=lambda n=module_name: open_module(n), **button_opts).pack(side="left", padx=20)

    footer = tk.Frame(root)
    footer.pack(side="bottom", fill="x", pady=10)
    tk.Label(footer, text=f"🔒 Zalogowano jako: {uzytkownik}", font=("Segoe UI", 10)).pack(side="left", padx=20)
    tk.Button(footer, text="Wyloguj", command=root.quit).pack(side="right", padx=20)

    root.mainloop()

# 🔐 Ekran logowania
def pokaz_logowanie():
    login_win = tk.Tk()
    login_win.title("Logowanie")
    login_win.geometry("300x160")
    login_win.resizable(False, False)

    tk.Label(login_win, text="Login:").pack(pady=5)
    login_entry = tk.Entry(login_win)
    login_entry.pack()

    tk.Label(login_win, text="Hasło:").pack(pady=5)
    haslo_entry = tk.Entry(login_win, show="*")
    haslo_entry.pack()

    def zaloguj():
        login = login_entry.get()
        haslo = haslo_entry.get()
        if login in UZYTKOWNICY and check_password(haslo, UZYTKOWNICY[login]):
            login_win.destroy()
            start_aplikacji(login)
        else:
            messagebox.showerror("Błąd logowania", "Nieprawidłowy login lub hasło.")

    tk.Button(login_win, text="Zaloguj", command=zaloguj).pack(pady=10)

    login_win.mainloop()

# 🔁 Start programu
if __name__ == "__main__":
    pokaz_logowanie()

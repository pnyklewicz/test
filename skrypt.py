import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import csv
from datetime import datetime
import os

# --- Funkcje do wczytywania danych z CSV ---

def wczytaj_kierowcow(sciezka):
    kierowcy = {}
    if not os.path.isfile(sciezka):
        print(f"Brak pliku {sciezka}, wczytuję dane testowe.")
        # przykładowe dane testowe
        kierowcy = {
            "Jan Kowalski": {"kategorie": {"B"}, "status": "dostepny"},
            "Anna Nowak": {"kategorie": {"B", "C"}, "status": "choroba"},
            "Piotr Zielinski": {"kategorie": {"B", "C"}, "status": "urlop"},
        }
        return kierowcy

    with open(sciezka, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for wiersz in reader:
            imie = wiersz.get("imie", "").strip()
            nazwisko = wiersz.get("nazwisko", "").strip()
            if not imie or not nazwisko:
                continue
            nazwisko_imie = f"{imie} {nazwisko}"
            kat_str = wiersz.get("kategorie", "").strip()
            kategorie = set(k.strip() for k in kat_str.split(",") if k.strip())
            status = wiersz.get("status", "dostepny").strip().lower()
            urlop_od = wiersz.get("urlop_od", "").strip()
            urlop_do = wiersz.get("urlop_do", "").strip()

            # Jeśli jest urlop i jest dzisiaj w tym okresie, status zmieniamy na urlop
            if urlop_od and urlop_do:
                try:
                    od = datetime.strptime(urlop_od, "%Y-%m-%d").date()
                    do = datetime.strptime(urlop_do, "%Y-%m-%d").date()
                    today = datetime.today().date()
                    if od <= today <= do:
                        status = "urlop"
                except Exception:
                    pass

            kierowcy[nazwisko_imie] = {
                "kategorie": kategorie,
                "status": status
            }
    return kierowcy

def wczytaj_auta(sciezka):
    auta = []
    if not os.path.isfile(sciezka):
        print(f"Brak pliku {sciezka}, wczytuję dane testowe.")
        # przykładowe dane testowe
        auta = [
            ("ABC123", set(), "sprawne", "Toyota Corolla"),
            ("XYZ987", set(), "niesprawne", "Ford Transit"),
        ]
        return auta

    with open(sciezka, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for wiersz in reader:
            rejestracja = wiersz.get("rejestracja", "").strip()
            marka = wiersz.get("marka", "").strip()
            model = wiersz.get("model", "").strip()
            status = wiersz.get("status", "sprawne").strip().lower()
            if not rejestracja:
                continue
            wymagania = set()  # możesz tu dodać wymagania kategorii jeśli masz
            auta.append((rejestracja, wymagania, status, f"{marka} {model}"))
    return auta

# --- Stałe ---

kursy = ["I kurs", "II kurs", "Dalsze kursy"]

STATUS_KIEROWCY_COLORS = {
    "dostepny": "black",
    "choroba": "#fbb",
    "urlop": "#ffeb99",
}

# --- Dialog wyboru kierowcy ---

class KierowcaDialog(simpledialog.Dialog):
    def __init__(self, parent, kierowcy_lista):
        self.kierowcy_lista = kierowcy_lista
        self.wybrany = None
        super().__init__(parent, title="Wybierz kierowcę")

    def body(self, master):
        tk.Label(master, text="Wybierz kierowcę:").pack(pady=5)
        self.combo = ttk.Combobox(master, values=self.kierowcy_lista, state="readonly")
        self.combo.pack(padx=10)
        return self.combo

    def apply(self):
        self.wybrany = self.combo.get()

# --- Główna klasa aplikacji jako Frame ---

class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("System przypisywania kierowców do aut i kursów")
        self.master.geometry("950x480")

        # Wczytujemy dane z plików CSV (dostosuj ścieżki)
        self.kierowcy = wczytaj_kierowcow("kierowcy.csv")
        self.auta = wczytaj_auta("auta.csv")

        if not self.auta:
            messagebox.showwarning("Brak danych", "Brak danych o autach do wyświetlenia.")
        if not self.kierowcy:
            messagebox.showwarning("Brak danych", "Brak danych o kierowcach do wyświetlenia.")

        self.przypisania = {(auto[0], kurs): None for auto in self.auta for kurs in kursy}
        self.status_auta = {auto[0]: (auto[2] == "sprawne") for auto in self.auta}
        self.status_kierowcy = {k: v["status"] for k, v in self.kierowcy.items()}

        self.combobox = None
        self.clicked_auto = None
        self.clicked_kierowca = None

        self.create_widgets()
        self.refresh_kierowcy_list()
        self.refresh_table()

    def create_widgets(self):
        frame_left = tk.Frame(self)
        frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(frame_left, text="Kierowcy (dostępni):").pack()

        self.lst_kierowcy = tk.Listbox(frame_left, height=25, selectmode=tk.SINGLE)
        self.lst_kierowcy.pack(fill=tk.Y)

        self.lst_kierowcy.bind("<Button-3>", self.on_right_click_kierowca)

        # Menu kontekstowe dla kierowców (status i dodaj)
        self.menu_kierowca = tk.Menu(self, tearoff=0)
        self.menu_kierowca.add_command(label="Ustaw jako dostępny", command=lambda: self.set_status_kierowcy("dostepny"))
        self.menu_kierowca.add_command(label="Ustaw jako zwolnienie chorobowe", command=lambda: self.set_status_kierowcy("choroba"))
        self.menu_kierowca.add_command(label="Ustaw jako urlop", command=lambda: self.set_status_kierowcy("urlop"))
        self.menu_kierowca.add_separator()
        self.menu_kierowca.add_command(label="Dodaj kierowcę do aktywnego auta i kursu", command=self.menu_dodaj_kierowce)

        frame_right = tk.Frame(self)
        frame_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tbl = ttk.Treeview(frame_right, columns=["auto"] + kursy, show="headings", height=15)
        self.tbl.heading("auto", text="Auto")
        self.tbl.column("auto", width=200, anchor=tk.W)

        for k in kursy:
            self.tbl.heading(k, text=k)
            self.tbl.column(k, width=150, anchor=tk.CENTER)

        self.tbl.pack(fill=tk.BOTH, expand=True)

        for auto, wym, status, opis in self.auta:
            self.tbl.insert("", tk.END, iid=auto, values=[f"{auto} ({opis})"] + [""] * len(kursy))

        self.tbl.bind("<Button-1>", self.on_left_click_table)
        self.tbl.bind("<Button-3>", self.on_right_click_auto)

        # Menu kontekstowe dla aut
        self.menu_auto = tk.Menu(self, tearoff=0)
        self.menu_auto.add_command(label="Oznacz jako sprawne", command=self.set_auto_sprawne)
        self.menu_auto.add_command(label="Oznacz jako niesprawne", command=self.set_auto_niesprawne)

        self.pack(fill="both", expand=True)

    def refresh_kierowcy_list(self):
        self.lst_kierowcy.delete(0, tk.END)
        for k in self.kierowcy.keys():
            self.lst_kierowcy.insert(tk.END, k)
            kolor = STATUS_KIEROWCY_COLORS.get(self.status_kierowcy.get(k, "dostepny"), "black")
            self.lst_kierowcy.itemconfig(tk.END, fg=kolor)

    def refresh_table(self):
        for auto, wym, status, opis in self.auta:
            row = []
            for kurs in kursy:
                kier = self.przypisania.get((auto, kurs))
                row.append(kier if kier else "")

            self.tbl.item(auto, values=[f"{auto} ({opis})"] + row)

            if not self.status_auta.get(auto, True):
                self.tbl.tag_configure(auto, background="#f88")
                self.tbl.item(auto, tags=(auto,))
            else:
                self.tbl.tag_configure(auto, background="white")
                self.tbl.item(auto, tags=(auto,))

        self.master.title("System przypisywania kierowców do aut i kursów")

    def on_left_click_table(self, event):
        if self.combobox:
            self.combobox.destroy()
            self.combobox = None

        row_id = self.tbl.identify_row(event.y)
        col = self.tbl.identify_column(event.x)

        if not row_id or col == "#1":  # Kolumna z autami - brak interakcji
            return

        kurs_index = int(col.replace("#", "")) - 2
        if kurs_index < 0 or kurs_index >= len(kursy):
            return
        kurs = kursy[kurs_index]

        auto = row_id

        # Lista dostępnych kierowców spełniających wymagania
        kierowcy_lista = []
        for k, dane in self.kierowcy.items():
            if dane["status"] != "dostepny":
                continue
            kierowcy_lista.append(k)

        if not kierowcy_lista:
            messagebox.showinfo("Brak kierowców", "Brak dostępnych kierowców do przypisania.")
            return

        # Utwórz combobox nad komórką
        bbox = self.tbl.bbox(row_id, col)
        if not bbox:
            return
        x, y, width, height = bbox

        self.combobox = ttk.Combobox(self.tbl, values=kierowcy_lista, state="readonly")
        self.combobox.place(x=x, y=y, width=width, height=height)
        self.combobox.focus()
        self.combobox.bind("<<ComboboxSelected>>", lambda e: self.on_combobox_selected(auto, kurs))

    def on_combobox_selected(self, auto, kurs):
        if self.combobox:
            wybrany = self.combobox.get()
            self.przypisania[(auto, kurs)] = wybrany
            self.refresh_table()
            self.combobox.destroy()
            self.combobox = None

    def on_right_click_kierowca(self, event):
        index = self.lst_kierowcy.nearest(event.y)
        if index < 0:
            return
        self.lst_kierowcy.selection_clear(0, tk.END)
        self.lst_kierowcy.selection_set(index)
        self.clicked_kierowca = self.lst_kierowcy.get(index)
        self.menu_kierowca.tk_popup(event.x_root, event.y_root)

    def set_status_kierowcy(self, status):
        if not self.clicked_kierowca:
            return
        self.status_kierowcy[self.clicked_kierowca] = status
        self.refresh_kierowcy_list()
        self.clicked_kierowca = None

    def menu_dodaj_kierowce(self):
        # Pobierz listę kierowców dostępnych
        kierowcy_dostepni = [k for k, d in self.kierowcy.items() if self.status_kierowcy.get(k, "dostepny") == "dostepny"]
        if not kierowcy_dostepni:
            messagebox.showinfo("Brak kierowców", "Brak dostępnych kierowców do przypisania.")
            return

        dlg = KierowcaDialog(self, kierowcy_dostepni)
        if dlg.wybrany:
            # Dodaj kierowcę do pierwszego auta i kursu, które nie mają przypisania
            for (auto, kurs), kier in self.przypisania.items():
                if kier is None:
                    self.przypisania[(auto, kurs)] = dlg.wybrany
                    break
            self.refresh_table()

    def on_right_click_auto(self, event):
        row_id = self.tbl.identify_row(event.y)
        if not row_id:
            return
        self.clicked_auto = row_id
        self.menu_auto.tk_popup(event.x_root, event.y_root)

    def set_auto_sprawne(self):
        if not self.clicked_auto:
            return
        self.status_auta[self.clicked_auto] = True
        self.refresh_table()
        self.clicked_auto = None

    def set_auto_niesprawne(self):
        if not self.clicked_auto:
            return
        self.status_auta[self.clicked_auto] = False
        self.refresh_table()
        self.clicked_auto = None

# --- Uruchomienie okna ---

def open_planowanie_window(root):
    okno = tk.Toplevel(root)
    app = App(okno)
    app.pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # ukryj główne okno, jeśli chcesz
    open_planowanie_window(root)
    root.mainloop()

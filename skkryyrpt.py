import csv
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

STATUS_KIEROWCY_COLORS = {
    "dostepny": "black",
    "choroba": "#fbb",
    "urlop": "#ffeb99",
}

def wczytaj_kierowcow_csv(sciezka):
    kierowcy_dict = {}
    status_kierowcy_dict = {}
    with open(sciezka, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            imie = row['imie'].strip()
            nazwisko = row['nazwisko'].strip()
            klucz = f"{imie} {nazwisko}"
            kat = set(cat.strip() for cat in row['kategorie'].split(',') if cat.strip())
            kierowcy_dict[klucz] = kat
            status_kierowcy_dict[klucz] = row.get('status', 'dostepny').lower()
    return kierowcy_dict, status_kierowcy_dict

def wczytaj_auta_csv(sciezka):
    auta_list = []
    with open(sciezka, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nazwa = row['nazwa'].strip()
            kat = set(cat.strip() for cat in row['kategorie'].split(',') if cat.strip())
            auta_list.append((nazwa, kat))
    return auta_list

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

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System przypisywania kierowców do aut i kursów")
        self.geometry("950x480")

        # Wczytanie danych z CSV
        self.kierowcy, self.status_kierowcy = wczytaj_kierowcow_csv('kierowcy.csv')
        self.auta = wczytaj_auta_csv('auta.csv')

        self.kursy = ["I kurs", "II kurs", "Dalsze kursy"]

        self.przypisania = {(auto, kurs): None for auto, _ in self.auta for kurs in self.kursy}
        self.kierowcy_dostepni = {k: set(self.kierowcy.keys()) for k in self.kursy}
        self.status_auta = {auto: True for auto, _ in self.auta}

        self.aktywne_auto = None
        self.aktywny_kurs = None
        self.combobox = None

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
        
        self.menu_kierowca = tk.Menu(self, tearoff=0)
        self.menu_kierowca.add_command(label="Ustaw jako dostępny", command=lambda: self.set_status_kierowcy("dostepny"))
        self.menu_kierowca.add_command(label="Ustaw jako zwolnienie chorobowe", command=lambda: self.set_status_kierowcy("choroba"))
        self.menu_kierowca.add_command(label="Ustaw jako urlop", command=lambda: self.set_status_kierowcy("urlop"))
        self.menu_kierowca.add_separator()
        self.menu_kierowca.add_command(label="Dodaj kierowcę do aktywnego auta i kursu", command=self.menu_dodaj_kierowce)

        frame_right = tk.Frame(self)
        frame_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tbl = ttk.Treeview(frame_right, columns=["auto"] + self.kursy, show="headings", height=len(self.auta))
        self.tbl.heading("auto", text="Auto")
        self.tbl.column("auto", width=120, anchor=tk.W)

        for k in self.kursy:
            self.tbl.heading(k, text=k)
            self.tbl.column(k, width=150, anchor=tk.CENTER)

        self.tbl.pack(fill=tk.BOTH, expand=True)

        for auto, wym in self.auta:
            self.tbl.insert("", tk.END, iid=auto, values=[auto] + [""] * len(self.kursy))

        self.tbl.bind("<Button-1>", self.on_left_click_table)
        self.tbl.bind("<Button-3>", self.on_right_click_auto)

        self.menu_auto = tk.Menu(self, tearoff=0)
        self.menu_auto.add_command(label="Oznacz jako sprawne", command=self.set_auto_sprawne)
        self.menu_auto.add_command(label="Oznacz jako niesprawne", command=self.set_auto_niesprawne)

        self.clicked_auto = None
        self.clicked_kierowca = None

    def refresh_kierowcy_list(self):
        self.lst_kierowcy.delete(0, tk.END)
        for k in self.kierowcy.keys():
            self.lst_kierowcy.insert(tk.END, k)
            kolor = STATUS_KIEROWCY_COLORS.get(self.status_kierowcy.get(k, "dostepny"), "black")
            self.lst_kierowcy.itemconfig(tk.END, fg=kolor)

    def refresh_table(self):
        for auto, wym in self.auta:
            row = []
            for kurs in self.kursy:
                kier = self.przypisania[(auto, kurs)]
                row.append(kier if kier else "")

            self.tbl.item(auto, values=[auto] + row)

            if not self.status_auta.get(auto, True):
                self.tbl.tag_configure(auto, background="#f88")
                self.tbl.item(auto, tags=(auto,))
            else:
                self.tbl.tag_configure(auto, background="white")
                self.tbl.item(auto, tags=(auto,))

        if self.aktywne_auto and self.aktywny_kurs:
            self.title(f"Aktywne auto: {self.aktywne_auto}, kurs: {self.aktywny_kurs}")
        else:
            self.title("System przypisywania kierowców do aut i kursów")

    def on_left_click_table(self, event):
        if self.combobox:
            self.combobox.destroy()
            self.combobox = None

        row_id = self.tbl.identify_row(event.y)
        col = self.tbl.identify_column(event.x)

        if not row_id or not col:
            return

        col_index = int(col[1:]) - 1
        if col_index == 0:
            return

        kurs = self.kursy[col_index - 1]
        auto = row_id

        wym = next(w for a, w in self.auta if a == auto)

        kandydaci = [""] + [k for k, uprawnienia in self.kierowcy.items()
                     if self.status_kierowcy.get(k, "dostepny") == "dostepny" and wym.issubset(uprawnienia)]

        kandydaci = [""] + [k for k in kandydaci[1:]
                     if not any(self.przypisania[(a, kurs)] == k and a != auto for a, _ in self.auta)]

        if not kandydaci:
            messagebox.showinfo("Brak kierowców", "Brak dostępnych kierowców z wymaganymi uprawnieniami i nieprzypisanych do tego kursu.")
            return

        bbox = self.tbl.bbox(row_id, col)
        if not bbox:
            return
        x, y, width, height = bbox

        self.combobox = ttk.Combobox(self.tbl, values=kandydaci, state="readonly")
        self.combobox.place(x=x, y=y, width=width, height=height)
        self.combobox.focus()

        obecny = self.przypisania[(auto, kurs)]
        if obecny in kandydaci:
            self.combobox.set(obecny)
        else:
            self.combobox.set("")

        def zatwierdz(event=None):
            wybor = self.combobox.get()
            if wybor not in kandydaci:
                self.combobox.destroy()
                self.combobox = None
                return
            if wybor == "":
                self.przypisania[(auto, kurs)] = None
            else:
                self.przypisania[(auto, kurs)] = wybor
            self.refresh_table()
            self.combobox.destroy()
            self.combobox = None

        self.combobox.bind("<<ComboboxSelected>>", zatwierdz)
        self.combobox.bind("<FocusOut>", lambda e: (self.combobox.destroy(), setattr(self, "combobox", None)))

    def on_right_click_auto(self, event):
        region = self.tbl.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.tbl.identify_row(event.y)
        col = self.tbl.identify_column(event.x)

        if row_id == "" or col == "":
            return

        if col == "#1":
            self.clicked_auto = row_id
            self.menu_auto.tk_popup(event.x_root, event.y_root)

    def set_auto_sprawne(self):
        if self.clicked_auto:
            self.status_auta[self.clicked_auto] = True
            self.refresh_table()

    def set_auto_niesprawne(self):
        if self.clicked_auto:
            self.status_auta[self.clicked_auto] = False
            self.refresh_table()

    def on_right_click_kierowca(self, event):
        selection = self.lst_kierowcy.nearest(event.y)
        if selection >= 0:
            self.clicked_kierowca = self.lst_kierowcy.get(selection)
            self.menu_kierowca.tk_popup(event.x_root, event.y_root)

    def set_status_kierowcy(self, status):
        if self.clicked_kierowca:
            self.status_kierowcy[self.clicked_kierowca] = status
            self.refresh_kierowcy_list()

    def menu_dodaj_kierowce(self):
        if not self.aktywne_auto or not self.aktywny_kurs:
            messagebox.showwarning("Brak aktywnego auta i kursu", "Proszę najpierw kliknąć w tabelę i wybrać auto oraz kurs.")
            return
        wym = next(w for a, w in self.auta if a == self.aktywne_auto)
        kandydaci = [k for k, uprawnienia in self.kierowcy.items()
                     if self.status_kierowcy.get(k, "dostepny") == "dostepny" and wym.issubset(uprawnienia)]

        kandydaci = [k for k in kandydaci
                     if not any(self.przypisania[(a, self.aktywny_kurs)] == k and a != self.aktywne_auto for a, _ in self.auta)]

        if not kandydaci:
            messagebox.showinfo("Brak kierowców", "Brak dostępnych kierowców z wymaganymi uprawnieniami i nieprzypisanych do tego kursu.")
            return

        dlg = KierowcaDialog(self, kandydaci)
        if dlg.wybrany:
            self.przypisania[(self.aktywne_auto, self.aktywny_kurs)] = dlg.wybrany
            self.refresh_table()

if __name__ == "__main__":
    app = App()
    app.mainloop()

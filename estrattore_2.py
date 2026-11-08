import os
import sys
import tkinter as tk
import zipfile
from tkinter import messagebox, ttk

from progress_window import ExtractionProgressWindow


class DarkFileBrowser(tk.Toplevel):
    """Browser scuro: seleziona un file (.zip) oppure una cartella.

    choose_directories=False -> modalità file: doppio clic su un .zip lo sceglie.
    choose_directories=True  -> modalità cartella: si naviga e si conferma
                                la cartella corrente con l'apposito pulsante.
    """

    def __init__(
        self,
        parent,
        palette,
        title="Seleziona",
        start_dir=None,
        file_ext=".zip",
        choose_directories=False,
    ):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=palette["BG_MAIN"])
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.choose_directories = choose_directories
        self.file_ext = file_ext.lower()
        self.palette = palette

        self.current_dir = os.path.abspath(start_dir or os.path.expanduser("~"))

        self.geometry("700x500")
        self.minsize(520, 380)

        # Barra superiore: percorso + pulsante su
        top = tk.Frame(self, bg=palette["BG_MAIN"])
        top.pack(fill="x", padx=12, pady=(12, 6))

        self.path_var = tk.StringVar(value=self.current_dir)
        path_entry = tk.Entry(
            top,
            textvariable=self.path_var,
            bg=palette["BG_CARD"],
            fg=palette["FG_TEXT"],
            insertbackground=palette["FG_TEXT"],
            relief="flat",
            font=("Segoe UI", 10),
        )
        path_entry.pack(side="left", fill="x", expand=True, ipady=5)
        path_entry.bind("<Return>", self._on_path_enter)

        btn_up = tk.Button(
            top,
            text="⬆ Su",
            command=self._go_up,
            bg=palette["ACCENT"],
            fg="#ffffff",
            activebackground=palette["ACCENT_HOVER"],
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            cursor="hand2",
        )
        btn_up.pack(side="left", padx=(8, 0), ipady=3)

        # Lista file/cartelle
        list_frame = tk.Frame(self, bg=palette["BG_MAIN"])
        list_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.listbox = tk.Listbox(
            list_frame,
            bg=palette["BG_CARD"],
            fg=palette["FG_TEXT"],
            selectbackground=palette["ACCENT"],
            selectforeground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=palette["SEP"],
            highlightcolor=palette["ACCENT"],
            font=("Segoe UI", 10),
            activestyle="none",
        )
        scrollbar = tk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.listbox.yview,
            bg=palette["BG_CARD"],
            troughcolor=palette["BG_MAIN"],
        )
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        self.listbox.bind("<Return>", self._on_double_click)

        # Pulsanti inferiori
        bottom = tk.Frame(self, bg=palette["BG_MAIN"])
        bottom.pack(fill="x", padx=12, pady=(6, 12))

        btn_cancel = tk.Button(
            bottom,
            text="Annulla",
            command=self._cancel,
            bg=palette["BG_CARD"],
            fg=palette["FG_TEXT"],
            activebackground=palette["SEP"],
            activeforeground=palette["FG_TEXT"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=16,
            pady=6,
            cursor="hand2",
        )
        btn_cancel.pack(side="right")

        if self.choose_directories:
            # Modalità cartella: conferma la cartella corrente
            btn_pick = tk.Button(
                bottom,
                text="✅ Estrai qui",
                command=self._pick_current_dir,
                bg=palette["ACCENT"],
                fg="#ffffff",
                activebackground=palette["ACCENT_HOVER"],
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=6,
                cursor="hand2",
            )
            btn_pick.pack(side="right", padx=(0, 8))
        else:
            # Modalità file: conferma il file selezionato
            btn_open = tk.Button(
                bottom,
                text="Apri",
                command=self._confirm_selection,
                bg=palette["ACCENT"],
                fg="#ffffff",
                activebackground=palette["ACCENT_HOVER"],
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=6,
                cursor="hand2",
            )
            btn_open.pack(side="right", padx=(0, 8))

        self.bind("<Escape>", lambda e: self._cancel())

        self._refresh()
        self.wait_window()

    # --- Navigazione ---
    def _refresh(self):
        self.listbox.delete(0, "end")
        self.entries = []
        try:
            names = os.listdir(self.current_dir)
        except (PermissionError, FileNotFoundError):
            names = []

        # In modalità cartella mostra SOLO directory
        if self.choose_directories:
            entries_iter = sorted(
                (n for n in names if os.path.isdir(os.path.join(self.current_dir, n))),
                key=str.lower,
            )
            for d in entries_iter:
                self.entries.append((d, True))
                self.listbox.insert("end", f"📁  {d}")
        else:
            dirs = sorted(
                (n for n in names if os.path.isdir(os.path.join(self.current_dir, n))),
                key=str.lower,
            )
            files = sorted(
                (
                    n
                    for n in names
                    if os.path.isfile(os.path.join(self.current_dir, n))
                    and n.lower().endswith(self.file_ext)
                ),
                key=str.lower,
            )
            for d in dirs:
                self.entries.append((d, True))
                self.listbox.insert("end", f"📁  {d}")
            for f in files:
                self.entries.append((f, False))
                self.listbox.insert("end", f"📦  {f}")

        if not self.entries:
            self.listbox.insert("end", "(cartella vuota)")

        self.path_var.set(self.current_dir)

    def _go_up(self):
        parent = os.path.dirname(self.current_dir.rstrip(os.sep))
        if parent and parent != self.current_dir:
            self.current_dir = parent
            self._refresh()

    def _on_path_enter(self, event=None):
        path = os.path.expanduser(self.path_var.get().strip())
        if os.path.isdir(path):
            self.current_dir = os.path.abspath(path)
            self._refresh()
        elif os.path.isfile(path) and not self.choose_directories:
            self.result = os.path.abspath(path)
            self.destroy()

    def _on_double_click(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        name, is_dir = self.entries[sel[0]]
        full = os.path.join(self.current_dir, name)
        if is_dir:
            self.current_dir = full
            self._refresh()
        elif not self.choose_directories:
            self.result = full
            self.destroy()

    def _confirm_selection(self):
        sel = self.listbox.curselection()
        if sel and not self.entries[sel[0]][1]:
            self.result = os.path.join(self.current_dir, self.entries[sel[0]][0])
            self.destroy()
        else:
            self._on_path_enter()

    def _pick_current_dir(self):
        """Modalità cartella: conferma la cartella attualmente aperta."""
        self.result = self.current_dir
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class DarkZipExtractorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("🔥 Estrattore Selettivo Giochi v2.5")
        self.root.geometry("520x670")
        self.root.minsize(450, 550)

        # --- Palette Colori Tema Scuro ---
        self.BG_MAIN = "#1e1e24"  # Sfondo principale scuro
        self.BG_CARD = "#2a2a32"  # Sfondo sezioni e liste
        self.FG_TEXT = "#f0f0f5"  # Testo principale chiaro
        self.FG_MUTED = "#a0a0aa"  # Testo secondario/disabilitato
        self.ACCENT = "#4f46e5"  # Blu moderno per pulsanti
        self.ACCENT_HOVER = "#6366f1"
        self.SEP = "#3f3f46"  # Colore separatori

        self.palette = {
            "BG_MAIN": self.BG_MAIN,
            "BG_CARD": self.BG_CARD,
            "FG_TEXT": self.FG_TEXT,
            "FG_MUTED": self.FG_MUTED,
            "ACCENT": self.ACCENT,
            "ACCENT_HOVER": self.ACCENT_HOVER,
            "SEP": self.SEP,
        }

        self.root.configure(bg=self.BG_MAIN)

        # --- Configurazione Stile TTK ---
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Stili generali per elementi TTK
        self.style.configure(
            ".",
            font=("Segoe UI", 10),
            background=self.BG_MAIN,
            foreground=self.FG_TEXT,
        )
        self.style.configure("TFrame", background=self.BG_MAIN, foreground=self.FG_TEXT)

        # LabelFrame personalizzato scuro
        self.style.configure(
            "TLabelframe",
            background=self.BG_MAIN,
            foreground=self.FG_TEXT,
            bordercolor=self.BG_CARD,
        )
        self.style.configure(
            "TLabelframe.Label", background=self.BG_MAIN, foreground=self.FG_TEXT
        )

        # Bottoni personalizzati scuri
        self.style.configure(
            "Dark.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.ACCENT,
            foreground="#ffffff",
            borderwidth=0,
            focuscolor="none",
        )
        self.style.map(
            "Dark.TButton",
            background=[("active", self.ACCENT_HOVER), ("disabled", "#3f3f46")],
            foreground=[("disabled", self.FG_MUTED)],
        )

        # Checkbutton scuri
        self.style.configure(
            "TCheckbutton",
            background=self.BG_CARD,
            foreground=self.FG_TEXT,
            focuscolor="none",
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", self.BG_CARD)],
            foreground=[("active", self.FG_TEXT)],
        )

        # Scrollbar minimale scura
        self.style.configure(
            "TScrollbar",
            gripcount=0,
            background=self.BG_CARD,
            darkcolor=self.BG_MAIN,
            lightcolor=self.BG_MAIN,
            troughcolor=self.BG_MAIN,
            bordercolor=self.BG_MAIN,
            arrowcolor=self.FG_TEXT,
        )

        self.zip_path = "./"
        self.last_browser_dir = "./"  # Ricorda l'ultima cartella usata nel browser

        # --- Struttura Interfaccia Grafica (UI) ---

        # 1. Sezione Caricamento File
        self.top_frame = ttk.Frame(root, padding="15 15 15 5")
        self.top_frame.pack(fill="x")

        self.btn_select = ttk.Button(
            self.top_frame,
            text="📁 Seleziona File ZIP",
            command=self.load_zip,
            style="Dark.TButton",
        )
        self.btn_select.pack(fill="x", ipady=4)

        self.lbl_file = tk.Label(
            self.top_frame,
            text="Carica il pacchetto ZIP dei giochi per iniziare.",
            font=("Segoe UI", 10, "italic"),
            bg=self.BG_MAIN,
            fg=self.FG_MUTED,
            wraplength=480,
            justify="center",
        )
        self.lbl_file.pack(pady=12)

        # Separatore lineare scuro
        self.sep = tk.Frame(root, height=1, bg=self.SEP)
        self.sep.pack(fill="x", padx=15, pady=5)

        # 2. Pulsanti di Selezione Rapida Tutto/Nulla
        self.action_bar = ttk.Frame(root, padding="15 5 15 5")
        self.action_bar.pack(fill="x")

        self.btn_all = ttk.Button(
            self.action_bar,
            text="☑ Seleziona Tutti",
            command=self.select_all,
            state="disabled",
            style="Dark.TButton",
        )
        self.btn_all.pack(side="left", padx=2, expand=True, fill="x")

        self.btn_none = ttk.Button(
            self.action_bar,
            text="☒ Deseleziona Tutti",
            command=self.deselect_all,
            state="disabled",
            style="Dark.TButton",
        )
        self.btn_none.pack(side="left", padx=2, expand=True, fill="x")

        # 3. Contenitore Lista Giochi (Canvas + Frame interno)
        self.frame_list = ttk.LabelFrame(
            root, text=" 🎮 Elenco Giochi Rilevati nello ZIP ", padding=10
        )
        self.frame_list.pack(pady=10, fill="both", expand=True, padx=15)

        # Sfondo scuro impostato direttamente sul canvas nativo di tkinter
        self.canvas = tk.Canvas(
            self.frame_list,
            bg=self.BG_CARD,
            borderwidth=0,
            highlightthickness=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self.frame_list, orient="vertical", command=self.canvas.yview
        )

        # Frame interno alla lista, con sfondo scuro coordinato
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.BG_CARD)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Supporto alla rotella del mouse (Scroll)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)  # rotella Linux
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)  # rotella Linux

        # 4. Sezione Inferiore: Pulsante Estrazione Principale
        self.bottom_frame = ttk.Frame(root, padding="15 5 15 15")
        self.bottom_frame.pack(fill="x")

        self.btn_extract = ttk.Button(
            self.bottom_frame,
            text="🚀 Estrai i Giochi Selezionati",
            command=self.extract_games,
            state="disabled",
            style="Dark.TButton",
        )
        self.btn_extract.pack(fill="x", ipady=8)

    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def _open_dark_browser(self, title, choose_directories=False):
        """Apre il browser scuro e memorizza l'ultima cartella visitata."""
        start = self.last_browser_dir if self.last_browser_dir else None
        browser = DarkFileBrowser(
            self.root,
            self.palette,
            title=title,
            start_dir=start,
            file_ext=".zip",
            choose_directories=choose_directories,
        )
        if browser.result:
            self.last_browser_dir = (
                browser.current_dir
                if choose_directories
                else os.path.dirname(browser.result)
            )
        return browser.result

    def select_all(self):
        for var in self.game_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.game_vars.values():
            var.set(False)

    def load_zip(self):
        # Browser file scuro personalizzato (niente dialog bianco di Tk)
        chosen = self._open_dark_browser("Seleziona il pacchetto ZIP dei giochi")
        if not chosen:
            return

        self.zip_path = chosen
        self.lbl_file.config(
            text=f"📦 Archivio Caricato: {os.path.basename(self.zip_path)}",
            fg="#60a5fa",  # Colore azzurro chiaro sul testo
        )

        # Reset della vecchia lista
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.game_vars = {}

        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                top_level_dirs = set()
                for name in z.namelist():
                    parts = name.split("/")
                    if parts and parts[0]:
                        top_level_dirs.add(parts[0])

                if not top_level_dirs:
                    messagebox.showwarning(
                        "Attenzione", "Nessuna cartella di gioco valida nello ZIP."
                    )
                    return

                # Popola la lista con checkbox scure
                for game in sorted(top_level_dirs):
                    var = tk.BooleanVar(value=True)
                    self.game_vars[game] = var

                    # Riquadro riga scuro
                    row_frame = tk.Frame(self.scrollable_frame, bg=self.BG_CARD, pady=4)
                    row_frame.pack(fill="x", anchor="w")

                    chk = ttk.Checkbutton(row_frame, text=game, variable=var)
                    chk.pack(side="left", padx=10)

            # Sblocca i pulsanti operativi
            self.btn_extract.config(state="normal")
            self.btn_all.config(state="normal")
            self.btn_none.config(state="normal")

        except Exception as e:
            messagebox.showerror(
                "Errore", f"Impossibile leggere il file ZIP:\n{str(e)}"
            )

    def extract_games(self):
        # Anche per la destinazione usiamo il nostro browser scuro,
        # in modalità "scegli cartella" (niente filedialog bianco!)
        dest_dir = self._open_dark_browser(
            "Dove vuoi estrarre i giochi?", choose_directories=True
        )
        if not dest_dir:
            return

        selected_games = [game for game, var in self.game_vars.items() if var.get()]

        if not selected_games:
            messagebox.showwarning("Attenzione", "Seleziona almeno un gioco!")
            return

        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                all_files = z.namelist()
                files_to_extract = [
                    file
                    for file in all_files
                    if any(
                        file.startswith(game + "/") or file == game
                        for game in selected_games
                    )
                ]

                # --- Finestra di progresso scura ---
                pw = ExtractionProgressWindow(
                    self.root, self.palette, total=len(files_to_extract)
                )
                for file in files_to_extract:
                    if pw.cancelled:  # l'utente ha premuto Annulla
                        break
                    z.extract(file, dest_dir)
                    pw.step(file)  # aggiorna barra, nome file, contatore

                pw.close()

                if pw.cancelled:
                    messagebox.showwarning(
                        "Annullato", "Estrazione interrotta dall'utente."
                    )
                else:
                    messagebox.showinfo("Fatto!", "Estrazione completata con successo!")
        except Exception as e:
            messagebox.showerror(
                "Errore di Estrazione", f"Si è verificato un errore:\n{str(e)}"
            )
        finally:
            self.btn_extract.config(
                text="🚀 Estrai i Giochi Selezionati", state="normal"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = DarkZipExtractorApp(root)
    root.mainloop()

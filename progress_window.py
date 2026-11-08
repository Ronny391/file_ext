"""progress_window.py

Finestra di avanzamento per l'estrazione dei giochi.
Importabile dal file principale con:

    from progress_window import ExtractionProgressWindow
"""

import time
import tkinter as tk
from tkinter import ttk


class ExtractionProgressWindow(tk.Toplevel):
    """Finestra modale scura con barra di progresso e pulsante Annulla.

    Uso tipico (estrazione gira nel thread principale):

        pw = ExtractionProgressWindow(root, palette, total=len(files_to_extract))
        for i, file in enumerate(files_to_extract):
            if pw.cancelled:
                break
            z.extract(file, dest_dir)
            pw.step(file)          # aggiorna barra + nome file + contatore
        pw.close()
    """

    def __init__(self, parent, palette, total=None):
        super().__init__(parent)
        self.title("⏳ Estrazione in corso")
        self.configure(bg=palette["BG_MAIN"])
        self.transient(parent)
        self.grab_set()  # blocca l'interazione con la finestra principale
        self.resizable(False, False)
        self.cancelled = False

        self.total = total
        self.done = 0
        self.start_time = time.time()

        w, h = 420, 190
        # Centra la finestra sopra il parent
        parent_x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        parent_y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(parent_x, 0)}+{max(parent_y, 0)}")

        # Titolo
        tk.Label(
            self,
            text="⏳ Estrazione in corso…",
            font=("Segoe UI", 12, "bold"),
            bg=palette["BG_MAIN"],
            fg=palette["FG_TEXT"],
        ).pack(pady=(18, 6))

        # Nome del file corrente
        self.lbl_file = tk.Label(
            self,
            text="Preparazione…",
            font=("Segoe UI", 9),
            bg=palette["BG_MAIN"],
            fg=palette["FG_MUTED"],
            wraplength=380,
        )
        self.lbl_file.pack(pady=(0, 10))

        # Barra di progresso
        style = ttk.Style(self)
        style.theme_use(parent.tk.call("ttk::style", "theme", "use"))
        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=palette["BG_CARD"],
            background=palette["ACCENT"],
            bordercolor=palette["BG_MAIN"],
            lightcolor=palette["ACCENT"],
            darkcolor=palette["ACCENT"],
        )
        self.bar = ttk.Progressbar(
            self,
            style="Dark.Horizontal.TProgressbar",
            maximum=100,
            length=360,
            mode="determinate",
        )
        self.bar.pack(pady=(0, 10))

        # Contatore + tempo
        self.lbl_count = tk.Label(
            self,
            text="",
            font=("Segoe UI", 9),
            bg=palette["BG_MAIN"],
            fg=palette["FG_TEXT"],
        )
        self.lbl_count.pack()

        # Pulsante Annulla
        tk.Button(
            self,
            text="✖ Annulla",
            command=self._cancel,
            bg=palette["BG_CARD"],
            fg=palette["FG_TEXT"],
            activebackground=palette["SEP"],
            activeforeground=palette["FG_TEXT"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=5,
            cursor="hand2",
        ).pack(pady=(12, 14))

        # Protocollo: la X della finestra fa da Annulla
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._refresh_bar()

    # --- API pubblica ---
    def set_total(self, total):
        """Imposta il numero totale di file (se non noto alla creazione)."""
        self.total = max(total, 1)
        self._refresh_bar()

    def step(self, filename):
        """Chiamare dopo l'estrazione di ogni file."""
        self.done += 1
        self.lbl_file.config(text=f"📦 {filename}")
        self._refresh_bar()

    def close(self):
        self.grab_release()
        self.destroy()

    # --- Interno ---
    def _cancel(self):
        self.cancelled = True
        self.lbl_file.config(text="⏹ Annullamento… attesa fine estrazione")

    def _refresh_bar(self):
        pct = min(int(self.done / self.total * 100), 100) if self.total else 0
        self.bar["value"] = pct
        elapsed = time.time() - self.start_time
        count_text = f"{self.done}/{self.total} file  ·  {elapsed:.1f}s  ·  {pct}%"
        self.lbl_count.config(text=count_text)
        # L'estrazione gira nel main thread: serve pompare gli eventi
        # affinché la finestra si ridisegni ad ogni file
        self.update_idletasks()
        self.update()

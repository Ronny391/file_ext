import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import requests

# =====================================================================
#  CONFIGURA I TUOI LINK QUI
#  Inserisci il "Nome Personalizzato" e il "Link di Download" effettivo
# =====================================================================
LINK_PREDEFINITI = [
    {
        "nome": "finals week",
        "url": "https://ankergames.net/download-file/4c94f43dc5b260b8d907f8b1c5bb002f8770a5040ded5b71",
    },
    {"nome": "Manuale_Utente.pdf", "url": "https://example.com"},
    {"nome": "Immagine_Logo.png", "url": "https://example.com"},
    {"nome": "Archivio_Dati.zip", "url": "https://example.com"},
]


def download_selezionati():
    # Raccoglie solo gli elementi che hanno la spunta selezionata
    selezionati = []
    for item, var in zip(LINK_PREDEFINITI, variabili_checkbox):
        if var.get() == 1:
            selezionati.append(item)

    if not selezionati:
        messagebox.showwarning("Attenzione", "Seleziona almeno un file da scaricare!")
        return

    # Chiede dove salvare i file
    download_dir = filedialog.askdirectory(
        title="Seleziona la cartella di destinazione"
    )
    if not download_dir:
        return

    # Disabilita la UI durante il processo
    btn_download.config(state=tk.DISABLED)
    lbl_status.config(text="Download in corso...", fg="blue")

    # Avvia il download in background
    threading.Thread(
        target=worker, args=(selezionati, download_dir), daemon=True
    ).start()


def worker(lista_download, download_dir):
    success_count = 0

    for index, item in enumerate(lista_download, 1):
        nome_file = item["nome"]
        url = item["url"]

        filepath = os.path.join(download_dir, nome_file)

        # Aggiorna lo stato nella UI
        lbl_status.config(
            text=f"Scaricamento {index}/{len(lista_download)}: {nome_file}..."
        )

        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            success_count += 1
        except Exception as e:
            print(f"Errore con {nome_file}: {e}")

    # Ripristina la UI alla fine
    root.after(
        0, lambda: finish_download(success_count, len(lista_download), download_dir)
    )


def finish_download(success, total, directory):
    btn_download.config(state=tk.NORMAL)
    lbl_status.config(text=f"Completato! Scaricati {success}/{total} file.", fg="green")
    messagebox.showinfo(
        "Fine Processo", f"Download terminati!\n{success} file salvati in:\n{directory}"
    )


# --- Interfaccia Grafica ---
root = tk.Tk()
root.title("Downloader Selettivo")
root.geometry("550x450")

# Contenitore principale per la lista con scrollbar
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

lbl_instruction = tk.Label(
    main_frame,
    text="Seleziona i file che desideri scaricare:",
    font=("Arial", 11, "bold"),
)
lbl_instruction.pack(anchor="w", pady=(0, 5))

# Creazione di un'area scorrevole per ospitare molti link
canvas = tk.Canvas(main_frame, borderwidth=0, highlightthickness=0)
scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Generazione dinamica delle Checkbox basata sulla lista LINK_PREDEFINITI
variabili_checkbox = []
for item in LINK_PREDEFINITI:
    var = tk.IntVar()
    # Mostra il nome pulito. Passando sopra con il mouse potresti vedere l'URL, ma qui mostriamo solo il nome per pulizia
    cb = tk.Checkbutton(
        scrollable_frame,
        text=item["nome"],
        variable=var,
        font=("Arial", 10),
        anchor="w",
        justify="left",
    )
    cb.pack(fill="x", anchor="w", pady=4)
    variabili_checkbox.append(var)

# Area di stato inferiore
status_frame = tk.Frame(root)
status_frame.pack(fill="x", padx=15, pady=10)

lbl_status = tk.Label(
    status_frame, text="Pronto", font=("Arial", 10, "italic"), fg="gray"
)
lbl_status.pack(pady=5)

btn_download = tk.Button(
    status_frame,
    text="Scarica Elementi Selezionati",
    command=download_selezionati,
    bg="#007BFF",
    fg="white",
    font=("Arial", 11, "bold"),
    padx=15,
    pady=8,
)
btn_download.pack()

root.mainloop()

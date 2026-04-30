"""
py2apk masaüstü arayüzü.
auto-py-to-exe'den ilham alan, tkinter tabanlı GUI.
Build motoru ile tam entegre.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading


def launch_gui():
    """Ana GUI penceresini başlat."""
    root = tk.Tk()
    root.title("auto-py-to-apk (py2apk) v0.1.0")
    root.geometry("750x650")
    root.resizable(True, True)

    try:
        root.iconbitmap(default="")
    except:
        pass

    style = ttk.Style()
    style.theme_use("clam")

    BG_COLOR = "#f0f0f0"
    ACCENT_COLOR = "#4A90D9"
    LOG_BG = "#1e1e1e"
    LOG_FG = "#d4d4d4"

    root.configure(bg=BG_COLOR)

    # === Üst Bilgi ===
    header_frame = tk.Frame(root, bg=ACCENT_COLOR, height=80)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)

    tk.Label(header_frame, text="🐍 auto-py-to-apk", font=("Arial", 20, "bold"),
             fg="white", bg=ACCENT_COLOR).pack(pady=(15, 0))

    tk.Label(header_frame, text="Python → APK", font=("Arial", 9),
             fg="white", bg=ACCENT_COLOR).pack()

    # === Ana İçerik ===
    content_frame = tk.Frame(root, bg=BG_COLOR)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # --- Ayarlar Bölümü ---
    settings_frame = tk.LabelFrame(content_frame, text="⚙️ Uygulama Ayarları",
                                   font=("Arial", 11, "bold"), bg=BG_COLOR,
                                   fg="#333", padx=15, pady=15)
    settings_frame.pack(fill=tk.X, pady=(0, 15))
    settings_frame.columnconfigure(1, weight=1)

    def add_row(parent, row, label_text, widget):
        tk.Label(parent, text=label_text, bg=BG_COLOR, font=("Arial", 10)).grid(row=row, column=0, sticky="w", pady=5)
        widget.grid(row=row, column=1, sticky="ew", pady=5, padx=(15, 0))

    def browse_file(entry_widget, title, filetypes):
        filename = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def make_file_row(parent, row, label, entry, title, filetypes):
        tk.Label(parent, text=label, bg=BG_COLOR, font=("Arial", 10)).grid(row=row, column=0, sticky="w", pady=5)
        frm = tk.Frame(parent, bg=BG_COLOR)
        frm.grid(row=row, column=1, sticky="ew", pady=5, padx=(15, 0))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(frm, text="📁", font=("Arial", 10), width=4, relief="solid",
                  command=lambda: browse_file(entry, title, filetypes)).pack(side=tk.RIGHT, padx=(5, 0))

    row = 0
    app_name_entry = tk.Entry(settings_frame, font=("Arial", 10), relief="solid", borderwidth=1)
    app_name_entry.insert(0, "BenimUygulamam")
    add_row(settings_frame, row, "Uygulama Adı:", app_name_entry); row += 1

    domain_entry = tk.Entry(settings_frame, font=("Arial", 10), relief="solid", borderwidth=1)
    domain_entry.insert(0, "com.example.benimuygulamam")
    add_row(settings_frame, row, "Ters Domain:", domain_entry); row += 1

    py_file_entry = tk.Entry(settings_frame, font=("Arial", 10), relief="solid", borderwidth=1)
    make_file_row(settings_frame, row, "Python Dosyası:", py_file_entry, "Python dosyası seç",
                  [("Python files", "*.py"), ("All files", "*.*")]); row += 1

    icon_entry = tk.Entry(settings_frame, font=("Arial", 10), relief="solid", borderwidth=1)
    make_file_row(settings_frame, row, "Simge (.png):", icon_entry, "Simge dosyası seç",
                  [("PNG files", "*.png"), ("All files", "*.*")]); row += 1

    req_entry = tk.Entry(settings_frame, font=("Arial", 10), relief="solid", borderwidth=1)
    make_file_row(settings_frame, row, "requirements.txt:", req_entry, "requirements.txt seç",
                  [("Text files", "*.txt"), ("All files", "*.*")]); row += 1

    # İzinler
    tk.Label(settings_frame, text="İzinler:", bg=BG_COLOR, font=("Arial", 10)).grid(row=row, column=0, sticky="w", pady=5)
    perm_frame = tk.Frame(settings_frame, bg=BG_COLOR)
    perm_frame.grid(row=row, column=1, sticky="w", pady=5, padx=(15, 0))
    internet_var = tk.BooleanVar(value=True)
    storage_var = tk.BooleanVar(value=False)
    camera_var = tk.BooleanVar(value=False)
    tk.Checkbutton(perm_frame, text="İnternet", variable=internet_var, bg=BG_COLOR, font=("Arial", 9)).pack(side=tk.LEFT)
    tk.Checkbutton(perm_frame, text="Depolama", variable=storage_var, bg=BG_COLOR, font=("Arial", 9)).pack(side=tk.LEFT, padx=8)
    tk.Checkbutton(perm_frame, text="Kamera", variable=camera_var, bg=BG_COLOR, font=("Arial", 9)).pack(side=tk.LEFT)

    # --- Build Butonu ---
    build_btn_frame = tk.Frame(content_frame, bg=BG_COLOR)
    build_btn_frame.pack(fill=tk.X, pady=(0, 15))

    build_btn = tk.Button(
        build_btn_frame, text="🔨 BUILD (APK Oluştur)", font=("Arial", 14, "bold"),
        bg="#28a745", fg="white", activebackground="#218838", activeforeground="white",
        relief="flat", padx=30, pady=10, cursor="hand2"
    )
    build_btn.pack()

    # --- İlerleme Çubuğu ---
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(content_frame, variable=progress_var, maximum=100, mode="determinate")
    progress_bar.pack(fill=tk.X, pady=(0, 5))

    status_label = tk.Label(content_frame, text="Hazır", bg=BG_COLOR, font=("Arial", 9, "italic"), fg="#666")
    status_label.pack(anchor="w")

    # --- Log Konsolu ---
    tk.Label(content_frame, text="📋 Build Logları:", bg=BG_COLOR, font=("Arial", 10, "bold"), fg="#333").pack(anchor="w", pady=(10, 5))

    log_frame = tk.Frame(content_frame, bg="#1e1e1e", relief="solid", borderwidth=1)
    log_frame.pack(fill=tk.BOTH, expand=True)

    log_text = tk.Text(log_frame, wrap=tk.WORD, bg=LOG_BG, fg=LOG_FG,
                       insertbackground="white", font=("Consolas", 9), relief="flat", borderwidth=0)
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=log_scrollbar.set)

    log_text.tag_config("success", foreground="#4ec86e")
    log_text.tag_config("error", foreground="#e0555a")
    log_text.tag_config("warning", foreground="#e0b653")
    log_text.tag_config("info", foreground="#6cb2eb")
    log_text.tag_config("header", foreground="#ffffff", font=("Consolas", 9, "bold"))

    # === Mantıksal Katman ===
    def log(message, tag=None):
        log_text.insert(tk.END, message + "\n", tag)
        log_text.see(tk.END)
        root.update_idletasks()

    def update_progress(value, text=""):
        progress_var.set(value)
        if text:
            status_label.config(text=text)
        root.update_idletasks()

    def enable_ui(enabled=True):
        state = "normal" if enabled else "disabled"
        build_btn.config(state=state)
        app_name_entry.config(state=state)
        domain_entry.config(state=state)
        py_file_entry.config(state=state)
        icon_entry.config(state=state)
        req_entry.config(state=state)

    def start_build():
        app_name = app_name_entry.get().strip()
        domain = domain_entry.get().strip()
        py_file = py_file_entry.get().strip()
        icon_file = icon_entry.get().strip()
        req_file = req_entry.get().strip()

        errors = []
        if not app_name:
            errors.append("Uygulama adı boş olamaz!")
        if not domain:
            errors.append("Domain boş olamaz!")
        if not py_file or not os.path.exists(py_file):
            errors.append("Geçerli bir Python dosyası seçin!")

        if errors:
            for err in errors:
                log(f"❌ {err}", "error")
            messagebox.showerror("Hata", "\n".join(errors))
            return

        permissions = []
        if internet_var.get():
            permissions.append("INTERNET")
        if storage_var.get():
            permissions.append("WRITE_EXTERNAL_STORAGE")
        if camera_var.get():
            permissions.append("CAMERA")

        build_config = {
            "app_name": app_name,
            "domain": domain,
            "py_file": py_file,
            "icon_file": icon_file,
            "req_file": req_file,
            "permissions": permissions,
        }

        enable_ui(False)
        log_text.delete(1.0, tk.END)
        update_progress(0, "Build başlatılıyor...")

        def build_thread():
            try:
                from py2apk.builder import build_apk
                build_apk(config=build_config, log_callback=log, progress_callback=update_progress)
                root.after(0, lambda: messagebox.showinfo("Başarılı",
                                                          f"✅ APK oluşturuldu!\n\nKonum: Masaüstü/{app_name}.apk"))
            except Exception as e:
                log(f"❌ Build başarısız: {e}", "error")
                root.after(0, lambda: messagebox.showerror("Hata", f"Build başarısız oldu:\n\n{e}"))
            finally:
                root.after(0, lambda: enable_ui(True))
                root.after(0, lambda: update_progress(0, "Hazır"))

        threading.Thread(target=build_thread, daemon=True).start()

    build_btn.config(command=start_build)

    # === Başlangıç Logları ===
    log("═" * 60, "header")
    log("  🚀 py2apk v0.1.0 hazır.", "success")
    log("  📱 Python kodunu APK'ya dönüştürme aracı", "info")
    log("  💡 Dosyaları seçin ve Build butonuna basın.", "info")
    log("═" * 60, "header")

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
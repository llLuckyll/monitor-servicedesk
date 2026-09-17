import datetime
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import winsound

from PIL import ImageGrab
import pytesseract
from screeninfo import get_monitors

APP_TITLE = "Monitor Service Desk"
DEFAULT_REFRESH_INTERVAL_MINUTES = 25
OCR_INTERVAL_SECONDS = 2

TESSERACT_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)

for tesseract_path in TESSERACT_PATHS:
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        break


class MultiMonitorSnipTool:
    """Allows selecting a rectangular screen region across multiple monitors."""

    def __init__(self, master, on_selected_callback):
        self.master = master
        self.callback = on_selected_callback

        try:
            monitors = get_monitors()
            self.min_x = min(m.x for m in monitors)
            self.min_y = min(m.y for m in monitors)
            self.max_x = max(m.x + m.width for m in monitors)
            self.max_y = max(m.y + m.height for m in monitors)
        except Exception:
            self.min_x = 0
            self.min_y = 0
            self.max_x = master.winfo_screenwidth()
            self.max_y = master.winfo_screenheight()

        width = self.max_x - self.min_x
        height = self.max_y - self.min_y

        self.snip_surface = tk.Toplevel(master)
        self.snip_surface.attributes("-alpha", 0.3)
        self.snip_surface.attributes("-topmost", True)
        self.snip_surface.overrideredirect(True)
        self.snip_surface.geometry(f"{width}x{height}+{self.min_x}+{self.min_y}")
        self.snip_surface.config(cursor="cross")

        self.canvas = tk.Canvas(
            self.snip_surface, cursor="cross", bg="grey", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.start_x = None
        self.start_y = None
        self.rect = None

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x + 1, self.start_y + 1,
            outline="red", width=2
        )

    def on_move_press(self, event):
        if self.rect is not None:
            self.canvas.coords(
                self.rect, self.start_x, self.start_y, event.x, event.y
            )

    def on_button_release(self, event):
        if self.start_x is None or self.start_y is None:
            self.snip_surface.destroy()
            return

        end_x, end_y = event.x, event.y

        real_x1 = min(self.start_x, end_x) + self.min_x
        real_y1 = min(self.start_y, end_y) + self.min_y
        real_x2 = max(self.start_x, end_x) + self.min_x
        real_y2 = max(self.start_y, end_y) + self.min_y

        self.snip_surface.destroy()

        if (real_x2 - real_x1) > 5 and (real_y2 - real_y1) > 5:
            self.callback((real_x1, real_y1, real_x2, real_y2))


class ServiceDeskMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("420x480")
        self.root.resizable(False, False)

        self.region = None
        self.current_value = "--"
        self.previous_value = "--"
        self.is_monitoring = False

        self.refresh_interval_seconds = DEFAULT_REFRESH_INTERVAL_MINUTES * 60
        self.seconds_left = self.refresh_interval_seconds
        self.last_refresh_str = "Nenhuma"

        self.ocr_thread = None
        self.timer_thread = None

        self.create_widgets()

    def create_widgets(self):
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=10)

        self.btn_select = tk.Button(
            frame_buttons, text="1. Selecionar número",
            command=self.select_region, width=28
        )
        self.btn_select.pack(pady=3)

        self.btn_test_ocr = tk.Button(
            frame_buttons, text="2. Testar leitura",
            command=self.test_ocr, width=28
        )
        self.btn_test_ocr.pack(pady=3)

        self.btn_test_sound = tk.Button(
            frame_buttons, text="3. Testar som",
            command=self.play_alert, width=28
        )
        self.btn_test_sound.pack(pady=3)

        self.btn_config_refresh = tk.Button(
            frame_buttons, text="4. Configurar ciclo de atualização",
            command=self.config_refresh_dialog, width=28
        )
        self.btn_config_refresh.pack(pady=3)

        self.btn_start = tk.Button(
            frame_buttons, text="5. Iniciar monitoramento",
            command=self.start_monitoring, width=28, bg="#d4edda"
        )
        self.btn_start.pack(pady=3)

        self.btn_stop = tk.Button(
            frame_buttons, text="6. Parar",
            command=self.stop_monitoring, width=28,
            state=tk.DISABLED, bg="#f8d7da"
        )
        self.btn_stop.pack(pady=3)

        ttk.Separator(self.root, orient="horizontal").pack(
            fill="x", padx=15, pady=5
        )

        frame_info = tk.Frame(self.root)
        frame_info.pack(pady=5)

        self.lbl_values = tk.Label(
            frame_info,
            text="Valor Atual: --    |    Valor Anterior: --",
            font=("Arial", 10, "bold")
        )
        self.lbl_values.pack(pady=2)

        self.lbl_status = tk.Label(
            frame_info, text="Status: Parado",
            fg="red", font=("Arial", 10, "bold")
        )
        self.lbl_status.pack(pady=2)

        frame_refresh = tk.LabelFrame(
            self.root, text=" Ciclo de atualização ",
            font=("Arial", 9, "bold")
        )
        frame_refresh.pack(fill="x", padx=15, pady=5)

        self.lbl_refresh_cfg = tk.Label(
            frame_refresh, text="Intervalo: 25 minutos"
        )
        self.lbl_refresh_cfg.pack(anchor="w", padx=10, pady=1)

        self.lbl_next_refresh = tk.Label(
            frame_refresh, text="Próxima atualização em: --:--"
        )
        self.lbl_next_refresh.pack(anchor="w", padx=10, pady=1)

        self.lbl_last_refresh = tk.Label(
            frame_refresh, text="Último ciclo registrado: Nenhuma"
        )
        self.lbl_last_refresh.pack(anchor="w", padx=10, pady=1)

        self.lbl_status_refresh = tk.Label(
            frame_refresh, text="Status do ciclo: OK", fg="green"
        )
        self.lbl_status_refresh.pack(anchor="w", padx=10, pady=1)

    def select_region(self):
        self.root.iconify()
        time.sleep(0.3)
        MultiMonitorSnipTool(self.root, self.on_region_selected)

    def on_region_selected(self, bbox):
        self.region = bbox
        self.root.deiconify()
        messagebox.showinfo(
            "Região Selecionada",
            f"Região definida com sucesso:\n{self.region}"
        )

    def capture_and_read(self):
        """Captures the selected region and returns a numeric OCR result."""
        if not self.region:
            return None

        try:
            image = ImageGrab.grab(bbox=self.region, all_screens=True)
            custom_config = r"--psm 6 -c tessedit_char_whitelist=0123456789"
            text = pytesseract.image_to_string(
                image, config=custom_config
            ).strip()
            return text if text.isdigit() else None
        except Exception:
            return None

    def test_ocr(self):
        if not self.region:
            messagebox.showwarning(
                "Aviso", "Selecione uma região da tela primeiro!"
            )
            return

        value = self.capture_and_read()

        if value is not None:
            messagebox.showinfo(
                "Resultado OCR", f"Número detectado: {value}"
            )
        else:
            messagebox.showwarning(
                "Resultado OCR",
                "Nenhum número válido foi identificado na região selecionada."
            )

    def play_alert(self):
        """Plays an audible alert without blocking the main interface."""

        def sound_thread():
            try:
                winsound.PlaySound(
                    "SystemHand",
                    winsound.SND_ALIAS | winsound.SND_ASYNC
                )
            except Exception:
                pass

            for _ in range(3):
                try:
                    winsound.Beep(440, 350)
                    winsound.Beep(480, 350)
                    time.sleep(0.2)
                except Exception:
                    break

        threading.Thread(target=sound_thread, daemon=True).start()

    def config_refresh_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuração do ciclo")
        dialog.geometry("400x240")
        dialog.resizable(False, False)

        tk.Label(
            dialog, text="Ciclo de atualização (25 min)",
            font=("Arial", 10, "bold")
        ).pack(pady=10)

        info = (
            "O monitoramento não depende de um navegador específico.\n\n"
            "Para atualizar a página do sistema, utilize uma extensão "
            "de atualização automática no navegador escolhido e configure "
            "o intervalo desejado.\n\n"
            "O aplicativo apenas controla e exibe o ciclo de tempo."
        )

        tk.Message(dialog, text=info, width=360).pack(pady=5)

        tk.Button(
            dialog, text="Entendi",
            command=dialog.destroy, width=15
        ).pack(pady=15)

    def start_monitoring(self):
        if not self.region:
            messagebox.showwarning(
                "Aviso",
                "Selecione a região do número antes de iniciar!"
            )
            return

        self.is_monitoring = True

        self.btn_select.config(state=tk.DISABLED)
        self.btn_test_ocr.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.lbl_status.config(
            text="Status: Monitorando", fg="green"
        )

        initial_value = self.capture_and_read()

        if initial_value is not None:
            self.current_value = initial_value
            self.previous_value = initial_value
            self.update_labels()

        self.seconds_left = self.refresh_interval_seconds

        self.ocr_thread = threading.Thread(
            target=self.ocr_loop, daemon=True
        )
        self.ocr_thread.start()

        self.timer_thread = threading.Thread(
            target=self.timer_loop, daemon=True
        )
        self.timer_thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False

        self.btn_select.config(state=tk.NORMAL)
        self.btn_test_ocr.config(state=tk.NORMAL)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

        self.lbl_status.config(
            text="Status: Parado", fg="red"
        )
        self.lbl_next_refresh.config(
            text="Próxima atualização em: --:--"
        )

    def ocr_loop(self):
        while self.is_monitoring:
            time.sleep(OCR_INTERVAL_SECONDS)
            detected = self.capture_and_read()

            if detected is not None and detected != self.current_value:
                self.previous_value = self.current_value
                self.current_value = detected

                self.root.after(0, self.update_labels)
                self.play_alert()

    def timer_loop(self):
        while self.is_monitoring:
            time.sleep(1)
            self.seconds_left -= 1

            minutes, seconds = divmod(self.seconds_left, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

            self.root.after(
                0,
                lambda value=time_str: self.lbl_next_refresh.config(
                    text=f"Próxima atualização em: {value}"
                )
            )

            if self.seconds_left <= 0:
                self.update_refresh_status()
                self.seconds_left = self.refresh_interval_seconds

    def update_refresh_status(self):
        """Registers the end of a refresh cycle.

        The actual browser/page refresh is external to this application,
        keeping the monitor browser-independent.
        """
        self.last_refresh_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.root.after(0, self.update_refresh_ui)

    def update_labels(self):
        self.lbl_values.config(
            text=(
                f"Valor Atual: {self.current_value}"
                f"    |    Valor Anterior: {self.previous_value}"
            )
        )

    def update_refresh_ui(self):
        self.lbl_last_refresh.config(
            text=f"Último ciclo registrado: {self.last_refresh_str}"
        )
        self.lbl_status_refresh.config(
            text="Status do ciclo: OK", fg="green"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceDeskMonitorApp(root)
    root.mainloop()

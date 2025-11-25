from json import dump, load
from os import getenv, makedirs, path, remove
from random import uniform
from threading import Thread
from time import sleep, time

from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Button as MouseButton, Controller as MouseController

from tkinter import Event, TclError

from customtkinter import (
    CTk, CTkButton, CTkCheckBox, CTkEntry, CTkFrame, CTkFont, CTkLabel,
    DoubleVar, BooleanVar, set_appearance_mode, set_default_color_theme
)


class Settings:
    app_title = "AutoClicker"
    app_version = "1.4"
    settings_folder_name = "AutoClicker"
    init_size = "490x180"
    scaled_size = "490x210"

    def __init__(self):
        self.min_delay = 0.1
        self.max_delay = 0.3
        self.start_key = "f8"
        self.quit_key = "f9"
        self.save_settings = False
        self.winfo_x = None
        self.winfo_y = None
        self.load()

    def _get_config_path(self, create_if_not_exists=False) -> str:
        appdata_path = getenv("APPDATA")
        if appdata_path:
            folder = path.join(appdata_path, self.settings_folder_name)
            if create_if_not_exists:
                makedirs(folder, exist_ok=True)
            filepath = path.join(folder, "settings.json")
        else:
            folder = path.dirname(path.abspath(__file__))
            filepath = path.join(folder, "settings.json")
        return filepath

    @staticmethod
    def _parse_float(value: DoubleVar) -> float | None:
        try:
            return value.get()
        except (ValueError, TclError):
            return None

    def save(
        self, min_delay: DoubleVar, max_delay: DoubleVar, start_key: str, quit_key: str,
        save_settings: bool, winfo_x: int, winfo_y: int
    ) -> None:
        settings_file_path = self._get_config_path(create_if_not_exists=True)
        data = {
            "min_delay": self._parse_float(min_delay) or self.min_delay,
            "max_delay": self._parse_float(max_delay) or self.max_delay,
            "start_key": start_key,
            "quit_key": quit_key,
            "save_settings": save_settings,
            "winfo_x": winfo_x,
            "winfo_y": winfo_y
        }
        with open(settings_file_path, "w", encoding="utf-8") as settings_file:
            dump(data, settings_file, indent=2)

    def load(self) -> None:
        settings_file_path = self._get_config_path()
        if not path.exists(settings_file_path):
            return
        with open(settings_file_path, "r", encoding="utf-8") as settings_file:
            data = load(settings_file)
        self.min_delay = data.get("min_delay", self.min_delay)
        self.max_delay = data.get("max_delay", self.max_delay)
        self.start_key = data.get("start_key", self.start_key)
        self.quit_key = data.get("quit_key", self.quit_key)
        self.save_settings = data.get("save_settings", self.save_settings)
        self.winfo_x = data.get("winfo_x", self.winfo_x)
        self.winfo_y = data.get("winfo_y", self.winfo_y)

    def reset_settings(self) -> None:
        settings_file_path = self._get_config_path()
        if not path.exists(settings_file_path):
            return
        remove(settings_file_path)


class AutoClicker:
    def __init__(self, master):
        self.settings = Settings()

        set_appearance_mode("dark")
        set_default_color_theme("dark-blue")

        self.init_size = self.settings.init_size
        self.clicking = False
        self.click_count = 0

        self.master = master
        self.master.title(self.settings.app_title)
        self.master.resizable(False, False)
        self.master.geometry(self.init_size)
        self.master.protocol("WM_DELETE_WINDOW", self.on_quit)

        self.thread = None
        self.timer_start = None
        self.update_timer_running = False

        self.always_on_top_var = BooleanVar(value=True)
        self.master.wm_attributes("-topmost", True)

        self.save_settings_var = BooleanVar(value=self.settings.save_settings)

        self.min_delay_var = DoubleVar(value=self.settings.min_delay)
        self.max_delay_var = DoubleVar(value=self.settings.max_delay)

        self.start_key = self.settings.start_key
        self.quit_key = self.settings.quit_key
        self.listening_for = None
        self.hotkey_prompt = None

        self.master.columnconfigure(0, weight=1, minsize=270)
        self.master.columnconfigure(1, weight=1, minsize=250)
        self.master.rowconfigure(0, weight=1)

        # Left frame (settings)
        left_frame = CTkFrame(master)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5))
        left_frame.columnconfigure(1, weight=1)

        left_frame.columnconfigure(0, weight=0)  # labels
        left_frame.columnconfigure(1, weight=0)  # hotkeys
        left_frame.columnconfigure(2, weight=0)  # buttons

        # Start/Stop hotkey
        self.start_key_label = CTkLabel(left_frame, text="Start/Stop hotkey:")
        self.start_key_label.grid(row=0, column=0, sticky="w")
        self.start_key_display = CTkLabel(
            left_frame, text=self.start_key.upper(), fg_color="green", corner_radius=5,
            font=CTkFont(size=14, weight="bold"),  width=50, height=25, anchor="center"
        )
        self.start_key_display.grid(row=0, column=1, sticky="w", padx=(1, 0))
        self.set_start_key_btn = CTkButton(
            left_frame, text="Set hotkey", command=self.listen_for_start_key, width=100, height=25)
        self.set_start_key_btn.grid(row=0, column=2, sticky="w", pady=2)

        # Quit hotkey
        self.quit_key_label = CTkLabel(left_frame, text="Exit hotkey:")
        self.quit_key_label.grid(row=1, column=0, sticky="w")
        self.quit_key_display = CTkLabel(
            left_frame, text=self.quit_key.upper(), fg_color="green", corner_radius=5,
            font=CTkFont(size=14, weight="bold"),width=50, height=25, anchor="center"
        )
        self.quit_key_display.grid(row=1, column=1, sticky="w", padx=(1, 0))
        self.set_quit_key_btn = CTkButton(
            left_frame, text="Set hotkey", command=self.listen_for_quit_key, width=100, height=25)
        self.set_quit_key_btn.grid(row=1, column=2, sticky="w", pady=2)

        # Delay settings
        CTkLabel(left_frame, text="Min. delay (sec):").grid(row=3, column=0, sticky="w")
        self.min_delay_entry = CTkEntry(left_frame, textvariable=self.min_delay_var, width=60)
        self.min_delay_entry.grid(row=3, column=1, sticky="w", pady=2)

        CTkLabel(left_frame, text="Max. delay (sec):").grid(row=4, column=0, sticky="w")
        self.max_delay_entry = CTkEntry(left_frame, textvariable=self.max_delay_var, width=60)
        self.max_delay_entry.grid(row=4, column=1, sticky="w", pady=2)

        # Always on top checkbox
        self.always_on_top_cb = CTkCheckBox(
            left_frame, text="Always on top", variable=self.always_on_top_var,
            command=self.toggle_always_on_top
        )
        self.always_on_top_cb.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 0))

        # Save settings checkbox
        self.save_settings_cb = CTkCheckBox(
            left_frame, text="Save settings", variable=self.save_settings_var)
        self.save_settings_cb.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 0))

        # Right frame (status/stats)
        right_frame = CTkFrame(master)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        right_frame.columnconfigure(0, weight=1)

        self.status_label = CTkLabel(
            right_frame, text="Status: Stopped", text_color="#b80202",
            font=CTkFont(size=16, weight="bold")
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.click_label = CTkLabel(right_frame, text="Clicks: 0", font=CTkFont(size=14))
        self.click_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.timer_label = CTkLabel(right_frame, text="Time elapsed: 0 sec", font=CTkFont(size=14))
        self.timer_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

        # pynput hotkeys
        self.listener = None

        self.listener_thread = Thread(target=self.listen_hotkeys, daemon=True)
        self.listener_thread.start()

        # Update window position
        self.center_window_or_load_position()

    def center_window_or_load_position(self) -> None:
        self.master.update_idletasks()
        size: list[str] = self.init_size.split("x")
        width: int = int(size[0])
        height: int = int(size[1])
        screen_width: int = self.master.winfo_screenwidth()
        screen_height: int = self.master.winfo_screenheight()

        if self.settings.winfo_x and self.settings.winfo_y:
            self.settings.winfo_x = 0 if self.settings.winfo_x < 0 else self.settings.winfo_x
            self.settings.winfo_y = 0 if self.settings.winfo_y < 0 else self.settings.winfo_y
            if self.settings.winfo_y + height > screen_height:
                self.settings.winfo_y = screen_height - height - 40
            x: int = self.settings.winfo_x
            y: int = self.settings.winfo_y
        else:
            x: int = (screen_width // 2) - (width // 2)
            y: int = (screen_height // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def listen_hotkeys(self) -> None:
        pressed_keys = set()

        def on_press(key):
            try:
                if hasattr(key, "char") and key.char:
                    key_name = key.char.lower()
                else:
                    key_name = str(key).split(".")[-1]
            except Exception:
                key_name = str(key).split(".")[-1]

            if key_name in pressed_keys:
                return
            pressed_keys.add(key_name)

            if not self.listening_for:
                if key_name == self.start_key:
                    self.master.after(0, self.toggle_clicking)
                elif key_name == self.quit_key:
                    self.master.after(0, self.on_quit)

        def on_release(key):
            try:
                if hasattr(key, "char") and key.char:
                    key_name = key.char.lower()
                else:
                    key_name = str(key).split(".")[-1]
            except Exception:
                key_name = str(key).split(".")[-1]
            if key_name in pressed_keys:
                pressed_keys.remove(key_name)

        with KeyboardListener(on_press=on_press, on_release=on_release) as listener:
            self.listener = listener
            listener.join()

    def show_key_prompt(self, text: str) -> None:
        frame = self.set_start_key_btn.master
        if self.hotkey_prompt is None:
            self.hotkey_prompt = CTkLabel(frame, text=text, text_color="#ffaa00")
        self.hotkey_prompt.grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 5))
        self.hotkey_prompt.update()
        self.master.geometry(self.settings.scaled_size)

    def hide_key_prompt(self) -> None:
        if self.hotkey_prompt is not None:
            self.hotkey_prompt.grid_remove()
        self.master.geometry(self.init_size)

    def listen_for_start_key(self) -> None:
        if not self.clicking and self.listening_for is None:
            self.listening_for = "start"
            self.show_key_prompt("Press any key to set Start hotkey...")
            self.master.bind_all("<Key>", self.on_key_press)

    def listen_for_quit_key(self) -> None:
        if not self.clicking and self.listening_for is None:
            self.listening_for = "quit"
            self.show_key_prompt("Press any key to set Exit hotkey...")
            self.master.bind_all("<Key>", self.on_key_press)

    def on_key_press(self, event: Event) -> None:
        key = event.keysym.lower()
        if self.listening_for == "start":
            if key == self.quit_key:
                return

            self.master.unbind_all("<Key>")
            self.start_key = key
            self.start_key_display.configure(text=self.start_key.upper())
        elif self.listening_for == "quit":
            if key == self.start_key:
                return

            self.master.unbind_all("<Key>")
            self.quit_key = key
            self.quit_key_display.configure(text=self.quit_key.upper())

        self.hide_key_prompt()
        self.listening_for = None

    def toggle_always_on_top(self) -> None:
        self.master.wm_attributes("-topmost", self.always_on_top_var.get())

    def get_delay(self) -> float:
        try:
            min_delay = self.min_delay_var.get()
            max_delay = self.max_delay_var.get()
            if min_delay > max_delay:
                self.min_delay_var.set(max_delay)
                self.max_delay_var.set(min_delay)
            return round(uniform(self.min_delay_var.get(), self.max_delay_var.get()), 4)
        except Exception:
            self.min_delay_var.set(self.settings.min_delay)
            self.max_delay_var.set(self.settings.max_delay)
            return round(uniform(self.settings.min_delay, self.settings.max_delay), 4)

    def reset_entry_focus(self) -> None:
        self.status_label.focus_set()

    def toggle_clicking(self) -> None:
        self.clicking = not self.clicking
        if self.clicking:
            self.start_timer()
            self.status_label.configure(text="Status: Clicking", text_color="green")
            self.click_count = 0
            self.thread = Thread(target=self.click_loop, daemon=True)
            self.thread.start()
        else:
            self.stop_timer()
            self.status_label.configure(text="Status: Stopped", text_color="#b80202")
            self.thread.join()
        self.reset_entry_focus()

    def click_loop(self) -> None:
        mouse_controller = MouseController()
        while self.clicking:
            mouse_controller.click(MouseButton.left)
            self.click_count += 1
            self.master.after(
                0, lambda: self.click_label.configure(text=f"Clicks: {self.click_count}"))
            sleep(self.get_delay())

    def start_timer(self) -> None:
        self.timer_start = time()
        self.update_timer_running = True
        self.update_timer()

    def stop_timer(self) -> None:
        self.update_timer_running = False
        self.master.after(0, self.timer_label.configure, {"text": "Time elapsed: 0 sec"})

    def update_timer(self) -> None:
        if self.update_timer_running:
            elapsed = int(time() - self.timer_start)
            self.timer_label.configure(text=f"Time elapsed: {elapsed} sec")
            self.master.after(1000, self.update_timer)

    def on_quit(self) -> None:
        if self.save_settings_var.get():
            self.settings.save(
                self.min_delay_var, self.max_delay_var, self.start_key, self.quit_key,
                self.save_settings_var.get(), self.master.winfo_x(), self.master.winfo_y()
            )
        else:
            self.settings.reset_settings()
        self.clicking = False
        if self.listener is not None:
            self.listener.stop()
        self.master.quit()


if __name__ == "__main__":
    root = CTk()
    app = AutoClicker(root)
    root.mainloop()

# pyinstaller --onefile --windowed --clean --strip --exclude-module=altgraph --exclude-module=keyboard --exclude-module=pefile --exclude-module=pillow --exclude-module=pip --exclude-module=pyinstaller --exclude-module=pyinstaller-hooks-contrib --exclude-module=pymsgbox --exclude-module=pyperclip --exclude-module=pyrect --exclude-module=pyscreeze --exclude-module=pytweening --exclude-module=pywin32-ctypes --exclude-module=setuptools --upx-dir=D:\soft\upx .\autoclicker.py

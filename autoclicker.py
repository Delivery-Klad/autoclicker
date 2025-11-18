from random import uniform
from threading import Thread
from time import sleep, time
from tkinter import Button, Entry, Frame, Label, Tk, BooleanVar, Checkbutton, Event, END
from pyautogui import click
from keyboard import add_hotkey, remove_hotkey, wait


class AutoClicker:
    def __init__(self, master):
        self.init_size = "490x150"
        self.init_min_delay = 0.01
        self.init_max_delay = 0.03
        self.clicking = False
        self.click_count = 0

        self.master = master
        self.master.title("Autoclicker")
        self.master.resizable(False, False)
        self.master.geometry(self.init_size)
        self.master.protocol("WM_DELETE_WINDOW", self.quit)

        self.thread = None
        self.timer_start = None
        self.update_timer_running = False

        # Always on top настройка с дефолтом True
        self.always_on_top_var = BooleanVar(value=True)
        self.master.wm_attributes("-topmost", True)

        # default hotkeys
        self.start_key = "f8"
        self.quit_key = "f9"
        self.listening_for = None  # None, "start", "quit"

        # dark theme
        self.bg_color = "#222222"
        self.fg_color = "#eeeeee"
        self.btn_bg = "#444444"
        self.btn_fg = "#ffffff"
        self.master.config(bg=self.bg_color)

        self.master.columnconfigure(0, weight=1, minsize=270)
        self.master.columnconfigure(1, weight=1, minsize=250)
        self.master.rowconfigure(0, weight=1)

        # left frame (settings)
        left_frame = Frame(master, bg=self.bg_color)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.columnconfigure(1, weight=1)

        # hotkeys
        self.hotkey_prompt = None

        self.start_key_label = Label(
            left_frame, text=f"Start/Stop hotkey: {self.start_key.upper()}", bg=self.bg_color,
            fg=self.fg_color
        )
        self.start_key_label.grid(row=0, column=0, sticky="w")
        self.set_start_key_btn = Button(
            left_frame, text="Set hotkey", command=self.listen_for_start_key, width=10, height=1,
            bg=self.btn_bg, fg=self.btn_fg
        )
        self.set_start_key_btn.grid(row=0, column=1, sticky="w", pady=2)

        self.quit_key_label = Label(left_frame, text=f"Exit hotkey: {self.quit_key.upper()}",
                                    bg=self.bg_color, fg=self.fg_color)
        self.quit_key_label.grid(row=1, column=0, sticky="w")
        self.set_quit_key_btn = Button(
            left_frame, text="Set hotkey", command=self.listen_for_quit_key, width=10, height=1,
            bg=self.btn_bg, fg=self.btn_fg
        )
        self.set_quit_key_btn.grid(row=1, column=1, sticky="w", pady=2)

        # delay
        Label(
            left_frame, text="Min. delay (sec):", bg=self.bg_color, fg=self.fg_color
        ).grid(row=3, column=0, sticky="w")
        self.min_delay_entry = Entry(left_frame, width=5)
        self.min_delay_entry.insert(0, str(self.init_min_delay))
        self.min_delay_entry.grid(row=3, column=1, sticky="w", pady=2)

        Label(
            left_frame, text="Max. delay (sec):", bg=self.bg_color, fg=self.fg_color
        ).grid(row=4, column=0, sticky="w")
        self.max_delay_entry = Entry(left_frame, width=5)
        self.max_delay_entry.insert(0, str(self.init_max_delay))
        self.max_delay_entry.grid(row=4, column=1, sticky="w", pady=2)

        # always on top checkbox
        Checkbutton(
            left_frame, text="Always on top", variable=self.always_on_top_var,
            command=self.toggle_always_on_top, bg=self.bg_color, fg=self.fg_color,
            activebackground=self.bg_color, activeforeground=self.fg_color,
            selectcolor=self.bg_color
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # right frame (status/stats)
        right_frame = Frame(master, bg=self.bg_color)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_frame.columnconfigure(0, weight=1)

        self.status_label = Label(
            right_frame, text="Status: Stopped", fg="red", font=("Arial", 14, "bold"),
            bg=self.bg_color
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.click_label = Label(
            right_frame, text="Clicks: 0", font=("Arial", 12), bg=self.bg_color, fg=self.fg_color)
        self.click_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.timer_label = Label(
            right_frame, text="Time elapsed: 0 sec", font=("Arial", 12), bg=self.bg_color,
            fg=self.fg_color
        )
        self.timer_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

        self.hotkeys = []
        self.apply_settings()

        self.hotkey_thread = Thread(target=self.listen_hotkeys, daemon=True)
        self.hotkey_thread.start()

    @classmethod
    def listen_hotkeys(cls) -> None:
        wait()

    def show_key_prompt(self, text: str) -> None:
        frame = self.set_start_key_btn.master
        if self.hotkey_prompt is None:
            self.hotkey_prompt = Label(frame, text=text, fg="#ffaa00", bg=self.bg_color)
        self.hotkey_prompt.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 5))
        self.hotkey_prompt.update()
        self.master.geometry("490x180")

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
        self.master.unbind_all("<Key>")

        if self.listening_for == "start":
            self.start_key = key
            self.start_key_label.config(text=f"Start/Stop hotkey: {self.start_key.upper()}")
        elif self.listening_for == "quit":
            self.quit_key = key
            self.quit_key_label.config(text=f"Exit hotkey: {self.quit_key.upper()}")

        self.hide_key_prompt()
        self.listening_for = None
        self.apply_settings()

    def toggle_always_on_top(self) -> None:
        self.master.wm_attributes("-topmost", self.always_on_top_var.get())

    def get_delay(self) -> float:
        try:
            min_delay = float(self.min_delay_entry.get())
            max_delay = float(self.max_delay_entry.get())
            if min_delay > max_delay:
                min_delay, max_delay = max_delay, min_delay
            return uniform(min_delay, max_delay)
        except ValueError:
            self.min_delay_entry.delete(0, END)
            self.min_delay_entry.insert(0, str(self.init_min_delay))
            self.max_delay_entry.delete(0, END)
            self.max_delay_entry.insert(0, str(self.init_max_delay))
            return uniform(self.init_min_delay, self.init_max_delay)

    def toggle_clicking(self) -> None:
        self.clicking = not self.clicking
        if self.clicking:
            self.start_timer()
            self.status_label.config(text="Status: Clicking", fg="green")
            self.click_count = 0
            self.thread = Thread(target=self.click_loop, daemon=True)
            self.thread.start()
        else:
            self.stop_timer()
            self.status_label.config(text="Status: Stopped", fg="red")
        self.reset_entry_focus()

    def click_loop(self) -> None:
        while self.clicking:
            click()
            self.click_count += 1
            self.master.after(0, self.click_label.config, {"text": f"Clicks: {self.click_count}"})
            sleep(self.get_delay())

    def start_timer(self) -> None:
        self.timer_start = time()
        self.update_timer_running = True
        self.update_timer()

    def stop_timer(self) -> None:
        self.update_timer_running = False
        self.master.after(0, self.timer_label.config, {"text": "Time elapsed: 0 sec"})

    def update_timer(self) -> None:
        if self.update_timer_running:
            elapsed = int(time() - self.timer_start)
            self.timer_label.config(text=f"Time elapsed: {elapsed} sec")
            self.master.after(1000, self.update_timer)

    def apply_settings(self) -> None:
        # reset hotkeys
        for hotkey in self.hotkeys:
            remove_hotkey(hotkey)
        self.hotkeys.clear()

        # add new hotkeys
        if self.start_key:
            self.hotkeys.append(add_hotkey(self.start_key, self.toggle_clicking))
        if self.quit_key:
            self.hotkeys.append(add_hotkey(self.quit_key, self.quit))

        self.master.focus_set()

    def reset_entry_focus(self) -> None:
        self.status_label.focus_set()

    def quit(self) -> None:
        self.clicking = False
        self.master.quit()


if __name__ == "__main__":
    root = Tk()
    app = AutoClicker(root)
    root.mainloop()

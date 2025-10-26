from random import uniform
from threading import Thread
from time import sleep, time
from tkinter import Button, END, Entry, Frame, Label, Tk
from pyautogui import click
from keyboard import add_hotkey, remove_hotkey, wait


class Clicker:
    def __init__(self, master):
        self.thread = None
        self.timer_start = None
        self.update_timer_running = False

        self.clicking = False
        self.click_count = 0
        self.min_delay = 0.01
        self.max_delay = 0.03

        self.master = master
        self.master.title("Autoclicker")
        self.master.geometry("490x160")
        self.master.protocol("WM_DELETE_WINDOW", self.quit)

        self.master.columnconfigure(0, weight=1, minsize=270)
        self.master.columnconfigure(1, weight=1, minsize=250)
        self.master.rowconfigure(0, weight=1)

        # left frame (settings)
        left_frame = Frame(master)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.columnconfigure(1, weight=1)

        Label(left_frame, text="Start/Stop button:").grid(row=0, column=0, sticky="w")
        self.start_key_entry = Entry(left_frame, width=3)
        self.start_key_entry.insert(0, "z")
        self.start_key_entry.grid(row=0, column=1, sticky="w", pady=2)
        self.start_key_entry.bind(
            "<KeyRelease>", lambda e: self.limit_entry_length(self.start_key_entry))

        Label(left_frame, text="Exit button:").grid(row=1, column=0, sticky="w")
        self.quit_key_entry = Entry(left_frame, width=3)
        self.quit_key_entry.insert(0, "x")
        self.quit_key_entry.grid(row=1, column=1, sticky="w", pady=2)
        self.quit_key_entry.bind(
            "<KeyRelease>", lambda e: self.limit_entry_length(self.quit_key_entry))

        Label(left_frame, text="Min. delay (sec):").grid(row=2, column=0, sticky="w")
        self.min_delay_entry = Entry(left_frame, width=5)
        self.min_delay_entry.insert(0, str(self.min_delay))
        self.min_delay_entry.grid(row=2, column=1, sticky="w", pady=2)

        Label(left_frame, text="Max. delay (sec):").grid(row=3, column=0, sticky="w")
        self.max_delay_entry = Entry(left_frame, width=5)
        self.max_delay_entry.insert(0, str(self.max_delay))
        self.max_delay_entry.grid(row=3, column=1, sticky="w", pady=2)

        Button(
            left_frame, text="Apply settings", command=self.apply_settings
        ).grid(row=4, column=0, columnspan=2, pady=15, sticky="ew")

        # right frame (status/stats)
        right_frame = Frame(master)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_frame.columnconfigure(0, weight=1)

        self.status_label = Label(
            right_frame, text="Status: Stopped", fg="red", font=("Arial", 14, "bold"))
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.click_label = Label(right_frame, text="Clicks: 0", font=("Arial", 12))
        self.click_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        self.timer_label = Label(right_frame, text="Time elapsed: 0 sec", font=("Arial", 12))
        self.timer_label.grid(row=2, column=0, sticky="w", pady=(5, 0))

        self.hotkeys = []
        self.apply_settings()

        self.hotkey_thread = Thread(target=self.listen_hotkeys, daemon=True)
        self.hotkey_thread.start()

    @staticmethod
    def limit_entry_length(entry_widget: Entry):
        value = entry_widget.get()
        if len(value) > 1:
            entry_widget.delete(1, END)

    @staticmethod
    def listen_hotkeys():
        wait()

    def get_delay(self):
        try:
            min_delay = float(self.min_delay_entry.get())
            max_delay = float(self.max_delay_entry.get())
            if min_delay > max_delay:
                min_delay, max_delay = max_delay, min_delay
            return uniform(min_delay, max_delay)
        except ValueError:
            return uniform(self.min_delay, self.max_delay)

    def toggle_clicking(self):
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

    def click_loop(self):
        while self.clicking:
            click()
            self.click_count += 1
            self.master.after(0, self.click_label.config, {"text": f"Clicks: {self.click_count}"})
            sleep(self.get_delay())

    def start_timer(self):
        self.timer_start = time()
        self.update_timer_running = True
        self.update_timer()

    def stop_timer(self):
        self.update_timer_running = False
        self.master.after(0, self.timer_label.config, {"text": "Time elapsed: 0 sec"})

    def update_timer(self):
        if self.update_timer_running:
            elapsed = int(time() - self.timer_start)
            self.timer_label.config(text=f"Time elapsed: {elapsed} sec")
            self.master.after(1000, self.update_timer)

    def apply_settings(self):
        for hotkey in self.hotkeys:
            remove_hotkey(hotkey)
        self.hotkeys.clear()

        start_key = self.start_key_entry.get().strip()
        quit_key = self.quit_key_entry.get().strip()

        if start_key:
            self.hotkeys.append(add_hotkey(start_key, self.toggle_clicking))
        if quit_key:
            self.hotkeys.append(add_hotkey(quit_key, self.quit))

        self.master.focus_set()

    def quit(self):
        self.clicking = False
        self.master.quit()


if __name__ == "__main__":
    root = Tk()
    app = Clicker(root)
    root.mainloop()

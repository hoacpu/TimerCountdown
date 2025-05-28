import tkinter as tk
from tkinter import messagebox
import time
import threading
from datetime import datetime, timedelta
import pygame
import os
from tkinter import ttk
from tkinter import filedialog
from tkinter import colorchooser
import json


# ---- TIMER CLASS ----
class CountdownTimer:
    def __init__(self, root, seconds, loop, update_ui_callback, app):

        self.root = root
        self.seconds_init = seconds
        self.seconds_left = seconds
        self.loop = loop
        self.running = True
        self.update_ui_callback = update_ui_callback
        self.app = app
        self.update_timer()

    def update_timer(self):
        if not self.running:
            return

        if self.app.cancel_schedule_flag.get():
            self.app.timer_label.config(text="00:00")
            self.timer_running.set(False)
            return

        if self.seconds_left > 0:
            if self.app.cancel_schedule_flag.get() == "True":
                print("Scheduled timer was cancelled.  inside the update timer function")
                return
            mins, secs = divmod(self.seconds_left, 60)
            self.app.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.seconds_left -= 1
            self.root.after(1000, self.update_timer)
            if self.seconds_left < 10:
                threading.Thread(target=self.app.play_sound).start()
        else:  # time up
            self.app.timer_label.config(text="00:00")
            threading.Thread(target=self.app.play_sound).start()
            if self.loop and self.running:
                self.seconds_left = self.seconds_init
                self.update_timer()
            elif self.running:
                messagebox.showinfo("Timer", "⏰ Time is up!")
                self.update_ui_callback()

    def stop(self):
        self.running = False
        self.app.timer_label.config(text="Timer Stopped")
        self.update_ui_callback()


class App:
    def __init__(self, master):
        self.timer_window = master
        self.timer_window.title("Menubar Toggle Example")
        self.SOUND_FOLDER = os.getcwd() + "\\audio"
        self.SUPPORTED_EXTENSIONS = (".wav", ".mp3")
        self.timer_job_id = None
        self.schedule_thread = None
        self.countdown_time = 60
        self.loop_flag = "false"
        self.menu_visible = True
        self.CONFIG_FILE = "timer_config.json"
        self.sync_mode = None
        self.title_bar_hidden = False
        self.win_x = 0
        self.win_y = 0
        self.guiSetup()

    def init_mixer(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self, data):
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print("Failed to save config:", e)

    def change_font_color(self):
        # Open color chooser dialog
        color = colorchooser.askcolor(title="Choose Font Color")
        if color[1]:  # color[1] is the hex code
            self.timer_label.config(fg=color[1])  # Set foreground color

        self.config = self.load_config()
        self.config["font_color"] = color[1]
        self.save_config(self.config)

    def change_bg_color(self):
        # Open color chooser
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[1]:
            self.timer_window.configure(bg=color[1])
            self.timer_label.configure(bg=color[1])  # Keep label background in sync

        self.config = self.load_config()
        self.config["background_color"] = color[1]
        self.save_config(self.config)

    def toggle_title_bar(self):
        self.title_bar_hidden = not self.title_bar_hidden
        self.timer_window.overrideredirect(self.title_bar_hidden)

        # To apply changes on most platforms, re-positioning the window helps
        if self.title_bar_hidden:
            self.timer_window.geometry("+100+100")  # move to avoid flicker
        else:
            self.timer_window.update_idletasks()
            self.timer_window.deiconify()

    # add mouse event handlers
    def start_move(self, event):
        self.timer_window._drag_start_x = event.x
        self.timer_window._drag_start_y = event.y

    def do_move(self, event):
        x = self.timer_window.winfo_pointerx() - self.timer_window._drag_start_x
        y = self.timer_window.winfo_pointery() - self.timer_window._drag_start_y
        self.timer_window.geometry(f"+{x}+{y}")

    def toggle_menu(self, event=None):

        if self.menu_visible:
            self.timer_window.config(menu="")
            self.menu_visible = False
        else:
            self.timer_window.config(menu=self.menu_bar)
            self.menu_visible = True

        self.toggle_title_bar()

    # ---- SOUND FUNCTION ----
    def play_sound(self):
        if not self.selected_sound_file.get():
            return

        try:
            self.init_mixer()
            selected_file = self.selected_sound_file.get()
            if selected_file:
                sound_path = os.path.join(self.SOUND_FOLDER, selected_file)
                sound = pygame.mixer.Sound(sound_path)
                pygame.mixer.music.set_volume(self.volume_var.get())
                sound.play()
        except Exception as e:
            print(f"Sound error: {e}")

    def get_sound_files(self):
        return [f for f in os.listdir(self.SOUND_FOLDER) if f.lower().endswith(self.SUPPORTED_EXTENSIONS)]

    def toggle_topmost_from_menu(self):
        self.timer_window.attributes("-topmost", self.topmost_var.get())
        self.config = self.load_config()
        self.config["top_most"] = self.topmost_var.get()
        self.save_config(self.config)

    def choose_sound_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Sound File",
            filetypes=[("Audio Files", "*.wav *.mp3")]
        )
        if file_path:
            self.selected_sound_file.set(file_path)

    def set_schedule_time(self):

        def save_time():
            self.sync_mode = "none"
            self.schedule_time_str.set(self.entry.get().strip())

            self.config = self.load_config()
            self.config["schedule_time"] = self.entry.get().strip()
            self.save_config(self.config)

            self.start_timer()
            self.popup.destroy()

        self.popup = tk.Toplevel(self.timer_window)
        self.popup.title("Set Scheduled Start Time")
        self.popup.geometry("250x100")
        tk.Label(self.popup, text="Enter time (HH:MM):", font=("Helvetica", 10)).pack(pady=5)
        self.entry = tk.Entry(self.popup, font=("Helvetica", 12), justify="center")

        self.config = self.load_config()
        self.schedule_time_str.set(self.config.get("schedule_time", "6:30"))
        self.entry.insert(0, self.schedule_time_str.get())
        self.entry.pack()
        tk.Button(self.popup, text="OK", command=save_time).pack(pady=5)

    def open_volume_control(self):
        def set_volume(val):
            volume = float(val) / 100  # Convert 0-100 scale to 0.0-1.0
            self.volume_var.set(volume)
            pygame.mixer.music.set_volume(volume)

        self.popup = tk.Toplevel(self.timer_window)
        self.popup.title("Set Sound Volume")
        self.popup.geometry("300x100")
        tk.Label(self.popup, text="Volume (%)", font=("Helvetica", 10)).pack(pady=5)

        self.scale = tk.Scale(self.popup, from_=0, to=100, orient="horizontal",
                              command=set_volume)
        self.scale.set(int(self.volume_var.get() * 100))
        self.scale.pack()

    def show_popup(self, event):
        self.popup_menu.tk_popup(event.x_root, event.y_root)

    def set_timer_font(self, size_label):
        sizes = {
            "Small": 16,
            "Medium": 24,
            "Large": 32,
            "Extra Large": 48
        }
        new_size = sizes.get(size_label, 24)
        self.timer_label.config(font=("Arial", new_size))
        self.config = self.load_config()
        self.config["font_size_label"] = size_label
        self.save_config(self.config)

    def set_timer_duration(self):
        self.popup = tk.Toplevel(self.timer_window)
        self.popup.title("Set Timer Duration")

        ttk.Label(self.popup, text="Enter duration in seconds:").pack(padx=10, pady=5)
        self.duration_var = tk.StringVar()

        self.entry = ttk.Entry(self.popup, textvariable=self.duration_var)
        self.entry.insert(0, self.countdown_time)
        self.entry.pack(padx=10, pady=5)
        self.entry.focus()

        def apply_duration():
            try:
                new_time = int(self.duration_var.get())
                if new_time > 0:
                    self.countdown_time = new_time
                    self.popup.destroy()

                    # Save to config
                    self.config = self.load_config()
                    self.config["timer_duration"] = new_time
                    self.save_config(self.config)

                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")

        ttk.Button(self.popup, text="OK", command=apply_duration).pack(pady=5)

    def toggle_loop(self):
        # Save to config
        self.config = self.load_config()
        self.config["loop_timer"] = self.loop_var.get()
        self.save_config(self.config)

    # ---- START TIMER ----
    def start_timer(self):
        try:
            seconds = self.countdown_time
            loop = self.loop_var.get()
            # mode = self.sync_mode.get()
            mode = "none"

            self.cancel_schedule_flag.set(False)

            def begin_timer_after_sync_or_schedule():
                # Handle even/odd syncing
                if mode in ("even", "odd"):
                    now = datetime.now()
                    next_minute = now.replace(second=0, microsecond=0)
                    next_minute += timedelta(minutes=(1 if now.minute % 2 == (0 if mode == "odd" else 1) else 2))
                    wait_seconds = (next_minute - now).total_seconds()
                    self.timer_label.config(text=f"Syncing to next {mode} minute...")
                    threading.Thread(target=self.delayed_start, args=(wait_seconds, seconds, loop)).start()
                else:
                    self.timer_instance = CountdownTimer(self.timer_window, seconds, loop, self.reset_ui, self)

            if self.schedule_time_str.get():
                try:
                    schedule_time = datetime.strptime(self.schedule_time_str.get(), "%H:%M").replace(
                        year=datetime.now().year,
                        month=datetime.now().month,
                        day=datetime.now().day
                    )
                    now = datetime.now()
                    if schedule_time <= now:
                        schedule_time += timedelta(days=1)

                    wait_seconds = (schedule_time - now).total_seconds()
                    self.timer_label.config(text=f"Waiting for {schedule_time.strftime('%H:%M')} to start...")

                    def wait_and_start():
                        nonlocal wait_seconds
                        while wait_seconds > 0:
                            if self.cancel_schedule_flag.get():
                                print("Scheduled thread cancelled before start.")
                                return
                            time.sleep(1)
                            wait_seconds -= 1

                        if not self.cancel_schedule_flag.get():
                            self.timer_window.after(0, begin_timer_after_sync_or_schedule)

                    schedule_thread = threading.Thread(target=wait_and_start)
                    schedule_thread.start()
                    print(f"Start scheduler timer: job_id={self.timer_job_id}, running={self.timer_running.get()}")
                    return  # skip normal start
                except ValueError:
                    messagebox.showerror("Invalid Time", "Please enter time in HH:MM format.")
                    self.reset_ui()
                    return

            # elif mode in ("even", "odd"):
            #     now = datetime.now()
            #     current_minute = now.minute
            #     seconds = now.second
            #
            #     if sync_mode.get() == "even":
            #         target_minute = current_minute + 1 if current_minute % 2 != 0 else current_minute + 2
            #     else:  # odd
            #         target_minute = current_minute + 1 if current_minute % 2 == 0 else current_minute + 2
            #
            #     wait_time = ((target_minute - current_minute) * 60) - seconds
            #     timer_label.config(text=f"Waiting for {'even' if sync_mode.get() == 'even' else 'odd'} minute...")
            #     threading.Thread(target=lambda: (
            #     time.sleep(wait_time), timer_window.after(0, begin_timer_after_sync_or_schedule))).start()

            else:
                if self.sync_mode.get() == "none" and self.schedule_time_str.get() == "":
                    print(f"Start timer1: job_id={self.timer_job_id}, running={self.timer_running.get()}")
                    # timer_instance = CountdownTimer(timer_window, seconds, loop, reset_ui, self)
                    begin_timer_after_sync_or_schedule()

        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a valid number.")

    def delayed_start(self, wait_seconds, countdown_seconds, loop):
        time.sleep(wait_seconds)
        # Countdown starts on the main thread
        self.timer_window.after(0, lambda: self.start_after_sync(countdown_seconds, loop))

    def start_after_sync(self, countdown_seconds, loop):

        self.timer_instance = CountdownTimer(self.timer_window, countdown_seconds, loop, self.reset_ui, self)

    # ---- RESET UI ----
    def reset_ui(self):
        # self.entry.config(state='normal')
        # start_button.config(state='normal')
        # stop_button.config(state='disabled')
        return

    def stop_timer(self):
        # Stop countdown if it's running

        if self.timer_running.get():
            if self.timer_job_id:
                self.timer_window.after_cancel(self.timer_job_id)
                self.timer_job_id = None
                self.timer_running.set(False)
                # timer_instance.stop()
            self.timer_running.set(False)

        # Cancel scheduler (even if countdown has started)
        self.cancel_schedule_flag.set(True)

        if self.timer_instance:
            self.timer_instance.stop()
            print("stop timer instance")
            # Cancel any pending scheduled thread

        # # Reset modes
        self.schedule_time_str.set("")
        self.sync_mode.set("none")

        # Update UI
        # timer_label.config(font=("Arial", new_size))
        self.timer_label.config(text="00:00")

    def create_popup_menu(self):
        # Right-click popup menu
        self.popup_menu = tk.Menu(self.timer_window, tearoff=0)
        # Font Size Submenu
        self.font_size_menu = tk.Menu(self.popup_menu, tearoff=0)
        for label in ["Small", "Medium", "Large", "Extra Large"]:
            self.font_size_menu.add_command(label=label, command=lambda l=label: self.set_timer_font(l))

        self.popup_menu.add_command(label="Start Timer", command=self.start_timer)
        self.popup_menu.add_command(label="Stop Timer", command=self.stop_timer)
        self.popup_menu.add_separator()

        self.popup_menu.add_command(label="Start on Schedule...", command=self.set_schedule_time)
        self.popup_menu.add_command(label="Set Timer Duration...", command=self.set_timer_duration)

        self.popup_menu.add_separator()
        self.popup_menu.add_checkbutton(
            label="Minimize Mode",
            onvalue=True,
            offvalue=False,
            variable=self.menu_visible,
            command=self.toggle_menu)

        # add looper timer
        self.popup_menu.add_checkbutton(
            label="Loop Timer",
            onvalue=True,
            offvalue=False,
            variable=self.loop_var,
            command=self.toggle_loop
        )
        self.timer_window.bind("<Button-3>", self.show_popup)
        self.popup_menu.add_checkbutton(
            label="Always on Top",
            onvalue=True,
            offvalue=False,
            variable=self.topmost_var,
            command=self.toggle_topmost_from_menu
        )

        self.popup_menu.add_separator()
        self.volume_var = tk.DoubleVar(value=1.0)
        self.popup_menu.add_command(label="Sound Volume...", command=self.open_volume_control)

        self.popup_menu.add_separator()
        self.popup_menu.add_cascade(label="Font Size", menu=self.font_size_menu)
        self.popup_menu.add_command(label="Font Color", command=self.change_font_color)
        self.popup_menu.add_command(label="Background Color", command=self.change_bg_color)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Exit", command=self.timer_window.quit)

    def create_file_menu(self):
        # Create the main menu bar
        # Create the 'File' dropdown menu
        self.menu_visible = True
        self.menu_bar = None
        self.menu_bar = tk.Menu(self.timer_window)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        # Set the menu
        self.timer_window.config(menu=self.menu_bar)
        self.timer_window.bind("<Escape>", self.toggle_menu)
        # add looper timer
        self.config = self.load_config()
        self.loop_var = tk.BooleanVar(value=self.config.get("loop_timer", "false"))
        self.file_menu.add_checkbutton(
            label="Loop Timer",
            onvalue=True,
            offvalue=False,
            variable=self.loop_var,
            command=self.toggle_loop
        )
        # Select Sound File
        self.selected_sound_file = tk.StringVar(value="coin_ringing.wav")  # default
        self.file_menu.add_command(label="Select Sound File...", command=self.choose_sound_file)
        # add schedule_time_str
        self.timer_job_id = None
        self.schedule_time_str = tk.StringVar(value="")
        self.cancel_schedule_flag = tk.BooleanVar(value=False)
        self.timer_running = tk.BooleanVar(value=False)
        self.file_menu.add_command(label="Start on Schedule...", command=self.set_schedule_time)
        # add sound volumn to file menu
        self.volume_var = tk.DoubleVar(value=1.0)
        self.file_menu.add_command(label="Sound Volume...", command=self.open_volume_control)
        # sync option
        self.sync_mode = tk.StringVar(value="none")  # options: "none", "even", "odd"
        self.sync_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Sync Start", menu=self.sync_menu)
        self.sync_menu.add_radiobutton(label="None", variable=self.sync_mode, value="none")
        self.sync_menu.add_radiobutton(label="Even Minute", variable=self.sync_mode, value="even")
        self.sync_menu.add_radiobutton(label="Odd Minute", variable=self.sync_mode, value="odd")
        self.file_menu.add_command(label="Set Timer Duration...", command=self.set_timer_duration)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.timer_window.quit)
        self.timer_window.config(menu=self.menu_bar)

    def create_view_menu(self):
        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        for label in ["Small", "Medium", "Large", "Extra Large"]:
            self.view_menu.add_command(label=label, command=lambda l=label: self.set_timer_font(l))
        # Track the 'Always on Top' state
        self.config = self.load_config()
        self.topmost_var = tk.BooleanVar(value=self.config.get("top_most", "false"))
        self.view_menu.add_checkbutton(
            label="Always on Top ✓",
            onvalue=True,
            offvalue=False,
            variable=self.topmost_var,
            command=self.toggle_topmost_from_menu
        )
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

    def guiSetup(self):
        # ----------------------------
        # GUI SETUP
        # ----------------------------

        # ---- MAIN WINDOW ----

        self.timer_window.title("⏱️ Synced Countdown Timer")
        self.timer_window.bind("<Button-1>", self.start_move)
        self.timer_window.bind("<B1-Motion>", self.do_move)

        config = self.load_config()
        self.countdown_time = config.get("timer_duration", self.countdown_time)

        # sync_mode option
        self.sync_mode = tk.StringVar(value="none")

        self.sync_frame = tk.Frame(self.timer_window)
        self.sync_frame.pack(pady=5)

        self.timer_label = tk.Label(self.timer_window, text="Ready", font=("Helvetica", 36))
        self.timer_label.pack(pady=10)
        self.saved_label = config.get("font_size_label")
        self.set_timer_font(self.saved_label)
        # load timer font color
        self.timer_label.config(fg=self.config.get("font_color", "black"))

        # load background color
        self.timer_window.configure(bg=self.config.get("background_color", "white"))
        self.timer_label.configure(bg=self.config.get("background_color", "white"))

        self.timer_instance = None

        self.create_file_menu()

        self.create_view_menu()

        # Main popup options

        self.create_popup_menu()


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

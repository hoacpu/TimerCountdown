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
import pytz


class TimezoneClockApp(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Selectable Multi-Timezone Clock")
        self.geometry("450x500")
        # Store timezone widgets
        self.clocks = {}  # { tz_name: (frame, label_time) }

        # timezones = [
        #     "UTC", "GMT", "PST", "EST", "CET", "IST",
        #     "Asia/Kolkata", "America/New_York", "Europe/London"
        # ]

        # Dropdown for timezone selection
        self.timezone_var = tk.StringVar()
        self.timezone_dropdown = ttk.Combobox(self,
                                              textvariable=self.timezone_var)

        self.timezone_dropdown['values'] = sorted(pytz.all_timezones)
        self.timezone_dropdown.set("Select Timezone")

        self.timezone_dropdown.pack(pady=10)
        # Button to add timezone
        self.add_button = tk.Button(self, text="Add Timezone", command=self.add_timezone)
        self.add_button.pack()
        # Frame to hold timezone clocks
        self.clock_frame = tk.Frame(self)
        self.clock_frame.pack(pady=10, fill='both', expand=True)

        self.update_clocks()


    def add_timezone(self):

        tz = self.timezone_var.get()
        if tz and tz not in self.clocks:
            frame = tk.Frame(self.clock_frame, bd=1, relief="sunken", padx=5, pady=5)
            frame.pack(pady=5, fill="x", padx=10)

            # Timezone label
            label_title = tk.Label(frame, text=tz, font=("Arial", 12, "bold"))
            label_title.pack(anchor="w")

            # Time label
            label_time = tk.Label(frame, text="", font=("Arial", 14))
            label_time.pack(anchor="w")

            # Remove button
            remove_btn = tk.Button(frame, text="Remove", command=lambda tz=tz: self.remove_timezone(tz))
            remove_btn.pack(anchor="e", pady=2)

            self.clocks[tz] = (frame, label_time)

    def remove_timezone(self, tz):
        if tz in self.clocks:
            frame, _ = self.clocks[tz]
            frame.destroy()
            del self.clocks[tz]

    def update_clocks(self):
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        for tz_name, (frame, label_time) in self.clocks.items():
            try:
                local_time = now_utc.astimezone(pytz.timezone(tz_name))
                label_time.config(text=local_time.strftime("%H:%M:%S"))
            except Exception as e:
                label_time.config(text="Error")
        self.after(1000, self.update_clocks)


# ---- TIMER CLASS ----
class CountdownTimer(tk.Toplevel):
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
        else:  #time up
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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Menubar Toggle Example")
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
        self.config_file = self.load_config()
        self.config_file["name"] = self.config_file.get("name", "default")
        self.volume_var = tk.DoubleVar(value=self.config_file.get("volume", 1.0))
        self.topmost_var = tk.BooleanVar(value=self.config_file.get("top_most", "False"))
        self.second_left_var = tk.StringVar(value=self.config_file.get("second_left", 5))
        self.loop_var = tk.BooleanVar(value=self.config_file.get("loop_timer", "false"))
        self.selected_sound_file = tk.StringVar(value=self.config_file.get("sound_path", "coin_ringing.wav"))
        self.font_size_label = self.config_file.get("font_size_label",20)
        self.schedule_time_str = tk.StringVar(value=self.config_file.get("schedule_time", "6:30"))
        self.duration_var = tk.StringVar(value=self.config_file.get("timer_duration", "60"))

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

        self.config_file = self.load_config()
        self.config_file["font_color"] = color[1]
        self.save_config(self.config_file)

    def change_bg_color(self):
        # Open color chooser
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[1]:
            self.configure(bg=color[1])
            self.timer_label.configure(bg=color[1])  # Keep label background in sync

        self.config_file = self.load_config()
        self.config_file["background_color"] = color[1]
        self.save_config(self.config_file)

    def toggle_title_bar(self):
        self.title_bar_hidden = not self.title_bar_hidden
        self.overrideredirect(self.title_bar_hidden)

        # To apply changes on most platforms, re-positioning the window helps
        if self.title_bar_hidden:
            self.geometry("+100+100")  # move to avoid flicker
        else:
            self.update_idletasks()
            self.deiconify()

    # add mouse event handlers
    def start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y


    def do_move(self, event):
        x = self.winfo_pointerx() - self._drag_start_x
        y = self.winfo_pointery() - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def do_move_popup(self, event):
        x = self.winfo_pointerx() - self._drag_start_x
        y = self.winfo_pointery() - self._drag_start_y
        self.popup.geometry(f"+{x}+{y}")


    def toggle_menu(self, event=None):
        if self.menu_visible:
            self.config(menu="")
            self.menu_visible = False
        else:
            self.config(menu=self.menu_bar)
            self.menu_visible = True
        self.toggle_title_bar()


    # ---- SOUND FUNCTION ----
    def play_sound(self):

        if not self.selected_sound_file.get():
            return
        try:
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
        self.attributes("-topmost", self.topmost_var.get())
        self.config_file = self.load_config()
        self.config_file["top_most"] = self.topmost_var.get()
        self.save_config(self.config_file)


    def choose_sound_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Sound File",
            filetypes=[("Audio Files", "*.wav *.mp3")]
        )
        if file_path:
            self.selected_sound_file.set(file_path)
            self.config_file = self.load_config()
            self.config_file["sound_path"] = file_path
            self.save_config(self.config_file)


    def set_schedule_time(self):

        def save_time():
            self.sync_mode = "none"
            sch_time = self.hour_var.get().strip()+":"+self.minute_var.get()
            self.schedule_time_str.set(sch_time)

            self.config_file = self.load_config()
            self.config_file["schedule_time"] = sch_time
            self.save_config(self.config_file)

            self.start_timer()
            self.popup.destroy()

        self.popup = tk.Toplevel(self)
        self.popup.title("Set Scheduled Start Time")
        self.popup.geometry("250x100")
        self.popup.bind("<Button-1>", self.start_move)
        self.popup.bind("<B1-Motion>", self.do_move_popup)
        tk.Label(self.popup, text="Schedule Start Time:").pack(pady=(15, 5))
        dropdown_frame = tk.Frame(self.popup)
        dropdown_frame.pack()

        self.config_file = self.load_config()

        sch_time = self.schedule_time_str.get().split(":")

        self.hour_var = tk.StringVar(value=sch_time[0])
        self.minute_var = tk.StringVar(value=sch_time[1])

        hours = [f"{i:02d}" for i in range(24)]
        minutes = [f"{i:02d}" for i in range(60)]

        self.hour_menu = tk.OptionMenu(dropdown_frame, self.hour_var, *hours)
        self.minute_menu = tk.OptionMenu(dropdown_frame, self.minute_var, *minutes)

        self.hour_menu.pack(side="left", padx=5)
        self.minute_menu.pack(side="left", padx=5)

        tk.Button(self.popup, text="OK", command=save_time).pack(pady=5)


    def open_volume_control(self):
        def set_volume(val):
            volume = float(val) / 100  # Convert 0-100 scale to 0.0-1.0
            self.config_file = self.load_config()
            self.config_file["volume"] = volume
            self.save_config(self.config_file)
            print (f"sound volume value : {volume}")
            self.volume_var.set(volume)
            pygame.mixer.music.set_volume(volume)

        self.popup = tk.Toplevel(self)
        self.popup.title("Set Sound Volume")
        self.popup.geometry("430x150")
        self.popup.bind("<Button-1>", self.start_move)
        self.popup.bind("<B1-Motion>", self.do_move_popup)
        tk.Label(self.popup, text="Volume (%):", font=('Arial', 12)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.scale = tk.Scale(self.popup, from_=0, to=100, orient="horizontal",
                         command=set_volume)
        self.scale.set(int(self.volume_var.get() * 100))
        self.scale.grid(row=0, column=1, padx=10, pady=10)

        # Create and place the second left label and entry
        tk.Label(self.popup, text="Sound On After Number Seconds:", font=('Arial', 12)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        second_left_entry = tk.Entry(self.popup, textvariable=self.second_left_var, width=10, font=('Arial', 12))
        second_left_entry.grid(row=1, column=1, padx=10, pady=10)

        def apply_second_left():
            try:
                second_left = int(self.second_left_var.get())
                self.popup.destroy()
                # Save to config
                self.config_file = self.load_config()
                self.config_file["second_left"] = second_left
                self.save_config(self.config_file)

            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")
        ttk.Button(self.popup, text="OK", command=apply_second_left).grid(row=2, column=1, padx=10, pady=10)


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
        self.config_file = self.load_config()
        self.config_file["font_size_label"] = size_label
        self.save_config(self.config_file)

    def set_timer_duration(self):
        self.popup = tk.Toplevel(self)
        self.popup.title("Set Timer Duration")

        ttk.Label(self.popup, text="Enter duration in seconds:").pack(padx=10, pady=5)

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
                    self.config_file = self.load_config()
                    self.config_file["timer_duration"] = new_time
                    self.save_config(self.config_file)

                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")

        ttk.Button(self.popup, text="OK", command=apply_duration).pack(pady=5)

    def toggle_loop(self):
        # Save to config
        self.config_file = self.load_config()
        self.config_file["loop_timer"] = self.loop_var.get()
        self.save_config(self.config_file)

    # ---- START TIMER ----
    def start_timer(self):
        try:
            seconds = self.countdown_time
            loop = self.loop_var.get()

            self.cancel_schedule_flag.set(False)

            def begin_timer_after_sync_or_schedule():
                self.timer_instance = CountdownTimer(self, seconds, loop, self.reset_ui, self)

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
                            self.after(0, begin_timer_after_sync_or_schedule)

                    schedule_thread = threading.Thread(target=wait_and_start)
                    schedule_thread.start()
                    print(f"Start scheduler timer: job_id={self.timer_job_id}, running={self.timer_running.get()}")
                    return  # skip normal start
                except ValueError:
                    messagebox.showerror("Invalid Time", "Please enter time in HH:MM format.")
                    self.reset_ui()
                    return
            else:
                if self.schedule_time_str.get() == "":
                    print(f"Start timer1: job_id={self.timer_job_id}, running={self.timer_running.get()}")
                    # timer_instance = CountdownTimer(timer_window, seconds, loop, reset_ui, self)
                    begin_timer_after_sync_or_schedule()

        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a valid number.")


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
                self.after_cancel(self.timer_job_id)
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
        # self.sync_mode.set("none")

        # Update UI
        # timer_label.config(font=("Arial", new_size))
        self.timer_label.config(text="00:00")

    def create_popup_menu(self):
        # Right-click popup menu
        self.popup_menu = tk.Menu(self, tearoff=0)
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
        self.bind("<Button-3>", self.show_popup)
        self.popup_menu.add_checkbutton(
            label="Always on Top",
            onvalue=True,
            offvalue=False,
            variable=self.topmost_var,
            command=self.toggle_topmost_from_menu
        )
        self.attributes("-topmost", self.topmost_var.get())

        self.popup_menu.add_separator()
        # add sound volumn to file menu
        self.volume_var = tk.DoubleVar(value=1.0)
        self.popup_menu.add_command(label="Sound Volume...", command=self.open_volume_control)
        self.popup_menu.add_command(label="Sound File...", command=self.choose_sound_file)

        self.popup_menu.add_separator()
        self.popup_menu.add_cascade(label="Font Size", menu=self.font_size_menu)
        self.popup_menu.add_command(label="Font Color", command=self.change_font_color)
        self.popup_menu.add_command(label="Background Color", command=self.change_bg_color)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Exit", command=self.quit)

    def open_new_timer(self):
        prompt = tk.Toplevel(self)
        prompt.title("New Timer Duration")
        prompt.geometry("250x100")
        name_var = tk.StringVar()
        label = tk.Label(prompt, text="Enter the Timer Name")
        label.pack(pady=(10,0))
        name_entry = tk.Entry(prompt,textvariable = name_var)
        name_entry.pack()
        def start():
            try:
                name = name_entry.get()
                prompt.destroy()
                app = App()
                app.title(name)
                app.mainloop()
            except ValueError:
                label.config(text="Please enter a valid number!")
        tk.Button(prompt, text="Start Timer", command=start).pack(pady=5)

    def open_new_clock(self):
        clock = TimezoneClockApp()
        clock.mainloop()


    def create_file_menu(self):
        # Create the main menu bar
        # Create the 'File' dropdown menu
        self.menu_visible = True
        self.menu_bar = None
        self.menu_bar = tk.Menu(self)
        # Set the menu
        self.configure(menu=self.menu_bar)
        self.bind("<Escape>", self.toggle_menu)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Timer", command=self.open_new_timer)
        self.file_menu.add_command(label="New Clock", command=self.open_new_clock)
        self.file_menu.add_separator()

        self.file_menu.add_command(label="Start Timer", command=self.start_timer)
        self.file_menu.add_command(label="Stop Timer", command=self.stop_timer)
        self.file_menu.add_separator()
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # add looper timer

        self.file_menu.add_checkbutton(
            label="Loop Timer",
            onvalue=True,
            offvalue=False,
            variable=self.loop_var,
            command=self.toggle_loop
        )
        # Select Sound File
          # default
        self.file_menu.add_command(label="Select Sound File...", command=self.choose_sound_file)
        # add schedule_time_str
        self.timer_job_id = None
        self.cancel_schedule_flag = tk.BooleanVar(value=False)
        self.timer_running = tk.BooleanVar(value=False)
        self.file_menu.add_command(label="Start on Schedule...", command=self.set_schedule_time)
        # add sound volumn to file menu
        self.volume_var = tk.DoubleVar(value=1.0)
        self.file_menu.add_command(label="Sound Volume...", command=self.open_volume_control)
        self.file_menu.add_command(label="Set Timer Duration...", command=self.set_timer_duration)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        self.configure(menu=self.menu_bar)

    def create_view_menu(self):
        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        for label in ["Small", "Medium", "Large", "Extra Large"]:
            self.view_menu.add_command(label=label, command=lambda l=label: self.set_timer_font(l))
        # Track the 'Always on Top' state
        self.config_file = self.load_config()

        self.view_menu.add_checkbutton(
            label="Always on Top ✓",
            onvalue=True,
            offvalue=False,
            variable=self.topmost_var,
            command=self.toggle_topmost_from_menu
        )
        self.attributes("-topmost", self.topmost_var.get())
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)


    def guiSetup(self):
        # ----------------------------
        # GUI SETUP
        # ----------------------------

        # ---- MAIN WINDOW ----

        self.title("⏱️ Synced Countdown Timer")
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

        config = self.load_config()
        self.countdown_time = config.get("timer_duration", self.countdown_time)
        #initial sound volume
        self.init_mixer()


        # self.timer_name_label = tk.Label(self, text="Default", font=("Helvetica", 8))
        # self.timer_name_label.pack(pady=2)
        self.timer_label = tk.Label(self, text="Ready", font=("Helvetica", 36))
        self.timer_label.pack(pady=10)

        self.set_timer_font(self.font_size_label)
        #load timer font color
        self.timer_label.config(fg=self.config_file.get("font_color","black"))

        #load background color
        self.configure(bg=self.config_file.get("background_color","white"))
        self.timer_label.configure(bg=self.config_file.get("background_color","white"))
        # self.timer_name_label.configure(bg=self.config_file.get("background_color","white"))
        self.timer_instance = None
        self.create_file_menu()
        self.create_view_menu()
        # Main popup options
        self.create_popup_menu()


# Run the app
if __name__ == "__main__":
    app = App()
    app.mainloop()

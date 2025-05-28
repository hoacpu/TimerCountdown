import tkinter as tk
from tkinter import ttk
from datetime import datetime
import pytz

class TimezoneClockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Selectable Multi-Timezone Clock")
        self.geometry("450x500")

        # Dropdown for timezone selection
        self.timezone_var = tk.StringVar()
        self.timezone_dropdown = ttk.Combobox(self, textvariable=self.timezone_var)
        self.timezone_dropdown['values'] = sorted(pytz.all_timezones)
        self.timezone_dropdown.pack(pady=10)

        # Button to add timezone
        self.add_button = tk.Button(self, text="Add Timezones", command=self.add_timezone)
        self.add_button.pack()

        # Frame to hold timezone clocks
        self.clock_frame = tk.Frame(self)
        self.clock_frame.pack(pady=10, fill='both', expand=True)

        # Store timezone widgets
        self.clocks = {}  # { tz_name: (frame, label_time) }

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

if __name__ == "__main__":
    app = TimezoneClockApp()
    app.mainloop()

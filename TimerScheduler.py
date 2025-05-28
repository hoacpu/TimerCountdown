import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta

# Initialize GUI
window = tk.Tk()
window.title("Smart Timer")

# State variables
timer_job_id = None
schedule_thread = None

# Tkinter Variables
countdown_time = 10  # seconds
timer_running = tk.BooleanVar(value=False)
cancel_schedule_flag = tk.BooleanVar(value=False)
schedule_time_str = tk.StringVar()
sync_mode = tk.StringVar(value="none")

# UI Elements
timer_label = ttk.Label(window, text="Timer Ready", font=("Arial", 24))
timer_label.pack(pady=20)

entry_frame = ttk.Frame(window)
entry_frame.pack()

ttk.Label(entry_frame, text="Schedule Time (HH:MM):").pack(side="left")
ttk.Entry(entry_frame, textvariable=schedule_time_str, width=10).pack(side="left")

start_button = ttk.Button(window, text="Start")
stop_button = ttk.Button(window, text="Stop", state="disabled")
start_button.pack(pady=5)
stop_button.pack(pady=5)

# --- Core Logic ---

def count_down(seconds_left):
    global timer_job_id

    if cancel_schedule_flag.get():
        timer_label.config(text="Timer cancelled.")
        start_button.config(state="normal")
        stop_button.config(state="disabled")
        timer_running.set(False)
        return

    if seconds_left <= 0:
        timer_label.config(text="⏰ Time's up!")
        timer_running.set(False)
        start_button.config(state="normal")
        stop_button.config(state="disabled")
        return

    mins, secs = divmod(seconds_left, 60)
    timer_label.config(text=f"{mins:02}:{secs:02}")
    timer_running.set(True)
    timer_job_id = window.after(1000, lambda: count_down(seconds_left - 1))

def begin_timer_after_schedule():
    if not cancel_schedule_flag.get():
        count_down(countdown_time)

def start_timer():
    global schedule_thread
    start_button.config(state="disabled")
    stop_button.config(state="normal")
    cancel_schedule_flag.set(False)

    if schedule_time_str.get().strip():
        try:
            # Parse and calculate delay
            schedule_time = datetime.strptime(schedule_time_str.get(), "%H:%M").replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )
            now = datetime.now()
            if schedule_time <= now:
                schedule_time += timedelta(days=1)
            delay = int((schedule_time - now).total_seconds())

            timer_label.config(text=f"⏳ Waiting for {schedule_time.strftime('%H:%M')}...")

            # Scheduler thread
            def wait_and_start():
                remaining = delay
                while remaining > 0:
                    if cancel_schedule_flag.get():
                        print("Scheduled timer cancelled before start.")
                        return
                    time.sleep(1)
                    remaining -= 1
                if not cancel_schedule_flag.get():
                    window.after(0, begin_timer_after_schedule)

            schedule_thread = threading.Thread(target=wait_and_start, daemon=True)
            schedule_thread.start()
            return
        except ValueError:
            messagebox.showerror("Invalid Time", "Use format HH:MM")
            stop_timer()
            return

    # No schedule: start immediately
    begin_timer_after_schedule()

def stop_timer():
    global timer_job_id

    # Cancel active countdown
    if timer_running.get() and timer_job_id:
        window.after_cancel(timer_job_id)
        timer_job_id = None
        timer_running.set(False)

    # Cancel scheduler
    cancel_schedule_flag.set(True)

    # Reset GUI
    timer_label.config(text="Timer stopped.")
    start_button.config(state="normal")
    stop_button.config(state="disabled")
    schedule_time_str.set("")
    sync_mode.set("none")

# Button bindings
start_button.config(command=start_timer)
stop_button.config(command=stop_timer)

# Run app
window.mainloop()

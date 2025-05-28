import time
import sys
from threading import Thread
import queue

class DisplayTime(Thread):

    def __init__(self,time_queue):
        super().__init__()
        self.time_queue = time_queue

    def run(self):
        while True:
            time_str = self.time_queue.get()
            if time_str is None:
                break
            print(f"\r{time_str}", end="", flush=True)
            time.sleep(1)
            self.time_queue.task_done()


class MyTimer(Thread):
    def __init__(self,time_queue):
        super().__init__()
        self.time_queue = time_queue
        current_time = time.strftime("%H:%M:%S")  # Get the current time as a string
        # self.time_queue.put(current_time)


    def run(self):
        while True:
            # Update the current time and print it dynamically
            current_time = time.strftime("%H:%M:%S")
            self.time_queue.put(current_time)
            time.sleep(1)  # Wait for 1 second before updating
            # self.time_queue.task_done()

def display_time():
    try:
        while True:
            current_time = time.strftime("%H:%M:%S")
            print(f"\r{current_time}", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        #Handle ctrl+c to exit gracefully
        print ("\nExiting...")
        sys.exit()

def display_time_thread():
    try:
        while True:
            current_time = time.strftime("%H:%M:%S")
            print(f"\r{current_time}", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit()


if __name__ == "__main__":
    # display_time()

    # myTimer = Thread(target=display_time_thread)
    # myTimer.start()
    # myTimer.join()
    my_time_queue = queue.Queue()

    timer = MyTimer(my_time_queue)
    display = DisplayTime(my_time_queue)
    try:
        timer.start()
        display.start()
        timer.join()
        display.join()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit()

    my_time_queue.join()





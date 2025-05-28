import time
from threading import Thread

def counter(count):
    while count > 0:
        print(f"\rcountdown: {count}",  end="", flush=True)
        time.sleep(1)
        count -= 1

if __name__ == "__main__":
    myTimer = Thread(target=counter, args=(10,))
    myTimer.start()
    myTimer.join()

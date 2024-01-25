import threading
import time
import logging
import datetime

class utils:
    class TimerThread(threading.Thread):
        def __init__(self, interval, callback, stop_event):
            super(utils.TimerThread, self).__init__()
            self.interval = interval
            self.callback = callback
            self.stop_event = stop_event

        def run(self):
            while not self.stop_event.is_set():
                start_time = time.time()
                elapsed_time = time.time() - start_time

                if not self.stop_event.is_set():
                    self.callback()

                    # Adjust the interval if needed
                    remaining_time = self.interval - elapsed_time
                    while remaining_time > 0 and not self.stop_event.is_set():
                        time.sleep(1)
                        remaining_time -= 1

    class TimerThread2(threading.Thread):
        def __init__(self, interval, event, stop_event):
            super(utils.TimerThread2, self).__init__()
            self.interval = interval
            self.event = event
            self.stop_event = stop_event

        def run(self):
            while not self.stop_event.is_set():
                start_time = time.time()
                elapsed_time = time.time() - start_time

                if not self.stop_event.is_set():
                    self.event.set()

                    # Adjust the interval if needed
                    remaining_time = self.interval - elapsed_time
                    while remaining_time > 0 and not self.stop_event.is_set():
                        time.sleep(1)
                        remaining_time -= 1

    class logger:

        def __init__(self, log_file='solbind.log'):
            logging.basicConfig(filename=log_file, level=logging.INFO)

        def log_message(self, message):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"{timestamp} - {message}"
            logging.info(formatted_message)

        def read_log(self):
            with open('solbind.log', 'r') as file:
                log_content = file.read()
                print(log_content)

        def print_and_log(self, message):
            print(message)
            self.log_message(message)


    def pulse_for_thread(thread_name, pulse_interval, timer_thread):
        print(f'{thread_name} received a pulse!')
        timer_thread.interval = pulse_interval  # Restart the timer with the specified interval
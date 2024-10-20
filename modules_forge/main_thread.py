# This file is the main thread that handles all gradio calls for major t2i or i2i processing.
# Other gradio calls (like those from extensions) are not influenced.
# By using one single thread to process all major calls, model moving is significantly faster.


import time
import traceback
import threading
import os
import gc
import torch


lock = threading.Lock()
last_id = 0
waiting_list = []
finished_list = []
last_exception = None


class Task:
    def __init__(self, task_id, func, args, kwargs):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.exception = None

    def work(self):
        global last_exception
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.exception = None
            last_exception = None
        except Exception as e:
            traceback.print_exc()
            print(e)
            self.exception = e
            last_exception = e


def loop():
    global lock, last_id, waiting_list, finished_list
    while True:
        time.sleep(0.01)
        if len(waiting_list) > 0:
            with lock:
                task = waiting_list.pop(0)

            task.work()

            with lock:
                finished_list.append(task)


def async_run(func, *args, **kwargs):
    global lock, last_id, waiting_list, finished_list
    with lock:
        last_id += 1
        new_task = Task(task_id=last_id, func=func, args=args, kwargs=kwargs)
        waiting_list.append(new_task)
    return new_task.task_id


# Create lock file to check if webui is busy
LOCK_FILE = "/tmp/ai_generator.lock"

def run_and_wait_result(func, *args, **kwargs):
    global lock, last_id, waiting_list, finished_list

    # Create the lock file at the start of the task
    open(LOCK_FILE, 'w').close()

    try:
        current_id = async_run(func, *args, **kwargs)
        while True:
            time.sleep(0.01)
            finished_task = None
            for t in finished_list.copy():  # thread safe shallow copy without needing a lock
                if t.task_id == current_id:
                    finished_task = t
                    break
            if finished_task is not None:
                with lock:
                    finished_list.remove(finished_task)

                # Perform garbage collection and clear GPU cache after task completion
                gc.collect()  # Trigger Python garbage collection
                torch.cuda.empty_cache()  # Free GPU memory cache
                print("Garbage collection and GPU memory cache cleared after task completion.")

                return finished_task.result
    finally:
        # Remove the lock file when the task is complete
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        print("Lock file removed.")

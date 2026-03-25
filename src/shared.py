import threading

DATA_LOCK = threading.Lock()
STOP_EVENT = threading.Event()
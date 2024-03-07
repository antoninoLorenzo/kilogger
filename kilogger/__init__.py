import sys
from pathlib import Path

# default log path
U_HOME = Path('~')
LOGLOC = str(U_HOME.expanduser() / '.cache' / 'report.log')

# time that is waited to interrupt logging and check running processes
DEFAULT_TIMEOUT = 10


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

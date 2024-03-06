# Kilogger
This is an educational purpose keylogger.
**What it can do?**
Right now not so much, it can capture keys; also you can specify processes to listen to, when the 'victim' runs a program the logger starts logging.

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

## Other
[VirusTotal](https://www.virustotal.com/gui/home/upload) score (for `main.py`):

<img src="./static/virus_total_score.PNG" style="width:92px;height:92px"/>

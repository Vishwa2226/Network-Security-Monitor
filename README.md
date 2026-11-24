# Network Security Monitor

A local real-time network monitoring dashboard built with Python, Flask-SocketIO, Scapy and Npcap.

## Features
- Live packet capture from a selected local network adapter.
- Packet totals, approximate traffic rate and protocol distribution.
- Recent packet table with source/destination addresses, ports, lengths and TCP flags.
- Conservative heuristic alerts for possible port scanning or unusually high SYN activity.
- Start/stop capture controls and adapter selection.
- Local-first operation; no packet contents are uploaded to a cloud service.

> **Capture scope:** This captures traffic visible to the selected computer's adapter. On ordinary Windows Wi-Fi this generally means traffic to/from this computer, not all devices on the wireless LAN. Cisco Packet Tracer simulation traffic is separate and is not automatically captured by Scapy on the laptop.

## Requirements
- Windows 10/11
- Python 3.11+
- Npcap installed (https://npcap.com/)
- Administrator privileges may be required for live capture.

## Setup (Windows PowerShell)
Open PowerShell in this project folder and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000, select the active Wi-Fi or Ethernet adapter, and click **Start capture**.

If PowerShell blocks activation, run:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

## Generate harmless test traffic
In another PowerShell window, run:
```powershell
ping 8.8.8.8 -n 5
nslookup example.com
```
Then open an ordinary HTTPS website and observe packets in the dashboard.

## Troubleshooting
- **No interfaces:** install/reinstall Npcap and restart the terminal.
- **Permission error:** close Wireshark/other capture sessions and run PowerShell as Administrator.
- **No packets:** choose the adapter with your active IPv4 address and generate traffic.
- **Port 5000 is busy:** set `PORT=5001` before running.
- The app binds to localhost by default. Do not expose it to the public internet.

## Detection limitations
Alerts are simple traffic heuristics, not proof of compromise or a replacement for an IDS. Legitimate software can cause false positives. Verify suspicious observations in Wireshark before reporting an incident. TLS application payloads are encrypted and are not decrypted by this tool.

## Project structure
```
app.py
analyzer.py
capture.py
run.py
requirements.txt
templates/index.html
static/style.css
static/app.js
docs/PROJECT_SCOPE.md
```

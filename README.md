# Network Security Monitor

**Hosted dashboard + Windows packet-capture helper.** Open the dashboard from a browser, pair your Windows helper once, then start/stop capture from the website.

## How it works
- **Hosted dashboard:** Flask + Flask-SocketIO, deployable to Render.
- **Windows helper:** Scapy + Npcap + Python Socket.IO client.
- The helper opens an outbound HTTPS/WebSocket connection to the dashboard. No inbound port or router configuration is needed on your laptop.
- A random private pairing token groups the helper and browser into a private live session.
- The website sends Start/Stop commands; the helper captures traffic locally and forwards packet summaries.

## 1. Deploy the website
1. Sign in to Render: https://dashboard.render.com/
2. Select **New** → **Blueprint**.
3. Connect GitHub and choose `Vishwa2226/Network-Security-Monitor`.
4. Render reads `render.yaml`. Review the service and deploy it.
5. After deployment, copy the HTTPS service URL, such as `https://network-security-monitor.onrender.com`.

The included Blueprint configures Python 3.11, dependencies, Gunicorn with one Eventlet worker, a health check and a generated secret key. Render supports inbound WebSockets to web services and outbound WebSocket connections from clients. References: [Render WebSockets](https://render.com/docs/websocket), [Render Blueprint YAML](https://render.com/docs/blueprint-spec), [Render Python version](https://render.com/docs/python-version).

The free Render service can spin down after 15 minutes without inbound HTTP requests or WebSocket messages. The helper sends a small stats heartbeat every 5 seconds while connected, which provides inbound WebSocket activity; free services can still be restarted by the platform. See [Render free instance limitations](https://render.com/docs/free).

## 2. Install Npcap once
Install Npcap from https://npcap.com/ on your Windows laptop. Restart the terminal after installation. If live capture is denied, close Wireshark and run the helper as Administrator.

## 3. Start the Windows helper
1. Download the repository using GitHub **Code** → **Download ZIP**, then extract it.
2. Open the extracted folder, then open the `agent` folder.
3. Double-click `start_agent.bat`.
4. On first launch it creates a Python virtual environment and installs the helper packages. It then displays a random pairing token.
5. Copy the token. When prompted, paste the deployed Render HTTPS URL. The URL is saved locally for next time.
6. Keep the helper console open (minimise it if desired).

## 4. Start capture from your website
1. Open your Render HTTPS URL in Chrome.
2. Paste the pairing token in **Pair Windows helper**, then click **Connect**.
3. Wait until the helper shows **online**. Choose the active Wi-Fi or Ethernet adapter.
4. Click **Start Capture**. The dashboard shows real packet rows, protocols, endpoints, traffic-rate estimates and heuristic alerts.
5. Click **Stop** to stop capture from the website.

## Pairing-token security
- Treat the token like a password. Anyone who has it can view that live feed and control its capture session.
- The token is stored in `agent/pairing_token.txt` on the laptop and is ignored by Git.
- Never commit, post, or include the token in screenshots or reports.
- To rotate it, close the helper, delete `agent/pairing_token.txt`, restart the helper and pair with the new token.
- Use only the HTTPS hosted dashboard URL. The hosted service does not intentionally store a packet archive.

## Important scope and limitations
- The helper can capture only packets visible to the selected laptop adapter. Ordinary Wi-Fi operation normally exposes the laptop's own traffic, not all traffic from other devices on the same network.
- TLS application payloads remain encrypted; this dashboard does not decrypt them.
- The alerts are basic educational heuristics, not proof of compromise or a full IDS. False positives are possible.
- Cisco Packet Tracer Simulation Mode is separate and is not automatically captured by the laptop's Scapy helper. Treat Packet Tracer simulation results and laptop packet captures as separate evidence unless traffic is deliberately bridged or a PCAP is exported and analyzed separately.

## Harmless test traffic
With capture running, open a separate PowerShell window and run:
```powershell
ping 8.8.8.8 -n 5
nslookup example.com
```
Then visit an HTTPS website and observe the packet table.

## Project structure
```
app.py
analyzer.py
capture.py
run.py
requirements.txt
render.yaml
.python-version
agent/
  agent.py
  start_agent.bat
  requirements.txt
templates/index.html
static/style.css
static/app.js
docs/PROJECT_SCOPE.md
```

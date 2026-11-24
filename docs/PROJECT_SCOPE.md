# Project scope and demonstration guide

## End-to-end demonstration
1. Deploy the hosted dashboard using the Render Blueprint.
2. Install Npcap on the Windows laptop.
3. Double-click `agent/start_agent.bat`. On first run, it creates a private pairing token. Copy the token from the helper console.
4. Open the hosted dashboard URL, paste the pairing token and click Connect.
5. Wait for **Windows helper online**, select the active Wi-Fi adapter and click Start Capture.
6. In another PowerShell window run `ping 8.8.8.8 -n 5` and `nslookup example.com`, then open an HTTPS website.
7. Observe protocol distribution, endpoints, approximate bandwidth and recent packets. Stop capture from the dashboard.

## Suggested report evidence
- Hosted dashboard before pairing.
- Helper console with the token hidden.
- Dashboard showing the helper online and adapter list.
- Live packet table during ICMP and DNS traffic.
- Protocol chart, endpoint summaries and heuristic alert panel.
- Record adapter name, local IP, date/time and test commands.

## Scope and limitations
- The helper captures only frames exposed to the selected laptop adapter, typically traffic to/from that laptop rather than all devices on the Wi-Fi network.
- It does not decrypt TLS application data.
- It does not scan remote devices or inject packets.
- Alert rules are educational heuristics; false positives are possible.
- Cisco Packet Tracer Simulation Mode is not automatically captured by Scapy on the laptop. Treat Packet Tracer and laptop capture results separately unless you export a PCAP or deliberately bridge traffic.
- The public dashboard forwards live telemetry but does not persist a packet archive.

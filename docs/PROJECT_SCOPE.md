# Project scope and demonstration guide

## Demonstration sequence
1. Start the dashboard and select the active Wi-Fi adapter.
2. Start packet capture.
3. In a separate PowerShell window run `ping 8.8.8.8 -n 5` and `nslookup example.com`.
4. Open an ordinary HTTPS website.
5. Observe packet counters, protocol distribution, endpoints and recent packet details.
6. Stop capture and record the results.

## Suggested report evidence
- Screenshot before capture (zero baseline).
- Screenshot while generating ICMP and DNS traffic.
- Screenshot showing protocol distribution and recent packet rows.
- Screenshot showing selected adapter and stopped state.
- Note adapter name, local IP, date/time and test commands.

## Scope and limitations
- Only frames exposed to the selected adapter are visible.
- The project does not decrypt TLS application data.
- It does not scan remote devices or inject packets.
- Alert rules are educational heuristics; false positives are possible.
- Packet Tracer Simulation Mode is not automatically captured by Scapy on the laptop. Treat Packet Tracer and local Wireshark/Scapy captures as separate evidence unless a PCAP export or bridged capture path is used.

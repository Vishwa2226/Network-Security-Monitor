"""Packet normalization and conservative educational traffic heuristics."""
from collections import Counter, defaultdict, deque
from datetime import datetime
from threading import Lock
import time

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.dns import DNS
from scapy.layers.l2 import ARP


class PacketAnalyzer:
    def __init__(self, emit):
        self.emit = emit
        self.lock = Lock()
        self.total = 0
        self.bytes_total = 0
        self.protocols = Counter()
        self.sources = Counter()
        self.destinations = Counter()
        self.recent = deque(maxlen=120)
        self.rate_window = deque()
        self.syn_events = defaultdict(deque)
        self.cooldowns = {}
        self.alerts_total = 0
        self.alert_log = deque(maxlen=30)
        self.started = time.time()

    def _alert(self, key, severity, title, detail):
        now = time.time()
        if now - self.cooldowns.get(key, 0) < 15:
            return
        self.cooldowns[key] = now
        alert = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "severity": severity,
            "title": title,
            "detail": detail,
        }
        self.alerts_total += 1
        self.alert_log.appendleft(alert)
        self.emit("alert", alert)

    def process(self, packet):
        now = time.time()
        src = dst = "—"
        sport = dport = None
        flags = "—"
        proto = "OTHER"

        if IP in packet:
            ip = packet[IP]
            src, dst = ip.src, ip.dst
            if TCP in packet:
                tcp = packet[TCP]
                proto = "TCP"
                sport, dport = int(tcp.sport), int(tcp.dport)
                flags = str(tcp.flags)
                if "S" in flags and "A" not in flags:
                    events = self.syn_events[src]
                    events.append((now, dport))
                    while events and now - events[0][0] > 10:
                        events.popleft()
                    distinct = len({port for _, port in events})
                    if distinct >= 12:
                        self._alert(
                            "scan:" + src, "warning", "Possible port-scan pattern",
                            f"{src} sent SYN packets to {distinct} distinct destination ports within 10 seconds. This heuristic is not proof of an attack."
                        )
                    elif len(events) >= 30:
                        self._alert(
                            "syn:" + src, "info", "High SYN activity",
                            f"{src} generated {len(events)} SYN attempts within 10 seconds."
                        )
            elif UDP in packet:
                proto = "UDP"
                sport, dport = int(packet[UDP].sport), int(packet[UDP].dport)
                if DNS in packet:
                    proto = "DNS"
            elif ICMP in packet:
                proto = "ICMP"
        elif ARP in packet:
            proto = "ARP"
            src, dst = packet[ARP].psrc, packet[ARP].pdst

        size = len(packet)
        entry = {
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "protocol": proto, "source": src, "destination": dst,
            "source_port": sport, "destination_port": dport,
            "length": size, "flags": flags,
        }
        with self.lock:
            self.total += 1
            self.bytes_total += size
            self.protocols[proto] += 1
            if src != "—":
                self.sources[src] += 1
            if dst != "—":
                self.destinations[dst] += 1
            self.recent.appendleft(entry)
            self.rate_window.append((now, size))
            while self.rate_window and now - self.rate_window[0][0] > 5:
                self.rate_window.popleft()

        self.emit("packet", entry)
        if self.total % 5 == 0:
            self.emit("stats", self.snapshot())

    def snapshot(self):
        with self.lock:
            now = time.time()
            while self.rate_window and now - self.rate_window[0][0] > 5:
                self.rate_window.popleft()
            pps = len(self.rate_window) / 5.0
            bps = sum(size for _, size in self.rate_window) * 8 / 5.0
            return {
                "total_packets": self.total,
                "total_bytes": self.bytes_total,
                "pps": round(pps, 1),
                "kbps": round(bps / 1000, 2),
                "protocols": dict(self.protocols),
                "top_sources": self.sources.most_common(6),
                "top_destinations": self.destinations.most_common(6),
                "alerts_total": self.alerts_total,
                "uptime": int(now - self.started),
                "recent": list(self.recent)[:20],
                "alerts": list(self.alert_log),
            }

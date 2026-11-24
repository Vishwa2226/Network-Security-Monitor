"""Scapy/Npcap interface discovery and live capture manager."""
from threading import Lock
from scapy.all import AsyncSniffer, conf, get_if_addr


class CaptureManager:
    def __init__(self, analyzer, emit):
        self.analyzer = analyzer
        self.emit = emit
        self.sniffer = None
        self.running = False
        self.interface = None
        self.lock = Lock()

    def interfaces(self):
        result = []
        try:
            devices = list(conf.ifaces.values())
        except Exception:
            devices = []
        for dev in devices:
            # network_name is the Npcap device path accepted by Scapy on Windows.
            handle = getattr(dev, "network_name", None) or getattr(dev, "name", None)
            if not handle:
                continue
            try:
                ip = get_if_addr(handle) or "0.0.0.0"
            except Exception:
                ip = getattr(dev, "ip", None) or "0.0.0.0"
            name = getattr(dev, "description", None) or getattr(dev, "name", None) or str(handle)
            result.append({"id": str(handle), "name": str(name), "ip": str(ip)})
        result.sort(key=lambda item: (
            item["ip"] in ("0.0.0.0", "127.0.0.1"),
            item["name"].lower()
        ))
        return result

    def start(self, interface):
        with self.lock:
            if self.running:
                return False, "Capture is already running."
            if interface not in {item["id"] for item in self.interfaces()}:
                return False, "Selected interface is not available. Refresh the dashboard."
            try:
                sniffer = AsyncSniffer(iface=interface, prn=self.analyzer.process, store=False)
                sniffer.start()
                self.sniffer = sniffer
                self.interface = interface
                self.running = True
            except Exception as exc:
                self.sniffer = None
                self.running = False
                return False, f"Could not start capture: {exc}"
        self.emit("capture_status", {
            "running": True, "interface": interface, "message": "Capture started"
        })
        return True, "Capture started."

    def stop(self):
        with self.lock:
            if not self.running:
                return True, "Capture is already stopped."
            sniffer = self.sniffer
            self.running = False
            self.sniffer = None
        try:
            if sniffer and sniffer.running:
                sniffer.stop()
        except Exception as exc:
            self.emit("capture_status", {
                "running": False, "message": f"Stopped with warning: {exc}"
            })
            return False, str(exc)
        self.emit("capture_status", {"running": False, "message": "Capture stopped"})
        return True, "Capture stopped."

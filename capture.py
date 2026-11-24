"""Scapy/Npcap interface discovery and live capture worker."""
from scapy.all import AsyncSniffer, get_if_list, get_if_addr, conf


class CaptureManager:
    def __init__(self, analyzer, emit):
        self.analyzer = analyzer
        self.emit = emit
        self.sniffer = None
        self.running = False
        self.interface = None

    def interfaces(self):
        result = []
        descriptions = {}
        try:
            for dev in conf.ifaces.values():
                name = getattr(dev, "name", "")
                description = getattr(dev, "description", "") or name
                descriptions[name] = description
        except Exception:
            pass

        for iface in get_if_list():
            try:
                ip = get_if_addr(iface) or "0.0.0.0"
            except Exception:
                ip = "0.0.0.0"
            result.append({
                "id": iface,
                "name": descriptions.get(iface, iface),
                "ip": ip,
            })
        result.sort(key=lambda item: (
            item["ip"] in ("0.0.0.0", "127.0.0.1"),
            item["name"].lower()
        ))
        return result

    def start(self, interface):
        if self.running:
            return False, "Capture is already running."
        if interface not in {item["id"] for item in self.interfaces()}:
            return False, "Selected interface is not available. Refresh the interface list."
        try:
            self.sniffer = AsyncSniffer(
                iface=interface,
                prn=self.analyzer.process,
                store=False,
                promisc=True,
            )
            self.sniffer.start()
            self.interface = interface
            self.running = True
            self.emit("capture_status", {
                "running": True, "interface": interface, "message": "Capture started"
            })
            return True, "Capture started."
        except Exception as exc:
            self.sniffer = None
            self.running = False
            return False, f"Could not start capture: {exc}"

    def stop(self):
        if not self.running:
            return True, "Capture is already stopped."
        sniffer = self.sniffer
        self.running = False
        self.sniffer = None
        try:
            if sniffer and sniffer.running:
                sniffer.stop()
        except Exception as exc:
            self.emit("capture_status", {"running": False, "message": f"Stopped with warning: {exc}"})
            return False, str(exc)
        self.emit("capture_status", {"running": False, "message": "Capture stopped"})
        return True, "Capture stopped."

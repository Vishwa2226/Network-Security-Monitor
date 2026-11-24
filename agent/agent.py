"""Windows Npcap sensor that connects outbound to the hosted dashboard."""
from pathlib import Path
import secrets
import sys
import threading
import time

import socketio

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyzer import PacketAnalyzer
from capture import CaptureManager

HERE = Path(__file__).resolve().parent
TOKEN_FILE = HERE / "pairing_token.txt"
URL_FILE = HERE / "dashboard_url.txt"


def load_token():
    if TOKEN_FILE.exists():
        value = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            return value
    value = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(value, encoding="utf-8")
    return value


def load_dashboard_url():
    saved = URL_FILE.read_text(encoding="utf-8").strip() if URL_FILE.exists() else ""
    if saved:
        return saved.rstrip("/")
    value = input("\nPaste the hosted dashboard URL (https://...): ").strip().rstrip("/")
    if not value.startswith("https://"):
        raise ValueError("Use your HTTPS hosted dashboard URL.")
    URL_FILE.write_text(value, encoding="utf-8")
    return value


def main():
    token = load_token()
    print("\nNETWORK SECURITY MONITOR - WINDOWS SENSOR")
    print("------------------------------------------")
    print("Private pairing token (paste into your dashboard):")
    print(token)
    print("\nKeep this token secret. Do not post it in GitHub or screenshots.")

    dashboard_url = load_dashboard_url()
    client = socketio.Client(
        reconnection=True,
        logger=False,
        engineio_logger=False,
        ssl_verify=True,
    )

    analyzer = PacketAnalyzer(
        lambda event, data: client.emit("agent_" + event, data) if client.connected else None
    )
    capture = CaptureManager(
        analyzer,
        lambda event, data: client.emit("agent_capture_status", data) if client.connected else None,
    )
    stop_heartbeat = threading.Event()

    @client.event
    def connect():
        print("Connected to hosted dashboard.")
        client.emit("agent_interfaces", capture.interfaces())
        client.emit("agent_stats", analyzer.snapshot())

    @client.event
    def disconnect():
        print("Dashboard connection closed. Trying to reconnect…")
        if capture.running:
            capture.stop()

    @client.on("control_start")
    def on_start(data):
        interface = (data or {}).get("interface", "")
        ok, message = capture.start(interface)
        print(message)
        if not ok and client.connected:
            client.emit("agent_capture_status", {"running": False, "message": message})

    @client.on("control_stop")
    def on_stop(data=None):
        ok, message = capture.stop()
        print(message)

    @client.on("connect_error")
    def on_connect_error(data):
        print("Connection error:", data)

    def heartbeat():
        while not stop_heartbeat.wait(5):
            if client.connected:
                client.emit("agent_stats", analyzer.snapshot())

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()

    print("\nConnecting to:", dashboard_url)
    try:
        client.connect(
            dashboard_url,
            auth={"token": token, "role": "agent"},
            transports=["websocket", "polling"],
            wait_timeout=30,
        )
        print("Helper ready. Keep this window open; you can minimise it.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping helper…")
    except Exception as exc:
        print("\nCould not connect:", exc)
        print("Check the dashboard URL and make sure the hosted service has deployed.")
    finally:
        stop_heartbeat.set()
        if capture.running:
            capture.stop()
        if client.connected:
            client.disconnect()
        try:
            input("Press Enter to close this window...")
        except EOFError:
            pass


if __name__ == "__main__":
    main()

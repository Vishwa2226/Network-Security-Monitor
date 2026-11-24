"""Local Flask-SocketIO application."""
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO
from analyzer import PacketAnalyzer
from capture import CaptureManager

app = Flask(__name__)
app.config["SECRET_KEY"] = "local-network-monitor"
socketio = SocketIO(app, async_mode="threading")

analyzer = PacketAnalyzer(lambda event, data: socketio.emit(event, data))
capture = CaptureManager(analyzer, lambda event, data: socketio.emit(event, data))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/interfaces")
def api_interfaces():
    return jsonify({"interfaces": capture.interfaces()})


@app.get("/api/status")
def api_status():
    return jsonify({
        "running": capture.running,
        "interface": capture.interface,
        "stats": analyzer.snapshot(),
    })


@app.post("/api/start")
def api_start():
    body = request.get_json(silent=True) or {}
    ok, message = capture.start(body.get("interface", ""))
    return jsonify({"ok": ok, "message": message}), (200 if ok else 400)


@app.post("/api/stop")
def api_stop():
    ok, message = capture.stop()
    return jsonify({"ok": ok, "message": message}), (200 if ok else 500)


@socketio.on("connect")
def on_connect():
    socketio.emit("stats", analyzer.snapshot())
    socketio.emit("capture_status", {
        "running": capture.running, "interface": capture.interface
    })


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=False, allow_unsafe_werkzeug=True)

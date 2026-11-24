"""Hosted dashboard relay. Only paired agents can publish telemetry."""
import os
import secrets
from hashlib import sha256
from threading import RLock

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
socketio = SocketIO(app, async_mode="eventlet")

lock = RLock()
sessions = {}          # SID -> {room, role}
agents = {}            # hashed room -> agent SID
interface_cache = {}   # hashed room -> latest interface list
stats_cache = {}       # hashed room -> most recent stats snapshot
capture_status_cache = {}  # hashed room -> most recent capture status


def session_room(token):
    return "monitor_" + sha256(token.encode("utf-8")).hexdigest()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "network-security-monitor"})


@socketio.on("connect")
def on_connect(auth=None):
    auth = auth or {}
    token = auth.get("token")
    role = auth.get("role")
    if not isinstance(token, str) or len(token) < 32 or role not in ("agent", "viewer"):
        return False

    room = session_room(token)
    sid = request.sid
    with lock:
        if role == "agent":
            current = agents.get(room)
            if current and current != sid:
                return False
            agents[room] = sid
            interface_cache.pop(room, None)
            stats_cache.pop(room, None)
            capture_status_cache[room] = {"running": False, "message": "Helper connected"}
        sessions[sid] = {"room": room, "role": role}

    join_room(room)
    if role == "viewer":
        with lock:
            online = room in agents
            interfaces = interface_cache.get(room, [])
            stats = stats_cache.get(room)
            capture_status = capture_status_cache.get(room)
        emit("agent_status", {"online": online})
        if interfaces:
            emit("interfaces", interfaces)
        if stats:
            emit("stats", stats)
        if capture_status:
            emit("capture_status", capture_status)
    else:
        socketio.emit("agent_status", {"online": True}, to=room)
    return True


@socketio.on("disconnect")
def on_disconnect(reason=None):
    sid = request.sid
    with lock:
        info = sessions.pop(sid, None)
        if info and info["role"] == "agent" and agents.get(info["room"]) == sid:
            agents.pop(info["room"], None)
            interface_cache.pop(info["room"], None)
            room = info["room"]
        else:
            room = None
    if room:
        socketio.emit("agent_status", {"online": False}, to=room)


def authenticated_agent_room():
    info = sessions.get(request.sid)
    return info["room"] if info and info["role"] == "agent" else None


@socketio.on("agent_interfaces")
def on_agent_interfaces(items):
    room = authenticated_agent_room()
    if not room:
        return
    safe_items = items if isinstance(items, list) else []
    with lock:
        interface_cache[room] = safe_items[:40]
    socketio.emit("interfaces", safe_items[:40], to=room)


@socketio.on("agent_packet")
def on_agent_packet(data):
    room = authenticated_agent_room()
    if room and isinstance(data, dict):
        socketio.emit("packet", data, to=room)


@socketio.on("agent_stats")
def on_agent_stats(data):
    room = authenticated_agent_room()
    if room and isinstance(data, dict):
        with lock:
            stats_cache[room] = data
        socketio.emit("stats", data, to=room)


@socketio.on("agent_alert")
def on_agent_alert(data):
    room = authenticated_agent_room()
    if room and isinstance(data, dict):
        socketio.emit("alert", data, to=room)


@socketio.on("agent_capture_status")
def on_agent_capture_status(data):
    room = authenticated_agent_room()
    if room and isinstance(data, dict):
        with lock:
            capture_status_cache[room] = data
        socketio.emit("capture_status", data, to=room)


@socketio.on("request_start")
def on_request_start(data):
    info = sessions.get(request.sid)
    if not info or info["role"] != "viewer":
        return
    room = info["room"]
    with lock:
        agent_sid = agents.get(room)
        known_interfaces = {i.get("id") for i in interface_cache.get(room, []) if isinstance(i, dict)}
    interface = (data or {}).get("interface") if isinstance(data, dict) else None
    if not agent_sid:
        emit("control_error", {"message": "Capture helper is offline. Start the Windows helper first."})
    elif not isinstance(interface, str) or interface not in known_interfaces:
        emit("control_error", {"message": "Choose an available network adapter."})
    else:
        socketio.emit("control_start", {"interface": interface}, to=agent_sid)


@socketio.on("request_stop")
def on_request_stop():
    info = sessions.get(request.sid)
    if not info or info["role"] != "viewer":
        return
    with lock:
        agent_sid = agents.get(info["room"])
    if agent_sid:
        socketio.emit("control_stop", {}, to=agent_sid)
    else:
        emit("control_error", {"message": "Capture helper is offline."})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)

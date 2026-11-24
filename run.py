"""Run the local Network Security Monitor dashboard."""
import os
from app import app, socketio

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.getenv("PORT", "5000"))
    print(f"Network Security Monitor: http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

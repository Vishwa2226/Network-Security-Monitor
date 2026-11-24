"""Local development server for the hosted dashboard."""
import os
from app import socketio, app

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)

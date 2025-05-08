from flask import Flask, request
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/api/games", methods=["POST"])
def create_game():
    print("Game created")
    return {"message": "Game created"}

if __name__ == '__main__':
    socketio.run(app)
import eventlet
eventlet.monkey_patch()

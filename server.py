import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/api/games", methods=["POST"])
def create_game():
    print("Game created")
    return {"message": "Game created"}

if __name__ == '__main__':
    socketio.run(app)

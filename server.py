from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Reitti pelin luomiseen
@app.route("/api/games", methods=["POST"])
def create_game():
    print("Game created")
    return {"message": "Game created"}

# Pelin reitti
@app.route("/game")
def game():
    return render_template("game.html")  # Tämä lataa pelin sivun

# Etusivun reitti
@app.route('/')
def home():
    return render_template('index.html')  # Tämä näyttää HTML-tiedoston

# WebSocket-viestintä, esim. peliin liittymisen käsittely
@socketio.on('join_game')
def handle_join_game(data):
    print(f"Player joined: {data['player_name']}")
    emit('game_update', {'message': f"{data['player_name']} joined the game!"})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=10000)  # Ajetaan palvelin portissa 10000

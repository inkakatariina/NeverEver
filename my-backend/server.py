
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Lisää CORS-asetus

# Reitti pelin luomiseen
@app.route("/api/games", methods=["POST"])
def create_game():
    # Tässä voit luoda pelihuoneen tai muita pelin aloituslogiikoita
    print("Game created")
    return jsonify({"message": "Game created"}), 201  # Käytetään jsonify-tarkoitusta

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
    player_name = data.get('player_name')
    
    if player_name:
        print(f"Player joined: {player_name}")
        emit('game_update', {'message': f"{player_name} joined the game!"}, broadcast=True)  # Lähetetään kaikille
    else:
        emit('game_update', {'message': 'Player name is required!'})  # Virheellinen data

# Lisätään peliin liittyminen huoneeseen (join room)
@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    player_name = data.get('player_name')
    
    if room and player_name:
        join_room(room)
        emit('game_update', {'message': f"{player_name} has joined the room {room}."}, room=room)  # Lähetetään vain huoneeseen
    else:
        emit('game_update', {'message': 'Room and player name are required!'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=10000)  # Ajetaan palvelin portissa 10000

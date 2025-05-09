from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room, emit
import os
import json
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Load game questions from JSON file
with open('data.json', 'r') as file:
    data = json.load(file)
    questions = data['questions']

# Store game rooms
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/<room_id>')
def game(room_id):
    if room_id not in rooms:
        return "Room not found", 404
    return render_template('game.html', room_id=room_id)

@app.route('/api/create-room', methods=['POST'])
def create_room():
    room_id = generate_room_id()
    rooms[room_id] = {
        'players': [],
        'current_question_index': 0,
        'questions': random.sample(questions, 30)  # Select 30 random questions
    }
    return jsonify({'room_id': room_id})

def generate_room_id():
    while True:
        room_id = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        if room_id not in rooms:
            return room_id

@socketio.on('join')
def on_join(data):
    username = data['username']
    room_id = data['room']
    
    if room_id not in rooms:
        emit('error', {'message': 'Room not found'})
        return
    
    join_room(room_id)
    rooms[room_id]['players'].append({'username': username, 'id': request.sid})
    
    emit('room_update', {'players': [p['username'] for p in rooms[room_id]['players']]}, room=room_id)
    emit('joined', {'username': username}, room=room_id)

@socketio.on('start_game')
def on_start_game(data):
    room_id = data['room']
    if room_id in rooms:
        rooms[room_id]['current_question_index'] = 0
        emit('game_started', room=room_id)
        send_next_question(room_id)

@socketio.on('next_question')
def on_next_question(data):
    room_id = data['room']
    if room_id in rooms:
        send_next_question(room_id)

def send_next_question(room_id):
    room = rooms[room_id]
    if room['current_question_index'] < len(room['questions']):
        question = room['questions'][room['current_question_index']]
        room['current_question_index'] += 1
        emit('new_question', {
            'question': question,
            'question_number': room['current_question_index'],
            'total_questions': len(room['questions'])
        }, room=room_id)
    else:
        emit('game_over', room=room_id)

@socketio.on('disconnect')
def on_disconnect():
    for room_id in list(rooms.keys()):
        room = rooms[room_id]
        for i, player in enumerate(room['players']):
            if player['id'] == request.sid:
                username = player['username']
                room['players'].pop(i)
                emit('player_left', {'username': username}, room=room_id)
                emit('room_update', {'players': [p['username'] for p in room['players']]}, room=room_id)
                
                # Remove empty rooms
                if not room['players']:
                    rooms.pop(room_id)
                break

if __name__ == '__main__':
    socketio.run(app, debug=True)

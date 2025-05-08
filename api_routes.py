from flask import Blueprint, request, jsonify
from db_utils import (
    create_game, add_player, add_questions_to_game, 
    record_answer, get_game_players, get_question_answers,
    mark_game_inactive
)
import json

api = Blueprint('api', __name__)

@api.route('/games', methods=['POST'])
def create_new_game():
    data = request.json
    host_id = data.get('host_id')
    host_name = data.get('host_name')
    game_modes = data.get('game_modes', [])
    
    if not host_id or not host_name or not game_modes:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    game = create_game(host_id, host_name, game_modes)
    
    return jsonify({
        'id': game.id,
        'host_id': game.host_id,
        'game_modes': game.game_modes.split(',')
    }), 201

@api.route('/games/<game_id>/players', methods=['POST'])
def join_game(game_id):
    data = request.json
    player_id = data.get('player_id')
    player_name = data.get('player_name')
    
    if not player_id or not player_name:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    player = add_player(game_id, player_id, player_name)
    
    return jsonify({
        'id': player.id,
        'name': player.name,
        'game_id': player.game_id,
        'is_host': player.is_host
    }), 201

@api.route('/games/<game_id>/questions', methods=['POST'])
def add_game_questions(game_id):
    data = request.json
    questions = data.get('questions', [])
    
    if not questions:
        return jsonify({'error': 'No questions provided'}), 400
    
    add_questions_to_game(game_id, questions)
    
    return jsonify({'success': True}), 201

@api.route('/answers', methods=['POST'])
def submit_answer():
    data = request.json
    player_id = data.get('player_id')
    question_id = data.get('question_id')
    answer_value = data.get('answer')
    
    if player_id is None or question_id is None or answer_value is None:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    answer = record_answer(player_id, question_id, answer_value)
    
    return jsonify({
        'id': answer.id,
        'player_id': answer.player_id,
        'question_id': answer.question_id,
        'answer': answer.answer
    }), 201

@api.route('/games/<game_id>/end', methods=['POST'])
def end_game(game_id):
    success = mark_game_inactive(game_id)
    
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Game not found'}), 404
import os
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_socketio import SocketIO
from models import db, Game, Player, Question, Answer
from api_routes import api
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure DATABASE_URL is properly formatted for SQLAlchemy
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///neverhaveiever.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key')

# Initialize database
db.init_app(app)

# Register the API blueprint
app.register_blueprint(api, url_prefix='/api')

# Initialize Socket.IO with CORS allowed
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Import socket event handlers
from socket_events import register_socket_events
register_socket_events(socketio)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

# API endpoints for database interaction
@app.route('/api/games', methods=['GET'])
def get_games():
    games = Game.query.filter_by(is_active=True).all()
    result = [{
        'id': game.id,
        'created_at': game.created_at,
        'player_count': len(game.players)
    } for game in games]
    return jsonify(result)

@app.route('/api/games/<game_id>', methods=['GET'])
def get_game(game_id):
    game = Game.query.get_or_404(game_id)
    result = {
        'id': game.id,
        'host_id': game.host_id,
        'created_at': game.created_at,
        'is_active': game.is_active,
        'game_modes': game.game_modes,
        'players': [{
            'id': player.id,
            'name': player.name,
            'is_host': player.is_host
        } for player in game.players]
    }
    return jsonify(result)

@app.route('/api/games/<game_id>/questions', methods=['GET'])
def get_game_questions(game_id):
    game = Game.query.get_or_404(game_id)
    questions = Question.query.filter_by(game_id=game_id).order_by(Question.order_index).all()
    result = [{
        'id': question.id,
        'text': question.text,
        'category': question.category,
        'order_index': question.order_index
    } for question in questions]
    return jsonify(result)

@app.route('/api/questions/<question_id>/answers', methods=['GET'])
def get_question_answers(question_id):
    answers = Answer.query.filter_by(question_id=question_id).all()
    result = [{
        'id': answer.id,
        'player_id': answer.player_id,
        'player_name': answer.player.name,
        'answer': answer.answer,
        'answered_at': answer.answered_at
    } for answer in answers]
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Tämä vastaa Renderin vaatimia asetuksia

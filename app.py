import os
import logging
from flask import Flask, send_from_directory, jsonify
from flask_socketio import SocketIO
from models import db, Game, Player, Question, Answer
from api_routes import api

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, static_folder='.', static_url_path='')

# DATABASE URL - PostgreSQL fix for SQLAlchemy
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///neverhaveiever.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key')

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Register API routes
app.register_blueprint(api, url_prefix='/api')

# Register socket events
from socket_events import register_socket_events
register_socket_events(socketio)

# Ensure database tables are created
with app.app_context():
    db.create_all()

# Serve the index.html for the root
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve other files (e.g., JS/CSS from root)
@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

# API: Get active games
@app.route('/api/games', methods=['GET'])
def get_games():
    games = Game.query.filter_by(is_active=True).all()
    result = [{
        'id': game.id,
        'created_at': game.created_at,
        'player_count': len(game.players)
    } for game in games]
    return jsonify(result)

# API: Get single game by ID
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

# API: Get questions for a game
@app.route('/api/games/<game_id>/questions', methods=['GET'])
def get_game_questions(game_id):
    _ = Game.query.get_or_404(game_id)
    questions = Question.query.filter_by(game_id=game_id).order_by(Question.order_index).all()
    result = [{
        'id': q.id,
        'text': q.text,
        'category': q.category,
        'order_index': q.order_index
    } for q in questions]
    return jsonify(result)

# API: Get answers for a question
@app.route('/api/questions/<question_id>/answers', methods=['GET'])
def get_question_answers(question_id):
    answers = Answer.query.filter_by(question_id=question_id).all()
    result = [{
        'id': a.id,
        'player_id': a.player_id,
        'player_name': a.player.name,
        'answer': a.answer,
        'answered_at': a.answered_at
    } for a in answers]
    return jsonify(result)

# Main entry point - use SocketIO to run the app
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)

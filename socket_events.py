from flask_socketio import emit, join_room, leave_room
from models import db, Game, Player, Question, Answer
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def register_socket_events(socketio):
    """
    Register all socket.io event handlers
    """
    @socketio.on('connect')
    def handle_connect():
        logger.debug("Client connected")
        emit('connection_response', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.debug("Client disconnected")

    @socketio.on('join_game')
    def handle_join_game(data):
        """Handle a player joining a game"""
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        if not game_id or not player_id:
            emit('error', {'message': 'Missing game_id or player_id'})
            return
        
        logger.debug(f"Player {player_id} joining game {game_id}")
        
        # Join the socket.io room for this game
        join_room(game_id)
        
        try:
            # Get the game and player from the database
            game = Game.query.get(game_id)
            player = Player.query.get(player_id)
            
            if not game:
                emit('error', {'message': 'Game not found'})
                return
                
            if not player:
                emit('error', {'message': 'Player not found'})
                return
            
            # Get list of all players in the game
            players = Player.query.filter_by(game_id=game_id).all()
            player_list = [{
                'id': p.id,
                'name': p.name,
                'is_host': p.is_host
            } for p in players]
            
            # Notify all clients in the room that a new player joined
            emit('player_joined', {
                'player': {
                    'id': player.id,
                    'name': player.name,
                    'is_host': player.is_host
                },
                'players': player_list
            }, to=game_id)
            
            # Send the player a welcome message
            emit('join_success', {
                'game_id': game_id,
                'players': player_list,
                'is_host': player.is_host
            })
            
            logger.debug(f"Player {player.name} joined game {game_id} successfully")
            
        except Exception as e:
            logger.error(f"Error in join_game: {str(e)}")
            emit('error', {'message': f'Server error: {str(e)}'})
    
    @socketio.on('start_game')
    def handle_start_game(data):
        """Start a game (host only)"""
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        
        if not game_id or not player_id:
            emit('error', {'message': 'Missing game_id or player_id'})
            return
        
        try:
            # Check if player is the host
            player = Player.query.get(player_id)
            if not player or not player.is_host:
                emit('error', {'message': 'Only the host can start the game'})
                return
            
            # Get first question
            question = Question.query.filter_by(game_id=game_id).order_by(Question.order_index).first()
            if not question:
                emit('error', {'message': 'No questions found for this game'})
                return
            
            # Notify all players that the game has started
            emit('game_started', {
                'question': {
                    'id': question.id,
                    'text': question.text,
                    'category': question.category
                }
            }, to=game_id)
            
            logger.debug(f"Game {game_id} started by host {player.name}")
            
        except Exception as e:
            logger.error(f"Error in start_game: {str(e)}")
            emit('error', {'message': f'Server error: {str(e)}'})
    
    @socketio.on('submit_answer')
    def handle_submit_answer(data):
        """Submit an answer to a question"""
        player_id = data.get('player_id')
        question_id = data.get('question_id')
        answer_value = data.get('answer')
        game_id = data.get('game_id')
        
        if player_id is None or question_id is None or answer_value is None or not game_id:
            emit('error', {'message': 'Missing required parameters'})
            return
        
        # Record the answer
        try:
            # Get the player and question to verify they exist
            player = Player.query.get(player_id)
            question = Question.query.get(question_id)
            
            if not player or not question:
                emit('error', {'message': 'Player or question not found'})
                return
            
            # Check if player has already answered
            existing_answer = Answer.query.filter_by(
                player_id=player_id,
                question_id=question_id
            ).first()
            
            if existing_answer:
                # Update existing answer
                existing_answer.answer = answer_value
                db.session.commit()
            else:
                # Create new answer
                answer = Answer(
                    player_id=player_id,
                    question_id=question_id,
                    answer=answer_value
                )
                db.session.add(answer)
                db.session.commit()
            
            # Get all answers for this question
            all_answers = Answer.query.filter_by(question_id=question_id).all()
            answer_data = [{
                'player_id': ans.player_id,
                'player_name': ans.player.name,
                'answer': ans.answer
            } for ans in all_answers]
            
            # Notify all players in the game about the new answer
            emit('answer_submitted', {
                'player_id': player_id,
                'player_name': player.name,
                'question_id': question_id,
                'answer': answer_value,
                'all_answers': answer_data
            }, to=game_id)
            
            logger.debug(f"Player {player.name} answered question {question_id}")
            
        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            emit('error', {'message': f'Error submitting answer: {str(e)}'})
    
    @socketio.on('next_question')
    def handle_next_question(data):
        """Move to the next question (host only)"""
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        current_question_id = data.get('current_question_id')
        
        if not game_id or not player_id or not current_question_id:
            emit('error', {'message': 'Missing required parameters'})
            return
        
        try:
            # Check if player is the host
            player = Player.query.get(player_id)
            if not player or not player.is_host:
                emit('error', {'message': 'Only the host can move to the next question'})
                return
            
            # Get current question to find its order_index
            current_question = Question.query.get(current_question_id)
            if not current_question:
                emit('error', {'message': 'Current question not found'})
                return
            
            # Get next question
            next_question = Question.query.filter(
                Question.game_id == game_id,
                Question.order_index > current_question.order_index
            ).order_by(Question.order_index).first()
            
            if not next_question:
                # No more questions, game is over
                emit('game_over', {}, to=game_id)
                logger.debug(f"Game {game_id} is over, no more questions")
                return
            
            # Notify all players about the new question
            emit('new_question', {
                'question': {
                    'id': next_question.id,
                    'text': next_question.text,
                    'category': next_question.category
                }
            }, to=game_id)
            
            logger.debug(f"Game {game_id} moved to next question {next_question.id}")
            
        except Exception as e:
            logger.error(f"Error moving to next question: {str(e)}")
            emit('error', {'message': f'Server error: {str(e)}'})
            
    @socketio.on('error_occurred')
    def handle_error(error):
        """Log client-side errors"""
        logger.error(f"Client error: {error}")
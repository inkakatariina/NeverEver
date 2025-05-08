import random
import string
from models import db, Game, Player, Question, Answer
import logging

logger = logging.getLogger(__name__)

def generate_game_id(length=6):
    """Generate a random uppercase alphanumeric game ID"""
    characters = string.ascii_uppercase + string.digits
    while True:
        game_id = ''.join(random.choice(characters) for _ in range(length))
        # Check if ID already exists
        existing_game = Game.query.get(game_id)
        if not existing_game:
            return game_id

def create_game(host_id, host_name, game_modes):
    """Create a new game in the database"""
    try:
        # Generate unique game ID
        game_id = generate_game_id()
        
        # Convert game modes list to comma-separated string
        modes_string = ','.join(game_modes)
        
        # Create the game
        game = Game(
            id=game_id,
            host_id=host_id,
            game_modes=modes_string
        )
        db.session.add(game)
        db.session.flush()  # Flush to get the game ID
        
        # Create host player
        host = Player(
            id=host_id,
            name=host_name,
            game_id=game.id,
            is_host=True
        )
        db.session.add(host)
        db.session.commit()
        
        logger.debug(f"Created game {game_id} with host {host_name}")
        return game
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating game: {str(e)}")
        raise

def add_player(game_id, player_id, player_name):
    """Add a player to an existing game"""
    try:
        # Check if game exists
        game = Game.query.get(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Check if player already exists
        existing_player = Player.query.get(player_id)
        if existing_player:
            return existing_player
        
        # Create new player
        player = Player(
            id=player_id,
            name=player_name,
            game_id=game_id,
            is_host=False
        )
        db.session.add(player)
        db.session.commit()
        
        logger.debug(f"Added player {player_name} to game {game_id}")
        return player
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding player: {str(e)}")
        raise

def add_questions_to_game(game_id, questions_data):
    """Add questions to a game"""
    try:
        # Check if game exists
        game = Game.query.get(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Add each question with an order index
        for i, q_data in enumerate(questions_data):
            question = Question(
                game_id=game_id,
                text=q_data['text'],
                category=q_data['category'],
                order_index=i
            )
            db.session.add(question)
            
        db.session.commit()
        logger.debug(f"Added {len(questions_data)} questions to game {game_id}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding questions: {str(e)}")
        raise

def record_answer(player_id, question_id, answer_value):
    """Record a player's answer to a question"""
    try:
        # Check if player exists
        player = Player.query.get(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")
        
        # Check if question exists
        question = Question.query.get(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        # Check if answer already exists
        existing_answer = Answer.query.filter_by(
            player_id=player_id,
            question_id=question_id
        ).first()
        
        if existing_answer:
            # Update existing answer
            existing_answer.answer = answer_value
            db.session.commit()
            logger.debug(f"Updated answer for player {player_id} to question {question_id}")
            return existing_answer
        else:
            # Create new answer
            answer = Answer(
                player_id=player_id,
                question_id=question_id,
                answer=answer_value
            )
            db.session.add(answer)
            db.session.commit()
            logger.debug(f"Recorded answer for player {player_id} to question {question_id}")
            return answer
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recording answer: {str(e)}")
        raise

def get_game_players(game_id):
    """Get all players in a game"""
    try:
        players = Player.query.filter_by(game_id=game_id).all()
        return players
    except Exception as e:
        logger.error(f"Error getting game players: {str(e)}")
        return []

def get_question_answers(question_id):
    """Get all answers for a question"""
    try:
        answers = Answer.query.filter_by(question_id=question_id).all()
        return answers
    except Exception as e:
        logger.error(f"Error getting question answers: {str(e)}")
        return []

def mark_game_inactive(game_id):
    """Mark a game as inactive"""
    try:
        game = Game.query.get(game_id)
        if not game:
            return False
        
        game.is_active = False
        db.session.commit()
        logger.debug(f"Marked game {game_id} as inactive")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking game inactive: {str(e)}")
        return False
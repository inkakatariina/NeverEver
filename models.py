from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Game(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    host_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    game_modes = db.Column(db.String(255), nullable=False) # Comma-separated list of modes
    players = db.relationship('Player', backref='game', lazy=True, cascade="all, delete-orphan")
    questions = db.relationship('Question', backref='game', lazy=True, cascade="all, delete-orphan")

class Player(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    game_id = db.Column(db.String(10), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    is_host = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='player', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(10), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(50), db.ForeignKey('player.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id', ondelete='CASCADE'), nullable=False)
    answer = db.Column(db.Boolean, nullable=False)  # True for "I have", False for "I have not"
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
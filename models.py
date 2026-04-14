from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # 'player' or 'coach'
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
class TrainingSession(db.Model):
    __tablename__ = 'training_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # 'gym' or 'field'
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Performance metrics
    bodyweight = db.Column(db.Float, nullable=True)
    bench_press = db.Column(db.Float, nullable=True)
    squat = db.Column(db.Float, nullable=True)
    broad_jump = db.Column(db.Float, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref='training_sessions')
    
    def __repr__(self):
        return f'<Session {self.session_type} on {self.date}>'
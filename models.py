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
    access_code = db.Column(db.String(10), unique=True, nullable=True)  # For players
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def calculate_streak(self):
        """Calculate current training streak"""
        from datetime import date, timedelta
        
        sessions = TrainingSession.query.filter_by(user_id=self.id).order_by(TrainingSession.date.desc()).all()
        
        if not sessions:
            return 0
        
        # Check if most recent session is today or yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)
        most_recent = sessions[0].date
        
        # If last session is older than yesterday, streak is broken
        if most_recent < yesterday:
            return 0
        
        # Count consecutive days
        streak = 0
        expected_date = today if most_recent == today else yesterday
        
        for session in sessions:
            if session.date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            elif session.date < expected_date:
                # Gap found, streak broken
                break
        
        return streak
    
    def get_rank(self):
        """Get rank based on total sessions logged"""
        total_sessions = TrainingSession.query.filter_by(user_id=self.id).count()
        
        if total_sessions >= 365:  # 1 year of training
            return "Hall of Famer"
        elif total_sessions >= 180:  # 6 months consistent
            return "All-Star"
        elif total_sessions >= 90:   # 3 months solid
            return "Pro"
        elif total_sessions >= 30:   # 1 month committed
            return "Starter"
        elif total_sessions >= 10:   # Getting started
            return "Rookie"
        else:
            return "Beginner"
    
    def get_rank_progress(self):
        """Get progress to next rank"""
        total_sessions = TrainingSession.query.filter_by(user_id=self.id).count()
        
        ranks = [
            (10, "Rookie"),
            (30, "Starter"),
            (90, "Pro"),
            (180, "All-Star"),
            (365, "Hall of Famer")
        ]
        
        for i, (threshold, rank_name) in enumerate(ranks):
            if total_sessions < threshold:
                return {
                    'current_rank': ranks[i-1][1] if i > 0 else "Beginner",
                    'next_rank': rank_name,
                    'sessions_needed': threshold - total_sessions,
                    'total_sessions': total_sessions
                }
        
        # Max rank achieved
        return {
            'current_rank': "Hall of Famer",
            'next_rank': None,
            'sessions_needed': 0,
            'total_sessions': total_sessions
        }
    
    def generate_access_code(self):
        """Generate a unique 6-character access code for players"""
        import random
        import string
        
        if self.role != 'player':
            return None
        
        # Generate random 6-character code
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            # Check if code already exists
            existing = User.query.filter_by(access_code=code).first()
            if not existing:
                return code
    
    def get_or_create_access_code(self):
        """Get existing access code or create new one"""
        if self.role != 'player':
            return None
        
        if self.access_code:
            return self.access_code
        
        # Generate and save new code
        self.access_code = self.generate_access_code()
        db.session.commit()
        return self.access_code
    
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


class CoachPlayerAccess(db.Model):
    __tablename__ = 'coach_player_access'
    
    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    coach = db.relationship('User', foreign_keys=[coach_id], backref='my_players')
    player = db.relationship('User', foreign_keys=[player_id], backref='my_coaches')
    
    # Unique constraint: one coach-player pair
    __table_args__ = (db.UniqueConstraint('coach_id', 'player_id', name='unique_coach_player'),)
    
    def __repr__(self):
        return f'<CoachAccess Coach:{self.coach_id} Player:{self.player_id}>'
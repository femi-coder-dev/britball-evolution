from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, TrainingSession
from datetime import date, datetime
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///britball.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        position = request.form.get('position')
        role = request.form.get('role')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            position=position,
            role=role
        )
        new_user.set_password(password)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ User registered successfully: {username}")
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            print(f"✅ User logged in: {user.username}")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return f"<h1>Welcome {current_user.username}!</h1><p>Dashboard coming soon...</p><a href='/log-session'>Log Session</a> | <a href='/logout'>Logout</a>"

@app.route('/log-session', methods=['GET', 'POST'])
@login_required
def log_session():
    if request.method == 'POST':
        session_type = request.form.get('session_type')
        session_date_str = request.form.get('date')
        notes = request.form.get('notes')
        
        # Convert string date to date object
        session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
        
        # Get optional metrics
        bodyweight = request.form.get('bodyweight')
        bench_press = request.form.get('bench_press')
        squat = request.form.get('squat')
        broad_jump = request.form.get('broad_jump')
        
        # Create new training session
        new_session = TrainingSession(
            user_id=current_user.id,
            session_type=session_type,
            date=session_date,
            notes=notes,
            bodyweight=float(bodyweight) if bodyweight else None,
            bench_press=float(bench_press) if bench_press else None,
            squat=float(squat) if squat else None,
            broad_jump=float(broad_jump) if broad_jump else None
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        print(f"✅ Session logged: {session_type} on {session_date} by {current_user.username}")
        flash('Session logged successfully! Keep it up! 🔥', 'success')
        return redirect(url_for('dashboard'))
    
    # For GET request, pass today's date to template
    today = date.today().isoformat()
    return render_template('log_session.html', today=today)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
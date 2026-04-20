from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, TrainingSession, CoachPlayerAccess
from datetime import date, datetime
import os
import random

MOTIVATIONAL_QUOTES = [
    "Consistency beats intensity every time.",
    "Another session. Another step forward.",
    "The grind is the glory.",
    "Champions are built in the off-season.",
    "Every rep counts. Every session matters.",
    "No shortcuts. No excuses. Just work.",
    "The best athletes are the most consistent ones.",
    "Progress is progress, no matter how small.",
    "Philippians 4:13:I can do all things through Christ who strengthens me.",
    "Deuteronomy 31:6: Be strong and courageous. Do not fear or be in dread of them, for it is the Lord your God who goes with you. He will not leave you or forsake you.",
    "Galatians 6:9: And let us not grow weary of doing good, for in due season we will reap, if we do not give up.",
    "Joshua 1:9: Be strong and courageous. Do not be afraid.",
    "James 1:12: Blessed is the one who perseveres under trial.",
    " Proverbs 27:17: “As iron sharpens iron, so one person sharpens another.",
    "Hard work beats talent when talent doesn’t work hard.",
    "It’s not whether you get knocked down; it’s whether you get up.",
    "Success is not final, failure is not fatal: It is the courage to continue that counts.",
    "The only place where success comes before work is in the dictionary.",
    "Don’t watch the clock; do what it does. Keep going.",
    "Winners never quit, and quitters never win.",
    "The difference between the impossible and the possible lies in a person’s determination.",
    "You miss 100% of the shots you don’t take.",
    "The harder the battle, the sweeter the victory.",
    "Success usually comes to those who are too busy to be looking for it.",
    "Don’t be afraid to give up the good to go for the great.",
    "Most people give up just when they’re about to achieve success. They quit on the one yard line.",
    "I find that the harder I work, the more luck I seem to have.",
    "Focus on your goals, not the obstacles",

]

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-fallback-key-not-for-production')
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
        existing_username = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('register'))

        if existing_username:
            flash('Username already taken. Please choose another.', 'error')
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
    # Redirect coaches to coach dashboard
    if current_user.role == 'coach':
        return redirect(url_for('coach_dashboard'))
    
    # Player dashboard
    streak = current_user.calculate_streak()
    rank = current_user.get_rank()
    rank_progress = current_user.get_rank_progress()
    
    # Get or create access code
    access_code = current_user.get_or_create_access_code()
    
    # Get recent sessions (last 10)
    recent_sessions = TrainingSession.query.filter_by(user_id=current_user.id)\
        .order_by(TrainingSession.date.desc())\
        .limit(10)\
        .all()
    
    return render_template('dashboard.html', 
                         streak=streak,
                         rank=rank,
                         rank_progress=rank_progress,
                         access_code=access_code,
                         recent_sessions=recent_sessions)

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

        # NFR08 - Input validation for performance metrics
        def validate_metric(value, min_val, max_val, name):
            if value:
                try:
                    f = float(value)
                    if f <= min_val or f > max_val:
                        return f'{name} must be between {min_val} and {max_val}.'
                except ValueError:
                    return f'{name} must be a valid number.'
            return None

        errors = [
            validate_metric(bodyweight, 0, 500, 'Bodyweight'),
            validate_metric(bench_press, 0, 500, 'Bench press'),
            validate_metric(squat, 0, 500, 'Squat'),
            validate_metric(broad_jump, 0, 1000, 'Broad jump'),
        ]
        errors = [e for e in errors if e]

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('log_session'))

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
        flash('Session logged successfully! Keep it up!', 'success')
        flash(random.choice(MOTIVATIONAL_QUOTES), 'motivation')
        return redirect(url_for('dashboard'))
    
    # For GET request, pass today's date to template
    today = date.today().isoformat()
    return render_template('log_session.html', today=today)

@app.route('/coach/dashboard')
@login_required
def coach_dashboard():
    # Check if user is a coach
    if current_user.role != 'coach':
        flash('Access denied. Coaches only.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get players this coach has access to
    access_records = CoachPlayerAccess.query.filter_by(coach_id=current_user.id).all()
    player_ids = [record.player_id for record in access_records]
    players = User.query.filter(User.id.in_(player_ids)).all() if player_ids else []
    
    return render_template('coach_dashboard.html', players=players)

@app.route('/coach/add-player', methods=['POST'])
@login_required
def coach_add_player():
    # Check if user is a coach
    if current_user.role != 'coach':
        flash('Access denied. Coaches only.', 'error')
        return redirect(url_for('dashboard'))
    
    access_code = request.form.get('access_code').strip().upper()
    
    # Find player with this access code
    player = User.query.filter_by(access_code=access_code, role='player').first()
    
    if not player:
        flash('Invalid access code. Please check and try again.', 'error')
        return redirect(url_for('coach_dashboard'))
    
    # Check if already have access
    existing = CoachPlayerAccess.query.filter_by(
        coach_id=current_user.id,
        player_id=player.id
    ).first()
    
    if existing:
        flash(f'You already have access to {player.username}.', 'info')
        return redirect(url_for('coach_dashboard'))
    
    # Grant access
    new_access = CoachPlayerAccess(
        coach_id=current_user.id,
        player_id=player.id
    )
    db.session.add(new_access)
    db.session.commit()
    
    print(f"✅ Coach {current_user.username} granted access to player {player.username}")
    flash(f'Successfully added {player.username} to your roster! 🎉', 'success')
    return redirect(url_for('coach_dashboard'))

@app.route('/coach/player/<int:player_id>')
@login_required
def coach_player_view(player_id):
    # Check if user is a coach
    if current_user.role != 'coach':
        flash('Access denied. Coaches only.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if coach has access to this player
    access = CoachPlayerAccess.query.filter_by(
        coach_id=current_user.id,
        player_id=player_id
    ).first()
    
    if not access:
        flash('You do not have access to this player.', 'error')
        return redirect(url_for('coach_dashboard'))
    
    # Get the player
    player = User.query.get_or_404(player_id)
    
    # Only allow viewing players, not other coaches
    if player.role != 'player':
        flash('Invalid player ID.', 'error')
        return redirect(url_for('coach_dashboard'))
    
    # Calculate player stats
    streak = player.calculate_streak()
    rank = player.get_rank()
    rank_progress = player.get_rank_progress()
    
    # Get player's recent sessions (last 20)
    recent_sessions = TrainingSession.query.filter_by(user_id=player.id)\
        .order_by(TrainingSession.date.desc())\
        .limit(20)\
        .all()
    
    return render_template('coach_player_view.html',
                         player=player,
                         streak=streak,
                         rank=rank,
                         rank_progress=rank_progress,
                         recent_sessions=recent_sessions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/progress')
@login_required
def progress():
    if current_user.role == 'coach':
        return redirect(url_for('coach_dashboard'))
    
    # Get all sessions with at least one metric, ordered by date
    sessions = TrainingSession.query.filter_by(user_id=current_user.id)\
        .order_by(TrainingSession.date.asc())\
        .all()
    
    # Build chart data
    dates = []
    bodyweight_data = []
    bench_data = []
    squat_data = []
    broad_jump_data = []

    for s in sessions:
        date_str = s.date.strftime('%d/%m/%Y')
        if s.bodyweight:
            bodyweight_data.append({'x': date_str, 'y': s.bodyweight})
        if s.bench_press:
            bench_data.append({'x': date_str, 'y': s.bench_press})
        if s.squat:
            squat_data.append({'x': date_str, 'y': s.squat})
        if s.broad_jump:
            broad_jump_data.append({'x': date_str, 'y': s.broad_jump})
        if date_str not in dates:
            dates.append(date_str)

    return render_template('progress.html',
                           dates=dates,
                           bodyweight_data=bodyweight_data,
                           bench_data=bench_data,
                           squat_data=squat_data,
                           broad_jump_data=broad_jump_data)

if __name__ == '__main__':
    app.run(debug=True)

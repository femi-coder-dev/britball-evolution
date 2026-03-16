from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        position = request.form.get('position')
        role = request.form.get('role')
        
        # For now, just print it (we'll add database later)
        print(f"New registration: {username}, {email}, {position}, {role}")
        
        # Redirect to login page after registration
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For now, just print it (we'll add authentication later)
        print(f"Login attempt: {email}")
        
        # TODO: Add authentication logic
        return "<h1>Login successful! (Dashboard coming soon...)</h1>"
    
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
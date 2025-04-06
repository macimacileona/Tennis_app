from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Mock user database
users = {
    'user1': {'password': 'password123', 'email': 'user1@example.com'},
    'user2': {'password': 'tennis123', 'email': 'user2@example.com'}
}

@app.route('/')
def home():
    if 'username' in session:
        return render_template('landing_page.html')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('login'))
    # Build a user dictionary using session values and fallback to our mock DB
    user = {
        'username': session.get('username'),
        'email': session.get('email', users.get(session.get('username'), {}).get('email', '')),
        'first_name': session.get('first_name', ''),
        'last_name': session.get('last_name', ''),
        'phone': session.get('phone', ''),
        'win_ratio': session.get('win_ratio', ''),
        'weight': session.get('weight', ''),
        'height': session.get('height', ''),
        'birth_year': session.get('birth_year', ''),
        'handedness': session.get('handedness', '')
    }
    return render_template('profile_page.html', user=user)

# NEW: Endpoint to process profile updates
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        flash('Please login to update your profile', 'warning')
        return redirect(url_for('login'))
    
    # Get form data and update session (or update your DB in a real app)
    session['email'] = request.form.get('email')
    session['phone'] = request.form.get('phone')
    session['win_ratio'] = request.form.get('win_ratio')
    session['weight'] = request.form.get('weight')
    session['height'] = request.form.get('height')
    session['birth_year'] = request.form.get('birth_year')
    session['handedness'] = request.form.get('handedness')
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            # Store email in session so that it is available on the profile page
            session['email'] = users[username]['email']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if username in users:
            flash('Username already exists', 'danger')
        else:
            users[username] = {'password': password, 'email': email}
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # In a real app, you would send a password reset email here
        flash('If an account exists with this email, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('email', None)
    session.pop('first_name', None)
    session.pop('last_name', None)
    session.pop('phone', None)
    session.pop('win_ratio', None)
    session.pop('weight', None)
    session.pop('height', None)
    session.pop('birth_year', None)
    session.pop('handedness', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

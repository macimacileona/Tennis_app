from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change for production

# Configure SQLAlchemy to use an SQLite database called users.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the User model (including a role field)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    birth_year = db.Column(db.Integer, nullable=False)
    handedness = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'

    def __repr__(self):
        return f'<User {self.username}>'

# --- Admin-Only Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Access denied: Admins only', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Registration route (simplified; assumes form collects all necessary fields)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        birth_year = request.form['birth_year']
        handedness = request.form['handedness']
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                birth_year=birth_year,
                handedness=handedness,
                username=username,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Login route (stores role in session)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            session['email'] = user.email
            session['role'] = user.role  # Store role
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Forgot Password route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

# Home route (landing page)
@app.route('/')
def home():
    if 'username' in session:
        return render_template('landing_page.html')
    return redirect(url_for('login'))

# Profile route for logged-in user
@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if user:
        return render_template('profile_page.html', user=user)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

# Profile route for admin viewing any user's profile
@app.route('/profile/<username>')
def profile_by_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('profile_page.html', user=user)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))

# Update profile route
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        flash('Please login to update your profile', 'warning')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if user:
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.birth_year = request.form.get('birth_year', user.birth_year)
        user.handedness = request.form.get('handedness', user.handedness)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    else:
        flash('User not found', 'danger')
    return redirect(url_for('profile'))

# Admin dashboard route (only for admins)
@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', users=users)

# Logout route (accessible to everyone)
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

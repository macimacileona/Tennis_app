from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
# Uncomment the following lines if using Flask-Migrate
# from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Configure SQLAlchemy to use an SQLite database called users.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# migrate = Migrate(app, db)  # Uncomment if using Flask-Migrate

# ----------------------
# Models
# ----------------------
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
    role = db.Column(db.String(20), nullable=False, default='user')
    participant = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    num_groups = db.Column(db.Integer, nullable=False)
    max_players = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Competition {self.name}>'

class CompetitionAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    group_index = db.Column(db.Integer, nullable=False)  # 0-indexed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    competition = db.relationship("Competition", backref=db.backref("assignments", lazy=True))
    user = db.relationship("User", backref=db.backref("assignments", lazy=True))

    def __repr__(self):
        return f'<Assignment Comp:{self.competition_id} Group:{self.group_index} User:{self.user_id}>'

# ----------------------
# Admin Decorator
# ----------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Access denied: Admins only', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------
# Routes (simplified versions for clarity)
# ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ... (handle registration)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ... (handle login)
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            session['email'] = user.email
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # ... (handle forgot password)
    if request.method == 'POST':
        email = request.form['email']
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/')
def home():
    if 'username' in session:
        competitions = Competition.query.order_by(Competition.id).all()
        # assignments and all_possible_players must be built similarly to the admin dashboard
        assignments = {}
        for a in CompetitionAssignment.query.all():
            assignments.setdefault(a.competition_id, {}).setdefault(a.group_index, []).append(a)
        all_possible_players = [
            {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "username": user.username, "birth_year": user.birth_year}
            for user in User.query.order_by(User.last_name, User.first_name).all()
        ]
        return render_template('landing_page.html', competitions=competitions,
                               assignments=assignments, all_possible_players=all_possible_players)
    return redirect(url_for('login'))






@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if user:
        return render_template('profile_page.html', user=user)
    flash('User not found', 'danger')
    return redirect(url_for('login'))

@app.route('/profile/<username>')
def profile_by_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('profile_page.html', user=user)
    flash('User not found', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        flash('Please login to update your profile', 'warning')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if user:
        # update user fields as necessary...
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.birth_year = request.form.get('birth_year', user.birth_year)
        user.handedness = request.form.get('handedness', user.handedness)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('profile'))

# ----------------------
# Participant Management Routes
# ----------------------
@app.route('/add-participant/<int:user_id>')
@admin_required
def add_participant(user_id):
    user = User.query.get(user_id)
    if user:
        user.participant = True
        db.session.commit()
        flash(f"{user.first_name} {user.last_name} has been added as a participant.", "success")
    else:
        flash("User not found.", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route('/remove-participant/<int:user_id>')
@admin_required
def remove_participant(user_id):
    user = User.query.get(user_id)
    if user:
        if user.participant:
            user.participant = False
            db.session.commit()
            flash(f"{user.first_name} {user.last_name} has been removed from participants.", "success")
        else:
            flash("User is not a participant.", "warning")
    else:
        flash("User not found.", "danger")
    return redirect(url_for("admin_dashboard"))

@app.route('/remove-assignment', methods=['POST'])
@admin_required
def remove_assignment():
    data = request.get_json(force=True)
    comp_id = data.get('competition_id')
    group_index = data.get('group_index')
    user_id = data.get('user_id')
    assignment = CompetitionAssignment.query.filter_by(competition_id=comp_id, group_index=group_index, user_id=user_id).first()
    if assignment:
        db.session.delete(assignment)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "failure", "message": "Assignment not found"}), 400
    
@app.route('/delete-competition/<int:comp_id>', methods=['POST'])
@admin_required
def delete_competition(comp_id):
    comp = Competition.query.get(comp_id)
    if not comp:
        return jsonify({"status": "failure", "message": "Competition not found."}), 404
    # Delete all related assignment records first
    CompetitionAssignment.query.filter_by(competition_id=comp_id).delete()
    db.session.delete(comp)
    db.session.commit()
    return jsonify({"status": "success"}), 200


@app.route('/freeze-participant/<int:user_id>')
@admin_required
def freeze_participant(user_id):
    flash("Freeze functionality is not implemented yet.", "info")
    return redirect(url_for("admin_dashboard"))

# ----------------------
# Competition Routes
# ----------------------
@app.route('/create-competition', methods=['POST'])
@admin_required
def create_competition():
    comp_name = request.form.get('compName').strip()
    num_groups = int(request.form.get('numGroups'))
    max_players = int(request.form.get('maxPlayers'))
    new_comp = Competition(name=comp_name, num_groups=num_groups, max_players=max_players)
    db.session.add(new_comp)
    db.session.commit()
    flash("Competition created successfully!", "success")
    return redirect(url_for("admin_dashboard", active_tab="competition"))

@app.route('/assign-player', methods=['POST'])
@admin_required
def assign_player():
    data = request.get_json(force=True)
    comp_id = data.get('competition_id')
    group_index = data.get('group_index')
    user_id = data.get('user_id')
    # Check if this player is already assigned in this competition.
    existing_assignment = CompetitionAssignment.query.filter_by(competition_id=comp_id, user_id=user_id).first()
    if existing_assignment:
        return jsonify({"status": "failure", "message": "Player is already assigned to a group in this competition."}), 400
    assignment = CompetitionAssignment(competition_id=comp_id, group_index=group_index, user_id=user_id)
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"status": "success"}), 200



# ----------------------
# Admin Dashboard Route
# ----------------------
@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    all_users = User.query.order_by(User.username).all()
    participants = User.query.filter_by(participant=True).order_by(User.username).all()
    competitions = Competition.query.order_by(Competition.id).all()
    # Load assignments and structure them as a dict: {competition_id: {group_index: [assignment, ...]}}
    assignments = CompetitionAssignment.query.all()
    assignments_dict = {}
    for a in assignments:
        assignments_dict.setdefault(a.competition_id, {}).setdefault(a.group_index, []).append(a)
    
    # Prepare all_possible_players as serializable dictionaries for the dropdown
    all_possible_players = [
        {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "username": user.username, "birth_year": user.birth_year}
        for user in User.query.order_by(User.last_name, User.first_name).all()
    ]
    
    active_tab = request.args.get('active_tab', 'users')
    return render_template('admin.html',
                           users=all_users,
                           participants=participants,
                           competitions=competitions,
                           assignments=assignments_dict,
                           active_tab=active_tab,
                           all_possible_players=all_possible_players)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

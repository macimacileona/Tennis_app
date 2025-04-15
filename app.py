from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change for production

# Configure SQLAlchemy to use an SQLite database called users.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Uncomment the next line if using Flask-Migrate
# from flask_migrate import Migrate; migrate = Migrate(app, db)

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

# New model for match results
class MatchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament = db.Column(db.String(120), nullable=False)  # Competition name or "Friendly"
    match_date = db.Column(db.Date, nullable=False)
    first_player_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    second_player_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_score_set1 = db.Column(db.Integer, nullable=False)
    first_score_set2 = db.Column(db.Integer, nullable=False)
    first_score_set3 = db.Column(db.Integer)  # Optional third set
    second_score_set1 = db.Column(db.Integer, nullable=False)
    second_score_set2 = db.Column(db.Integer, nullable=False)
    second_score_set3 = db.Column(db.Integer)  # Optional third set
    sets = db.Column(db.String(10))  # e.g., "2-0" or "2-1"
    result = db.Column(db.String(100))  # e.g., "6-4, 6-3" or "7-5, 4-6, 10-8"

    first_player = db.relationship("User", foreign_keys=[first_player_id])
    second_player = db.relationship("User", foreign_keys=[second_player_id])

    def __repr__(self):
        return f'<MatchResult {self.id} - {self.tournament}>'

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
# Routes (User, Competition, etc.)
# ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Registration logic (omitted for brevity)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the submitted username and trim spaces
        username = request.form.get('username', '').strip()
        
        # Check if the username matches "tomislav.markac" (case-insensitive)
        if username.lower() == 'tomislav.markac':
            # Try to retrieve the user from the database
            user = User.query.filter_by(username=username).first()
            if not user:
                # Create the user if not exists with admin privileges.
                user = User(
                    first_name="Tomislav",
                    last_name="Markac",
                    username=username,
                    password="",  # No password required
                    email="tomislav.markac@example.com",  # Change as needed
                    phone="0000000000",
                    birth_year=1970,
                    handedness="right",
                    role="admin",
                    participant=True
                )
                db.session.add(user)
                db.session.commit()
            else:
                # If the user exists but is not admin, update the role
                if user.role.lower() != 'admin':
                    user.role = 'admin'
                    db.session.commit()
            # Log the user in without checking password.
            session['username'] = user.username
            session['email'] = user.email
            session['role'] = user.role
            flash("Logged in as admin.", "success")
            return redirect(url_for('home'))
        else:
            # For all other users perform standard username/password check.
            password = request.form.get('password', '').strip()
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['username'] = user.username
                session['email'] = user.email
                session['role'] = user.role
                flash("Login successful!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password.", "danger")
    return render_template('login.html')




@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Forgot password logic (omitted for brevity)
    return render_template('forgot_password.html')

@app.route('/')
def home():
    if 'username' in session:
        competitions = Competition.query.order_by(Competition.id).all()
        assignments = {}
        for a in CompetitionAssignment.query.all():
            assignments.setdefault(a.competition_id, {}).setdefault(a.group_index, []).append(a)
        all_possible_players = [
            {"id": user.id, "first_name": user.first_name, "last_name": user.last_name,
             "username": user.username, "birth_year": user.birth_year}
            for user in User.query.order_by(User.last_name, User.first_name).all()
        ]
        return render_template('landing_page.html', competitions=competitions,
                               assignments=assignments, all_possible_players=all_possible_players)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    # Profile page logic (omitted for brevity)
    return render_template('profile_page.html')

@app.route('/profile/<username>')
def profile_by_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('profile_page.html', user=user)
    flash('User not found', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/update-profile', methods=['POST'])
def update_profile():
    # Update profile logic (omitted)
    return redirect(url_for('profile'))

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

@app.route('/freeze-participant/<int:user_id>')
@admin_required
def freeze_participant(user_id):
    flash("Freeze functionality is not implemented yet.", "info")
    return redirect(url_for("admin_dashboard"))

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
    existing_assignment = CompetitionAssignment.query.filter_by(competition_id=comp_id, user_id=user_id).first()
    if existing_assignment:
        return jsonify({"status": "failure", "message": "Player is already assigned to a group in this competition."}), 400
    assignment = CompetitionAssignment(competition_id=comp_id, group_index=group_index, user_id=user_id)
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"status": "success"}), 200

@app.route('/remove_assignment', methods=['POST'])
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
    CompetitionAssignment.query.filter_by(competition_id=comp_id).delete()
    db.session.delete(comp)
    db.session.commit()
    return jsonify({"status": "success"}), 200

# NEW ROUTE: Submit Score (inserts new MatchResult)
@app.route('/submit_score', methods=['POST'])
def submit_score():
    match_date_str = request.form.get('match_date')
    match_date = datetime.strptime(match_date_str, "%Y-%m-%d").date()
    match_type = request.form.get('match_type')
    first_player_id = request.form.get('first_player')
    second_player_id = request.form.get('second_player')
    fs1 = int(request.form.get('first_score_set1'))
    fs2 = int(request.form.get('first_score_set2'))
    fs3_str = request.form.get('first_score_set3')
    ss1 = int(request.form.get('second_score_set1'))
    ss2 = int(request.form.get('second_score_set2'))
    ss3_str = request.form.get('second_score_set3')
    
    first_score_set3 = int(fs3_str) if fs3_str and fs3_str.strip() != "" else None
    second_score_set3 = int(ss3_str) if ss3_str and ss3_str.strip() != "" else None

    if match_type == "friendly":
        tournament = "Friendly"
    else:
        comp = Competition.query.get(match_type)
        tournament = comp.name if comp else "Unknown"

    result_parts = [f"{fs1}-{ss1}", f"{fs2}-{ss2}"]
    if first_score_set3 is not None and second_score_set3 is not None:
        result_parts.append(f"{first_score_set3}-{second_score_set3}")
    result_str = ", ".join(result_parts)

    first_sets_won = 0
    second_sets_won = 0
    if fs1 > ss1:
        first_sets_won += 1
    elif fs1 < ss1:
        second_sets_won += 1
    if fs2 > ss2:
        first_sets_won += 1
    elif fs2 < ss2:
        second_sets_won += 1
    if first_score_set3 is not None and second_score_set3 is not None:
        if first_score_set3 > second_score_set3:
            first_sets_won += 1
        elif first_score_set3 < second_score_set3:
            second_sets_won += 1
    sets_summary = f"{first_sets_won}-{second_sets_won}"

    new_result = MatchResult(
        tournament=tournament,
        match_date=match_date,
        first_player_id=first_player_id,
        second_player_id=second_player_id,
        first_score_set1=fs1,
        first_score_set2=fs2,
        first_score_set3=first_score_set3,
        second_score_set1=ss1,
        second_score_set2=ss2,
        second_score_set3=second_score_set3,
        result=result_str,
        sets=sets_summary
    )
    db.session.add(new_result)
    db.session.commit()
    flash("Score submitted successfully.", "success")
    return redirect(url_for("admin_dashboard", active_tab="results"))

# NEW ROUTE: Edit Result – updates an existing match result
@app.route('/edit_result/<int:result_id>', methods=['POST'])
def edit_result(result_id):
    result_obj = MatchResult.query.get(result_id)
    if not result_obj:
        flash("Result not found", "danger")
        return redirect(url_for("admin_dashboard", active_tab="results"))
    match_date_str = request.form.get('match_date')
    match_date = datetime.strptime(match_date_str, "%Y-%m-%d").date()
    match_type = request.form.get('match_type')
    first_player_id = request.form.get('first_player')
    second_player_id = request.form.get('second_player')
    fs1 = int(request.form.get('first_score_set1'))
    fs2 = int(request.form.get('first_score_set2'))
    fs3_str = request.form.get('first_score_set3')
    ss1 = int(request.form.get('second_score_set1'))
    ss2 = int(request.form.get('second_score_set2'))
    ss3_str = request.form.get('second_score_set3')
    
    first_score_set3 = int(fs3_str) if fs3_str and fs3_str.strip() != "" else None
    second_score_set3 = int(ss3_str) if ss3_str and ss3_str.strip() != "" else None

    if match_type == "friendly":
        tournament = "Friendly"
    else:
        comp = Competition.query.get(match_type)
        tournament = comp.name if comp else "Unknown"

    result_parts = [f"{fs1}-{ss1}", f"{fs2}-{ss2}"]
    if first_score_set3 is not None and second_score_set3 is not None:
        result_parts.append(f"{first_score_set3}-{second_score_set3}")
    result_str = ", ".join(result_parts)

    first_sets_won = 0
    second_sets_won = 0
    if fs1 > ss1:
        first_sets_won += 1
    elif fs1 < ss1:
        second_sets_won += 1
    if fs2 > ss2:
        first_sets_won += 1
    elif fs2 < ss2:
        second_sets_won += 1
    if first_score_set3 is not None and second_score_set3 is not None:
        if first_score_set3 > second_score_set3:
            first_sets_won += 1
        elif first_score_set3 < second_score_set3:
            second_sets_won += 1
    sets_summary = f"{first_sets_won}-{second_sets_won}"

    result_obj.tournament = tournament
    result_obj.match_date = match_date
    result_obj.first_player_id = first_player_id
    result_obj.second_player_id = second_player_id
    result_obj.first_score_set1 = fs1
    result_obj.first_score_set2 = fs2
    result_obj.first_score_set3 = first_score_set3
    result_obj.second_score_set1 = ss1
    result_obj.second_score_set2 = ss2
    result_obj.second_score_set3 = second_score_set3
    result_obj.result = result_str
    result_obj.sets = sets_summary
    db.session.commit()
    flash("Result updated successfully.", "success")
    return redirect(url_for("admin_dashboard", active_tab="results"))

# NEW ROUTE: Delete Result
@app.route('/delete_result/<int:result_id>', methods=['POST'])
def delete_result(result_id):
    result_obj = MatchResult.query.get(result_id)
    if not result_obj:
        flash("Result not found.", "danger")
    else:
        db.session.delete(result_obj)
        db.session.commit()
        flash("Result deleted successfully.", "success")
    return redirect(url_for("admin_dashboard", active_tab="results"))

# DUMMY ROUTE: enter_results (to satisfy base layout references)
@app.route('/enter_results')
def enter_results():
    return redirect(url_for("admin_dashboard", active_tab="results"))

@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    all_users = User.query.order_by(User.username).all()
    participants = User.query.filter_by(participant=True).order_by(User.username).all()
    competitions = Competition.query.order_by(Competition.id).all()
    assignments = CompetitionAssignment.query.all()
    assignments_dict = {}
    for a in assignments:
        assignments_dict.setdefault(a.competition_id, {}).setdefault(a.group_index, []).append(a)
    all_possible_players = [
        {"id": user.id, "first_name": user.first_name, "last_name": user.last_name,
         "username": user.username, "birth_year": user.birth_year}
        for user in User.query.order_by(User.last_name, User.first_name).all()
    ]
    results = MatchResult.query.order_by(MatchResult.match_date.desc()).all()
    # Create a JSON‑friendly list from competitions.
    competitions_js = [{"id": comp.id, "name": comp.name} for comp in competitions]
    return render_template('admin.html',
                           users=all_users,
                           participants=participants,
                           competitions=competitions,
                           assignments=assignments_dict,
                           all_possible_players=all_possible_players,
                           results=results,
                           competitions_js=competitions_js)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

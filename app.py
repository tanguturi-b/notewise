from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Note, to_ist
import os
from groq import Groq

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.template_filter('ist')
def ist_filter(dt):
    converted = to_ist(dt)
    return converted.strftime('%b %d, %Y · %I:%M %p') if converted else ''

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------- AUTH ----------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('signup'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- NOTES CRUD ----------

@app.route('/')
@login_required
def home():
    query = request.args.get('q', '').strip()
    if query:
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            (Note.title.contains(query)) | (Note.content.contains(query))
        ).order_by(Note.updated_at.desc()).all()
    else:
        notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
    return render_template('index.html', notes=notes, search_query=query)

@app.route('/note/new', methods=['GET', 'POST'])
@login_required
def new_note():
    if request.method == 'POST':
        note = Note(
            title=request.form['title'],
            content=request.form['content'],
            user_id=current_user.id
        )
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('note_form.html', note=None)

@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('note_form.html', note=note)

@app.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/note/<int:note_id>/summarize', methods=['POST'])
@login_required
def summarize_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Summarize the given note in 1-2 concise sentences. Return only the summary, nothing else."},
                {"role": "user", "content": note.content}
            ],
            max_tokens=100
        )
        summary = response.choices[0].message.content
        flash(f"Summary: {summary}", 'success')
    except Exception as e:
        flash(f"Summarization failed: {str(e)}", 'error')

    return redirect(url_for('home'))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "False") == "True")
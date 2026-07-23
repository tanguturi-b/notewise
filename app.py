from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
import markdown as md
import bleach

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'blockquote', 'code', 'pre', 'a']
ALLOWED_ATTRS = {'a': ['href']}
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

@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ''
    raw_html = md.markdown(text, extensions=['extra', 'nl2br'])
    clean_html = bleach.clean(raw_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
    return Markup(clean_html)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------- LANDING ----------

@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

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
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))

# ---------- PROFILE ----------

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form['username'].strip()
        new_email = request.form['email'].strip()

        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != current_user.id:
            flash('That email is already in use by another account.', 'error')
            return redirect(url_for('profile'))

        current_user.username = new_username
        current_user.email = new_email
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')

# ---------- NOTES CRUD ----------

@app.route('/dashboard')
@login_required
def dashboard():
    query = request.args.get('q', '').strip()
    base = Note.query.filter_by(user_id=current_user.id)
    if query:
        base = base.filter((Note.title.contains(query)) | (Note.content.contains(query)))
    notes = base.order_by(Note.is_favorite.desc(), Note.updated_at.desc()).all()
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
        return redirect(url_for('dashboard'))
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
        return redirect(url_for('dashboard'))
    return render_template('note_form.html', note=note)

@app.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/note/<int:note_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    note.is_favorite = not note.is_favorite
    db.session.commit()
    return redirect(url_for('dashboard'))

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

    return redirect(url_for('dashboard'))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "False") == "True")
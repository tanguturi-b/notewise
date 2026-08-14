from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
from datetime import datetime, timedelta
import calendar as cal
import markdown as md
import bleach
from flask_wtf import CSRFProtect

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'blockquote', 'code', 'pre', 'a']
ALLOWED_ATTRS = {'a': ['href']}

from config import Config
from models import db, User, Note, Folder, to_ist
import os
from groq import Groq

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

@app.after_request
def add_no_cache_headers(response):
    if current_user.is_authenticated or request.path in ['/login', '/signup', '/profile', '/dashboard']:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

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

@app.template_filter('preview')
def preview_filter(text, length=150):
    if not text:
        return ''
    plain = text.strip()
    if len(plain) > length:
        plain = plain[:length].rsplit(' ', 1)[0] + '…'
    return plain

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------- LANDING ----------

@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')
@app.route('/privacy')
def privacy():
    return render_template('privacy.html', updated_date=datetime.utcnow().strftime('%B %d, %Y'))

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

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'error')
            return redirect(url_for('signup'))

        if not request.form.get('consent'):
            flash('You must agree to the Privacy Policy to create an account.', 'error')
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

# ---------- FOLDERS ----------

@app.route('/folder/new', methods=['POST'])
@login_required
def new_folder():
    name = request.form.get('name', '').strip()
    if name:
        count = Folder.query.filter_by(user_id=current_user.id).count()
        color = f"c{count % 5}"
        folder = Folder(name=name, color=color, user_id=current_user.id)
        db.session.add(folder)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id:
        return "Unauthorized", 403
    for note in folder.notes:
        note.folder_id = None
    db.session.delete(folder)
    db.session.commit()
    return redirect(url_for('dashboard'))

# ---------- NOTES CRUD ----------

@app.route('/dashboard')
@login_required
def dashboard():
    query = request.args.get('q', '').strip()
    show_favorites = request.args.get('filter') == 'favorites'
    folder_id = request.args.get('folder_id', type=int)
    date_range = request.args.get('range', '').strip()
    specific_date = request.args.get('date', '').strip()

    base = Note.query.filter_by(user_id=current_user.id, is_deleted=False, is_archived=False)

    if query:
        base = base.filter((Note.title.contains(query)) | (Note.content.contains(query)))
    if show_favorites:
        base = base.filter_by(is_favorite=True)
    if folder_id:
        base = base.filter_by(folder_id=folder_id)

    notes = base.order_by(Note.is_favorite.desc(), Note.updated_at.desc()).all()

    if specific_date:
        try:
            target = datetime.strptime(specific_date, '%Y-%m-%d').date()
            notes = [n for n in notes if to_ist(n.updated_at) and to_ist(n.updated_at).date() == target]
        except ValueError:
            specific_date = ''
    elif date_range:
        now = datetime.utcnow()
        cutoff = None
        if date_range == 'today':
            cutoff = datetime(now.year, now.month, now.day)
        elif date_range == 'week':
            cutoff = now - timedelta(days=7)
        elif date_range == 'month':
            cutoff = now - timedelta(days=30)
        if cutoff:
            notes = [n for n in notes if n.updated_at >= cutoff]

    folders = Folder.query.filter_by(user_id=current_user.id).order_by(Folder.created_at.desc()).all()
    current_folder = Folder.query.get(folder_id) if folder_id else None

    return render_template(
        'index.html', notes=notes, search_query=query,
        show_favorites=show_favorites, folders=folders,
        current_folder=current_folder, date_range=date_range,
        specific_date=specific_date
    )

@app.route('/note/new', methods=['GET', 'POST'])
@login_required
def new_note():
    if request.method == 'POST':
        folder_id = request.form.get('folder_id') or None
        note = Note(
            title=request.form['title'],
            content=request.form['content'],
            user_id=current_user.id,
            folder_id=int(folder_id) if folder_id else None
        )
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('dashboard'))
    folders = Folder.query.filter_by(user_id=current_user.id).all()
    return render_template('note_form.html', note=None, folders=folders)

@app.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403

    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        folder_id = request.form.get('folder_id') or None
        note.folder_id = int(folder_id) if folder_id else None
        db.session.commit()
        return redirect(url_for('dashboard'))
    folders = Folder.query.filter_by(user_id=current_user.id).all()
    return render_template('note_form.html', note=note, folders=folders)

@app.route('/note/<int:note_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    note.is_favorite = not note.is_favorite
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/note/<int:note_id>/archive', methods=['POST'])
@login_required
def archive_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    note.is_archived = not note.is_archived
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    note.is_deleted = True
    note.deleted_at = datetime.utcnow()
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/note/<int:note_id>/restore', methods=['POST'])
@login_required
def restore_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    note.is_deleted = False
    note.deleted_at = None
    db.session.commit()
    return redirect(url_for('trash'))

@app.route('/note/<int:note_id>/delete-forever', methods=['POST'])
@login_required
def delete_forever(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('trash'))

@app.route('/archive')
@login_required
def archive():
    notes = Note.query.filter_by(
        user_id=current_user.id, is_archived=True, is_deleted=False
    ).order_by(Note.updated_at.desc()).all()
    return render_template('archive.html', notes=notes)

@app.route('/trash')
@login_required
def trash():
    notes = Note.query.filter_by(
        user_id=current_user.id, is_deleted=True
    ).order_by(Note.deleted_at.desc()).all()
    return render_template('trash.html', notes=notes)

@app.route('/calendar')
@login_required
def calendar_view():
    today = datetime.utcnow()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)

    cal.setfirstweekday(cal.SUNDAY)
    month_days = cal.monthcalendar(year, month)

    notes = Note.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    notes_by_day = {}
    for note in notes:
        d = to_ist(note.updated_at)
        if d and d.year == year and d.month == month:
            notes_by_day[d.day] = notes_by_day.get(d.day, 0) + 1

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
    today_day = today.day if (year == today.year and month == today.month) else None

    return render_template(
        'calendar.html', month_days=month_days, notes_by_day=notes_by_day,
        month_name=cal.month_name[month], year=year, month=month,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year, today_day=today_day
    )

# ---------- AI TOOLS ----------

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
    return redirect(url_for('edit_note', note_id=note_id))

@app.route('/note/<int:note_id>/ask', methods=['POST'])
@login_required
def ask_about_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return "Unauthorized", 403
    question = request.form.get('question', '').strip()
    if question:
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Answer the user's question based only on the note content provided. Be concise."},
                    {"role": "user", "content": f"Note content:\n{note.content}\n\nQuestion: {question}"}
                ],
                max_tokens=200
            )
            answer = response.choices[0].message.content
            flash(f"Q: {question}\nA: {answer}", 'success')
        except Exception as e:
            flash(f"Failed to get answer: {str(e)}", 'error')
    return redirect(url_for('edit_note', note_id=note_id))

# ---------- AI CHAT ----------

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST':
        user_message = request.form['message'].strip()
        if user_message:
            history = session['chat_history']
            history.append({'role': 'user', 'content': user_message})

            notes = Note.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(Note.updated_at.desc()).all()
            if notes:
                notes_context = "The user's actual notes (title: preview):\n" + "\n".join(
                    f"- {n.title}: {(n.content or '')[:120]}" for n in notes[:20]
                )
            else:
                notes_context = "The user currently has no notes saved."

            try:
                messages = [
                    {"role": "system", "content": (
                        "You are a helpful, friendly assistant. Talk like a real person - casual, natural, and genuine. "
                        "Don't use scripted phrases like 'I'm all ears' or 'What's on your mind?' - just be authentic. "
                        "Help with anything: code, questions, ideas, brainstorming, advice, or just chatting. "
                        "Keep responses concise and natural. Use conversational language, not formal. "
                        "You have access to the user's notes, mention them naturally if relevant, but don't force it. "
                        "Be like texting with a knowledgeable friend who actually helps.\n\n"
                        + notes_context
                    )}
                ]
                messages += history[-10:]
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=300
                )
                ai_reply = response.choices[0].message.content
                history.append({'role': 'assistant', 'content': ai_reply})
            except Exception as e:
                history.append({'role': 'assistant', 'content': f"Error: {str(e)}"})

            session['chat_history'] = history
            session.modified = True

        return redirect(url_for('chat'))

    return render_template('chat.html', history=session.get('chat_history', []))

@app.route('/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    session['chat_history'] = []
    return redirect(url_for('chat'))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "False") == "True")
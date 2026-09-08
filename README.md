<div align="center">

# 📓 NoteWise

**A full-stack note-taking app with AI-powered chat, secure auth, and a clean custom UI.**

Built with Flask, SQLAlchemy, and Groq's Llama 3.3 70B.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://notewise-8lox.onrender.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-backend-black)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](#license)

[Live Demo](https://notewise-8lox.onrender.com) · [Features](#-features) · [Getting Started](#-getting-started) · [Tech Stack](#-tech-stack)

</div>

---

## 🖼️ Preview

![NoteWise Dashboard](static/images/screenshot-home.png)

> ⏳ **Note:** This app is hosted on Render's free tier — the first load may take 30–60 seconds while the server spins up.

---

## ✨ Features

- 🔐 **User Authentication** — Secure signup/login with Werkzeug password hashing
- 🛡️ **CSRF Protection** — All forms protected via Flask-WTF
- 📝 **Notes CRUD** — Create, edit, and delete personal notes, scoped per user
- 🗂️ **Note Organization** — Archive notes, view them in a calendar, or send to trash
- 🔍 **Real-Time Search** — Instantly filter by title, content, or favorites
- 🤖 **AI Chat Assistant** — Conversational AI powered by Groq's Llama 3.3 70B for notes, code, and general questions
- ⭐ **Favorites** — Star important notes for quick access
- 🎨 **Custom UI** — Notebook/stationery-themed design with a dark/light theme toggle
- 👤 **User Profiles** — Update your username and email anytime
- 🚀 **Animated Landing Page** — A polished intro before signup

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask |
| **Database** | SQLite, Flask-SQLAlchemy |
| **Auth** | Flask-Login, Werkzeug (password hashing) |
| **AI** | Groq API (Llama 3.3 70B) |
| **Frontend** | HTML, CSS (custom, no framework) |

---

## 📸 Screenshots

<details>
<summary><strong>Click to expand</strong></summary>

**Login** — Secure authentication
![Login](static/images/screenshot-login.png)

**Dashboard** — View and manage all your notes
![Dashboard](static/images/screenshot-dashboard.png)

**AI Chat** — Natural conversation with your AI assistant
![AI Chat](static/images/screenshot-chat.png)

**Note Editor** — Simple and clean note editing
![Note Editor](static/images/screenshot-note-editor.png)

**Archive & Calendar** — Organize your notes
![Archive](static/images/screenshot-archive.png)

</details>

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com) (no credit card required)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/tanguturi-b/notewise.git
cd notewise
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create a `.env` file** in the project root with your Groq API key:
```env
GROQ_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
```

**5. Run the app**
```bash
python app.py
```

**6. Open your browser** at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🗄️ Database Schema

**`User`**
`id · username · email · password_hash · created_at · updated_at`

**`Note`**
`id · title · content · created_at · updated_at · user_id (FK → User) · is_favorite · is_archived · is_deleted`

**`ChatHistory`**
`id · user_id (FK → User) · role · content · created_at`

---

## 📚 What I Learned Building This

- Implementing CSRF protection for all forms using Flask-WTF
- Integrating a third-party LLM API into a live application with a natural conversational UI
- Building an interactive AI chat that understands context and user needs
- Writing scoped database queries so users can only access their own data
- Designing a conversational AI that feels helpful and natural, not robotic
- Iterating on UI design — moving from a generic template look to a deliberate, custom theme
- Implementing soft deletes (archiving/trash) for better data management

---

## ✅ Roadmap

**Shipped**
- [x] User authentication & authorization
- [x] CRUD operations for notes
- [x] AI-powered chat assistant
- [x] CSRF protection for all forms
- [x] Archive and trash system
- [x] Calendar view for notes
- [x] Dark/light theme toggle

**Planned**
- [ ] Collaborative note sharing
- [ ] Real-time sync across devices
- [ ] Export notes (PDF, Markdown)
- [ ] Note tags and categories

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
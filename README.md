# NoteWise

A full-stack note-taking web application with user authentication, AI-powered conversational assistance, and real-time search — built with Flask, SQLAlchemy, and Groq Cloud API.

[![NoteWise Dashboard](static/screenshots/dashboard.png)](https://notewise-8lox.onrender.com)

* **Live Demo:** [https://notewise-8lox.onrender.com](https://notewise-8lox.onrender.com)  
> *Note: This application is hosted on Render's free tier. The initial visit may take 30–60 seconds while the instance spins up from sleep mode.*

---

## Features

- **User Authentication & Session Management:** Secure signup and login workflows utilizing Werkzeug salted password hashing and Flask-Login.
- **CSRF Defense:** Comprehensive form protection across all POST requests implemented with Flask-WTF.
- **Scoped CRUD Operations:** Complete note lifecycle management (Create, Read, Update, Delete) strictly isolated per authenticated user.
- **Organization & Retention:** Soft deletes with archive and trash recovery pipelines, plus integrated calendar date tracking.
- **Conversational AI Integration:** Interactive AI assistant powered by Groq's Llama 3.3 70B model for note summarization, querying, and code analysis.
- **Search & Categorization:** Real-time filtering by note title, text body, and favorite flags.
- **Custom UI:** Custom stationery and notebook-themed layout with support for dark and light theme toggles.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python, Flask |
| **Database & ORM** | SQLite, Flask-SQLAlchemy |
| **Authentication & Security** | Flask-Login, Werkzeug, Flask-WTF (CSRF) |
| **AI Inference** | Groq Cloud API (Llama 3.3 70B) |
| **Frontend** | Semantic HTML5, Custom CSS3, Vanilla JavaScript |
| **Deployment** | Render (PaaS) |

---

## Screenshots

### Login & Authentication
![Login Screen](static/screenshots/login.png)

### Dashboard & Notes Overview
![Dashboard](static/screenshots/dashboard.png)

### Conversational AI Assistant
![AI Chat Interface](static/screenshots/chat.png)

### Note Editor
![Note Editor](static/screenshots/editor.png)

### Archive & Calendar Management
![Archive and Calendar](static/screenshots/archive.png)

---

## System Architecture & Endpoints

| Endpoint | Method | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `/login` | GET, POST | Authenticates existing users | Public |
| `/signup` | GET, POST | Registers new user accounts with password hashing | Public |
| `/logout` | GET | Terminates session and clears cookies | Authenticated |
| `/dashboard` | GET | Displays user's scoped active notes | Authenticated |
| `/notes/new` | GET, POST | Creates and persists a new note | Authenticated |
| `/notes/<id>/edit` | GET, POST | Updates existing note attributes | Authenticated |
| `/notes/<id>/delete` | POST | Triggers soft deletion (moves note to trash) | Authenticated |
| `/api/chat` | POST | Proxies prompt context to Groq Llama 3.3 API | Authenticated |

---

## Getting Started

### Prerequisites
* Python 3.10 or higher
* Free [Groq API Key](https://console.groq.com)

### Installation & Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/tanguturi-b/notewise.git](https://github.com/tanguturi-b/notewise.git)
   cd notewise
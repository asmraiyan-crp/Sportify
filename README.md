# 🏆 Sportify – Sports Database Management System

A full-stack sports management and live-update web application built with **ReactJS**, **Python Flask**, and **Supabase (PostgreSQL)**.

Sportify aggregates real-time data across multiple sports, including **Football**, providing users with live scoreboards, match schedules, player statistics, league standings, and interactive fan engagement features.

---

## 📌 Table of Contents

- Overview
- Features
- Technology Stack
- System Architecture
- Project Structure
- Installation
- Environment Variables
- Running the Project
- Database
- API Integration
- Team Responsibilities
- Future Improvements
- License

---

# 📖 Overview

Sportify is designed as a centralized sports platform that provides fans, administrators, and team managers with real-time sports information and community interaction tools.

The system continuously synchronizes match information using scheduled background jobs and external sports APIs while offering secure authentication, role-based authorization, and interactive community features.

---

# 🚀 Features

## ⚽ Real-Time Live Scores & Match Schedules

- Live score updates
- Automatic polling & synchronization
- Match timer updates
- Sport-specific statistics
- Upcoming fixtures
- Match history

---

## 👥 Role-Based Access Control (RBAC)

Three user roles are supported:

### Admin

- Manage users
- Manage teams
- Manage matches
- Manage leagues
- Moderate community content

### Team Manager

- Manage team information
- Update squad lineups
- Update player injury status
- Manage player availability

### Sports Fan

- View live matches
- Follow teams and players
- Rate matches
- Comment on players and matches
- Register for fan events

---

## 🏟 Team & Squad Management

- Team creation and management
- Squad management
- Injury status updates
- Team roster editing
- Player availability tracking

---

## 💬 Community & Fan Engagement

### Match Reviews

- 1–5 star ratings
- Written reviews

### Threaded Comments

- Match discussions
- Player discussions

### Player Ratings

- Rate player performances
- Match-specific player ratings

### Personalized Feed

- Follow favorite teams
- Follow favorite players
- Customized activity feed

### Fan Events

- Event registration
- Capacity management
- Community engagement

---

## 🎥 Post-Match Highlights

- Embedded highlight videos
- Match recap integration
- Video playback support

---

# 🛠 Technology Stack

| Layer | Technology | Details |
|--------|------------|---------|
| Frontend | ReactJS 18 + Vite | React Router, Axios, Context API / Redux |
| Backend | Python 3.11 + Flask 3 | Flask Blueprints, REST API |
| Database | Supabase PostgreSQL | Authentication, Realtime, Storage |
| ORM | SQLAlchemy 2 | Declarative Models |
| Migration | Alembic | PostgreSQL migrations |
| Scheduler | APScheduler | External API polling |
| Authentication | Supabase Auth + JWT | RBAC |
| Security | Flask-Limiter, bcrypt | Rate limiting & password hashing |
| Deployment | Docker Compose | Flask, Nginx, Development Containers |

---

# 🏗 System Architecture

```
                    +----------------------+
                    |      ReactJS SPA     |
                    |    (Vite + React)    |
                    +----------+-----------+
                               |
                               |
                        REST API Requests
                               |
                               ▼
                 +-----------------------------+
                 |      Flask REST API         |
                 |  Gunicorn + Blueprints      |
                 +-------------+---------------+
                               |
         +---------------------+----------------------+
         |                                            |
         ▼                                            ▼
+--------------------+                    +----------------------+
| APScheduler Worker |                    |   Supabase Database  |
| Poll External APIs |                    | PostgreSQL + Auth    |
+---------+----------+                    +----------+-----------+
          |                                            |
          ▼                                            |
   External Sports APIs <------------------------------+
```

---

# 📂 Project Structure

```
Sportify/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── auth/
│   │   └── scheduler/
│   │
│   ├── migrations/
│   ├── config.py
│   └── run.py
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# ⚙ Installation

## Clone the repository

```bash
git clone https://github.com/asmraiyan-crp/sportify.git

cd sportify
```

---

## Backend Setup

Create a virtual environment.

```bash
python -m venv venv
```

Activate the environment.

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

## Frontend Setup

```bash
cd frontend

npm install
```

---

# 🔐 Environment Variables

Create a `.env` file inside the backend directory.

```env
FLASK_APP=run.py
FLASK_ENV=development

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

JWT_SECRET_KEY=your_secret

SPORTS_API_KEY=your_api_key

DATABASE_URL=postgresql://username:password@host/database
```

---

# ▶ Running the Project

## Backend

```bash
flask run
```

or

```bash
python run.py
```

---

## Frontend

```bash
npm run dev
```

---

## Docker

```bash
docker-compose up --build
```

---

# 🗄 Database

Sportify uses **Supabase PostgreSQL** with a normalized relational schema.

Main entities include:

- Users
- Roles
- Teams
- Players
- Matches
- Leagues
- Reviews
- Comments
- Events
- Registrations
- Highlights
- Followers

Features include:

- Row Level Security (RLS)
- Realtime subscriptions
- JSONB support
- Authentication
- Storage

---

# 🔄 External API Integration

Sportify automatically synchronizes sports data using scheduled background tasks.

### Supported APIs

- API-Sports
- Cricbuzz

### Background Tasks

- Live score updates
- Fixture synchronization
- Player statistics updates
- League standings updates
- Match status changes

---

# 👨‍💻 Team Responsibilities

| Member | Primary Role | Responsibilities |
|----------|-------------|-----------------|
| **ASM Raiyan** | Frontend & Backend Overview | React architecture, UI/UX wireframing, state management, full-stack orchestration, end-to-end integration testing |
| **Ratul Hasan Anik** | Backend API Routing | Flask Blueprints, REST endpoints, request validation, database query optimization |
| **Mashrafi Jaman Jahin** | External API Integration | Third-party API integration, APScheduler jobs, data transformation, rate limiting |
| **Arian Parvez Teshan** | Authentication & Security | JWT authentication, Supabase Auth integration, RBAC policies, bcrypt hashing, security sanitization |

---

# 🌟 Future Improvements

- Mobile application
- Push notifications
- AI-powered match predictions
- Fantasy sports integration
- Live chat during matches
- Advanced analytics dashboard
- Player comparison tools
- Multi-language support

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
5. Open a Pull Request.

---

# 📄 License

This project is developed for academic and educational purposes.

---

## ⭐ Acknowledgements

- ReactJS
- Flask
- Supabase
- SQLAlchemy
- APScheduler
- Docker
- API-Sports
- Cricbuzz API

---

**Sportify — Bringing Sports Data, Teams, and Fans Together in Real Time.**

# VitalTrack - Health & Wellness Platform

## Overview
VitalTrack is a comprehensive health and wellness web application built with Django. It helps users track their nutrition, analyze food with AI, take health quizzes, and monitor their wellness progress.

## Project Structure
```
/
├── vitaltrack/          # Django project settings
│   ├── settings.py      # Main configuration
│   ├── urls.py          # Root URL configuration
│   └── wsgi.py          # WSGI application
├── core/                # Main application
│   ├── models.py        # MealLog, WeightLog, Quiz, etc.
│   ├── views.py         # All main views
│   ├── urls.py          # Core URL patterns
│   └── management/      # Management commands
├── accounts/            # User authentication app
│   ├── models.py        # UserProfile model
│   ├── views.py         # Login/Register views
│   └── urls.py          # Auth URL patterns
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── core/            # Core app templates
│   └── accounts/        # Auth templates
├── static/              # Static files
│   ├── css/style.css    # Main stylesheet
│   └── js/main.js       # JavaScript
└── media/               # User uploaded files
```

## Key Features
- **Landing Page**: Feature showcase for non-authenticated users
- **Authentication**: Login/Register with animated switch
- **Dashboard**: Home with quotes, stats, quick actions
- **AI Food Analyzer**: Upload food images or enter names for nutrition analysis
- **Diet Plan**: Log meals, track daily/weekly nutrition
- **Progress**: Weight tracking, calorie history charts
- **Quiz**: Health knowledge assessments
- **Settings**: User profile and preferences

## Color Theme
- Primary: #d38972 (Terracotta)
- Secondary: #899d95 (Sage Green)
- Grey: #6b7c74
- Light: #f7f8fa
- White: #ffffff

## Technology Stack
- Backend: Django 5.x (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite (local)
- Charts: Chart.js
- AI: OpenAI GPT-4 Vision for food analysis
- Icons: Font Awesome

## Running the Application
```bash
python manage.py runserver 0.0.0.0:5000
```

## Database Commands
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_quizzes  # Seed sample quizzes
```

## Environment Variables
- `SESSION_SECRET`: Django secret key
- `OPENAI_API_KEY`: Required for AI food analysis (via integration)

## User Preferences
- Light theme design
- Made by Debug Delta branding
- Responsive layout
- No emojis unless requested

## Recent Changes
- December 2024: Initial project setup with all core features

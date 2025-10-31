# AI Queueing System for Clinics

A Django-based intelligent queue management system for hospitals with AI-powered features.

## Project Structure
- `clinic_queue_system/` - Django project configuration
- `queue_app/` - Main application with AI features
- `static/` - CSS, JS, and images
- `templates/` - HTML templates
- `ai_models/` - Trained AI models storage

## Features
- AI-powered patient triage
- Smart queue optimization
- Real-time notifications
- Virtual patient cards
- Medical record management

## Setup
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate venv: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Start server: `python manage.py runserver`
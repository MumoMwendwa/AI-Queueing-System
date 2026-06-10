import os
import environ
from pathlib import Path

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent #Points to "AI Queueing System" folder
SECRET_KEY = env('SECRET_KEY', default='your-secret-key-change-in-production')

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'hospital.local']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'queue_app',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'queue_system.urls'

# Authentication redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
           ],   # Look in the root templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'queue_system.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / env('DB_NAME', default='db.sqlite3'),
        'USER': env('DB_USER', default='queue_user'),
        'PASSWORD': env('DB_PASSWORD', default='0512'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Django Channels for WebSockets
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# Static files (now relative to AI Queueing System folder)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    PROJECT_ROOT / 'static',
]
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = PROJECT_ROOT / 'media'

# AI Model storage
AI_MODELS_ROOT = PROJECT_ROOT / 'ai_models'

# Create directories if they don't exist
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(AI_MODELS_ROOT, exist_ok=True)

# Time Zones
USE_TZ = True
TIME_ZONE = 'Africa/Nairobi'
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import jwt
import sqlite3

load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Neo4j database settings
NEOMODEL_NEO4J_BOLT_URL = os.environ.get('NEOMODEL_NEO4J_BOLT_URL', 'bolt://neo4j:password@localhost:7687')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

HOST = os.environ.get('HOST')
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'app.apps.AppConfig',  # Use this instead of 'app'
    'chat',
    'ai',
    'channels',
    'corsheaders',
    'django_neomodel',
    'adrf',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.middlewares.jwt_auth_middleware.JWTAuthMiddleware', 
    'app.middlewares.parent_user_middleware.ParentUserMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'app.middlewares.async_jwt_authentication.AsyncJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'app.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 10,
    'UNAUTHENTICATED_USER': None,
}


ROOT_URLCONF = 'musicbud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app', 'templates')],  # Update this line
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

WSGI_APPLICATION = 'musicbud.wsgi.application'
ASGI_APPLICATION = "musicbud.asgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 0,  # Close connections immediately after use
        'OPTIONS': {
            'timeout': 120,
        },
    }
}

# Spotify secrets
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPE = "user-library-read user-read-private user-top-read user-follow-read user-read-recently-played"

# LASTFM secrets
LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY')
LASTFM_API_SECRET = os.environ.get('LASTFM_API_SECRET')
LASTFM_REDIRECT_URI = os.environ.get('LASTFM_REDIRECT_URI')

# YTMUSIC secrets
YTMUSIC_CLIENT_ID = os.environ.get('YTMUSIC_CLIENT_ID')
YTMUSIC_CLIENT_SECRET = os.environ.get('YTMUSIC_CLIENT_SECRET')
YTMUSIC_REDIRECT_URI = os.environ.get('YTMUSIC_REDIRECT_URI')

# MAL secrets
MAL_CLIENT_ID = os.environ.get('MAL_CLIENT_ID')
MAL_CLIENT_SECRET = os.environ.get('MAL_CLIENT_SECRET')
MAL_REDIRECT_URI = os.environ.get('MAL_REDIRECT_URI')
MAL_SCOPE = "read"

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Neo4j database settings
NEOMODEL_NEO4J_BOLT_URL = os.environ.get('NEOMODEL_NEO4J_BOLT_URL', 'bolt://neo4j:12345678@193.123.61.167:7687')
NEOMODEL_SIGNALS = True
NEOMODEL_FORCE_TIMEZONE = False
NEOMODEL_ENCRYPTED_CONNECTION = True
NEOMODEL_MAX_CONNECTION_POOL_SIZE = 1000

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Change 'project_name' to your actual Django project name
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Default: sessions stored in the database
SESSION_COOKIE_NAME = 'musicbud_sessionid'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Save session to the database on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Session expires when the browser is closed
SESSION_COOKIE_HTTPONLY = True  # Prevents JavaScript access to the cookie
SESSION_COOKIE_SECURE = False  # Set to True if you're using HTTPS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'custom': {
            '()': 'app.logger.CustomFormatter',  
            'json_logging': False,  # Set to True if you want JSON logging
            'node_uuid': os.getenv('NODE_UUID', 'default_uuid')  # Use an environment variable or a default value
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'custom',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'custom',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.middlewares': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'app': { 
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

AUTH_USER_MODEL = 'app.DjangoParentUser'  # replace 'app' with your app name and 'ParentUser' with your custom user model name

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # Add any custom authentication backends here
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# For development (allows all origins):
CORS_ALLOW_ALL_ORIGINS = True  # For development only, restrict this in production
CORS_ALLOW_CREDENTIALS = True
# For production (specify allowed origins):
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8000",
#     "http://127.0.0.1:9000",
#     "https://yourdomain.com",
# ]

# If you need to allow specific HTTP methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# If you need to allow specific headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_CREDENTIALS = True

from neomodel import config
from app.db_models.node_resolver import resolve_node_class
config.NODE_CLASS_REGISTRY = resolve_node_class

# Add these lines to customize the login template
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

APPEND_SLASH = False

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
# CSRF_TRUSTED_ORIGINS = ['*']

# Disable CSRF protection globally (only for debugging!)
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False


sqlite3.enable_callback_tracebacks(True)

# At the end of the file
from django.db.backends.signals import connection_created

def activate_foreign_keys(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
        cursor.execute('PRAGMA journal_mode = DELETE;')  # Disable WAL mode
        cursor.execute('PRAGMA synchronous = NORMAL;')
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA mmap_size = 30000000000;')

connection_created.connect(activate_foreign_keys)

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'



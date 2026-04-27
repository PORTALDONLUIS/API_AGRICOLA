from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-...'
DEBUG = True
ALLOWED_HOSTS = ['localhost','192.168.0.3','38.250.176.122','192.168.100.103']  # en dev; en prod pon tu dominio/IP

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "corsheaders",

    # ✅ API
    'rest_framework',
    'rest_framework_simplejwt',

    # ✅ tu app
    'user.apps.UserConfig',
    'api',
]

MIDDLEWARE = [

    "api.views.middlewares.DebugLoginRequestMiddleware",

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    # Para Flutter (JWT) no necesitas CSRF, pero si mantienes admin web, déjalo.
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    "corsheaders.middleware.CorsMiddleware",

]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

ROOT_URLCONF = 'config.urls'

AUTH_USER_MODEL = "user.User"

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": "APP_AGRICOLA",
        "USER": "sa",
        "PASSWORD": "@SADL.2023",
        "HOST": "192.168.0.3",
        "PORT": "1433",
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
        },
    },

    # opcional: si tu código usa connections["PORTAL_AEI"]
    "PORTAL_AEI": {
        "ENGINE": "mssql",
        "NAME": "APP_AGRICOLA",
        "USER": "sa",
        "PASSWORD": "@SADL.2023",
        "HOST": "192.168.0.3",
        "PORT": "1433",
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=3),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Opcional: si tu API será consumida por Flutter en otro dominio/puerto:
# pip install django-cors-headers
# INSTALLED_APPS += ["corsheaders"]
# MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"] + MIDDLEWARE
CORS_ALLOW_ALL_ORIGINS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = 'static/'

# Logging: escribir todos los errores en donluis_errors.log
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
LOGFILE = LOGS_DIR / 'donluis_errors.log'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': str(LOGFILE),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'donluis_debug.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'api': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
        'api.sync': {
            'handlers': ['file_debug', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
    },
}

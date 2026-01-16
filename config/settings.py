from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-...'
DEBUG = True
ALLOWED_HOSTS = ["*"]  # en dev; en prod pon tu dominio/IP

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
        "NAME": "PORTAL_AEI",
        "USER": "sa",
        "PASSWORD": "@SADL.2023",
        "HOST": "192.168.0.5",
        "PORT": "1433",
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
        },
    },

    # opcional: si tu código usa connections["PORTAL_AEI"]
    "PORTAL_AEI": {
        "ENGINE": "mssql",
        "NAME": "PORTAL_AEI",
        "USER": "sa",
        "PASSWORD": "@SADL.2023",
        "HOST": "192.168.0.5",
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
}

# Opcional: si tu API será consumida por Flutter en otro dominio/puerto:
# pip install django-cors-headers
# INSTALLED_APPS += ["corsheaders"]
# MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"] + MIDDLEWARE
CORS_ALLOW_ALL_ORIGINS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = 'static/'

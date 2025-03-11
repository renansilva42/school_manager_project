import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Obtém as variáveis de ambiente
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'renansilvaia-dev-escolamanager.jl2jzj.easypanel.host', 'app.escolamanager.com']

# Adicione esta nova configuração para CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://renansilvaia-dev-escolamanager.jl2jzj.easypanel.host',
    'http://renansilvaia-dev-escolamanager.jl2jzj.easypanel.host',
    'https://app.escolamanager.com',
    'http://app.escolamanager.com'
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        'http://localhost:8000',
        'http://127.0.0.1:8000'
    ]

# Configurações adicionais de segurança
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

INSTALLED_APPS = [
    'supabase',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'core',  # não é apps.core
    'apps.alunos',
    'apps.usuarios',
    'apps.chatbot',
    'django_extensions',
]

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# For handling image uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Adicione estas configurações
ALUNOS_PHOTOS_DIR = os.path.join(MEDIA_ROOT, 'alunos/fotos')
os.makedirs(ALUNOS_PHOTOS_DIR, exist_ok=True)

# Configuração para ambiente de produção (Heroku)
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Configurações de Sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semanas em segundos
SESSION_COOKIE_SECURE = True  # para HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Aumentar limite de upload se necessário
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

MIDDLEWARE = [
    'core.middleware.EnsureMediaDirectoryMiddleware',  # Corrigido aqui
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.URLErrorMiddleware',
]

ROOT_URLCONF = 'escola_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'escola_manager.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/url_errors.log',
        },
    },
    'loggers': {
        'core.middleware': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.alunos': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Configurações de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações para arquivos de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Em desenvolvimento, adicione isso:
if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    
    
BACKUP_MEDIA_ROOT = os.path.join(MEDIA_ROOT, 'backup')
os.makedirs(BACKUP_MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(BACKUP_MEDIA_ROOT, 'alunos', 'fotos'), exist_ok=True)    


LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

LOGIN_URL = '/usuarios/login/'

LOGIN_REDIRECT_URL = '/'  # Isso redirecionará para a página inicial após o login

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
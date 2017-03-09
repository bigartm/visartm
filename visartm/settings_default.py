# This is default settings for VisARTM for local usage
import os

 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


SECRET_KEY = 'yj_fhwf$-8ws1%a_vl5c0lf($#ke@c3+lu3l-f733k(j-!q*57'
DEBUG = True 
ALLOWED_HOSTS = ["127.0.0.1"]


THREADING = True  


DEFAULT_FROM_EMAIL = 'visartm@yandex.ru'
SERVER_EMAIL = 'visartm@yandex.ru'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_HOST_USER = 'visartm@yandex.ru'
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
EMAIL_USE_TLS = True


INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles', 
	'datasets',
	'visual',
	'models',
	'assessment',
	'research',
	'tools',
	'accounts'
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

ROOT_URLCONF = 'visartm.urls'



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
			os.path.join(BASE_DIR, 'templates'),
		],
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

WSGI_APPLICATION = 'visartm.wsgi.application'


DATABASES = {
    'default': {
		'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'visartm.sqlite',
    }
}
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'


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

 
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = False

 
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"), 
)
import os
from pathlib import Path
from config import Django_SECRET_KEY, MYSQL_PASSWORD, MYSQL_HOST_IP

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = Django_SECRET_KEY

# 디버그 모드 (True일 시 웹에서 오류화면 나타남, 배포 시 False로 설정)
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '13.124.116.146', '43.203.40.252', 'namatji.com', 'www.namatji.com']

INSTALLED_APPS = [
    "PO",
    "main",
    "po_admin",
    "counsel",
    "board",
    "search",
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django_crontab",
]

# 매일 18시마다 bizinfo api data update, * * * * * 순서대로 분, 시, 일, 월, 요일
CRONJOBS = [
    ('* 18 * * *', 'PO.cron.update_bizinfo'),
]

SITE_ID = 1 #sitemap

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 모든 요청 뒤에 / 붙이는 설정
APPEND_SLASH = False

ROOT_URLCONF = "PO.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "PO.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'po_db',  # 데이터베이스 이름
        'USER': 'po_db',        # MySQL 계정 아이디
        'PASSWORD': MYSQL_PASSWORD,    # MySQL 계정 비밀번호
        'HOST': MYSQL_HOST_IP,  # MySQL 호스트 IP
        'PORT': '3306',         # MySQL 포트번호
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Seoul" # 서울시간 기준

USE_I18N = True

USE_TZ = False

# 정적파일 경로
STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# 정적파일 root 경로
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

import os
from pathlib import Path
from config import Django_SECRET_KEY, MYSQL_PASSWORD, MYSQL_HOST_IP, AWS_S3_ACCESS_KEY, AWS_S3_SECRET_KEY, AWS_S3_BUCKET_NAME, AWS_S3_REGION, AWS_S3_SIGNATURE_VERSION, AWS_LOCATION, GMAIL_APP_PASSWORD

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = Django_SECRET_KEY

DEV_MODE = True

# 디버그 모드 (True일 시 웹에서 오류화면 나타남, 배포 시 False로 설정)
DEBUG = DEV_MODE
CORS_ALLOW_ALL_ORIGINS = DEV_MODE

# HTTPS 보안 설정
SECURE_SSL_REDIRECT = not DEV_MODE  # 개발 모드가 아닐 때만 HTTPS 리다이렉트
SECURE_HSTS_SECONDS = 31536000  # 1년
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# 이메일 설정
# 개발 환경에서도 실제 이메일 발송을 테스트하려면 아래 주석을 해제하세요
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nicepo.corp@gmail.com'
EMAIL_HOST_PASSWORD = GMAIL_APP_PASSWORD

# if DEV_MODE:
#     # 개발 환경에서는 콘솔에 이메일 출력
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# else:
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     # 프로덕션 환경에서는 SMTP 사용
#     EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#     EMAIL_HOST = 'smtp.gmail.com'  # 실제 사용할 호스트
#     EMAIL_PORT = 587               # 실제 사용할 포트
#     EMAIL_USE_TLS = True           # TLS 사용
#     EMAIL_HOST_USER = 'a46884334@gmail.com'
#     EMAIL_HOST_PASSWORD = GMAIL_APP_PASSWORD

# 추가 이메일 서비스 설정 (참고용)
GMAIL_EMAIL_HOST = 'smtp.gmail.com'
NAVER_EMAIL_HOST = 'smtp.naver.com'
DAUM_EMAIL_HOST = 'smtp.daum.net'
GMAIL_EMAIL_PORT = 587
NAVER_EMAIL_PORT = 587
DAUM_EMAIL_PORT = 465


ALLOWED_HOSTS = ['localhost', '192.168.100.76', '172.30.1.19', '127.0.0.1', '13.124.116.146', '43.203.40.252', 'namatji.com', 'www.namatji.com', 'xn--jj0bw47b70a.com', 'www.xn--jj0bw47b70a.com', 'salesmate.ai.kr', 'www.salesmate.ai.kr']


INSTALLED_APPS = [
    "PO",
    "main",
    "po_admin",
    "counsel",
    "board",
    "search",
    "member",
    "blog",
    "diary",
    "salesmate",
    
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django_crontab",
    'django.contrib.humanize',
    "corsheaders",

    # Allauth
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.kakao",

    # AWS S3
    "storages",
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'kakao': {
        'SCOPE': [
            'profile_nickname',
            'profile_image',
            'account_email',
            'talk_message',

        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
    }
}

AWS_ACCESS_KEY_ID = AWS_S3_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = AWS_S3_SECRET_KEY
AWS_STORAGE_BUCKET_NAME = AWS_S3_BUCKET_NAME
AWS_S3_REGION_NAME = AWS_S3_REGION
AWS_S3_SIGNATURE_VERSION = AWS_S3_SIGNATURE_VERSION
AWS_LOCATION = AWS_LOCATION
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

# 매일 18시마다 bizinfo api data update, * * * * * 순서대로 분, 시, 일, 월, 요일
CRONJOBS = [
    ('30 18 * * *', 'django.core.management.call_command', ['update_bizinfo']), #매일 18시 30분
    
    ('0 8 * * 1', 'django.core.management.call_command', ['update_biztop']), #매주 월요일 08시
    
    ('0 10 * * *', 'django.core.management.call_command', ['solapi']), #매일 10시
    ('0 10 * * *', 'django.core.management.call_command', ['solapi_date_over']), #매일 10시
]

SITE_ID = 18 #sitemap 

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'allauth.account.middleware.AccountMiddleware',
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

SOCIALACCOUNT_ADAPTER = 'PO.adapters.MySocialAccountAdapter'
SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_REDIRECT_URL = "/member/popup-close/"
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True 

WSGI_APPLICATION = "PO.wsgi.application"

# 캐시 설정 (Redis 사용 - 멀티프로세스 환경에서 상태 공유)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'TIMEOUT': 1800,  # 30분
        'KEY_PREFIX': 'po_cache',
        'VERSION': 1,
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'po_db',  # 데이터베이스 이름
        'USER': 'po_db',        # MySQL 계정 아이디
        'PASSWORD': MYSQL_PASSWORD,    # MySQL 계정 비밀번호
        'HOST': MYSQL_HOST_IP,  # MySQL 호스트 IP
        'PORT': '3306',         # MySQL 포트번호
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
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

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul" # 서울시간 기준

USE_I18N = True

USE_L10N = True

USE_TZ = False

# 파일 인코딩 설정
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# 세션 설정
SESSION_COOKIE_AGE = 10800  # 3시간 (초 단위: 3 * 60 * 60 = 10800)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 브라우저 종료 시 세션 만료

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

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'diary': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

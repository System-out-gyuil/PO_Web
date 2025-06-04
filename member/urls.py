from django.urls import path
from .views import KakaoLoginView, PopupCloseView, WhoAmIView

urlpatterns = [
    path('', KakaoLoginView.as_view(), name='kakao_login'),  # 기본은 로그인 페이지
    path('popup-close/', PopupCloseView.as_view(), name='popup_close'),
    path('whoami/', WhoAmIView.as_view(), name='whoami'),
]

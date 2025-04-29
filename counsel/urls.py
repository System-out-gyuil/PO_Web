from django.urls import path
from .views import CounselFormView, ThankYouView

urlpatterns = [
    path('', CounselFormView.as_view(), name='counsel_form'),
    path('thank-you/', ThankYouView.as_view(), name='thank_you'),  # 추가
]

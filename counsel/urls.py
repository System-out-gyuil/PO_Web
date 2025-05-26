from django.urls import path
from .views import CounselFormView, InquiryView

urlpatterns = [
    path('', CounselFormView.as_view(), name='counsel_form'),
    path('inquiry/', InquiryView.as_view(), name='inquiry'),
]

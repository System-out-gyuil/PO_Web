from django.urls import path
from .views import CounselFormView

urlpatterns = [
    path('', CounselFormView.as_view(), name='counsel_form'),
]

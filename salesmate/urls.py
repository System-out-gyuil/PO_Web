from django.urls import path
from . import views

app_name = 'salesmate'

urlpatterns = [
  path('', views.SalesmateView.as_view(), name='salesmate_main'),
]
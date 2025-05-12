# board/urls.py
from django.urls import path
from .views import BoardView, BoardDetailView

app_name = 'board'

urlpatterns = [
    path('', BoardView.as_view(), name='list'),
    path('detail/<str:pblanc_id>/', BoardDetailView.as_view(), name='detail'),
]

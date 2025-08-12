# board/urls.py
from django.urls import path, re_path
from django.views.generic import RedirectView
from .views import BoardView, BoardDetailView

app_name = 'board'

urlpatterns = [
    # /board/PBLN_ 또는 /board/PBLN_숫자(or문자열)/ => /board/ 로 301
    re_path(
        r"^PBLN_(?:\w+)?/?$",
        RedirectView.as_view(pattern_name="board:list", permanent=True),  # /board/ 로 301
    ),

    path("", BoardView.as_view(), name="list"),
    path("detail/<str:pblanc_id>/", BoardDetailView.as_view(), name="detail"),
]

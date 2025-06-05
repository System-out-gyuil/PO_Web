from django.urls import path
from .views import BlogView, BlogGPTAPIView, BlogWriteView

app_name = 'blog'

urlpatterns = [
    path('', BlogView.as_view(), name='list'),
    path('naver-blog/', BlogGPTAPIView.as_view(), name='naver-blog'),
    path('naver-blog/write/', BlogWriteView.as_view(), name='naver-blog-write'),
]

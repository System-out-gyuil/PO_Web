from django.urls import path
from .views import BlogView, BlogGPTAPIView, DownloadZipView, SaveTxtView, BlogWriteView

app_name = 'blog'

urlpatterns = [
    path('', BlogView.as_view(), name='list'),
    path('naver-blog/', BlogGPTAPIView.as_view(), name='naver-blog'),
    path('naver-blog/save-txt/', SaveTxtView.as_view(), name='naver-blog-save-txt'),
    path('naver-blog/write/', BlogWriteView.as_view(), name='naver-blog-write'),
    path('naver-blog/download-zip/', DownloadZipView.as_view(), name='naver-blog-download-zip'),
]

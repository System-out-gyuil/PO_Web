from django.urls import path
from .views import AdminLoginView, AdminCounselListView, AdminCountListView

urlpatterns = [
    path('', AdminLoginView.as_view(), name='po_admin_login'),  # 기본은 로그인 페이지
    path('list/', AdminCounselListView.as_view(), name='po_admin_list'),  # 리스트 페이지
    path('count/', AdminCountListView.as_view(), name='po_admin_count'),  # 카운트 페이지
]

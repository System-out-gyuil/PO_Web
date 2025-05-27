from django.urls import path
from .views import AdminLoginView, AdminCounselListView, CountByDateView

urlpatterns = [
    path('', AdminLoginView.as_view(), name='po_admin_login'),  # 기본은 로그인 페이지
    path('list/', AdminCounselListView.as_view(), name='po_admin_list'),  # 리스트 페이지
    path("counts-by-date/", CountByDateView.as_view(), name="counts_by_date")
]

from django.urls import path
from .views import AdminLoginView, AdminCounselListView, CountByDateView, CustUserSaveView, CustUserUpdateView, CustUserPossibleProductView

urlpatterns = [
    path('', AdminLoginView.as_view(), name='po_admin_login'),  # 기본은 로그인 페이지
    path('list/', AdminCounselListView.as_view(), name='po_admin_list'),  # 리스트 페이지
    path("counts-by-date/", CountByDateView.as_view(), name="counts_by_date"),
    path("cust-user/save/", CustUserSaveView.as_view(), name="cust_user_save"),
    path("cust-user/update/", CustUserUpdateView.as_view(), name="cust_user_update"),
    path("cust-user/possible-product/", CustUserPossibleProductView.as_view(), name="cust_user_possible_product")
]

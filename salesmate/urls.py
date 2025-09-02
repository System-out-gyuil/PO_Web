from django.urls import path
from . import views

app_name = 'salesmate'

urlpatterns = [
    path('', views.SalesmateView.as_view(), name='salesmate_main'),
    path('login/', views.SalesmateLoginView.as_view(), name='salesmate_login'),
    path('signup/', views.SalesmateSignupView.as_view(), name='salesmate_signup'),
    path('check_email_duplicate/', views.SalesmateCheckEmailDuplicateView.as_view(), name='salesmate_check_email_duplicate'),
    path('send_verification_email/', views.SalesmateSendVerificationEmailView.as_view(), name='salesmate_send_verification_email'),
    path('verify_email/', views.SalesmateVerifyEmailView.as_view(), name='salesmate_verify_email'),
    path('logout/', views.SalesmateLogoutView.as_view(), name='salesmate_logout'),
    path('personal_info/', views.SalesmatePersonalInfoView.as_view(), name='salesmate_personal_info'),
    path('terms_of_service/', views.SalesmateTermsOfServiceView.as_view(), name='salesmate_terms_of_service'),
    path('admin/', views.SalesmateAdminView.as_view(), name='salesmate_admin'),
    path('admin/approve_user/', views.SalesmateApproveUserView.as_view(), name='salesmate_approve_user'),
    path('admin/reject_user/', views.SalesmateRejectUserView.as_view(), name='salesmate_reject_user'),
]
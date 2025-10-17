from django.urls import path
from . import views

from .login_views import LoginView, LogoutView, SignupView, ChangePasswordView, SendVerificationEmailView, VerifyEmailView, ForgotPasswordView, ResetPasswordView, CheckEmailDuplicateView, login_popup
from .main_views import DiaryMainView
from .file_handler import upload_file, delete_file, download_file, download_file_note
from .calendar_handlers import get_datetime_attributes, get_calendar_settings, save_calendar_settings, calendar_events
from .excel_handlers import preview_excel, upload_excel, download_excel_template
from .kanban_handlers import update_kanban_option_order, get_kanban_data, get_kanban_settings, save_kanban_settings, get_dropdown_attributes_for_kanban
from .attribute_handlers import delete_attribute_value, toggle_attribute_visibility, update_attribute_visibility, get_dropdown_attributes, add_attribute, delete_attribute, get_hidden_attributes, get_all_attributes, update_attribute_name, update_attribute_name
from .audio_handler import upload_audio_file, get_audio_files_by_date, delete_audio_file, update_audio_file_order, upload_note_file, delete_note_file, update_note_order_and_notes, get_file_preview_url_note, get_file_content_note, convert_hwp_to_pdf, get_file_preview_url, update_audio_text, update_audio_memo, update_audio_text_notes, update_audio_file_order_and_notes
from .cascade_handlers import toggle_cascade_attribute, get_cascade_attributes_list
from .auto_blog import blog_account_check_api
from .detail_openai import ai_chat, ai_chat_cache_clear, file_cache_management, performance_monitoring
from .admin_view import admin_dashboard, inquiry_list, inquiry_detail, alarm_list, alarm_create, alarm_edit, alarm_delete, inquiry_delete, admin_api, user_list, user_delete, user_toggle_admin, user_update_use_date, diary_count_list, diary_count_delete, class_form_list, class_form_delete, user_toggle_activate, log_list, log_export_excel, user_login_switch, payamount_list, payamount_update
from .ai_class_admin_views import ai_class_text_management, update_text_element, create_text_element, delete_text_element, get_text_element, get_all_text_elements, class_form_text_management, update_form_text_element, create_form_text_element, delete_form_text_element, get_form_text_element
from .diary_board import diary_board, get_announcements, get_announcement_detail, mark_as_read, download_announcement_file, announcement_detail_page, create_announcement, upload_announcement_file, get_announcement_file_url, get_announcement_download_url, announcement_category_list, announcement_category_create, announcement_category_delete, announcement_list_with_category, create_announcement_with_category, update_announcement, delete_announcement, download_s3_auto_blog_file
from .main_views import CompanyInfoView, PersonalInfoView, TermsOfServiceView
from .session_handlers import cleanup_session_cache_api, get_active_sessions_api
from .board_views import board_list_view, board_list_api, board_create, board_detail_view, board_file_upload, board_file_preview, board_file_download, board_detail_api, board_edit, board_categories_api, board_add_category, board_delete
from .funding_views import get_funding_recommendation, get_recommended_notices, update_debt_field, save_debt_details, update_expected_loans, update_loan_amount, get_debt_details, get_biz_recommendations, get_saved_biz_recommendations, save_biz_recommendations, clear_biz_recommendation_alerts
from .order import reorder_entries, save_column_order, update_detail_sort_order
from .hwp_convert import convert_hwp_to_pdf_board, convert_hwp_to_pdf
from .ai_class import ai_class, class_form, class_form_end
from .attribute_handlers import get_hidden_attributes, add_attribute, delete_attribute, update_attribute_name, update_attribute_visibility, get_dropdown_attributes, get_all_attributes
from .auto_docx import auto_docx, auto_docx_recommend, auto_docx_innovation, auto_docx_innovation_recommend
from .diary_use_preview import diary_use_preview
from .diary_pay import diary_pay
from .facebook_meta_db import facebook_meta_db
from .toss_payments import TossPaymentsView, TossPaymentsSuccessView, TossPaymentsFailView, PaymentAuthSuccessView, PaymentAuthFailView, SubscriptionManagementView, CancelSubscriptionView, UpdateBillingTypeView, RequestPaymentView, UnlinkCardView, RequestBillingAuthView
from .recommend_test import RecommendTestView

app_name = 'sales'

urlpatterns = [
    # API 엔드포인트를 최상단에 배치
    path('api/payment/auth-success/', PaymentAuthSuccessView.as_view(), name='payment_auth_success'),
    path('api/payment/auth-fail/', PaymentAuthFailView.as_view(), name='payment_auth_fail'),
    path('api/payment/request-payment/', RequestPaymentView.as_view(), name='request_payment'),
    path('api/payment/request-billing-auth/', RequestBillingAuthView.as_view(), name='request_billing_auth'),
    path('api/payment/unlink-card/', UnlinkCardView.as_view(), name='unlink_card'),
    path('test-payment/', RequestPaymentView.as_view(), name='test_payment'),
    
    # 일반 페이지들
    path('', DiaryMainView.as_view(), name='diary_main'),
    path('pay/', diary_pay, name='diary_pay'),
    path('toss_payments/', TossPaymentsView.as_view(), name='toss_payments'),
    path('toss-payments/success/', TossPaymentsSuccessView.as_view(), name='toss_payments_success'),
    path('toss-payments/fail/', TossPaymentsFailView.as_view(), name='toss_payments_fail'),
    
    # 구독 관리 관련 URL
    path('subscription/', SubscriptionManagementView.as_view(), name='subscription_management'),
    path('api/subscription/cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('api/subscription/update-billing-type/', UpdateBillingTypeView.as_view(), name='update_billing_type'),

    # 로그인 관련 URL
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login_popup/', login_popup, name='login_popup'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),

    path('check_login_status/', views.check_login_status, name='check_login_status'),
    path('get_current_user_id/', views.get_current_user_id, name='get_current_user_id'),
    
    # 이메일 인증 관련 URL
    path('send_verification_email/', SendVerificationEmailView.as_view(), name='send_verification_email'),
    path('verify_email/', VerifyEmailView.as_view(), name='verify_email'),
    path('verify_verification_code/', VerifyEmailView.as_view(), name='verify_verification_code'),
    path('check_email_duplicate/', CheckEmailDuplicateView.as_view(), name='check_email_duplicate'),
    
    # 비밀번호 찾기 관련 URL
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset_password/', ResetPasswordView.as_view(), name='reset_password'),
    
    # 테이블
    path('diary/', views.diary_list, name='diary_list'),
    path('regions/', views.region_list, name='region_list'),
    path('reorder/', reorder_entries, name='reorder_entries'),
    path('statuses/', views.status_list, name='status_list'),
    path('create_new_row/', views.create_new_row, name='create_new_row'),
    path('update_row_field/', views.update_row_field, name='update_row_field'),
    path('update_sales_field/', views.update_sales_field, name='update_sales_field'),
    path('dropdown_options/', views.dropdown_options, name='dropdown_options'),
    path('add_attribute/', add_attribute, name='add_attribute'),
    path('delete_attribute/', delete_attribute, name='delete_attribute'),
    path('get_user_attributes/', views.get_user_attributes, name='get_user_attributes'),
    path('get_kanban_data/', get_kanban_data, name='get_kanban_data'),
    path('save_column_order/', save_column_order, name='save_column_order'),
    path('delete_row/', views.delete_row, name='delete_row'),
    path('delete_attribute_value/', delete_attribute_value, name='delete_attribute_value'),
    path('entry_table_partial/', views.entry_table_partial, name='entry_table_partial'),
    path('toggle_attribute_visibility/', toggle_attribute_visibility, name='toggle_attribute_visibility'),
    path('get_hidden_attributes/', get_hidden_attributes, name='get_hidden_attributes'),
    path('get_all_attributes/', get_all_attributes, name='get_all_attributes'),
    path('get_dropdown_attributes/', get_dropdown_attributes, name='get_dropdown_attributes'),
    path('update_attribute_name/', update_attribute_name, name='update_attribute_name'),
    path('get_status_tabs/', views.get_status_tabs, name='get_status_tabs'),
    
    # hwp -> pdf 변환
    path('convert_hwp_to_pdf/', convert_hwp_to_pdf, name='convert_hwp_to_pdf'),
    path('convert_hwp_to_pdf_board/', convert_hwp_to_pdf_board, name='convert_hwp_to_pdf_board'),

    # 복제행 처리
    path('duplicate_row/', views.duplicate_row, name='duplicate_row'),
    path('get_dependent_rows/', views.get_dependent_rows, name='get_dependent_rows'),

    # 상세
    path('upload_file/', upload_file, name='upload_file'),
    path('download_file/<int:row_id>/<str:field_name>/<str:fileId>/', download_file, name='download_file'),
    path('delete_file/', delete_file, name='delete_file'),
    path('upload_audio_file/', upload_audio_file, name='upload_audio_file'),
    path('get_audio_files_by_date/', get_audio_files_by_date, name='get_audio_files_by_date'),
    path('delete_audio_file/', delete_audio_file, name='delete_audio_file'),
    path('update_audio_text/', update_audio_text, name='update_audio_text'),
    path('update_audio_memo/', update_audio_memo, name='update_audio_memo'),
    path('update_audio_file_order/', update_audio_file_order, name='update_audio_file_order'),
    path('update_expected_loans/', update_expected_loans, name='update_expected_loans'),
    path('update_loan_amount/', update_loan_amount, name='update_loan_amount'),
    path('update_debt_field/', update_debt_field, name='update_debt_field'),
    path('get_debt_details/<int:row_id>/', get_debt_details, name='get_debt_details'),
    path('save_debt_details/', save_debt_details, name='save_debt_details'),
    path('get_funding_recommendation/', get_funding_recommendation, name='get_funding_recommendation'),
    path('get_recommended_notices/', get_recommended_notices, name='get_recommended_notices'),
    path('get_biz_recommendations/', get_biz_recommendations, name='get_biz_recommendations'),
    path('get_saved_biz_recommendations/', get_saved_biz_recommendations, name='get_saved_biz_recommendations'),
    path('save_biz_recommendations/', save_biz_recommendations, name='save_biz_recommendations'),
    path('get_row_details/<int:row_id>/', views.get_row_details, name='get_row_details'),
    path('update_detail_sort_order/', update_detail_sort_order, name='update_detail_sort_order'),
    path('update_audio_text_notes/', update_audio_text_notes, name='update_audio_text_notes'),
    path('update_audio_file_order_and_notes/', update_audio_file_order_and_notes, name='update_audio_file_order_and_notes'),
    path('update_note_order_and_notes/', update_note_order_and_notes, name='update_note_order_and_notes'),
    path('get_file_preview_url/<str:row_id>/<str:field_name>/', get_file_preview_url, name='get_file_preview_url'),
    path('get_file_preview_url_note/<str:file_id>/', get_file_preview_url_note, name='get_file_preview_url_note'),
    path('get_file_content_note/<str:file_id>/', get_file_content_note, name='get_file_content_note'),
    path('upload_note_file/', upload_note_file, name='upload_note_file'),
    path('delete_note_file/', delete_note_file, name='delete_note_file'),
    path('clear_biz_recommendation_alerts/', clear_biz_recommendation_alerts, name='clear_biz_recommendation_alerts'),

    # 캘린더 설정 관련 API
    path('get_datetime_attributes/', get_datetime_attributes, name='get_datetime_attributes'),
    path('get_calendar_settings/', get_calendar_settings, name='get_calendar_settings'),
    path('save_calendar_settings/', save_calendar_settings, name='save_calendar_settings'),
    path('calendar_events/', calendar_events, name='calendar_events'),
    
    # Cascade 관련 API
    path('toggle_cascade_attribute/', toggle_cascade_attribute, name='toggle_cascade_attribute'),
    path('get_cascade_attributes_list/', get_cascade_attributes_list, name='get_cascade_attributes_list'),
    
    # 엑셀 파일 처리 관련 API
    path('preview_excel/', preview_excel, name='preview_excel'),
    path('upload_excel/', upload_excel, name='upload_excel'),
    path('download_excel_template/', download_excel_template, name='download_excel_template'),
    path('download_user_manual/', views.download_user_manual, name='download_user_manual'),

    # 칸반보드 관련 처리
    path('update_kanban_option_order/', update_kanban_option_order, name='update_kanban_option_order'),
    
    # 칸반보드 설정 관련 API
    path('get_kanban_settings/', get_kanban_settings, name='get_kanban_settings'),
    path('save_kanban_settings/', save_kanban_settings, name='save_kanban_settings'),
    path('get_dropdown_attributes_for_kanban/', get_dropdown_attributes_for_kanban, name='get_dropdown_attributes_for_kanban'),

    # 속성관리
    path('get_all_attributes/', get_all_attributes, name='get_all_attributes'),
    path('get_all_attributes/', get_all_attributes, name='get_all_attributes'),
    path('update_attribute_visibility/', update_attribute_visibility, name='update_attribute_visibility'),
    path('get_dropdown_attributes/', get_dropdown_attributes, name='get_dropdown_attributes'),
    
    path('save_column_width/', views.save_column_width, name='save_column_width'),
    path('get_column_widths/', views.get_column_widths, name='get_column_widths'),
    
    # 블로그 파일 업로드 관련 API
    path('cleanup_session_cache/', cleanup_session_cache_api, name='cleanup_session_cache'),
    path('get_active_sessions/', get_active_sessions_api, name='get_active_sessions'),
    path('blog_account_check_api/', blog_account_check_api, name='blog_account_check_api'),
    
    # AI 채팅 관련 API
    path('ai_chat/', ai_chat, name='ai_chat'),
    path('ai_chat_cache_clear/', ai_chat_cache_clear, name='ai_chat_cache_clear'),
    
    # 파일 캐시 관리 및 성능 모니터링 API
    path('file_cache_management/', file_cache_management, name='file_cache_management'),
    path('performance_monitoring/', performance_monitoring, name='performance_monitoring'),
    
    # 문의하기 관련 API
    path('submit_inquiry/', views.submit_inquiry, name='submit_inquiry'),
    path('download_file_note/<str:fileId>/', download_file_note, name='download_file_note'),
    
    # 게시판 관련 URL
    path('diary_board/', diary_board, name='diary_board'),
    path('diary_board/announcements/', get_announcements, name='get_announcements'),
    path('diary_board/announcement/<int:announcement_id>/', get_announcement_detail, name='get_announcement_detail'),
    path('diary_board/announcement/<int:announcement_id>/detail/', announcement_detail_page, name='announcement_detail_page'),
    path('diary_board/announcement/<int:announcement_id>/mark-read/', mark_as_read, name='mark_as_read'),
    path('diary_board/download/<path:saved_name>/', download_announcement_file, name='download_announcement_file'),
    path('diary_board/announcement/create/', create_announcement, name='create_announcement'),
    path('diary_board/announcement/upload-file/', upload_announcement_file, name='upload_announcement_file'),
    path('diary_board/announcement/file/<path:saved_name>/<str:action>/', get_announcement_file_url, name='get_announcement_file_url'),
    path('diary_board/announcement/download/<path:saved_name>/', get_announcement_download_url, name='get_announcement_download_url'),
    
    # 공고 게시판 카테고리 관련 URL
    path('diary_board/announcement/category/list/', announcement_category_list, name='announcement_category_list'),
    path('diary_board/announcement/category/create/', announcement_category_create, name='announcement_category_create'),
    path('diary_board/announcement/category/<int:category_id>/delete/', announcement_category_delete, name='announcement_category_delete'),
    
    # 공고 게시판 관련 URL (카테고리 지원)
    path('diary_board/announcement/', announcement_list_with_category, name='announcement_list_with_category'),
    path('diary_board/announcement/create/', create_announcement_with_category, name='create_announcement_with_category'),
    path('diary_board/announcement/<int:announcement_id>/update/', update_announcement, name='update_announcement'),
    path('diary_board/announcement/<int:announcement_id>/delete/', delete_announcement, name='delete_announcement'),
    
    # 게시판 관련 URL (일반 게시판)
    path('board_list/', board_list_view, name='board_list'),
    path('board/api/', board_list_api, name='board_list_api'),
    path('board/create/', board_create, name='board_create'),
    path('board/<int:board_id>/', board_detail_view, name='board_detail'),
    path('board/<int:board_id>/api/', board_detail_api, name='board_detail_api'),
    path('board/<int:board_id>/edit/', board_edit, name='board_edit'),
    path('board/<int:board_id>/delete/', board_delete, name='board_delete'),
    path('board/upload-file/', board_file_upload, name='board_file_upload'),
    path('board/file/<path:saved_name>/preview/', board_file_preview, name='board_file_preview'),
    path('board/file/<path:saved_name>/download/', board_file_download, name='board_file_download'),
    path('board/categories/', board_categories_api, name='board_categories_api'),
    path('board/add-category/', board_add_category, name='board_add_category'),
    # 알림 관련 URL
    path('diary_board/notifications/', views.get_notifications, name='get_notifications'),
    path('diary_board/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # 어드민 관련 URL
    path('diary_admin/board/', admin_dashboard, name='admin_dashboard'),
    path('diary_admin/inquiries/', inquiry_list, name='admin_inquiry_list'),
    path('diary_admin/inquiry/<int:inquiry_id>/', inquiry_detail, name='admin_inquiry_detail'),
    path('diary_admin/alarms/', alarm_list, name='admin_alarm_list'),
    path('diary_admin/alarm/create/', alarm_create, name='admin_alarm_create'),
    path('diary_admin/alarm/<int:alarm_id>/', alarm_edit, name='admin_alarm_edit'),
    path('diary_admin/alarm/<int:alarm_id>/delete/', alarm_delete, name='admin_alarm_delete'),
    path('diary_admin/inquiry/<int:inquiry_id>/delete/', inquiry_delete, name='admin_inquiry_delete'),
    path('diary_admin/api/', admin_api, name='admin_api'),
    path('diary_admin/users/', user_list, name='admin_user_list'),
    path('diary_admin/users/<int:user_id>/delete/', user_delete, name='admin_user_delete'),
    path('diary_admin/users/<int:user_id>/toggle_admin/', user_toggle_admin, name='admin_user_toggle_admin'),
    path('diary_admin/users/<int:user_id>/update_use_date/', user_update_use_date, name='admin_user_update_use_date'),
    path('diary_admin/diary_counts/', diary_count_list, name='diary_count_list'),
    path('diary_admin/diary_count/<int:diary_count_id>/delete/', diary_count_delete, name='diary_count_delete'),
    path('diary_admin/users/<int:user_id>/toggle_activate/', user_toggle_activate, name='user_toggle_activate'),
    path('diary_admin/users/<int:user_id>/login_switch/', user_login_switch, name='admin_user_login_switch'),
    path('diary_admin/logs/', log_list, name='admin_log_list'),
    path('diary_admin/logs/export/', log_export_excel, name='admin_log_export'),
    path('diary_admin/payamounts/', payamount_list, name='admin_payamount_list'),
    path('diary_admin/payamount/<int:payamount_id>/update/', payamount_update, name='admin_payamount_update'),
    # 회사 소개 관련 URL
    path('company_info/', CompanyInfoView.as_view(), name='company_info'),
    path('personal_info/', PersonalInfoView.as_view(), name='personal_info'),
    path('terms_of_service/', TermsOfServiceView.as_view(), name='terms_of_service'),

    # AI 법인영업 강의 관련 URL
    path('class/', ai_class, name='ai_class'),
    path('class_form/', class_form, name='class_form'),

    # AI 클래스 텍스트 관리 관련 URL (관리자 전용)
    path('diary_admin/ai_class/text/', ai_class_text_management, name='admin_ai_class_text_management'),
    path('diary_admin/ai_class/text/update/', update_text_element, name='admin_update_text_element'),
    path('diary_admin/ai_class/text/create/', create_text_element, name='admin_create_text_element'),
    path('diary_admin/ai_class/text/<int:element_id>/', get_text_element, name='admin_get_text_element'),
    path('diary_admin/ai_class/text/<int:element_id>/delete/', delete_text_element, name='admin_delete_text_element'),
    path('diary_admin/ai_class/text/all/', get_all_text_elements, name='admin_get_all_text_elements'),
    
    # AI 클래스 폼 텍스트 관리 관련 URL (관리자 전용)
    path('diary_admin/ai_class/form_text/', class_form_text_management, name='admin_class_form_text_management'),
    path('diary_admin/ai_class/form_text/update/', update_form_text_element, name='admin_update_form_text_element'),
    path('diary_admin/ai_class/form_text/create/', create_form_text_element, name='admin_create_form_text_element'),
    path('diary_admin/ai_class/form_text/<int:element_id>/', get_form_text_element, name='admin_get_form_text_element'),
    path('diary_admin/ai_class/form_text/<int:element_id>/delete/', delete_form_text_element, name='admin_delete_form_text_element'),

    # 원데이 클래스 관리 관련 URL
    path('diary_admin/class_forms/', class_form_list, name='admin_class_forms'),
    path('diary_admin/class_form/<int:class_form_id>/delete/', class_form_delete, name='admin_class_form_delete'),
    path('class_form_end/', class_form_end, name='class_form_end'),

    # 기업마당 공고
    path('bizinfo/', views.bizinfo, name='bizinfo'),
    
    # 일별 조회수 관련 API
    path('api/daily_view_counts/', views.get_daily_view_counts, name='daily_view_counts'),
    path('api/daily_view_details/', views.get_daily_view_details, name='daily_view_details'),

    # S3 자동 블로그 파일 다운로드
    path('diary_board/download_s3_auto_blog_file/', download_s3_auto_blog_file, name='download_s3_auto_blog_file'),

    # 자동 docx 생성
    path('auto_docx/', auto_docx, name='auto_docx'),
    path('auto_docx_recommend/', auto_docx_recommend, name='auto_docx_recommend'),
    path('auto_docx_innovation/', auto_docx_innovation, name='auto_docx_innovation'),
    path('auto_docx_innovation_recommend/', auto_docx_innovation_recommend, name='auto_docx_innovation_recommend'),

    # 다이어리 사용법 미리보기
    path('diary_use_preview/', diary_use_preview, name='diary_use_preview'),

    # 페이스북 메타 데이터
    path('facebook_meta_db/', facebook_meta_db, name='facebook_meta_db'),

    # 추천 테스트 관련 URL
    path('recommend_test/', RecommendTestView.as_view(), name='recommend_test'),
] 

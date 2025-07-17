from django.urls import path
from . import views
from .views import upload_note_file, delete_note_file, update_note_order_and_notes, get_file_preview_url, get_file_preview_url_note
from .login_views import LoginView, LogoutView, SignupView
from .main_views import DiaryMainView
from .file_handler import upload_file, delete_file, download_file
from .calendar_handlers import get_datetime_attributes, get_calendar_settings, save_calendar_settings, calendar_events
from .excel_handlers import preview_excel, upload_excel
from .kanban_handlers import update_kanban_option_order, get_kanban_data
from .attribute_handlers import delete_attribute_value, toggle_attribute_visibility, update_attribute_visibility, get_dropdown_attributes, add_attribute, delete_attribute
from .audio_handler import upload_audio_file, get_audio_files_by_date, delete_audio_file, update_audio_file_order
from .cascade_handlers import toggle_cascade_attribute, get_cascade_attributes_list

urlpatterns = [
    path('', DiaryMainView.as_view(), name='diary_main'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('diary/', views.diary_list, name='diary_list'),
    path('fu_events/', views.fu_events, name='fu_events'),
    path('fu_memo/<int:entry_id>/', views.fu_memo, name='fu_memo'),
    path('categories/', views.category_list, name='category_list'),
    path('regions/', views.region_list, name='region_list'),
    path('create/', views.create_entry, name='create_entry'),
    path('reorder/', views.reorder_entries, name='reorder_entries'),
    path('statuses/', views.status_list, name='status_list'),
    path('board/', views.board_view, name='board_view'),
    path('update/', views.update_entry, name='update_entry'),
    path('create_new_row/', views.create_new_row, name='create_new_row'),
    path('update_row_field/', views.update_row_field, name='update_row_field'),
    path('update_sales_field/', views.update_sales_field, name='update_sales_field'),
    path('dropdown_options/', views.dropdown_options, name='dropdown_options'),
    path('add_attribute/', add_attribute, name='add_attribute'),
    path('delete_attribute/', delete_attribute, name='delete_attribute'),
    path('get_row_details/<int:row_id>/', views.get_row_details, name='get_row_details'),
    path('get_user_attributes/', views.get_user_attributes, name='get_user_attributes'),
    path('get_kanban_data/', get_kanban_data, name='get_kanban_data'),
    path('upload_file/', upload_file, name='upload_file'),
    path('download_file/<int:row_id>/<str:field_name>/', download_file, name='download_file'),
    path('delete_file/', delete_file, name='delete_file'),
    path('upload_audio_file/', upload_audio_file, name='upload_audio_file'),
    path('get_audio_files_by_date/', get_audio_files_by_date, name='get_audio_files_by_date'),
    path('delete_audio_file/', delete_audio_file, name='delete_audio_file'),
    path('update_audio_text/', views.update_audio_text, name='update_audio_text'),
    path('update_audio_memo/', views.update_audio_memo, name='update_audio_memo'),
    path('update_audio_file_order/', update_audio_file_order, name='update_audio_file_order'),
    path('update_expected_loans/', views.update_expected_loans, name='update_expected_loans'),
    path('update_loan_amount/', views.update_loan_amount, name='update_loan_amount'),
    path('update_debt_field/', views.update_debt_field, name='update_debt_field'),
    path('get_debt_details/<int:row_id>/', views.get_debt_details, name='get_debt_details'),
    path('save_debt_details/', views.save_debt_details, name='save_debt_details'),
    path('get_funding_recommendation/', views.get_funding_recommendation, name='get_funding_recommendation'),
    path('get_recommended_notices/', views.get_recommended_notices, name='get_recommended_notices'),
    path('save_column_order/', views.save_column_order, name='save_column_order'),
    path('delete_row/', views.delete_row, name='delete_row'),
    path('delete_attribute_value/', delete_attribute_value, name='delete_attribute_value'),
    path('duplicate_row/', views.duplicate_row, name='duplicate_row'),
    path('update_audio_text_notes/', views.update_audio_text_notes, name='update_audio_text_notes'),
    path('update_audio_file_order_and_notes/', views.update_audio_file_order_and_notes, name='update_audio_file_order_and_notes'),
    path('entry_table_partial/', views.entry_table_partial, name='entry_table_partial'),
    path('toggle_attribute_visibility/', toggle_attribute_visibility, name='toggle_attribute_visibility'),
    path('get_hidden_attributes/', views.get_hidden_attributes, name='get_hidden_attributes'),
    path('get_all_attributes/', views.get_all_attributes, name='get_all_attributes'),
    path('get_dropdown_attributes/', get_dropdown_attributes, name='get_dropdown_attributes'),
    path('update_attribute_name/', views.update_attribute_name, name='update_attribute_name'),
    path('get_status_tabs/', views.get_status_tabs, name='get_status_tabs'),
    path('upload_note_file/', upload_note_file, name='upload_note_file'),
    path('delete_note_file/', delete_note_file, name='delete_note_file'),
    path('update_note_order_and_notes/', update_note_order_and_notes, name='update_note_order_and_notes'),
    path('get_file_preview_url/<str:row_id>/<str:field_name>/', get_file_preview_url, name='get_file_preview_url'),
    path('get_file_preview_url_note/<str:file_id>/', get_file_preview_url_note, name='get_file_preview_url_note'),
    
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

    # 칸반보드 관련 처리
    path('update_kanban_option_order/', update_kanban_option_order, name='update_kanban_option_order'),

    # 속성관리
    path('get_all_attributes/', views.get_all_attributes, name='get_all_attributes'),
    path('update_attribute_visibility/', update_attribute_visibility, name='update_attribute_visibility'),
    path('get_dropdown_attributes/', get_dropdown_attributes, name='get_dropdown_attributes'),
    
    path('save_column_width/', views.save_column_width, name='save_column_width'),
] 

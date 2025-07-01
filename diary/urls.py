from django.urls import path
from . import views

urlpatterns = [
    path('', views.diary_list, name='diary_list'),
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
    path('dropdown_options/', views.dropdown_options, name='dropdown_options'),
    path('add_attribute/', views.add_attribute, name='add_attribute'),
    path('delete_attribute/', views.delete_attribute, name='delete_attribute'),
    path('get_row_details/<int:row_id>/', views.get_row_details, name='get_row_details'),
    path('debug_fu_data/', views.debug_fu_data, name='debug_fu_data'),
    path('get_user_attributes/', views.get_user_attributes, name='get_user_attributes'),
    path('get_kanban_data/', views.get_kanban_data, name='get_kanban_data'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('download_file/<int:row_id>/<str:field_name>/', views.download_file, name='download_file'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('upload_audio_file/', views.upload_audio_file, name='upload_audio_file'),
] 
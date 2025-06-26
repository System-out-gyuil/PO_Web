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
] 
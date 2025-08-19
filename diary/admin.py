from django.contrib import admin
from .models import Alarm, AlarmCategory

# Register your models here.

@admin.register(AlarmCategory)
class AlarmCategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'user', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['category_name']
    ordering = ['-created_at']

@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

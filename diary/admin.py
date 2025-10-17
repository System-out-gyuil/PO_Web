from django.contrib import admin
from .models import Alarm, AlarmCategory, AIClassContent, AIClassTextElement

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

@admin.register(AIClassContent)
class AIClassContentAdmin(admin.ModelAdmin):
    list_display = ['section', 'title', 'updated_at']
    list_filter = ['section', 'created_at', 'updated_at']
    search_fields = ['title', 'subtitle', 'description', 'content']
    ordering = ['section']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('section', 'title', 'subtitle')
        }),
        ('내용', {
            'fields': ('description', 'content')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AIClassTextElement)
class AIClassTextElementAdmin(admin.ModelAdmin):
    list_display = ['key', 'description', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['key', 'text', 'description']
    ordering = ['key']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('key', 'description')
        }),
        ('텍스트 내용', {
            'fields': ('text',)
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

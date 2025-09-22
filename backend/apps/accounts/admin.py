from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    """Admin configuration for UserProfile"""
    
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'github_username', 'has_github_token', 'has_ai_keys',
        'is_active', 'created_at'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'github_username')
    ordering = ('-created_at',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('GitHub Integration', {
            'fields': ('github_username', '_github_token')
        }),
        ('AI Integration', {
            'fields': ('_openai_api_key', '_anthropic_api_key')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_github_token(self, obj):
        return obj.has_github_token()
    has_github_token.boolean = True
    has_github_token.short_description = 'GitHub Token'
    
    def has_ai_keys(self, obj):
        return obj.has_ai_keys()
    has_ai_keys.boolean = True
    has_ai_keys.short_description = 'AI Keys'
from django.contrib import admin
from .models import AIAgent, AgentTemplate


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'ai_provider', 'model_name', 'is_active', 'created_at']
    list_filter = ['ai_provider', 'is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user', 'is_active')
        }),
        ('AI Configuration', {
            'fields': ('ai_provider', 'model_name', 'temperature', 'max_tokens')
        }),
        ('Prompt Configuration', {
            'fields': ('system_prompt', 'analysis_prompt')
        }),
        ('Analysis Settings', {
            'fields': ('include_file_changes', 'include_commit_messages', 'focus_areas')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(AgentTemplate)
class AgentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_public', 'usage_count', 'created_at']
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'tags']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'tags', 'is_public')
        }),
        ('Template Configuration', {
            'fields': ('default_ai_provider', 'default_model', 'default_temperature', 'default_max_tokens')
        }),
        ('Prompt Templates', {
            'fields': ('system_prompt_template', 'analysis_prompt_template')
        }),
        ('Default Settings', {
            'fields': ('default_include_file_changes', 'default_include_commit_messages', 'default_focus_areas')
        }),
        ('Statistics', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['make_public', 'make_private']
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} templates were successfully made public.')
    make_public.short_description = "Make selected templates public"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} templates were successfully made private.')
    make_private.short_description = "Make selected templates private"
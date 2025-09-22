from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AnalysisTask, AnalysisResult, AnalysisExport, AnalysisTemplate


@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'repository_name', 'agent_name', 'status', 'progress_percentage', 'created_at']
    list_filter = ['status', 'created_at', 'agent__ai_provider']
    search_fields = ['user__username', 'repository__name', 'agent__name', 'developer_filter']
    readonly_fields = ['id', 'celery_task_id', 'created_at', 'started_at', 'completed_at', 'duration_display']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'repository', 'agent')
        }),
        ('Analysis Configuration', {
            'fields': ('developer_filter', 'date_from', 'date_to')
        }),
        ('Task Status', {
            'fields': ('status', 'progress_percentage', 'current_step', 'error_message')
        }),
        ('Task Management', {
            'fields': ('celery_task_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'duration_display'),
            'classes': ('collapse',)
        })
    )
    
    def repository_name(self, obj):
        return obj.repository.name
    repository_name.short_description = 'Repository'
    
    def agent_name(self, obj):
        return obj.agent.name
    agent_name.short_description = 'Agent'
    
    def duration_display(self, obj):
        if obj.duration:
            return str(obj.duration)
        return 'N/A'
    duration_display.short_description = 'Duration'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    actions = ['cancel_tasks']
    
    def cancel_tasks(self, request, queryset):
        cancelled_count = 0
        for task in queryset.filter(status__in=['pending', 'processing']):
            if task.celery_task_id:
                from celery import current_app
                current_app.control.revoke(task.celery_task_id, terminate=True)
            task.status = 'cancelled'
            task.save(update_fields=['status'])
            cancelled_count += 1
        
        self.message_user(request, f'{cancelled_count} tasks were cancelled.')
    cancel_tasks.short_description = "Cancel selected tasks"


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['task_id', 'repository_name', 'total_commits', 'tokens_used', 'analysis_cost', 'created_at']
    list_filter = ['created_at', 'task__agent__ai_provider']
    search_fields = ['task__repository__name', 'task__user__username']
    readonly_fields = ['task', 'tokens_used', 'analysis_cost', 'created_at', 'view_analysis']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('task',)
        }),
        ('Statistics', {
            'fields': ('total_commits', 'total_additions', 'total_deletions', 'total_files_changed')
        }),
        ('Analysis Data', {
            'fields': ('view_analysis', 'developer_stats')
        }),
        ('Cost Information', {
            'fields': ('tokens_used', 'analysis_cost')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def task_id(self, obj):
        return str(obj.task.id)[:8] + '...'
    task_id.short_description = 'Task ID'
    
    def repository_name(self, obj):
        return obj.task.repository.name
    repository_name.short_description = 'Repository'
    
    def view_analysis(self, obj):
        if obj.formatted_analysis:
            # Truncate for display
            analysis = obj.formatted_analysis[:200] + '...' if len(obj.formatted_analysis) > 200 else obj.formatted_analysis
            return format_html('<div style="max-width: 400px; white-space: pre-wrap;">{}</div>', analysis)
        return 'No analysis available'
    view_analysis.short_description = 'Analysis Preview'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(task__user=request.user)


@admin.register(AnalysisExport)
class AnalysisExportAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'format', 'status', 'file_size_mb', 'created_at', 'expires_at']
    list_filter = ['format', 'status', 'created_at', 'expires_at']
    search_fields = ['user__username', 'analysis_result__task__repository__name']
    readonly_fields = ['id', 'file_size_mb', 'created_at', 'completed_at', 'download_link']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'analysis_result')
        }),
        ('Export Configuration', {
            'fields': ('format', 'include_charts', 'include_raw_data')
        }),
        ('Export Status', {
            'fields': ('status', 'file_path', 'file_size', 'file_size_mb', 'download_link')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "0 MB"
    file_size_mb.short_description = 'File Size'
    
    def download_link(self, obj):
        if obj.status == 'completed' and obj.file_path:
            url = f'/media/exports/{obj.file_path}'
            return format_html('<a href="{}" target="_blank">Download</a>', url)
        return 'Not available'
    download_link.short_description = 'Download'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    actions = ['delete_expired_exports']
    
    def delete_expired_exports(self, request, queryset):
        from django.utils import timezone
        expired_exports = queryset.filter(expires_at__lt=timezone.now())
        
        deleted_count = 0
        for export in expired_exports:
            if export.file_path:
                import os
                from django.conf import settings
                file_path = os.path.join(settings.MEDIA_ROOT, 'exports', export.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            export.delete()
            deleted_count += 1
        
        self.message_user(request, f'{deleted_count} expired exports were deleted.')
    delete_expired_exports.short_description = "Delete expired exports"


@admin.register(AnalysisTemplate)
class AnalysisTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'agent_name', 'is_public', 'usage_count', 'created_at']
    list_filter = ['is_public', 'created_at', 'agent__ai_provider']
    search_fields = ['name', 'description', 'user__username', 'agent__name']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user', 'agent', 'is_public')
        }),
        ('Default Configuration', {
            'fields': ('default_date_range_days', 'default_developer_filter')
        }),
        ('Export Preferences', {
            'fields': ('default_export_format', 'default_include_charts', 'default_include_raw_data')
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
    
    def agent_name(self, obj):
        return obj.agent.name
    agent_name.short_description = 'Agent'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    actions = ['make_public', 'make_private']
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} templates were made public.')
    make_public.short_description = "Make selected templates public"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} templates were made private.')
    make_private.short_description = "Make selected templates private"
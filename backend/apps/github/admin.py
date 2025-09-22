from django.contrib import admin
from .models import Repository, Commit, CommitFile


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """Admin configuration for Repository"""
    
    list_display = (
        'name', 'user', 'language', 'stars_count', 'forks_count',
        'is_private', 'sync_status', 'last_synced', 'github_updated_at'
    )
    list_filter = (
        'language', 'is_private', 'is_fork', 'is_archived',
        'sync_status', 'github_created_at'
    )
    search_fields = ('name', 'full_name', 'description', 'user__username')
    ordering = ('-github_updated_at',)
    readonly_fields = (
        'github_id', 'commits_count', 'contributors_count',
        'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'full_name', 'description')
        }),
        ('GitHub Data', {
            'fields': (
                'github_id', 'language', 'stars_count', 'forks_count',
                'watchers_count', 'size'
            )
        }),
        ('Status', {
            'fields': ('is_private', 'is_fork', 'is_archived')
        }),
        ('URLs', {
            'fields': ('html_url', 'clone_url')
        }),
        ('Timestamps', {
            'fields': (
                'github_created_at', 'github_updated_at', 'github_pushed_at',
                'last_synced', 'sync_status'
            )
        }),
        ('Statistics', {
            'fields': ('commits_count', 'contributors_count'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class CommitFileInline(admin.TabularInline):
    """Inline admin for CommitFile"""
    model = CommitFile
    extra = 0
    readonly_fields = ('changes',)


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    """Admin configuration for Commit"""
    
    list_display = (
        'short_sha', 'repository', 'author_name', 'commit_date',
        'additions', 'deletions', 'total_changes', 'files_changed'
    )
    list_filter = ('commit_date', 'repository__language', 'author_name')
    search_fields = ('sha', 'message', 'author_name', 'author_email')
    ordering = ('-commit_date',)
    readonly_fields = ('total_changes', 'created_at', 'updated_at')
    inlines = [CommitFileInline]
    
    fieldsets = (
        ('Commit Info', {
            'fields': ('repository', 'sha', 'message', 'html_url')
        }),
        ('Author', {
            'fields': ('author_name', 'author_email', 'commit_date')
        }),
        ('Committer', {
            'fields': ('committer_name', 'committer_email')
        }),
        ('Statistics', {
            'fields': ('additions', 'deletions', 'total_changes', 'files_changed')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_sha(self, obj):
        return obj.sha[:8]
    short_sha.short_description = 'SHA'


@admin.register(CommitFile)
class CommitFileAdmin(admin.ModelAdmin):
    """Admin configuration for CommitFile"""
    
    list_display = (
        'filename', 'commit_sha', 'status', 'additions', 'deletions', 'changes'
    )
    list_filter = ('status',)
    search_fields = ('filename', 'commit__sha')
    readonly_fields = ('changes',)
    
    def commit_sha(self, obj):
        return obj.commit.sha[:8]
    commit_sha.short_description = 'Commit SHA'
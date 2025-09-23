from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.conf import settings

from apps.accounts.models import UserProfile
from apps.github.models import Repository, Commit
from apps.agents.models import AIAgent, AgentTemplate
from apps.analysis.models import AnalysisTask, AnalysisResult, AnalysisExport


class GitHubAnalyzerAdminSite(AdminSite):
    """Custom admin site for GitHub Analyzer"""
    
    site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'GitHub Analyzer Admin')
    site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'GitHub Analyzer')
    index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Welcome to GitHub Analyzer Administration')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view with statistics"""
        
        # User statistics
        total_users = UserProfile.objects.count()
        active_users = UserProfile.objects.filter(is_active=True).count()
        users_with_github = UserProfile.objects.exclude(github_username__isnull=True).exclude(github_username='').count()
        
        # Repository statistics
        total_repositories = Repository.objects.count()
        public_repos = Repository.objects.filter(is_private=False).count()
        private_repos = Repository.objects.filter(is_private=True).count()
        
        # Commit statistics
        total_commits = Commit.objects.count()
        total_additions = Commit.objects.aggregate(Sum('additions'))['additions__sum'] or 0
        total_deletions = Commit.objects.aggregate(Sum('deletions'))['deletions__sum'] or 0
        
        # Agent statistics
        total_agents = AIAgent.objects.count()
        active_agents = AIAgent.objects.filter(is_active=True).count()
        agent_templates = AgentTemplate.objects.count()
        public_templates = AgentTemplate.objects.filter(is_public=True).count()
        
        # Analysis statistics
        total_analyses = AnalysisTask.objects.count()
        completed_analyses = AnalysisTask.objects.filter(status='completed').count()
        pending_analyses = AnalysisTask.objects.filter(status='pending').count()
        processing_analyses = AnalysisTask.objects.filter(status='processing').count()
        
        # Recent activity
        recent_users = UserProfile.objects.order_by('-created_at')[:5]
        recent_repositories = Repository.objects.order_by('-created_at')[:5]
        recent_analyses = AnalysisTask.objects.order_by('-created_at')[:5]
        
        # Top repositories by commits
        top_repositories = Repository.objects.annotate(
            commit_count=Count('commits')
        ).order_by('-commit_count')[:5]
        
        # AI provider usage
        ai_provider_stats = AIAgent.objects.values('ai_provider').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context = {
            'title': 'Dashboard',
            'user_stats': {
                'total': total_users,
                'active': active_users,
                'with_github': users_with_github,
            },
            'repo_stats': {
                'total': total_repositories,
                'public': public_repos,
                'private': private_repos,
            },
            'commit_stats': {
                'total': total_commits,
                'additions': total_additions,
                'deletions': total_deletions,
            },
            'agent_stats': {
                'total': total_agents,
                'active': active_agents,
                'templates': agent_templates,
                'public_templates': public_templates,
            },
            'analysis_stats': {
                'total': total_analyses,
                'completed': completed_analyses,
                'pending': pending_analyses,
                'processing': processing_analyses,
            },
            'recent_users': recent_users,
            'recent_repositories': recent_repositories,
            'recent_analyses': recent_analyses,
            'top_repositories': top_repositories,
            'ai_provider_stats': ai_provider_stats,
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    def index(self, request, extra_context=None):
        """Override index to add dashboard link"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = 'admin:dashboard'
        return super().index(request, extra_context)


# Create custom admin site instance
admin_site = GitHubAnalyzerAdminSite(name='github_analyzer_admin')

# Register all models with the custom admin site
from apps.accounts.admin import UserProfileAdmin
from apps.github.admin import RepositoryAdmin, CommitAdmin, CommitFileAdmin
from apps.agents.admin import AIAgentAdmin, AgentTemplateAdmin
from apps.analysis.admin import (
    AnalysisTaskAdmin, AnalysisResultAdmin, 
    AnalysisExportAdmin, AnalysisTemplateAdmin
)

admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(Repository, RepositoryAdmin)
admin_site.register(Commit, CommitAdmin)
admin_site.register(AIAgent, AIAgentAdmin)
admin_site.register(AgentTemplate, AgentTemplateAdmin)
admin_site.register(AnalysisTask, AnalysisTaskAdmin)
admin_site.register(AnalysisResult, AnalysisResultAdmin)
admin_site.register(AnalysisExport, AnalysisExportAdmin)
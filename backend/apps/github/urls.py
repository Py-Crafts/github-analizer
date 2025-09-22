from django.urls import path
from .views import (
    RepositoryListView,
    RepositoryDetailView,
    SyncRepositoriesView,
    CommitListView,
    SyncCommitsView,
    RepositoryStatsView,
    DeveloperStatsView
)

urlpatterns = [
    path('repositories/', RepositoryListView.as_view(), name='repository-list'),
    path('repositories/<int:pk>/', RepositoryDetailView.as_view(), name='repository-detail'),
    path('repositories/<int:pk>/stats/', RepositoryStatsView.as_view(), name='repository-stats'),
    path('sync-repos/', SyncRepositoriesView.as_view(), name='sync-repositories'),
    
    path('commits/', CommitListView.as_view(), name='commit-list'),
    path('repositories/<int:repo_id>/sync-commits/', SyncCommitsView.as_view(), name='sync-commits'),
    
    path('developer-stats/', DeveloperStatsView.as_view(), name='developer-stats'),
]
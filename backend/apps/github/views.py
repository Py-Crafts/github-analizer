from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Repository, Commit
from .serializers import (
    RepositorySerializer,
    CommitSerializer,
    RepositoryStatsSerializer,
    DeveloperStatsSerializer,
    SyncStatusSerializer
)
from .tasks import sync_user_repositories, sync_repository_commits


class RepositoryListView(generics.ListAPIView):
    """List user's repositories"""
    
    serializer_class = RepositorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Repository.objects.filter(user=self.request.user)


class RepositoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Repository detail view"""
    
    serializer_class = RepositorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Repository.objects.filter(user=self.request.user)


class SyncRepositoriesView(generics.GenericAPIView):
    """Sync user repositories from GitHub"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if not user.has_github_token():
            return Response(
                {'error': 'GitHub token not configured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async task
        task = sync_user_repositories.delay(user.id)
        
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': 'Repository sync started'
        })


class CommitListView(generics.ListAPIView):
    """List commits with filtering"""
    
    serializer_class = CommitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Commit.objects.filter(repository__user=self.request.user)
        
        # Filter by repository
        repo_id = self.request.query_params.get('repository')
        if repo_id:
            queryset = queryset.filter(repository_id=repo_id)
        
        # Filter by author
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_name__icontains=author)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(commit_date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(commit_date__lte=end_date)
            except ValueError:
                pass
        
        return queryset.select_related('repository')


class SyncCommitsView(generics.GenericAPIView):
    """Sync commits for a specific repository"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, repo_id):
        try:
            repository = Repository.objects.get(
                id=repo_id,
                user=request.user
            )
        except Repository.DoesNotExist:
            return Response(
                {'error': 'Repository not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not request.user.has_github_token():
            return Response(
                {'error': 'GitHub token not configured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async task
        task = sync_repository_commits.delay(repository.id)
        
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': f'Commit sync started for {repository.name}'
        })


class RepositoryStatsView(generics.GenericAPIView):
    """Get repository statistics"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            repository = Repository.objects.get(
                id=pk,
                user=request.user
            )
        except Repository.DoesNotExist:
            return Response(
                {'error': 'Repository not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate statistics
        commits = repository.commits.all()
        
        stats = {
            'repository': RepositorySerializer(repository).data,
            'total_commits': commits.count(),
            'total_additions': commits.aggregate(Sum('additions'))['additions__sum'] or 0,
            'total_deletions': commits.aggregate(Sum('deletions'))['deletions__sum'] or 0,
            'total_changes': commits.aggregate(Sum('total_changes'))['total_changes__sum'] or 0,
        }
        
        # Contributors
        contributors = commits.values('author_name', 'author_email').annotate(
            commit_count=Count('id'),
            total_additions=Sum('additions'),
            total_deletions=Sum('deletions')
        ).order_by('-commit_count')
        
        stats['contributors'] = list(contributors)
        
        # Commit frequency (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_commits = commits.filter(commit_date__gte=thirty_days_ago)
        
        commit_frequency = {}
        for i in range(30):
            date = (timezone.now() - timedelta(days=i)).date()
            count = recent_commits.filter(commit_date__date=date).count()
            commit_frequency[date.isoformat()] = count
        
        stats['commit_frequency'] = commit_frequency
        
        # Language stats (simplified)
        stats['language_stats'] = {
            'primary_language': repository.language or 'Unknown'
        }
        
        serializer = RepositoryStatsSerializer(stats)
        return Response(serializer.data)


class DeveloperStatsView(generics.GenericAPIView):
    """Get developer statistics across all repositories"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get developer filter
        developer = request.query_params.get('developer')
        if not developer:
            return Response(
                {'error': 'Developer parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get commits for this developer
        commits = Commit.objects.filter(
            repository__user=user,
            author_name__icontains=developer
        )
        
        if not commits.exists():
            return Response(
                {'error': 'No commits found for this developer'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate statistics
        first_commit = commits.order_by('commit_date').first()
        last_commit = commits.order_by('-commit_date').first()
        
        stats = {
            'developer_name': first_commit.author_name,
            'developer_email': first_commit.author_email,
            'total_commits': commits.count(),
            'total_additions': commits.aggregate(Sum('additions'))['additions__sum'] or 0,
            'total_deletions': commits.aggregate(Sum('deletions'))['deletions__sum'] or 0,
            'total_changes': commits.aggregate(Sum('total_changes'))['total_changes__sum'] or 0,
            'repositories': list(commits.values_list('repository__name', flat=True).distinct()),
            'first_commit': first_commit.commit_date,
            'last_commit': last_commit.commit_date,
        }
        
        # Commit frequency (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_commits = commits.filter(commit_date__gte=thirty_days_ago)
        
        commit_frequency = {}
        for i in range(30):
            date = (timezone.now() - timedelta(days=i)).date()
            count = recent_commits.filter(commit_date__date=date).count()
            commit_frequency[date.isoformat()] = count
        
        stats['commit_frequency'] = commit_frequency
        
        serializer = DeveloperStatsSerializer(stats)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_status_view(request, task_id):
    """Get status of a Celery task"""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    response_data = {
        'task_id': task_id,
        'status': result.status,
        'message': 'Task in progress'
    }
    
    if result.ready():
        if result.successful():
            response_data['result'] = result.result
            response_data['message'] = 'Task completed successfully'
        else:
            response_data['message'] = f'Task failed: {str(result.result)}'
    elif result.state == 'PROGRESS':
        response_data.update(result.info)
    
    serializer = SyncStatusSerializer(response_data)
    return Response(serializer.data)
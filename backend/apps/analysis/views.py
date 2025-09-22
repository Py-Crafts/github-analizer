from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from datetime import timedelta
from .models import AnalysisTask, AnalysisResult, AnalysisExport, AnalysisTemplate
from .serializers import (
    AnalysisTaskSerializer,
    CreateAnalysisTaskSerializer,
    AnalysisResultSerializer,
    AnalysisExportSerializer,
    CreateAnalysisExportSerializer,
    AnalysisTemplateSerializer,
    AnalysisStatsSerializer,
    TaskProgressSerializer
)
from .tasks import run_analysis_task, create_export_task


class AnalysisTaskListCreateView(generics.ListCreateAPIView):
    """List and create analysis tasks"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateAnalysisTaskSerializer
        return AnalysisTaskSerializer
    
    def get_queryset(self):
        queryset = AnalysisTask.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by repository
        repository_id = self.request.query_params.get('repository')
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the analysis task
        task = AnalysisTask.objects.create(
            user=request.user,
            repository=serializer.validated_data['repository'],
            agent=serializer.validated_data['agent'],
            developer_filter=serializer.validated_data.get('developer_filter', ''),
            date_from=serializer.validated_data.get('date_from'),
            date_to=serializer.validated_data.get('date_to')
        )
        
        # Start the analysis task asynchronously
        celery_task = run_analysis_task.delay(task.id)
        task.celery_task_id = celery_task.id
        task.save(update_fields=['celery_task_id'])
        
        return Response(
            AnalysisTaskSerializer(task).data,
            status=status.HTTP_201_CREATED
        )


class AnalysisTaskDetailView(generics.RetrieveDestroyAPIView):
    """Analysis task detail view"""
    
    serializer_class = AnalysisTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AnalysisTask.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        
        # Cancel the task if it's still running
        if task.status in ['pending', 'processing'] and task.celery_task_id:
            from celery import current_app
            current_app.control.revoke(task.celery_task_id, terminate=True)
            task.status = 'cancelled'
            task.save(update_fields=['status'])
        
        return super().destroy(request, *args, **kwargs)


class AnalysisResultDetailView(generics.RetrieveAPIView):
    """Analysis result detail view"""
    
    serializer_class = AnalysisResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        task_id = self.kwargs['task_id']
        task = get_object_or_404(AnalysisTask, id=task_id, user=self.request.user)
        return get_object_or_404(AnalysisResult, task=task)


class AnalysisExportListCreateView(generics.ListCreateAPIView):
    """List and create analysis exports"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateAnalysisExportSerializer
        return AnalysisExportSerializer
    
    def get_queryset(self):
        return AnalysisExport.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the export
        export = AnalysisExport.objects.create(
            user=request.user,
            analysis_result=serializer.validated_data['analysis_result_id'],
            format=serializer.validated_data['format'],
            include_charts=serializer.validated_data['include_charts'],
            include_raw_data=serializer.validated_data['include_raw_data']
        )
        
        # Start the export task asynchronously
        create_export_task.delay(export.id)
        
        return Response(
            AnalysisExportSerializer(export).data,
            status=status.HTTP_201_CREATED
        )


class AnalysisTemplateListCreateView(generics.ListCreateAPIView):
    """List and create analysis templates"""
    
    serializer_class = AnalysisTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AnalysisTemplate.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        )
        
        # Filter by public templates only
        if self.request.query_params.get('public_only') == 'true':
            queryset = queryset.filter(is_public=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AnalysisTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Analysis template detail view"""
    
    serializer_class = AnalysisTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AnalysisTemplate.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_progress(request, task_id):
    """Get analysis task progress"""
    try:
        task = AnalysisTask.objects.get(id=task_id, user=request.user)
        
        serializer = TaskProgressSerializer({
            'task_id': task.id,
            'status': task.status,
            'progress_percentage': task.progress_percentage,
            'current_step': task.current_step,
            'error_message': task.error_message
        })
        
        return Response(serializer.data)
        
    except AnalysisTask.DoesNotExist:
        return Response(
            {'error': 'Task not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_task(request, task_id):
    """Cancel an analysis task"""
    try:
        task = AnalysisTask.objects.get(id=task_id, user=request.user)
        
        if task.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Task cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel the Celery task
        if task.celery_task_id:
            from celery import current_app
            current_app.control.revoke(task.celery_task_id, terminate=True)
        
        task.status = 'cancelled'
        task.save(update_fields=['status'])
        
        return Response({'message': 'Task cancelled successfully'})
        
    except AnalysisTask.DoesNotExist:
        return Response(
            {'error': 'Task not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def analysis_stats(request):
    """Get analysis statistics for the user"""
    user = request.user
    
    # Get date range (default to last 30 days)
    days = int(request.query_params.get('days', 30))
    date_from = timezone.now() - timedelta(days=days)
    
    tasks = AnalysisTask.objects.filter(user=user, created_at__gte=date_from)
    
    # Calculate statistics
    total_analyses = tasks.count()
    completed_analyses = tasks.filter(status='completed').count()
    failed_analyses = tasks.filter(status='failed').count()
    
    # Token and cost statistics
    results = AnalysisResult.objects.filter(
        task__user=user,
        task__created_at__gte=date_from
    )
    
    total_tokens = results.aggregate(Sum('tokens_used'))['tokens_used__sum'] or 0
    total_cost = results.aggregate(Sum('analysis_cost'))['analysis_cost__sum'] or 0
    
    # Average analysis time
    completed_tasks = tasks.filter(status='completed', started_at__isnull=False, completed_at__isnull=False)
    avg_time = None
    if completed_tasks.exists():
        durations = [(t.completed_at - t.started_at).total_seconds() for t in completed_tasks]
        avg_seconds = sum(durations) / len(durations)
        avg_time = str(timedelta(seconds=int(avg_seconds)))
    
    # Most used agent
    most_used_agent = tasks.values('agent__name').annotate(
        count=Count('agent')
    ).order_by('-count').first()
    
    # Most analyzed repository
    most_analyzed_repo = tasks.values('repository__name').annotate(
        count=Count('repository')
    ).order_by('-count').first()
    
    stats = {
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'failed_analyses': failed_analyses,
        'total_tokens_used': total_tokens,
        'total_cost': total_cost,
        'avg_analysis_time': avg_time or 'N/A',
        'most_used_agent': most_used_agent['agent__name'] if most_used_agent else 'N/A',
        'most_analyzed_repository': most_analyzed_repo['repository__name'] if most_analyzed_repo else 'N/A'
    }
    
    serializer = AnalysisStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_export(request, export_id):
    """Download an analysis export file"""
    try:
        export = AnalysisExport.objects.get(id=export_id, user=request.user)
        
        if export.status != 'completed' or not export.file_path:
            return Response(
                {'error': 'Export not ready for download'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if file has expired
        if export.expires_at and timezone.now() > export.expires_at:
            return Response(
                {'error': 'Export file has expired'},
                status=status.HTTP_410_GONE
            )
        
        # Return file download URL or serve file directly
        # This would typically involve serving the file from storage
        return Response({
            'download_url': f'/media/exports/{export.file_path}',
            'filename': f'analysis_export_{export.id}.{export.format}',
            'file_size': export.file_size
        })
        
    except AnalysisExport.DoesNotExist:
        return Response(
            {'error': 'Export not found'},
            status=status.HTTP_404_NOT_FOUND
        )
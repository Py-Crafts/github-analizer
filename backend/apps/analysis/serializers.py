from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import AnalysisTask, AnalysisResult, AnalysisExport, AnalysisTemplate
from apps.github.models import Repository
from apps.agents.models import AIAgent


class AnalysisTaskSerializer(serializers.ModelSerializer):
    """Serializer for analysis tasks"""
    
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalysisTask
        fields = [
            'id', 'repository', 'repository_name', 'agent', 'agent_name',
            'developer_filter', 'date_from', 'date_to', 'status',
            'progress_percentage', 'current_step', 'error_message',
            'created_at', 'started_at', 'completed_at', 'duration'
        ]
        read_only_fields = [
            'id', 'status', 'progress_percentage', 'current_step',
            'error_message', 'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        if obj.duration:
            return str(obj.duration)
        return None
    
    def validate(self, data):
        # Validate date range
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] >= data['date_to']:
                raise serializers.ValidationError("date_from must be before date_to")
        
        # Validate repository access
        user = self.context['request'].user
        repository = data.get('repository')
        if repository and not repository.user == user:
            raise serializers.ValidationError("You don't have access to this repository")
        
        # Validate agent access
        agent = data.get('agent')
        if agent and not agent.user == user:
            raise serializers.ValidationError("You don't have access to this agent")
        
        return data


class CreateAnalysisTaskSerializer(serializers.Serializer):
    """Serializer for creating analysis tasks"""
    
    repository_id = serializers.IntegerField()
    agent_id = serializers.IntegerField()
    developer_filter = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    date_range_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Validate repository
        try:
            repository = Repository.objects.get(id=data['repository_id'], user=user)
            data['repository'] = repository
        except Repository.DoesNotExist:
            raise serializers.ValidationError("Repository not found or access denied")
        
        # Validate agent
        try:
            agent = AIAgent.objects.get(id=data['agent_id'], user=user)
            data['agent'] = agent
        except AIAgent.DoesNotExist:
            raise serializers.ValidationError("Agent not found or access denied")
        
        # Handle date range
        if 'date_range_days' in data and not ('date_from' in data and 'date_to' in data):
            data['date_to'] = timezone.now()
            data['date_from'] = data['date_to'] - timedelta(days=data['date_range_days'])
        
        # Validate date range
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] >= data['date_to']:
                raise serializers.ValidationError("date_from must be before date_to")
        
        return data


class AnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for analysis results"""
    
    task = AnalysisTaskSerializer(read_only=True)
    
    class Meta:
        model = AnalysisResult
        fields = [
            'task', 'raw_analysis', 'formatted_analysis',
            'total_commits', 'total_additions', 'total_deletions',
            'total_files_changed', 'developer_stats', 'tokens_used',
            'analysis_cost', 'created_at'
        ]
        read_only_fields = ['created_at']


class AnalysisExportSerializer(serializers.ModelSerializer):
    """Serializer for analysis exports"""
    
    analysis_task_id = serializers.CharField(source='analysis_result.task.id', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalysisExport
        fields = [
            'id', 'analysis_result', 'analysis_task_id', 'format',
            'include_charts', 'include_raw_data', 'status',
            'file_path', 'file_size', 'file_size_mb',
            'created_at', 'completed_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'file_size',
            'created_at', 'completed_at', 'expires_at'
        ]
    
    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class CreateAnalysisExportSerializer(serializers.Serializer):
    """Serializer for creating analysis exports"""
    
    analysis_result_id = serializers.IntegerField()
    format = serializers.ChoiceField(choices=AnalysisExport.EXPORT_FORMATS)
    include_charts = serializers.BooleanField(default=True)
    include_raw_data = serializers.BooleanField(default=False)
    
    def validate_analysis_result_id(self, value):
        user = self.context['request'].user
        try:
            analysis_result = AnalysisResult.objects.get(
                id=value,
                task__user=user
            )
            return analysis_result
        except AnalysisResult.DoesNotExist:
            raise serializers.ValidationError("Analysis result not found or access denied")


class AnalysisTemplateSerializer(serializers.ModelSerializer):
    """Serializer for analysis templates"""
    
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    class Meta:
        model = AnalysisTemplate
        fields = [
            'id', 'name', 'description', 'agent', 'agent_name',
            'default_date_range_days', 'default_developer_filter',
            'default_export_format', 'default_include_charts',
            'default_include_raw_data', 'is_public', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def validate_agent(self, value):
        user = self.context['request'].user
        if not value.user == user:
            raise serializers.ValidationError("You don't have access to this agent")
        return value


class AnalysisStatsSerializer(serializers.Serializer):
    """Serializer for analysis statistics"""
    
    total_analyses = serializers.IntegerField()
    completed_analyses = serializers.IntegerField()
    failed_analyses = serializers.IntegerField()
    total_tokens_used = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=4)
    avg_analysis_time = serializers.CharField()
    most_used_agent = serializers.CharField()
    most_analyzed_repository = serializers.CharField()


class TaskProgressSerializer(serializers.Serializer):
    """Serializer for task progress updates"""
    
    task_id = serializers.UUIDField()
    status = serializers.CharField()
    progress_percentage = serializers.IntegerField()
    current_step = serializers.CharField()
    error_message = serializers.CharField(required=False)
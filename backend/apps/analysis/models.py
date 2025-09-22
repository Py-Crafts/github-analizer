from django.db import models
from django.contrib.auth import get_user_model
from apps.github.models import Repository
from apps.agents.models import AIAgent
import uuid

User = get_user_model()


class AnalysisTask(models.Model):
    """Model to track analysis tasks and their progress"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_tasks')
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='analysis_tasks')
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='analysis_tasks')
    
    # Task configuration
    developer_filter = models.CharField(max_length=255, blank=True, help_text="Filter by specific developer")
    date_from = models.DateTimeField(null=True, blank=True)
    date_to = models.DateTimeField(null=True, blank=True)
    
    # Task status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    current_step = models.CharField(max_length=255, blank=True)
    
    # Task metadata
    celery_task_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['repository', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Analysis {self.id} - {self.repository.name} by {self.agent.name}"
    
    @property
    def duration(self):
        """Calculate task duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def update_progress(self, percentage, step=None):
        """Update task progress"""
        self.progress_percentage = percentage
        if step:
            self.current_step = step
        self.save(update_fields=['progress_percentage', 'current_step'])


class AnalysisResult(models.Model):
    """Model to store analysis results"""
    
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='result')
    
    # Analysis data
    raw_analysis = models.TextField(help_text="Raw AI analysis response")
    formatted_analysis = models.TextField(help_text="Formatted analysis for display")
    
    # Statistics
    total_commits = models.IntegerField(default=0)
    total_additions = models.IntegerField(default=0)
    total_deletions = models.IntegerField(default=0)
    total_files_changed = models.IntegerField(default=0)
    
    # Developer statistics (JSON field for flexibility)
    developer_stats = models.JSONField(default=dict, help_text="Developer-specific statistics")
    
    # Analysis metadata
    tokens_used = models.IntegerField(default=0)
    analysis_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Result for {self.task}"


class AnalysisExport(models.Model):
    """Model to track analysis exports"""
    
    EXPORT_FORMATS = [
        ('excel', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_exports')
    analysis_result = models.ForeignKey(AnalysisResult, on_delete=models.CASCADE, related_name='exports')
    
    # Export configuration
    format = models.CharField(max_length=20, choices=EXPORT_FORMATS)
    include_charts = models.BooleanField(default=True)
    include_raw_data = models.BooleanField(default=False)
    
    # Export status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When the export file expires")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Export {self.id} - {self.format} for {self.analysis_result.task}"


class AnalysisTemplate(models.Model):
    """Model for saving analysis configurations as templates"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Template configuration
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE)
    default_date_range_days = models.IntegerField(default=30)
    default_developer_filter = models.CharField(max_length=255, blank=True)
    
    # Export preferences
    default_export_format = models.CharField(max_length=20, choices=AnalysisExport.EXPORT_FORMATS, default='excel')
    default_include_charts = models.BooleanField(default=True)
    default_include_raw_data = models.BooleanField(default=False)
    
    is_public = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} by {self.user.username}"
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
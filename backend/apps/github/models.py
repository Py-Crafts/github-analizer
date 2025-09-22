from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Repository(models.Model):
    """GitHub repository model"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositories')
    github_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Repository metadata
    language = models.CharField(max_length=100, blank=True, null=True)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    watchers_count = models.IntegerField(default=0)
    size = models.IntegerField(default=0)  # Size in KB
    
    # Repository status
    is_private = models.BooleanField(default=False)
    is_fork = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    # URLs
    html_url = models.URLField()
    clone_url = models.URLField()
    
    # Timestamps
    github_created_at = models.DateTimeField()
    github_updated_at = models.DateTimeField()
    github_pushed_at = models.DateTimeField(null=True, blank=True)
    
    # Sync metadata
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('syncing', 'Syncing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'repositories'
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'
        ordering = ['-github_updated_at']
        indexes = [
            models.Index(fields=['user', 'name']),
            models.Index(fields=['github_id']),
            models.Index(fields=['sync_status']),
        ]
    
    def __str__(self):
        return self.full_name
    
    @property
    def commits_count(self):
        """Get total commits count for this repository"""
        return self.commits.count()
    
    @property
    def contributors_count(self):
        """Get unique contributors count for this repository"""
        return self.commits.values('author_name').distinct().count()


class Commit(models.Model):
    """GitHub commit model"""
    
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='commits')
    sha = models.CharField(max_length=40, unique=True)
    
    # Commit metadata
    message = models.TextField()
    author_name = models.CharField(max_length=255)
    author_email = models.CharField(max_length=255)
    committer_name = models.CharField(max_length=255)
    committer_email = models.CharField(max_length=255)
    
    # Commit statistics
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    total_changes = models.IntegerField(default=0)
    files_changed = models.IntegerField(default=0)
    
    # Timestamps
    commit_date = models.DateTimeField()
    
    # URLs
    html_url = models.URLField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commits'
        verbose_name = 'Commit'
        verbose_name_plural = 'Commits'
        ordering = ['-commit_date']
        indexes = [
            models.Index(fields=['repository', 'commit_date']),
            models.Index(fields=['sha']),
            models.Index(fields=['author_name']),
            models.Index(fields=['commit_date']),
        ]
    
    def __str__(self):
        return f"{self.repository.name}: {self.sha[:8]} - {self.message[:50]}"
    
    def save(self, *args, **kwargs):
        # Calculate total changes
        self.total_changes = self.additions + self.deletions
        super().save(*args, **kwargs)


class CommitFile(models.Model):
    """Files changed in a commit"""
    
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=500)
    status = models.CharField(
        max_length=20,
        choices=[
            ('added', 'Added'),
            ('modified', 'Modified'),
            ('removed', 'Removed'),
            ('renamed', 'Renamed'),
        ]
    )
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    changes = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'commit_files'
        verbose_name = 'Commit File'
        verbose_name_plural = 'Commit Files'
        unique_together = ['commit', 'filename']
        indexes = [
            models.Index(fields=['commit', 'filename']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.commit.sha[:8]}: {self.filename}"
    
    def save(self, *args, **kwargs):
        # Calculate total changes
        self.changes = self.additions + self.deletions
        super().save(*args, **kwargs)
from rest_framework import serializers
from .models import Repository, Commit, CommitFile


class RepositorySerializer(serializers.ModelSerializer):
    """Serializer for Repository model"""
    
    commits_count = serializers.ReadOnlyField()
    contributors_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Repository
        fields = [
            'id', 'github_id', 'name', 'full_name', 'description',
            'language', 'stars_count', 'forks_count', 'watchers_count', 'size',
            'is_private', 'is_fork', 'is_archived',
            'html_url', 'clone_url',
            'github_created_at', 'github_updated_at', 'github_pushed_at',
            'last_synced', 'sync_status',
            'commits_count', 'contributors_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'github_id', 'commits_count', 'contributors_count',
            'created_at', 'updated_at'
        ]


class CommitFileSerializer(serializers.ModelSerializer):
    """Serializer for CommitFile model"""
    
    class Meta:
        model = CommitFile
        fields = [
            'id', 'filename', 'status', 'additions', 'deletions', 'changes'
        ]


class CommitSerializer(serializers.ModelSerializer):
    """Serializer for Commit model"""
    
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    files = CommitFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Commit
        fields = [
            'id', 'sha', 'message', 'author_name', 'author_email',
            'committer_name', 'committer_email',
            'additions', 'deletions', 'total_changes', 'files_changed',
            'commit_date', 'html_url',
            'repository_name', 'files',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_changes', 'repository_name', 'files',
            'created_at', 'updated_at'
        ]


class RepositoryStatsSerializer(serializers.Serializer):
    """Serializer for repository statistics"""
    
    repository = RepositorySerializer(read_only=True)
    total_commits = serializers.IntegerField()
    total_additions = serializers.IntegerField()
    total_deletions = serializers.IntegerField()
    total_changes = serializers.IntegerField()
    contributors = serializers.ListField(child=serializers.DictField())
    commit_frequency = serializers.DictField()
    language_stats = serializers.DictField()


class DeveloperStatsSerializer(serializers.Serializer):
    """Serializer for developer statistics"""
    
    developer_name = serializers.CharField()
    developer_email = serializers.CharField()
    total_commits = serializers.IntegerField()
    total_additions = serializers.IntegerField()
    total_deletions = serializers.IntegerField()
    total_changes = serializers.IntegerField()
    repositories = serializers.ListField(child=serializers.CharField())
    first_commit = serializers.DateTimeField()
    last_commit = serializers.DateTimeField()
    commit_frequency = serializers.DictField()


class SyncStatusSerializer(serializers.Serializer):
    """Serializer for sync operation status"""
    
    task_id = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()
    progress = serializers.IntegerField(required=False)
    total = serializers.IntegerField(required=False)
    result = serializers.DictField(required=False)
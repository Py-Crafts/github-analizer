import requests
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
from .models import Repository, Commit, CommitFile
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """GitHub API client with authentication"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get(self, endpoint, params=None):
        """Make GET request to GitHub API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            response.raise_for_status()
    
    def get_paginated(self, endpoint, params=None, max_pages=None):
        """Get all pages from a paginated endpoint"""
        items = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            page_params = (params or {}).copy()
            page_params.update({'page': page, 'per_page': 100})
            
            data = self.get(endpoint, page_params)
            if not data:
                break
            
            items.extend(data)
            
            # Check if there are more pages
            if len(data) < 100:
                break
            
            page += 1
        
        return items


@shared_task(bind=True)
def sync_user_repositories(self, user_id):
    """Sync all repositories for a user"""
    try:
        user = User.objects.get(id=user_id)
        
        if not user.has_github_token():
            return {'error': 'No GitHub token configured'}
        
        client = GitHubAPIClient(user.github_token)
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'message': 'Fetching repositories from GitHub...', 'progress': 0}
        )
        
        # Get user repositories
        repos_data = client.get_paginated('user/repos', {'type': 'all', 'sort': 'updated'})
        
        if not repos_data:
            return {'error': 'No repositories found or API error'}
        
        total_repos = len(repos_data)
        synced_count = 0
        
        for i, repo_data in enumerate(repos_data):
            try:
                # Update or create repository
                repository, created = Repository.objects.update_or_create(
                    github_id=repo_data['id'],
                    defaults={
                        'user': user,
                        'name': repo_data['name'],
                        'full_name': repo_data['full_name'],
                        'description': repo_data.get('description', ''),
                        'language': repo_data.get('language'),
                        'stars_count': repo_data.get('stargazers_count', 0),
                        'forks_count': repo_data.get('forks_count', 0),
                        'watchers_count': repo_data.get('watchers_count', 0),
                        'size': repo_data.get('size', 0),
                        'is_private': repo_data.get('private', False),
                        'is_fork': repo_data.get('fork', False),
                        'is_archived': repo_data.get('archived', False),
                        'html_url': repo_data['html_url'],
                        'clone_url': repo_data['clone_url'],
                        'github_created_at': datetime.fromisoformat(
                            repo_data['created_at'].replace('Z', '+00:00')
                        ),
                        'github_updated_at': datetime.fromisoformat(
                            repo_data['updated_at'].replace('Z', '+00:00')
                        ),
                        'github_pushed_at': datetime.fromisoformat(
                            repo_data['pushed_at'].replace('Z', '+00:00')
                        ) if repo_data.get('pushed_at') else None,
                        'last_synced': timezone.now(),
                        'sync_status': 'completed'
                    }
                )
                
                synced_count += 1
                
                # Update progress
                progress = int((i + 1) / total_repos * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f'Synced {synced_count}/{total_repos} repositories',
                        'progress': progress,
                        'total': total_repos,
                        'synced': synced_count
                    }
                )
                
            except Exception as e:
                logger.error(f"Error syncing repository {repo_data['name']}: {str(e)}")
                continue
        
        return {
            'message': f'Successfully synced {synced_count} repositories',
            'total': total_repos,
            'synced': synced_count
        }
        
    except Exception as e:
        logger.error(f"Error in sync_user_repositories: {str(e)}")
        return {'error': str(e)}


@shared_task(bind=True)
def sync_repository_commits(self, repository_id):
    """Sync commits for a specific repository"""
    try:
        repository = Repository.objects.get(id=repository_id)
        user = repository.user
        
        if not user.has_github_token():
            return {'error': 'No GitHub token configured'}
        
        client = GitHubAPIClient(user.github_token)
        
        # Update repository sync status
        repository.sync_status = 'syncing'
        repository.save()
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'message': f'Fetching commits for {repository.name}...', 'progress': 0}
        )
        
        # Get repository commits
        commits_data = client.get_paginated(
            f'repos/{repository.full_name}/commits',
            max_pages=10  # Limit to avoid too many API calls
        )
        
        if not commits_data:
            repository.sync_status = 'completed'
            repository.last_synced = timezone.now()
            repository.save()
            return {'message': 'No commits found'}
        
        total_commits = len(commits_data)
        synced_count = 0
        
        for i, commit_data in enumerate(commits_data):
            try:
                # Check if commit already exists
                if Commit.objects.filter(sha=commit_data['sha']).exists():
                    continue
                
                # Get detailed commit info
                detailed_commit = client.get(f'repos/{repository.full_name}/commits/{commit_data["sha"]}')
                
                if not detailed_commit:
                    continue
                
                # Create commit
                commit = Commit.objects.create(
                    repository=repository,
                    sha=commit_data['sha'],
                    message=commit_data['commit']['message'],
                    author_name=commit_data['commit']['author']['name'],
                    author_email=commit_data['commit']['author']['email'],
                    committer_name=commit_data['commit']['committer']['name'],
                    committer_email=commit_data['commit']['committer']['email'],
                    commit_date=datetime.fromisoformat(
                        commit_data['commit']['author']['date'].replace('Z', '+00:00')
                    ),
                    html_url=commit_data['html_url'],
                    additions=detailed_commit.get('stats', {}).get('additions', 0),
                    deletions=detailed_commit.get('stats', {}).get('deletions', 0),
                    files_changed=len(detailed_commit.get('files', []))
                )
                
                # Create commit files
                for file_data in detailed_commit.get('files', []):
                    CommitFile.objects.create(
                        commit=commit,
                        filename=file_data['filename'],
                        status=file_data['status'],
                        additions=file_data.get('additions', 0),
                        deletions=file_data.get('deletions', 0)
                    )
                
                synced_count += 1
                
                # Update progress
                progress = int((i + 1) / total_commits * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'message': f'Synced {synced_count}/{total_commits} commits',
                        'progress': progress,
                        'total': total_commits,
                        'synced': synced_count
                    }
                )
                
            except Exception as e:
                logger.error(f"Error syncing commit {commit_data['sha']}: {str(e)}")
                continue
        
        # Update repository sync status
        repository.sync_status = 'completed'
        repository.last_synced = timezone.now()
        repository.save()
        
        return {
            'message': f'Successfully synced {synced_count} commits for {repository.name}',
            'total': total_commits,
            'synced': synced_count
        }
        
    except Exception as e:
        logger.error(f"Error in sync_repository_commits: {str(e)}")
        # Update repository sync status to failed
        try:
            repository = Repository.objects.get(id=repository_id)
            repository.sync_status = 'failed'
            repository.save()
        except:
            pass
        return {'error': str(e)}
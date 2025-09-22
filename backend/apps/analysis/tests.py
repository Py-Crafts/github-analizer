"""
Test suite for the analysis app.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, date, timedelta
import json

from apps.analysis.models import AnalysisTask, AnalysisResult, AnalysisExport, AnalysisTemplate
from apps.analysis.serializers import AnalysisTaskSerializer, CreateAnalysisTaskSerializer
from apps.analysis.tasks import AIAnalysisClient, run_analysis_task
from apps.analysis.exceptions import (
    AIProviderError, GitHubAPIError, InsufficientDataError, 
    ValidationError, handle_ai_provider_error
)
from apps.analysis.utils import ExcelExporter, analyze_commit_patterns

User = get_user_model()


class AnalysisModelTests(TestCase):
    """Test cases for analysis models."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_analysis_task_creation(self):
        """Test creating an analysis task."""
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.repository_name, 'test/repo')
        self.assertEqual(task.status, 'pending')
        self.assertIsNotNone(task.created_at)
    
    def test_analysis_task_str_representation(self):
        """Test string representation of analysis task."""
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        expected = f"Analysis: test/repo (performance) - {task.created_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(task), expected)
    
    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        result = AnalysisResult.objects.create(
            task=task,
            analysis_result={'analysis': 'Test analysis'},
            ai_provider='openai',
            model_used='gpt-3.5-turbo',
            cost_usd=0.05
        )
        
        self.assertEqual(result.task, task)
        self.assertEqual(result.ai_provider, 'openai')
        self.assertEqual(result.cost_usd, 0.05)
    
    def test_analysis_template_creation(self):
        """Test creating an analysis template."""
        template = AnalysisTemplate.objects.create(
            name='Test Template',
            description='A test template',
            category='performance',
            system_prompt_template='Test system prompt',
            analysis_prompt_template='Test analysis prompt'
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertTrue(template.is_public)
        self.assertIsNotNone(template.created_at)


class AnalysisAPITests(APITestCase):
    """Test cases for analysis API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_analysis_task_authenticated(self):
        """Test creating analysis task with authenticated user."""
        url = reverse('analysis:task-list-create')
        data = {
            'repository_name': 'test/repo',
            'analysis_type': 'performance',
            'date_from': '2023-01-01',
            'date_to': '2023-12-31',
            'ai_provider': 'openai',
            'model': 'gpt-3.5-turbo'
        }
        
        with patch('apps.analysis.tasks.run_analysis_task.delay') as mock_task:
            mock_task.return_value = Mock(id='test-task-id')
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnalysisTask.objects.count(), 1)
        
        task = AnalysisTask.objects.first()
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.repository_name, 'test/repo')
    
    def test_create_analysis_task_unauthenticated(self):
        """Test creating analysis task without authentication."""
        self.client.force_authenticate(user=None)
        url = reverse('analysis:task-list-create')
        data = {
            'repository_name': 'test/repo',
            'analysis_type': 'performance'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_user_analysis_tasks(self):
        """Test listing user's analysis tasks."""
        # Create tasks for different users
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        AnalysisTask.objects.create(
            user=self.user,
            repository_name='user/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        AnalysisTask.objects.create(
            user=other_user,
            repository_name='other/repo',
            analysis_type='quality',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        url = reverse('analysis:task-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['repository_name'], 'user/repo')
    
    def test_get_analysis_task_detail(self):
        """Test retrieving analysis task detail."""
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        url = reverse('analysis:task-detail', kwargs={'pk': task.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], task.id)
        self.assertEqual(response.data['repository_name'], 'test/repo')
    
    def test_cancel_analysis_task(self):
        """Test canceling an analysis task."""
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today(),
            status='running',
            celery_task_id='test-task-id'
        )
        
        url = reverse('analysis:task-cancel', kwargs={'pk': task.pk})
        
        with patch('celery.current_app.control.revoke') as mock_revoke:
            response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, 'cancelled')
        mock_revoke.assert_called_once_with('test-task-id', terminate=True)


class AIAnalysisClientTests(TestCase):
    """Test cases for AI analysis client."""
    
    def setUp(self):
        self.client = AIAnalysisClient()
    
    @patch('openai.ChatCompletion.create')
    def test_openai_analysis_success(self, mock_openai):
        """Test successful OpenAI analysis."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            'analysis': 'Test analysis',
            'key_insights': ['Insight 1', 'Insight 2'],
            'recommendations': ['Rec 1', 'Rec 2']
        })
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_openai.return_value = mock_response
        
        result = self.client.analyze_with_openai(
            'Test prompt',
            'gpt-3.5-turbo',
            temperature=0.7,
            max_tokens=2000
        )
        
        self.assertIn('analysis', result)
        self.assertEqual(result['analysis'], 'Test analysis')
        self.assertEqual(len(result['key_insights']), 2)
    
    @patch('anthropic.Anthropic')
    def test_anthropic_analysis_success(self, mock_anthropic_class):
        """Test successful Anthropic analysis."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            'analysis': 'Test analysis',
            'key_insights': ['Insight 1'],
            'recommendations': ['Rec 1']
        })
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 150
        mock_response.usage.output_tokens = 250
        mock_client.messages.create.return_value = mock_response
        
        result = self.client.analyze_with_anthropic(
            'Test prompt',
            'claude-3-sonnet',
            temperature=0.7,
            max_tokens=2000
        )
        
        self.assertIn('analysis', result)
        self.assertEqual(result['analysis'], 'Test analysis')
    
    def test_calculate_openai_cost(self):
        """Test OpenAI cost calculation."""
        cost = self.client.calculate_openai_cost('gpt-3.5-turbo', 1000, 500)
        self.assertGreater(cost, 0)
        self.assertIsInstance(cost, float)
    
    def test_calculate_anthropic_cost(self):
        """Test Anthropic cost calculation."""
        cost = self.client.calculate_anthropic_cost('claude-3-sonnet', 1000, 500)
        self.assertGreater(cost, 0)
        self.assertIsInstance(cost, float)


class ExceptionHandlingTests(TestCase):
    """Test cases for custom exception handling."""
    
    def test_ai_provider_error_creation(self):
        """Test creating AI provider error."""
        error = AIProviderError('openai', 'Rate limit exceeded')
        
        self.assertEqual(error.provider, 'openai')
        self.assertEqual(error.code, 'AI_PROVIDER_ERROR')
        self.assertIn('openai', error.message)
    
    def test_github_api_error_creation(self):
        """Test creating GitHub API error."""
        error = GitHubAPIError('Repository not found', 404, {'message': 'Not Found'})
        
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.code, 'GITHUB_API_ERROR')
        self.assertIn('GitHub API error', error.message)
    
    def test_insufficient_data_error(self):
        """Test insufficient data error."""
        error = InsufficientDataError('commits', 5)
        
        self.assertEqual(error.data_type, 'commits')
        self.assertEqual(error.minimum_required, 5)
        self.assertEqual(error.code, 'INSUFFICIENT_DATA')
    
    def test_handle_ai_provider_error_openai_rate_limit(self):
        """Test handling OpenAI rate limit error."""
        with self.assertRaises(Exception) as context:
            handle_ai_provider_error('openai', Exception('rate limit exceeded'))
        
        # Should raise our custom exception, not the original
        self.assertIn('rate limit', str(context.exception).lower())


class UtilityTests(TestCase):
    """Test cases for utility functions."""
    
    def test_analyze_commit_patterns_empty_data(self):
        """Test commit pattern analysis with empty data."""
        result = analyze_commit_patterns([])
        self.assertEqual(result, {})
    
    def test_analyze_commit_patterns_with_data(self):
        """Test commit pattern analysis with sample data."""
        commit_data = [
            {
                'sha': 'abc123',
                'message': 'Fix bug',
                'date': '2023-01-01T10:00:00Z',
                'additions': 10,
                'deletions': 5
            },
            {
                'sha': 'def456',
                'message': 'Add feature',
                'date': '2023-01-02T14:00:00Z',
                'additions': 20,
                'deletions': 2
            }
        ]
        
        result = analyze_commit_patterns(commit_data)
        
        self.assertEqual(result['total_commits'], 2)
        self.assertEqual(result['avg_additions'], 15.0)
        self.assertEqual(result['avg_deletions'], 3.5)
        self.assertIn('most_active_hour', result)
        self.assertIn('commit_frequency', result)
    
    def test_excel_exporter_creation(self):
        """Test Excel exporter initialization."""
        exporter = ExcelExporter()
        self.assertIsNotNone(exporter.buffer)
        self.assertIsNone(exporter.workbook)


class SerializerTests(TestCase):
    """Test cases for serializers."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_analysis_task_serializer_valid_data(self):
        """Test analysis task serializer with valid data."""
        data = {
            'repository_name': 'test/repo',
            'analysis_type': 'performance',
            'date_from': '2023-01-01',
            'date_to': '2023-12-31',
            'ai_provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        serializer = CreateAnalysisTaskSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_create_analysis_task_serializer_invalid_date_range(self):
        """Test analysis task serializer with invalid date range."""
        data = {
            'repository_name': 'test/repo',
            'analysis_type': 'performance',
            'date_from': '2023-12-31',
            'date_to': '2023-01-01',  # End date before start date
            'ai_provider': 'openai',
            'model': 'gpt-3.5-turbo'
        }
        
        serializer = CreateAnalysisTaskSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('date_to', serializer.errors)
    
    def test_analysis_task_serializer_read_only_fields(self):
        """Test that certain fields are read-only in serializer."""
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today()
        )
        
        serializer = AnalysisTaskSerializer(task)
        data = serializer.data
        
        # These fields should be present in serialized data
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('status', data)
        self.assertIn('user', data)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TaskTests(TestCase):
    """Test cases for Celery tasks."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('apps.analysis.tasks.AIAnalysisClient.analyze_with_openai')
    @patch('apps.github.utils.GitHubClient.get_commits')
    def test_run_analysis_task_success(self, mock_get_commits, mock_analyze):
        """Test successful analysis task execution."""
        # Mock GitHub API response
        mock_get_commits.return_value = [
            {
                'sha': 'abc123',
                'message': 'Test commit',
                'date': '2023-01-01T10:00:00Z',
                'additions': 10,
                'deletions': 5,
                'files': ['file1.py']
            }
        ]
        
        # Mock AI analysis response
        mock_analyze.return_value = {
            'analysis': 'Test analysis result',
            'key_insights': ['Insight 1'],
            'recommendations': ['Recommendation 1'],
            'metadata': {'tokens_used': 300}
        }, 0.05
        
        task = AnalysisTask.objects.create(
            user=self.user,
            repository_name='test/repo',
            analysis_type='performance',
            date_from=date.today() - timedelta(days=30),
            date_to=date.today(),
            ai_provider='openai',
            model='gpt-3.5-turbo'
        )
        
        # Run the task
        run_analysis_task(task.id)
        
        # Check results
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        
        result = AnalysisResult.objects.get(task=task)
        self.assertEqual(result.ai_provider, 'openai')
        self.assertEqual(result.cost_usd, 0.05)
        self.assertIn('analysis', result.analysis_result)


class IntegrationTests(APITestCase):
    """Integration tests for the complete analysis workflow."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.analysis.tasks.run_analysis_task.delay')
    @patch('apps.github.utils.GitHubClient.get_commits')
    def test_complete_analysis_workflow(self, mock_get_commits, mock_task):
        """Test the complete analysis workflow from creation to completion."""
        # Mock task delay
        mock_task.return_value = Mock(id='test-task-id')
        
        # Mock GitHub data
        mock_get_commits.return_value = [
            {
                'sha': 'abc123',
                'message': 'Test commit',
                'date': '2023-01-01T10:00:00Z',
                'additions': 10,
                'deletions': 5
            }
        ]
        
        # 1. Create analysis task
        url = reverse('analysis:task-list-create')
        data = {
            'repository_name': 'test/repo',
            'analysis_type': 'performance',
            'date_from': '2023-01-01',
            'date_to': '2023-12-31',
            'ai_provider': 'openai',
            'model': 'gpt-3.5-turbo'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        task_id = response.data['id']
        
        # 2. Check task status
        url = reverse('analysis:task-detail', kwargs={'pk': task_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        
        # 3. Simulate task completion
        task = AnalysisTask.objects.get(id=task_id)
        task.status = 'completed'
        task.save()
        
        AnalysisResult.objects.create(
            task=task,
            analysis_result={
                'analysis': 'Test analysis',
                'key_insights': ['Insight 1'],
                'recommendations': ['Rec 1']
            },
            ai_provider='openai',
            model_used='gpt-3.5-turbo',
            cost_usd=0.05
        )
        
        # 4. Check completed task
        response = self.client.get(url)
        self.assertEqual(response.data['status'], 'completed')
        
        # 5. Get analysis results
        url = reverse('analysis:result-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
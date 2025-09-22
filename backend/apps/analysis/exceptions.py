"""
Custom exceptions for the analysis app.
"""

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Base exception for analysis-related errors."""
    
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code or 'ANALYSIS_ERROR'
        self.details = details or {}
        super().__init__(self.message)


class AIProviderError(AnalysisError):
    """Exception raised when AI provider API calls fail."""
    
    def __init__(self, provider, message, original_error=None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(
            message=f"AI Provider ({provider}) error: {message}",
            code='AI_PROVIDER_ERROR',
            details={'provider': provider, 'original_error': str(original_error) if original_error else None}
        )


class GitHubAPIError(AnalysisError):
    """Exception raised when GitHub API calls fail."""
    
    def __init__(self, message, status_code=None, response_data=None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(
            message=f"GitHub API error: {message}",
            code='GITHUB_API_ERROR',
            details={'status_code': status_code, 'response_data': response_data}
        )


class InsufficientDataError(AnalysisError):
    """Exception raised when there's insufficient data for analysis."""
    
    def __init__(self, data_type, minimum_required=None):
        self.data_type = data_type
        self.minimum_required = minimum_required
        message = f"Insufficient {data_type} for analysis"
        if minimum_required:
            message += f" (minimum required: {minimum_required})"
        
        super().__init__(
            message=message,
            code='INSUFFICIENT_DATA',
            details={'data_type': data_type, 'minimum_required': minimum_required}
        )


class ConfigurationError(AnalysisError):
    """Exception raised when there are configuration issues."""
    
    def __init__(self, config_type, message):
        self.config_type = config_type
        super().__init__(
            message=f"Configuration error ({config_type}): {message}",
            code='CONFIGURATION_ERROR',
            details={'config_type': config_type}
        )


class RateLimitError(AnalysisError):
    """Exception raised when API rate limits are exceeded."""
    
    def __init__(self, service, reset_time=None):
        self.service = service
        self.reset_time = reset_time
        message = f"Rate limit exceeded for {service}"
        if reset_time:
            message += f" (resets at {reset_time})"
        
        super().__init__(
            message=message,
            code='RATE_LIMIT_EXCEEDED',
            details={'service': service, 'reset_time': reset_time}
        )


class ExportError(AnalysisError):
    """Exception raised during export operations."""
    
    def __init__(self, export_type, message, file_format=None):
        self.export_type = export_type
        self.file_format = file_format
        super().__init__(
            message=f"Export error ({export_type}): {message}",
            code='EXPORT_ERROR',
            details={'export_type': export_type, 'file_format': file_format}
        )


class ValidationError(AnalysisError):
    """Exception raised for validation errors."""
    
    def __init__(self, field, message, value=None):
        self.field = field
        self.value = value
        super().__init__(
            message=f"Validation error for {field}: {message}",
            code='VALIDATION_ERROR',
            details={'field': field, 'value': value}
        )


def custom_exception_handler(exc, context):
    """
    Custom exception handler for analysis app exceptions.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle our custom exceptions
    if isinstance(exc, AnalysisError):
        logger.error(f"Analysis error: {exc.message}", extra={
            'code': exc.code,
            'details': exc.details,
            'context': context
        })
        
        # Determine HTTP status code based on exception type
        if isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, (AIProviderError, GitHubAPIError)):
            status_code = status.HTTP_502_BAD_GATEWAY
        elif isinstance(exc, RateLimitError):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, (InsufficientDataError, ConfigurationError)):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, ExportError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        custom_response_data = {
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.details
            }
        }
        
        return Response(custom_response_data, status=status_code)
    
    # Handle other exceptions
    if response is not None:
        # Log the error
        logger.error(f"API error: {exc}", extra={
            'status_code': response.status_code,
            'response_data': response.data,
            'context': context
        })
        
        # Customize the response format
        custom_response_data = {
            'error': {
                'code': 'API_ERROR',
                'message': 'An error occurred while processing your request.',
                'details': response.data
            }
        }
        response.data = custom_response_data
    
    return response


def handle_ai_provider_error(provider, error):
    """
    Convert AI provider specific errors to our custom exceptions.
    """
    error_message = str(error)
    
    # OpenAI specific errors
    if 'openai' in provider.lower():
        if 'rate limit' in error_message.lower():
            raise RateLimitError('OpenAI API')
        elif 'invalid api key' in error_message.lower():
            raise ConfigurationError('OpenAI API Key', 'Invalid API key provided')
        elif 'insufficient quota' in error_message.lower():
            raise ConfigurationError('OpenAI Quota', 'Insufficient API quota')
    
    # Anthropic specific errors
    elif 'anthropic' in provider.lower():
        if 'rate limit' in error_message.lower():
            raise RateLimitError('Anthropic API')
        elif 'authentication' in error_message.lower():
            raise ConfigurationError('Anthropic API Key', 'Authentication failed')
    
    # Generic AI provider error
    raise AIProviderError(provider, error_message, error)


def handle_github_error(error, response=None):
    """
    Convert GitHub API errors to our custom exceptions.
    """
    status_code = getattr(response, 'status_code', None) if response else None
    response_data = None
    
    if response and hasattr(response, 'json'):
        try:
            response_data = response.json()
        except:
            response_data = response.text if hasattr(response, 'text') else None
    
    error_message = str(error)
    
    if status_code == 403 and 'rate limit' in error_message.lower():
        reset_time = None
        if response and hasattr(response, 'headers'):
            reset_time = response.headers.get('X-RateLimit-Reset')
        raise RateLimitError('GitHub API', reset_time)
    elif status_code == 401:
        raise ConfigurationError('GitHub Token', 'Invalid or expired GitHub token')
    elif status_code == 404:
        raise GitHubAPIError('Repository or resource not found', status_code, response_data)
    else:
        raise GitHubAPIError(error_message, status_code, response_data)


def validate_analysis_data(commit_data, minimum_commits=1):
    """
    Validate that we have sufficient data for analysis.
    """
    if not commit_data:
        raise InsufficientDataError('commits', minimum_commits)
    
    if len(commit_data) < minimum_commits:
        raise InsufficientDataError(
            'commits', 
            f"{minimum_commits} (found {len(commit_data)})"
        )
    
    # Check for required fields in commit data
    required_fields = ['sha', 'message', 'date']
    for i, commit in enumerate(commit_data[:5]):  # Check first 5 commits
        for field in required_fields:
            if field not in commit:
                raise ValidationError(
                    f'commit[{i}].{field}',
                    f'Missing required field in commit data',
                    commit
                )


def validate_export_request(analysis_results, export_format):
    """
    Validate export request parameters.
    """
    if not analysis_results:
        raise InsufficientDataError('analysis results for export')
    
    if export_format not in ['summary', 'detailed']:
        raise ValidationError(
            'export_format',
            'Must be either "summary" or "detailed"',
            export_format
        )
    
    # Check if results have required data
    for result in analysis_results[:1]:  # Check first result
        if not result.analysis_result:
            raise InsufficientDataError('analysis content for export')
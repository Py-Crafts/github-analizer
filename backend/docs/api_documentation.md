# GitHub Analyzer API Documentation

## Overview

The GitHub Analyzer API provides comprehensive analysis of GitHub repositories and developer performance using AI-powered insights. This RESTful API allows users to create custom analysis agents, run automated analyses, and export results in various formats.

## Base URL

```
http://localhost:8000/api/
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### Login
```http
POST /auth/login/
```

**Request Body:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Token Refresh
```http
POST /auth/token/refresh/
```

**Request Body:**
```json
{
    "refresh": "your_refresh_token"
}
```

## API Endpoints

### GitHub Integration

#### List User Repositories
```http
GET /github/repositories/
```

**Query Parameters:**
- `page` (optional): Page number for pagination
- `per_page` (optional): Number of items per page (default: 20, max: 100)

**Response:**
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/github/repositories/?page=2",
    "previous": null,
    "results": [
        {
            "id": 123456789,
            "name": "my-project",
            "full_name": "username/my-project",
            "description": "A sample project",
            "private": false,
            "html_url": "https://github.com/username/my-project",
            "created_at": "2023-01-15T10:30:00Z",
            "updated_at": "2023-12-01T14:20:00Z",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 8
        }
    ]
}
```

#### Get Repository Details
```http
GET /github/repositories/{owner}/{repo}/
```

**Response:**
```json
{
    "id": 123456789,
    "name": "my-project",
    "full_name": "username/my-project",
    "description": "A sample project",
    "private": false,
    "html_url": "https://github.com/username/my-project",
    "created_at": "2023-01-15T10:30:00Z",
    "updated_at": "2023-12-01T14:20:00Z",
    "language": "Python",
    "stargazers_count": 42,
    "forks_count": 8,
    "size": 1024,
    "default_branch": "main",
    "topics": ["python", "api", "web"]
}
```

#### Get Repository Commits
```http
GET /github/repositories/{owner}/{repo}/commits/
```

**Query Parameters:**
- `since` (optional): ISO 8601 date string (e.g., "2023-01-01T00:00:00Z")
- `until` (optional): ISO 8601 date string
- `author` (optional): GitHub username to filter commits
- `page` (optional): Page number
- `per_page` (optional): Items per page (default: 30, max: 100)

**Response:**
```json
{
    "count": 250,
    "next": "http://localhost:8000/api/github/repositories/owner/repo/commits/?page=2",
    "previous": null,
    "results": [
        {
            "sha": "a1b2c3d4e5f6",
            "message": "Fix authentication bug",
            "author": {
                "name": "John Doe",
                "email": "john@example.com",
                "date": "2023-12-01T10:30:00Z"
            },
            "committer": {
                "name": "John Doe",
                "email": "john@example.com",
                "date": "2023-12-01T10:30:00Z"
            },
            "stats": {
                "additions": 15,
                "deletions": 8,
                "total": 23
            },
            "files": [
                {
                    "filename": "auth/views.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 5,
                    "changes": 15
                }
            ]
        }
    ]
}
```

#### Get Repository Contributors
```http
GET /github/repositories/{owner}/{repo}/contributors/
```

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "login": "johndoe",
            "id": 12345,
            "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
            "html_url": "https://github.com/johndoe",
            "contributions": 127,
            "type": "User"
        }
    ]
}
```

### AI Agents

#### List AI Agents
```http
GET /agents/
```

**Query Parameters:**
- `page` (optional): Page number
- `search` (optional): Search in name and description
- `ai_provider` (optional): Filter by AI provider (openai, anthropic)

**Response:**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Performance Analyzer",
            "description": "Analyzes developer performance metrics",
            "ai_provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "system_prompt": "You are an expert...",
            "analysis_prompt_template": "Analyze the performance of {developer_name}...",
            "analysis_config": {
                "include_file_changes": true,
                "include_commit_messages": true,
                "focus_areas": ["productivity", "code_quality"]
            },
            "created_at": "2023-11-01T10:00:00Z",
            "updated_at": "2023-11-15T14:30:00Z"
        }
    ]
}
```

#### Create AI Agent
```http
POST /agents/
```

**Request Body:**
```json
{
    "name": "Custom Performance Analyzer",
    "description": "My custom analyzer for team performance",
    "ai_provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are an expert software development analyst...",
    "analysis_prompt_template": "Analyze the performance of {developer_name} in {repository_name}...",
    "analysis_config": {
        "include_file_changes": true,
        "include_commit_messages": true,
        "focus_areas": ["productivity", "code_quality", "collaboration"]
    }
}
```

**Response:**
```json
{
    "id": 15,
    "name": "Custom Performance Analyzer",
    "description": "My custom analyzer for team performance",
    "ai_provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are an expert software development analyst...",
    "analysis_prompt_template": "Analyze the performance of {developer_name} in {repository_name}...",
    "analysis_config": {
        "include_file_changes": true,
        "include_commit_messages": true,
        "focus_areas": ["productivity", "code_quality", "collaboration"]
    },
    "created_at": "2023-12-01T15:45:00Z",
    "updated_at": "2023-12-01T15:45:00Z"
}
```

#### Get AI Agent Details
```http
GET /agents/{id}/
```

#### Update AI Agent
```http
PUT /agents/{id}/
PATCH /agents/{id}/
```

#### Delete AI Agent
```http
DELETE /agents/{id}/
```

#### Validate AI Agent Configuration
```http
POST /agents/validate/
```

**Request Body:**
```json
{
    "ai_provider": "openai",
    "model": "gpt-4",
    "system_prompt": "Test prompt",
    "analysis_prompt_template": "Test template"
}
```

**Response:**
```json
{
    "valid": true,
    "message": "Configuration is valid",
    "estimated_cost": 0.05,
    "warnings": []
}
```

#### Test AI Agent
```http
POST /agents/{id}/test/
```

**Request Body:**
```json
{
    "test_data": {
        "developer_name": "John Doe",
        "repository_name": "test/repo",
        "commit_data": [
            {
                "sha": "abc123",
                "message": "Fix bug",
                "date": "2023-12-01T10:00:00Z",
                "additions": 10,
                "deletions": 5
            }
        ]
    }
}
```

### Agent Templates

#### List Agent Templates
```http
GET /agents/templates/
```

**Query Parameters:**
- `category` (optional): Filter by category
- `is_public` (optional): Filter public templates (true/false)

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "name": "Developer Performance Analysis",
            "description": "Analyzes individual developer performance...",
            "category": "performance",
            "tags": "performance,productivity,developer,metrics",
            "default_ai_provider": "openai",
            "default_model": "gpt-3.5-turbo",
            "is_public": true,
            "created_at": "2023-11-01T10:00:00Z"
        }
    ]
}
```

#### Create Agent from Template
```http
POST /agents/templates/{id}/create-agent/
```

**Request Body:**
```json
{
    "name": "My Performance Agent",
    "description": "Custom description",
    "customizations": {
        "temperature": 0.8,
        "focus_areas": ["productivity", "collaboration"]
    }
}
```

### Analysis Tasks

#### List Analysis Tasks
```http
GET /analysis/tasks/
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, running, completed, failed, cancelled)
- `repository_name` (optional): Filter by repository
- `analysis_type` (optional): Filter by analysis type
- `date_from` (optional): Filter tasks created after date (YYYY-MM-DD)
- `date_to` (optional): Filter tasks created before date (YYYY-MM-DD)

**Response:**
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/analysis/tasks/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "repository_name": "username/my-project",
            "developer_name": "johndoe",
            "analysis_type": "performance",
            "date_from": "2023-11-01",
            "date_to": "2023-11-30",
            "status": "completed",
            "progress": 100,
            "ai_provider": "openai",
            "model": "gpt-4",
            "total_commits": 45,
            "total_additions": 1250,
            "total_deletions": 380,
            "file_changes": 125,
            "created_at": "2023-12-01T10:00:00Z",
            "completed_at": "2023-12-01T10:05:30Z",
            "celery_task_id": "abc123-def456-ghi789"
        }
    ]
}
```

#### Create Analysis Task
```http
POST /analysis/tasks/
```

**Request Body:**
```json
{
    "repository_name": "username/my-project",
    "developer_name": "johndoe",
    "analysis_type": "performance",
    "date_from": "2023-11-01",
    "date_to": "2023-11-30",
    "ai_provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "agent_id": 5,
    "analysis_config": {
        "include_file_changes": true,
        "include_commit_messages": true,
        "focus_areas": ["productivity", "code_quality"]
    }
}
```

**Response:**
```json
{
    "id": 26,
    "repository_name": "username/my-project",
    "developer_name": "johndoe",
    "analysis_type": "performance",
    "date_from": "2023-11-01",
    "date_to": "2023-11-30",
    "status": "pending",
    "progress": 0,
    "ai_provider": "openai",
    "model": "gpt-4",
    "created_at": "2023-12-01T15:30:00Z",
    "celery_task_id": "new-task-id-123"
}
```

#### Get Analysis Task Details
```http
GET /analysis/tasks/{id}/
```

#### Cancel Analysis Task
```http
POST /analysis/tasks/{id}/cancel/
```

**Response:**
```json
{
    "message": "Analysis task cancelled successfully",
    "status": "cancelled"
}
```

#### Get Task Progress
```http
GET /analysis/tasks/{id}/progress/
```

**Response:**
```json
{
    "task_id": 1,
    "status": "running",
    "progress": 75,
    "current_step": "Analyzing commits",
    "estimated_completion": "2023-12-01T10:08:00Z",
    "error_message": null
}
```

### Analysis Results

#### List Analysis Results
```http
GET /analysis/results/
```

**Query Parameters:**
- `task_id` (optional): Filter by task ID
- `ai_provider` (optional): Filter by AI provider
- `repository_name` (optional): Filter by repository
- `date_from` (optional): Filter results created after date
- `date_to` (optional): Filter results created before date

**Response:**
```json
{
    "count": 20,
    "results": [
        {
            "id": 1,
            "task": {
                "id": 1,
                "repository_name": "username/my-project",
                "developer_name": "johndoe",
                "analysis_type": "performance"
            },
            "analysis_result": {
                "analysis": "Based on the commit data analysis...",
                "key_insights": [
                    "High commit frequency indicates good productivity",
                    "Consistent code quality across commits",
                    "Strong focus on bug fixes and improvements"
                ],
                "recommendations": [
                    "Consider implementing code review process",
                    "Add more comprehensive tests",
                    "Document complex algorithms better"
                ],
                "metrics": {
                    "productivity_score": 8.5,
                    "code_quality_score": 7.8,
                    "consistency_score": 9.2
                },
                "metadata": {
                    "analysis_duration": 45.2,
                    "tokens_used": 2847,
                    "commit_count_analyzed": 45
                }
            },
            "ai_provider": "openai",
            "model_used": "gpt-4",
            "cost_usd": 0.15,
            "created_at": "2023-12-01T10:05:30Z"
        }
    ]
}
```

#### Get Analysis Result Details
```http
GET /analysis/results/{id}/
```

### Analysis Exports

#### List Exports
```http
GET /analysis/exports/
```

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "export_type": "excel",
            "export_format": "detailed",
            "file_path": "/exports/analysis_export_20231201_103000.xlsx",
            "file_size": 2048576,
            "status": "completed",
            "created_at": "2023-12-01T10:30:00Z",
            "expires_at": "2023-12-08T10:30:00Z",
            "download_count": 3
        }
    ]
}
```

#### Create Export
```http
POST /analysis/exports/
```

**Request Body:**
```json
{
    "export_type": "excel",
    "export_format": "detailed",
    "filters": {
        "repository_name": "username/my-project",
        "date_from": "2023-11-01",
        "date_to": "2023-11-30"
    }
}
```

#### Download Export
```http
GET /analysis/exports/{id}/download/
```

**Response:** File download with appropriate headers

### Analysis Templates

#### List Analysis Templates
```http
GET /analysis/templates/
```

#### Create Analysis Template
```http
POST /analysis/templates/
```

**Request Body:**
```json
{
    "name": "Custom Analysis Template",
    "description": "Template for team performance analysis",
    "template_config": {
        "analysis_type": "performance",
        "ai_provider": "openai",
        "model": "gpt-4",
        "default_date_range": 30,
        "focus_areas": ["productivity", "collaboration"]
    },
    "is_public": false
}
```

### Statistics

#### Get Analysis Statistics
```http
GET /analysis/statistics/
```

**Query Parameters:**
- `period` (optional): Time period (week, month, quarter, year)
- `repository_name` (optional): Filter by repository

**Response:**
```json
{
    "total_analyses": 150,
    "completed_analyses": 142,
    "failed_analyses": 5,
    "cancelled_analyses": 3,
    "total_cost": 45.67,
    "avg_analysis_time": 125.5,
    "most_analyzed_repositories": [
        {
            "repository_name": "username/main-project",
            "analysis_count": 25
        }
    ],
    "ai_provider_usage": {
        "openai": 120,
        "anthropic": 30
    },
    "analysis_types": {
        "performance": 80,
        "quality": 45,
        "security": 25
    }
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

### Error Response Format
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "repository_name",
            "value": "",
            "reason": "This field is required"
        }
    }
}
```

### Common Error Codes

- `400 Bad Request`: Invalid input data or parameters
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: External service error (GitHub API, AI providers)

### Custom Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `AI_PROVIDER_ERROR`: AI service error
- `GITHUB_API_ERROR`: GitHub API error
- `INSUFFICIENT_DATA`: Not enough data for analysis
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `CONFIGURATION_ERROR`: Invalid configuration
- `EXPORT_ERROR`: Export generation failed

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authenticated users**: 1000 requests per hour
- **Analysis tasks**: 10 concurrent tasks per user
- **Export generation**: 5 exports per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1701432000
```

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

Pagination response format:
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/endpoint/?page=2",
    "previous": null,
    "results": [...]
}
```

## Filtering and Searching

Many endpoints support filtering and searching:

### Common Filter Parameters
- `search`: Text search in relevant fields
- `ordering`: Sort results (prefix with `-` for descending)
- `created_at__gte`: Filter by creation date (greater than or equal)
- `created_at__lte`: Filter by creation date (less than or equal)

### Example
```http
GET /analysis/tasks/?search=performance&status=completed&ordering=-created_at
```

## Webhooks (Future Feature)

The API will support webhooks for real-time notifications:

### Webhook Events
- `analysis.task.completed`
- `analysis.task.failed`
- `export.ready`

### Webhook Payload Example
```json
{
    "event": "analysis.task.completed",
    "timestamp": "2023-12-01T10:05:30Z",
    "data": {
        "task_id": 1,
        "repository_name": "username/my-project",
        "status": "completed",
        "result_id": 1
    }
}
```

## SDK and Client Libraries

Official client libraries are available for:

- Python: `pip install github-analyzer-client`
- JavaScript/Node.js: `npm install github-analyzer-client`
- Go: `go get github.com/username/github-analyzer-go`

### Python Example
```python
from github_analyzer import GitHubAnalyzer

client = GitHubAnalyzer(api_key='your_jwt_token')

# Create analysis task
task = client.create_analysis_task(
    repository='username/my-project',
    analysis_type='performance',
    date_from='2023-11-01',
    date_to='2023-11-30'
)

# Wait for completion
result = client.wait_for_completion(task.id)
print(result.analysis)
```

## Support

For API support and questions:
- Documentation: [https://docs.github-analyzer.com](https://docs.github-analyzer.com)
- Issues: [https://github.com/username/github-analyzer/issues](https://github.com/username/github-analyzer/issues)
- Email: support@github-analyzer.com
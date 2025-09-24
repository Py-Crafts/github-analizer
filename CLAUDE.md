# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- `docker-compose up -d` - Start all services in development mode
- `docker-compose up -d postgres redis` - Start only database services
- `docker-compose logs -f` - View all service logs
- `docker-compose logs -f backend` - View backend logs only

### Database Operations
- `docker-compose exec backend python manage.py migrate` - Run database migrations
- `docker-compose exec backend python manage.py makemigrations` - Create new migrations
- `docker-compose exec backend python manage.py createsuperuser` - Create admin user
- `docker-compose exec backend python manage.py shell` - Django shell

### Testing
- `docker-compose exec backend python manage.py test` - Run all backend tests
- `docker-compose exec backend python manage.py test apps.analysis.tests` - Run specific app tests
- `docker-compose exec frontend npm test` - Run frontend tests

### Celery Tasks
- `docker-compose exec celery_worker celery -A config inspect active` - View active tasks
- `docker-compose exec celery_worker celery -A config purge` - Purge task queue
- Access Flower UI at http://localhost:5555 for task monitoring

### Setup and Deployment
- `./scripts/setup.sh --full` - Full development setup including dependencies
- `./scripts/deploy.sh deploy` - Production deployment

## Architecture Overview

### Core Applications
- **accounts** (`backend/apps/accounts/`) - User management and authentication using custom UserProfile model
- **github** (`backend/apps/github/`) - GitHub repository integration, stores Repository and Commit models
- **agents** (`backend/apps/agents/`) - AI agent management for different analysis providers (OpenAI, Anthropic, Google)
- **analysis** (`backend/apps/analysis/`) - Core analysis engine with AnalysisTask, AnalysisResult, and export functionality

### Key Models
- `UserProfile` (accounts.models) - Custom user model with GitHub integration
- `Repository` (github.models) - GitHub repository data with sync status
- `Commit` (github.models) - Individual commit data with statistics
- `AnalysisTask` (analysis.models) - Asynchronous analysis task tracking
- `AnalysisResult` (analysis.models) - Processed analysis results with developer statistics
- `AIAgent` (agents.models) - AI provider configuration and templates

### Technology Stack
- **Backend**: Django 4.2 + DRF with JWT authentication
- **Database**: PostgreSQL with Redis for caching and Celery
- **Task Queue**: Celery with Redis broker for async analysis
- **AI Integration**: Multiple providers (OpenAI, Anthropic, Google AI)
- **Export Formats**: Excel, CSV, JSON, PDF via openpyxl and xlsxwriter

### Authentication & Security
- JWT-based authentication with refresh tokens
- Custom user model with GitHub OAuth integration
- CORS configuration for frontend integration
- Rate limiting for analysis tasks (5 concurrent, 20/hour per user)

### Analysis Workflow
1. User creates AnalysisTask with repository and AI agent selection
2. Celery worker processes task asynchronously via `analysis.tasks`
3. GitHub data is fetched and stored in Repository/Commit models
4. AI agent analyzes commit patterns and developer activity
5. Results stored in AnalysisResult with formatted output
6. Export functionality generates reports in multiple formats

### Configuration
- Settings split into `config/settings/` (base.py, development.py, production.py)
- Environment variables managed via python-decouple
- Docker containerization with separate services for web, worker, beat scheduler
- Monitoring with Prometheus/Grafana integration

### API Structure
- `/api/auth/` - Authentication endpoints
- `/api/repositories/` - Repository management
- `/api/analysis/tasks/` - Analysis task CRUD
- `/api/analysis/results/` - Analysis results with filtering
- `/api/analysis/exports/` - Export generation and download
- API documentation available at `/api/docs/` via drf-spectacular

## Important Notes

### Development Environment
- Uses SQLite for development (`db.sqlite3`) but PostgreSQL in production
- Frontend service expects React/Next.js application (currently minimal Docker setup)
- Hot reloading enabled for backend via volume mounts
- Default admin credentials: admin/admin123

### AI Provider Integration
- Supports multiple AI providers with fallback mechanisms
- API keys configured via environment variables
- Analysis templates can be created for reusable configurations
- Token usage and cost tracking implemented

### File Organization
- Business logic primarily in apps/{app_name}/views.py and tasks.py
- Custom exception handling in `analysis.exceptions`
- Utility functions in `utils/` directory
- Static files served via WhiteNoise in production
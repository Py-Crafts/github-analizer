# GitHub Analyzer

GitHub Analyzer - bu GitHub repositoriyalarini tahlil qilish va AI yordamida dasturchilar faoliyatini baholash uchun mo'ljallangan to'liq ishlaydigan loyiha.

## 🚀 Features

- **AI-Powered Analysis**: Leverage multiple AI providers (OpenAI, Anthropic, Google) for intelligent code analysis
- **Repository Insights**: Deep analysis of commit patterns, code quality, and development trends
- **Multi-Format Reports**: Generate reports in JSON, PDF, and Excel formats
- **Real-time Processing**: Asynchronous task processing with Celery
- **Scalable Architecture**: Microservices-based design with Docker containerization
- **Comprehensive Monitoring**: Built-in monitoring with Prometheus and Grafana
- **Security First**: Production-ready security configurations and best practices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   (Next.js)     │◄──►│   (Django)      │◄──►│   (OpenAI, etc) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   PostgreSQL    │    │     Redis       │
│  (Load Balancer)│    │   (Database)    │    │    (Cache)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Traefik      │    │     Celery      │    │   Monitoring    │
│ (Reverse Proxy) │    │  (Task Queue)   │    │ (Prometheus)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Git

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/github-analyzer.git
cd github-analyzer
```

### 2. Environment Setup

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit the .env file with your configuration
nano backend/.env
```

### 3. Development Setup

```bash
# Make setup script executable
chmod +x scripts/setup.sh

# Run full setup (installs dependencies and sets up environment)
./scripts/setup.sh --full
```

### 4. Start Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/ (admin/admin123)
- **API Documentation**: http://localhost:8000/api/docs/

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/github_analyzer

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub API
GITHUB_TOKEN=your-github-token
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# AI Providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_AI_API_KEY=your-google-key

# Email (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### AI Provider Configuration

The system supports multiple AI providers. Configure at least one:

1. **OpenAI**: Set `OPENAI_API_KEY`
2. **Anthropic**: Set `ANTHROPIC_API_KEY`
3. **Google AI**: Set `GOOGLE_AI_API_KEY`

## 📊 Usage

### 1. Repository Analysis

```python
# Via API
POST /api/analysis/tasks/
{
    "repository_url": "https://github.com/owner/repo",
    "analysis_type": "comprehensive",
    "ai_provider": "openai"
}
```

### 2. Export Reports

```python
# Generate Excel report
POST /api/analysis/exports/
{
    "analysis_id": "uuid-here",
    "format": "excel",
    "include_details": true
}
```

### 3. Monitor Progress

```python
# Check task status
GET /api/analysis/tasks/{task_id}/
```

## 🚀 Production Deployment

### 1. Production Setup

```bash
# Copy production environment
cp backend/.env.example backend/.env.prod

# Edit production configuration
nano backend/.env.prod

# Set production environment
export ENVIRONMENT=production
```

### 2. SSL Configuration

```bash
# Generate SSL certificates (Let's Encrypt recommended)
certbot certonly --standalone -d yourdomain.com
```

### 3. Deploy

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh deploy
```

### 4. Monitoring

Access monitoring dashboards:

- **Grafana**: http://yourdomain.com:3001 (admin/admin)
- **Prometheus**: http://yourdomain.com:9090

## 🔍 API Documentation

### Authentication

The API uses JWT authentication:

```bash
# Login
POST /api/auth/login/
{
    "username": "your-username",
    "password": "your-password"
}

# Use token in subsequent requests
Authorization: Bearer <your-jwt-token>
```

### Key Endpoints

- `GET /api/repositories/` - List repositories
- `POST /api/analysis/tasks/` - Create analysis task
- `GET /api/analysis/results/` - List analysis results
- `POST /api/analysis/exports/` - Export analysis
- `GET /api/statistics/` - Get system statistics

## 🧪 Testing

### Run Tests

```bash
# Backend tests
docker-compose exec backend python manage.py test

# Frontend tests
docker-compose exec frontend npm test

# Integration tests
docker-compose exec backend python manage.py test apps.analysis.tests.IntegrationTestCase
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📈 Monitoring and Logging

### Logs

```bash
# View application logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f postgres
```

### Metrics

Key metrics monitored:

- Request rate and response time
- Error rates (4xx, 5xx)
- Database performance
- Celery task queue status
- GitHub API rate limits
- System resources (CPU, memory, disk)

### Alerts

Configured alerts for:

- Service downtime
- High error rates
- Resource exhaustion
- Database issues
- Task queue backlog

## 🔒 Security

### Security Features

- JWT authentication with refresh tokens
- Rate limiting on API endpoints
- CORS configuration
- Security headers (CSP, HSTS, etc.)
- Input validation and sanitization
- SQL injection protection
- XSS protection

### Security Best Practices

1. **Environment Variables**: Never commit secrets to version control
2. **HTTPS**: Always use HTTPS in production
3. **Database**: Use strong passwords and limit access
4. **API Keys**: Rotate API keys regularly
5. **Updates**: Keep dependencies updated

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint for JavaScript/TypeScript
- Write tests for new features
- Update documentation
- Follow conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Permission errors**: Check file permissions and Docker group membership
3. **Memory issues**: Increase Docker memory allocation
4. **API rate limits**: Configure GitHub token with higher limits

### Getting Help

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-username/github-analyzer/issues)
- 💬 [Discussions](https://github.com/your-username/github-analyzer/discussions)

## 🙏 Acknowledgments

- Django and Django REST Framework
- Next.js and React
- OpenAI, Anthropic, and Google AI
- Docker and Docker Compose
- Prometheus and Grafana
- All open-source contributors

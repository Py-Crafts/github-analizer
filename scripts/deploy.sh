#!/bin/bash

# GitHub Analyzer Deployment Script
# This script handles production deployment with safety checks and rollback capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/var/backups/github-analyzer"
LOG_FILE="/var/log/github-analyzer-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        error ".env file not found. Please create it from .env.example"
    fi
    
    # Check if required directories exist
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    success "Prerequisites check passed"
}

# Backup database
backup_database() {
    log "Creating database backup..."
    
    local backup_file="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Get database container name
    local db_container=$(docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" ps -q postgres)
    
    if [[ -n "$db_container" ]]; then
        docker exec "$db_container" pg_dump -U postgres github_analyzer > "$backup_file"
        success "Database backup created: $backup_file"
    else
        warning "Database container not found, skipping backup"
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost/health > /dev/null; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
}

# Rollback function
rollback() {
    warning "Rolling back to previous version..."
    
    # Stop current containers
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" down
    
    # Restore from backup if available
    local latest_backup=$(ls -t "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | head -n1)
    if [[ -n "$latest_backup" ]]; then
        log "Restoring database from backup: $latest_backup"
        # Restore database logic here
    fi
    
    # Start previous version (this would need version tagging)
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" up -d
    
    error "Rollback completed"
}

# Main deployment function
deploy() {
    log "Starting deployment process..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images
    log "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Create backup
    backup_database
    
    # Stop services gracefully
    log "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Start services
    log "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Run migrations
    log "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate --noinput
    
    # Collect static files
    log "Collecting static files..."
    docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py collectstatic --noinput
    
    # Health check
    if ! health_check; then
        rollback
    fi
    
    # Clean up old images
    log "Cleaning up old Docker images..."
    docker image prune -f
    
    success "Deployment completed successfully!"
}

# Update SSL certificates (if using Let's Encrypt)
update_ssl() {
    log "Updating SSL certificates..."
    
    if command -v certbot &> /dev/null; then
        certbot renew --quiet
        success "SSL certificates updated"
    else
        warning "Certbot not found, skipping SSL update"
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  deploy          Deploy the application"
    echo "  rollback        Rollback to previous version"
    echo "  backup          Create database backup"
    echo "  health          Perform health check"
    echo "  ssl             Update SSL certificates"
    echo "  logs            Show application logs"
    echo "  status          Show service status"
    echo "  -h, --help      Show this help message"
}

# Show logs
show_logs() {
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" logs -f --tail=100
}

# Show status
show_status() {
    docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" ps
}

# Main script logic
main() {
    case "${1:-}" in
        deploy)
            check_root
            check_prerequisites
            deploy
            ;;
        rollback)
            rollback
            ;;
        backup)
            backup_database
            ;;
        health)
            health_check
            ;;
        ssl)
            update_ssl
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Trap errors and perform rollback
trap 'rollback' ERR

# Run main function
main "$@"
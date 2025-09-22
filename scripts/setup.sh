#!/bin/bash

# GitHub Analyzer Setup Script
# This script sets up the development environment and initial configuration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker (Ubuntu/Debian)
install_docker() {
    if command_exists docker; then
        log "Docker is already installed"
        return 0
    fi
    
    log "Installing Docker..."
    
    # Update package index
    sudo apt-get update
    
    # Install prerequisites
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up stable repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Add current user to docker group
    sudo usermod -aG docker "$USER"
    
    success "Docker installed successfully"
}

# Install Docker Compose
install_docker_compose() {
    if command_exists docker-compose; then
        log "Docker Compose is already installed"
        return 0
    fi
    
    log "Installing Docker Compose..."
    
    # Download Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    success "Docker Compose installed successfully"
}

# Install Node.js (using NodeSource repository)
install_nodejs() {
    if command_exists node; then
        local node_version=$(node --version)
        log "Node.js is already installed: $node_version"
        return 0
    fi
    
    log "Installing Node.js..."
    
    # Install NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    
    # Install Node.js
    sudo apt-get install -y nodejs
    
    success "Node.js installed successfully"
}

# Install Python (if not available)
install_python() {
    if command_exists python3; then
        local python_version=$(python3 --version)
        log "Python is already installed: $python_version"
        return 0
    fi
    
    log "Installing Python..."
    
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
    
    success "Python installed successfully"
}

# Setup environment file
setup_env_file() {
    log "Setting up environment file..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            log "Created .env file from .env.example"
        else
            error ".env.example file not found"
        fi
    else
        log ".env file already exists"
    fi
    
    # Generate secret key if not set
    if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your-secret-key-here" .env; then
        local secret_key=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
        log "Generated new Django secret key"
    fi
    
    success "Environment file setup completed"
}

# Setup backend
setup_backend() {
    log "Setting up backend..."
    
    cd "$PROJECT_ROOT/backend"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d venv ]]; then
        python3 -m venv venv
        log "Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    
    if [[ -f requirements.txt ]]; then
        pip install -r requirements.txt
        log "Installed Python dependencies"
    else
        warning "requirements.txt not found, skipping Python dependencies"
    fi
    
    success "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    log "Setting up frontend..."
    
    cd "$PROJECT_ROOT/frontend"
    
    if [[ -f package.json ]]; then
        npm install
        log "Installed Node.js dependencies"
    else
        warning "package.json not found, skipping Node.js dependencies"
    fi
    
    success "Frontend setup completed"
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    cd "$PROJECT_ROOT"
    
    # Start database container
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker-compose exec backend python manage.py migrate
    
    # Create superuser if it doesn't exist
    docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"
    
    success "Database setup completed"
}

# Setup SSL certificates (development)
setup_ssl_dev() {
    log "Setting up development SSL certificates..."
    
    local ssl_dir="$PROJECT_ROOT/ssl"
    mkdir -p "$ssl_dir"
    
    if [[ ! -f "$ssl_dir/cert.pem" ]]; then
        # Generate self-signed certificate for development
        openssl req -x509 -newkey rsa:4096 -keyout "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        log "Generated self-signed SSL certificate for development"
    else
        log "SSL certificate already exists"
    fi
    
    success "SSL setup completed"
}

# Make scripts executable
setup_scripts() {
    log "Setting up scripts..."
    
    chmod +x "$PROJECT_ROOT/scripts/"*.sh
    
    success "Scripts setup completed"
}

# Show final instructions
show_instructions() {
    echo ""
    success "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update the .env file with your specific configuration"
    echo "2. Start the development environment: docker-compose up -d"
    echo "3. Access the application:"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:8000/api/"
    echo "   - Admin: http://localhost:8000/admin/ (admin/admin123)"
    echo "4. Check logs: docker-compose logs -f"
    echo ""
    echo "For production deployment, use: ./scripts/deploy.sh deploy"
}

# Main setup function
main() {
    log "Starting GitHub Analyzer setup..."
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        warning "This script is designed for Linux. Some features may not work on other systems."
    fi
    
    # Install prerequisites
    if [[ "${1:-}" != "--skip-install" ]]; then
        install_docker
        install_docker_compose
        install_nodejs
        install_python
    fi
    
    # Setup project
    setup_env_file
    setup_scripts
    
    # Setup components
    if [[ "${1:-}" == "--full" ]]; then
        setup_backend
        setup_frontend
        setup_database
        setup_ssl_dev
    fi
    
    show_instructions
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full          Full setup including backend, frontend, and database"
    echo "  --skip-install  Skip installation of system dependencies"
    echo "  -h, --help      Show this help message"
}

# Handle arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
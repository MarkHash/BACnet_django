# Installation Guide

This guide provides detailed installation instructions for all supported platforms.

## Platform Support

This application supports **cross-platform deployment** with automatic OS detection:

- **Linux/Mac**: Full Docker containerization with host networking
- **Windows**: Hybrid architecture with native BACnet networking

## Requirements

- **Python**: 3.12+
- **Django**: 5.2+
- **PostgreSQL**: 12+
- **BAC0**: 23.07.03+ (BACnet communication)
- **Docker**: Latest version
- **Git**: For cloning the repository

## Linux/Mac Installation (Docker)

### 1. Clone the repository
```bash
git clone <repository-url>
cd BACnet_django
```

### 2. Start with Docker Compose
```bash
docker-compose up -d
```

That's it! The application will be available at http://127.0.0.1:8000

### 3. Access the application
- **Web Interface**: http://127.0.0.1:8000/
- **Admin Interface**: http://127.0.0.1:8000/admin/
- **API Documentation**: http://127.0.0.1:8000/api/docs/

### 4. Default Admin Credentials
- **Username**: bacnet_user
- **Password**: password

## Windows Installation (Integrated Server)

### 1. Clone the repository
```bash
git clone <repository-url>
cd BACnet_django
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Docker infrastructure
```bash
docker-compose -f docker-compose.windows.yml up -d --build
```
This starts PostgreSQL, Redis, and Celery workers in Docker containers.

**⚠️ Important**: If you have local PostgreSQL installed, it may conflict with Docker PostgreSQL on port 5432. See [Troubleshooting](troubleshooting.md#postgresql-database-conflicts) if data isn't being saved.

### 5. Run the integrated server
```bash
python windows_integrated_server.py
```

### 6. Access the application
- **Web Interface**: http://127.0.0.1:8000/
- **Admin Interface**: http://127.0.0.1:8000/admin/

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_NAME=bacnet_django
DB_USER=bacnet_user
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

# BACnet Configuration
BACNET_INTERFACE=auto
BACNET_PORT=47808
```

### Django Settings

Key settings in `bacnet_project/settings.py`:

- **TIME_ZONE**: Set to your local timezone
- **DEBUG**: Set to False in production
- **ALLOWED_HOSTS**: Add your domain/IP for production
- **DATABASE**: PostgreSQL configuration with connection pooling

## Database Setup

### Initial Migration
```bash
# Apply database migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser
```

### Database Management
```bash
# Clean database for fresh start
python manage.py clean_db

# Import/export data using Django admin
# Access admin at http://127.0.0.1:8000/admin/
```

## Verification

### Test Installation
```bash
# Check if all services are running
docker-compose ps

# Test database connection
python manage.py dbshell

# Run basic system check
python manage.py check
```

### Test BACnet Discovery
1. Navigate to http://127.0.0.1:8000
2. Click "Start Discovery"
3. Check for discovered devices
4. Verify API endpoints at http://127.0.0.1:8000/api/docs/

## Performance Tuning

### PostgreSQL Optimization
```sql
-- Recommended PostgreSQL settings for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Docker Resource Limits
```yaml
# docker-compose.yml
services:
  db:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## Production Deployment

### Security Configuration
```python
# Production settings
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')  # Use environment variable
ALLOWED_HOSTS = ['your-domain.com', 'your-ip-address']

# Database security
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        }
    }
}
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/static/files/;
    }
}
```

## Troubleshooting Installation

### Common Issues

1. **Port Conflicts**
   - PostgreSQL: Check if port 5432 is already in use
   - Django: Check if port 8000 is available
   - BACnet: Ensure UDP port 47808 is not blocked

2. **Permission Issues**
   - Make sure Docker has appropriate permissions
   - Check file ownership in the project directory

3. **Network Issues**
   - Verify firewall settings for BACnet UDP traffic
   - Check Docker network configuration

### Platform-Specific Issues

#### Windows
- Use `127.0.0.1` instead of `localhost` to avoid IPv6 issues
- Stop local PostgreSQL service if conflicts occur
- Run PowerShell as Administrator for Docker commands

#### Linux/Mac
- Ensure Docker has host networking access
- Check SELinux/AppArmor policies if applicable
- Verify user is in docker group

### Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md) for detailed solutions
- Review logs: `docker-compose logs`
- Test API endpoints: `curl http://127.0.0.1:8000/api/v2/devices/status/`
- Join our community discussions for support
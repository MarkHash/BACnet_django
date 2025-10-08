# Cross-Platform Repository Structure Implementation

## File Structure to Create

### 1. Settings Structure
```
bacnet_project/settings/
├── __init__.py                 # Auto-detect platform
├── base.py                     # Shared settings
├── linux.py                    # Linux Docker host networking
└── windows.py                  # Windows hybrid approach
```

### 2. Deployment Structure
```
deployment/
├── detect_platform.py         # Platform detection script
├── deploy.py                   # Universal deployment script
├── linux/
│   ├── docker-compose.yml     # Linux host networking version
│   ├── .env.linux.example
│   └── deploy_linux.sh
├── windows/
│   ├── docker-compose.yml     # Windows version (no bacnet-worker)
│   ├── bacnet_worker_windows.py
│   ├── start_bacnet_worker.bat
│   ├── setup_windows_env.bat
│   └── .env.windows.example
└── shared/
    ├── base-services.yml       # Common services (db, redis, web)
    └── README.md              # Platform guide
```

## Implementation Code Examples

### bacnet_project/settings/__init__.py
```python
"""
Auto-detect platform and load appropriate settings
"""
import platform
import os

# Detect platform
system = platform.system().lower()

if system == 'linux':
    from .linux import *
elif system == 'windows':
    from .windows import *
elif system == 'darwin':  # macOS
    from .linux import *  # macOS can use Linux approach
else:
    # Default to base settings
    from .base import *

print(f"🖥️  Detected platform: {system}")
print(f"⚙️  Using settings: bacnet_project.settings.{system if system in ['linux', 'windows'] else 'base'}")
```

### bacnet_project/settings/base.py
```python
"""
Base Django settings shared across all platforms
"""
import os
import sys
from pathlib import Path
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv()

# Security
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if "test" in sys.argv or "GITHUB_ACTIONS" in os.environ:
        SECRET_KEY = "django-insecure-test-key-for-ci-only"
    else:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required")

DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = []

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "discovery",
    "django_celery_results",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bacnet_project.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bacnet_project.wsgi.application"

# Database - Platform-specific override required
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Australia/Melbourne"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery base configuration - Platform-specific override required
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_CREATE_MISSING_QUEUES = True

# Task routing
CELERY_TASK_ROUTES = {
    # BACnet tasks → 'bacnet' queue → Platform-specific worker
    'discovery.tasks.discover_devices': {'queue': 'bacnet'},
    'discovery.tasks.read_device_points': {'queue': 'bacnet'},
    'discovery.tasks.discover_device_points': {'queue': 'bacnet'},
    'discovery.tasks.read_point_value': {'queue': 'bacnet'},

    # General tasks → 'default' queue → Docker worker
    'discovery.tasks.calculate_hourly_stats': {'queue': 'default'},
    'discovery.tasks.calculate_daily_stats': {'queue': 'default'},
}

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "calculate-hourly-stats": {
        "task": "discovery.tasks.calculate_hourly_stats",
        "schedule": crontab(minute=0),
    },
    "calculate-daily-stats": {
        "task": "discovery.tasks.calculate_daily_stats",
        "schedule": crontab(hour=0, minute=5),
    },
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.utils.autoreload": {
            "level": "WARNING",
        },
        "BAC0_Root": {
            "level": "WARNING",
        },
    },
}
```

### bacnet_project/settings/linux.py
```python
"""
Linux-specific Django settings
Uses Docker host networking for BACnet access
"""
from .base import *

print("🐧 Linux settings loaded - Docker host networking enabled")

# Linux Docker host networking - containers use actual host network
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379")

# Database connection for Linux Docker host networking
DATABASES['default'].update({
    'HOST': os.getenv("DB_HOST", "localhost"),  # Direct host access
    'PORT': os.getenv("DB_PORT", "5432"),
})

# Linux-specific deployment marker
DEPLOYMENT_PLATFORM = "LINUX"
BACNET_DEPLOYMENT_TYPE = "DOCKER_HOST_NETWORKING"
```

### bacnet_project/settings/windows.py
```python
"""
Windows-specific Django settings
Uses hybrid Docker + Windows native worker approach
"""
from .base import *

print("🪟 Windows settings loaded - Hybrid deployment mode")

# Windows hybrid deployment - different connection strings for different processes
if os.getenv('WINDOWS_NATIVE_WORKER'):
    print("🔧 Windows native worker configuration")
    # Native Windows worker connects to Docker-exposed ports
    CELERY_BROKER_URL = "redis://localhost:6379"
    CELERY_RESULT_BACKEND = "redis://localhost:6379"

    DATABASES['default'].update({
        'HOST': 'localhost',  # Docker-exposed port
        'PORT': '5432',
    })

    # Windows worker logging
    LOGGING['handlers']['file'] = {
        'class': 'logging.FileHandler',
        'filename': 'windows_bacnet_worker.log',
        'formatter': 'verbose',
    }
    LOGGING['formatters'] = {
        'verbose': {
            'format': '[WINDOWS-WORKER] {levelname} {asctime} {module} {message}',
            'style': '{',
        },
    }

else:
    print("🐳 Docker services configuration")
    # Docker services use internal Docker networking
    CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://redis:6379")

    DATABASES['default'].update({
        'HOST': os.getenv("DB_HOST", "db"),  # Docker service name
        'PORT': os.getenv("DB_PORT", "5432"),
    })

# Windows-specific deployment marker
DEPLOYMENT_PLATFORM = "WINDOWS"
BACNET_DEPLOYMENT_TYPE = "HYBRID_DOCKER_NATIVE"
```

## Platform Detection Script

### deployment/detect_platform.py
```python
"""
Cross-platform deployment detection and setup
"""
import platform
import os
import sys
import subprocess
from pathlib import Path

class PlatformDetector:
    def __init__(self):
        self.system = platform.system().lower()
        self.is_docker_available = self._check_docker()
        self.is_wsl = self._check_wsl()

    def _check_docker(self):
        """Check if Docker is available"""
        try:
            subprocess.run(['docker', '--version'],
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_wsl(self):
        """Check if running in WSL"""
        return 'microsoft' in platform.release().lower()

    def get_deployment_strategy(self):
        """Determine the best deployment strategy"""
        if self.system == 'linux' and not self.is_wsl:
            return {
                'platform': 'linux',
                'strategy': 'docker_host_networking',
                'complexity': 'low',
                'description': 'Pure Docker with host networking'
            }
        elif self.system == 'linux' and self.is_wsl:
            return {
                'platform': 'wsl2',
                'strategy': 'docker_host_networking',
                'complexity': 'low',
                'description': 'Docker with WSL2 host networking'
            }
        elif self.system == 'windows':
            return {
                'platform': 'windows',
                'strategy': 'hybrid_docker_native',
                'complexity': 'medium',
                'description': 'Docker services + Windows native BACnet worker'
            }
        elif self.system == 'darwin':  # macOS
            return {
                'platform': 'macos',
                'strategy': 'docker_host_networking',
                'complexity': 'low',
                'description': 'Docker with macOS host networking'
            }
        else:
            return {
                'platform': 'unknown',
                'strategy': 'manual_configuration',
                'complexity': 'high',
                'description': 'Manual platform-specific configuration required'
            }

    def print_deployment_info(self):
        """Print deployment information"""
        strategy = self.get_deployment_strategy()

        print("=" * 50)
        print("🚀 BACnet Django Deployment Detection")
        print("=" * 50)
        print(f"🖥️  Platform: {self.system.title()}")
        print(f"🐳 Docker Available: {'✅' if self.is_docker_available else '❌'}")
        if self.system == 'linux':
            print(f"🪟 WSL Environment: {'✅' if self.is_wsl else '❌'}")
        print()
        print(f"📋 Recommended Strategy: {strategy['strategy']}")
        print(f"📊 Complexity Level: {strategy['complexity'].title()}")
        print(f"📝 Description: {strategy['description']}")
        print()

        # Platform-specific guidance
        if strategy['platform'] in ['linux', 'wsl2', 'macos']:
            print("🎯 Next Steps:")
            print("   1. cd deployment/linux/")
            print("   2. ./deploy_linux.sh")
            print("   3. Access: http://localhost:8000")

        elif strategy['platform'] == 'windows':
            print("🎯 Next Steps:")
            print("   1. cd deployment/windows/")
            print("   2. setup_windows_env.bat")
            print("   3. docker-compose up -d")
            print("   4. start_bacnet_worker.bat")
            print("   5. Access: http://localhost:8000")

        print("=" * 50)

        return strategy

if __name__ == "__main__":
    detector = PlatformDetector()
    strategy = detector.print_deployment_info()

    # Set environment variable for scripts
    os.environ['DETECTED_PLATFORM'] = strategy['platform']
    os.environ['DEPLOYMENT_STRATEGY'] = strategy['strategy']
```

## Universal Deployment Script

### deployment/deploy.py
```python
"""
Universal deployment script that auto-detects platform
"""
import os
import sys
import subprocess
from pathlib import Path
from detect_platform import PlatformDetector

def deploy_linux():
    """Deploy using Linux Docker host networking"""
    print("🐧 Deploying for Linux...")
    os.chdir('linux')

    # Copy environment file
    if not Path('.env').exists():
        if Path('.env.linux.example').exists():
            subprocess.run(['cp', '.env.linux.example', '.env'])
            print("📝 Created .env from template - please configure")

    # Deploy with Docker host networking
    subprocess.run(['docker-compose', 'up', '-d'])
    print("✅ Linux deployment complete!")
    print("🌐 Access: http://localhost:8000")

def deploy_windows():
    """Deploy using Windows hybrid approach"""
    print("🪟 Deploying for Windows...")
    os.chdir('windows')

    # Copy environment file
    if not Path('.env').exists():
        if Path('.env.windows.example').exists():
            subprocess.run(['copy', '.env.windows.example', '.env'], shell=True)
            print("📝 Created .env from template - please configure")

    # Setup Windows environment
    print("🔧 Setting up Windows environment...")
    subprocess.run(['setup_windows_env.bat'], shell=True)

    # Start Docker services
    print("🐳 Starting Docker services...")
    subprocess.run(['docker-compose', 'up', '-d'])

    print("✅ Windows deployment complete!")
    print("🎯 Next: Run start_bacnet_worker.bat")
    print("🌐 Access: http://localhost:8000")

def main():
    """Main deployment function"""
    detector = PlatformDetector()
    strategy = detector.print_deployment_info()

    # Confirm deployment
    response = input("\n🚀 Proceed with recommended deployment? (y/n): ")
    if response.lower() != 'y':
        print("❌ Deployment cancelled")
        return

    # Change to deployment directory
    os.chdir(Path(__file__).parent)

    # Deploy based on platform
    if strategy['platform'] in ['linux', 'wsl2', 'macos']:
        deploy_linux()
    elif strategy['platform'] == 'windows':
        deploy_windows()
    else:
        print("❌ Unsupported platform - manual configuration required")
        print("📖 See README-deployment.md for guidance")

if __name__ == "__main__":
    main()
```

This structure provides:
✅ **Auto-platform detection**
✅ **Unified settings architecture**
✅ **Deployment scripts for both platforms**
✅ **Clear separation of concerns**
✅ **Professional repository structure**

Want me to continue with the specific deployment files (docker-compose.yml for each platform)?
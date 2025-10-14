# Development Guide

This guide covers the development environment setup, architecture, testing, and contribution guidelines for the BACnet Django application.

## Development Environment Setup

### Prerequisites
- **Python**: 3.12+
- **Git**: Latest version
- **Docker**: Latest version
- **IDE**: VS Code, PyCharm, or similar with Python support

### Quick Setup
```bash
# Clone repository
git clone <repository-url>
cd BACnet_django

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Set up pre-commit hooks
pre-commit install
```

### Environment Configuration
```bash
# Create .env file
cp .env.example .env

# Configure database
docker-compose up -d db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Project Architecture

### Directory Structure
```
BACnet_django/
├── bacnet_project/          # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # Root URL routing
│   └── wsgi.py            # WSGI application
├── discovery/               # Main application
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   ├── management/         # Custom management commands
│   ├── models.py          # Database models
│   ├── views.py           # HTML views and function-based APIs
│   ├── api_views.py       # Class-based API views
│   ├── services.py        # BACnet communication service
│   ├── energy_analytics.py # HVAC energy analysis
│   ├── ml_utils.py        # Anomaly detection algorithms
│   ├── constants.py       # BACnet constants and mappings
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── serializers.py     # DRF serializers
│   └── urls.py           # URL routing
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── docker-compose.yml     # Docker configuration
└── manage.py              # Django management script
```

### Code Organization Principles

#### Separation of Concerns
- **`views.py`**: HTML rendering and function-based API endpoints
- **`api_views.py`**: Class-based API views with comprehensive documentation
- **`services.py`**: BACnet communication and business logic
- **`models.py`**: Database models and data validation
- **`serializers.py`**: API data serialization and validation

#### Enterprise Architecture
- **Type Safety**: 100% type hints across all modules
- **Error Handling**: Custom exception hierarchy with graceful recovery
- **Documentation**: Comprehensive docstrings and API documentation
- **Testing**: Unit tests with high coverage
- **Code Quality**: Flake8 compliance with consistent formatting

## Core Components

### BACnet Communication Layer

**File**: `discovery/services.py`

```python
class BACnetService:
    """
    Handles all BACnet communication using BAC0 library.
    Implements context manager pattern for connection lifecycle.
    """

    def __init__(self):
        self.bacnet = None
        self.anomaly_detector = AnomalyDetector()

    def discover_devices(self) -> List[BACnetDevice]:
        """Discover BACnet devices on network"""

    def read_point_value(self, device: BACnetDevice, point: BACnetPoint) -> str:
        """Read single point value from device"""
```

**Key Features**:
- Context manager for automatic connection cleanup
- Optimized batch reading with chunking
- Comprehensive error handling and recovery
- Anomaly detection integration

### Database Models

**File**: `discovery/models.py`

```python
class BACnetDevice(models.Model):
    """Represents a BACnet device on the network"""
    device_id = models.IntegerField(unique=True)
    address = models.GenericIPAddressField()
    vendor_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

class BACnetPoint(models.Model):
    """Represents a BACnet object/point on a device"""
    device = models.ForeignKey(BACnetDevice, on_delete=models.CASCADE)
    object_type = models.CharField(max_length=50)
    instance_number = models.IntegerField()
    identifier = models.CharField(max_length=100)

class BACnetReading(models.Model):
    """Historical reading from a BACnet point"""
    point = models.ForeignKey(BACnetPoint, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    read_time = models.DateTimeField(auto_now_add=True)
    anomaly_score = models.FloatField(null=True, blank=True)
    is_anomaly = models.BooleanField(default=False)
```

### API Architecture

**Modern API Design** (`api_views.py`):
- Class-based views using Django REST Framework
- Comprehensive serializers for data validation
- OpenAPI documentation with drf-spectacular
- Structured error responses with custom exceptions

**Legacy API Support** (`views.py`):
- Function-based views for backward compatibility
- Direct JsonResponse for simple endpoints
- Maintained for existing integrations

### Energy Analytics System

**File**: `discovery/energy_analytics.py`

```python
class EnergyAnalyticsService:
    """
    Processes temperature data to calculate energy metrics.
    Implements HVAC load estimation and ML forecasting.
    """

    def calculate_daily_metrics(self, date: Optional[date] = None) -> int:
        """Calculate energy metrics for all devices"""

    def _calculate_hvac_load(self, temp_deviation: float, reading_count: int) -> float:
        """Estimate HVAC energy consumption"""

    def _generate_ml_forecast(self, df: pd.DataFrame, device: BACnetDevice) -> Tuple[Optional[float], float]:
        """Generate ML forecast for next-day energy consumption"""
```

### Anomaly Detection System

**File**: `discovery/ml_utils.py`

```python
class AnomalyDetector:
    """
    Statistical anomaly detection for temperature sensors.
    Implements Z-score and IQR methods for robust detection.
    """

    def detect_z_score_anomaly(self, point: BACnetPoint, new_value: float) -> float:
        """Z-score based anomaly detection"""

    def detect_iqr_anomaly(self, point: BACnetPoint, new_value: float) -> tuple[float, bool]:
        """IQR based anomaly detection"""
```

## Development Workflow

### Code Style and Quality

#### Type Hints
All new code must include comprehensive type hints:

```python
from typing import Dict, List, Optional, Tuple, Union

def process_device_data(
    device: BACnetDevice,
    readings: List[BACnetReading]
) -> Dict[str, Union[int, float]]:
    """Process device data with full type annotations"""
    pass
```

#### Code Formatting
- **Line length**: 88 characters (Black default)
- **Import organization**: isort with Django profile
- **Docstrings**: Google style for consistency
- **Variable naming**: snake_case for Python, PascalCase for classes

#### Quality Checks
```bash
# Run all quality checks
flake8 discovery/
black --check discovery/
isort --check-only discovery/
mypy discovery/

# Auto-format code
black discovery/
isort discovery/
```

### Testing Strategy

#### Unit Tests
```python
# tests/test_services.py
from django.test import TestCase
from discovery.services import BACnetService
from discovery.models import BACnetDevice

class BACnetServiceTest(TestCase):
    def setUp(self):
        self.service = BACnetService()
        self.device = BACnetDevice.objects.create(
            device_id=2000,
            address='192.168.1.100'
        )

    def test_device_discovery(self):
        """Test device discovery functionality"""
        devices = self.service.discover_devices()
        self.assertIsInstance(devices, list)
```

#### Integration Tests
```python
# tests/test_api.py
from rest_framework.test import APITestCase
from django.urls import reverse

class DeviceAPITest(APITestCase):
    def test_device_status_api(self):
        """Test device status API endpoint"""
        url = reverse('device-status-api-v2')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
```

#### Test Commands
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report -m

# Run specific test
python manage.py test discovery.tests.test_services.BACnetServiceTest.test_device_discovery
```

### Database Development

#### Migrations
```bash
# Create migration
python manage.py makemigrations discovery

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate discovery 0001
```

#### Custom Management Commands
```python
# discovery/management/commands/analyze_energy.py
from django.core.management.base import BaseCommand
from discovery.energy_analytics import EnergyAnalyticsService

class Command(BaseCommand):
    help = 'Analyze energy consumption for all devices'

    def handle(self, *args, **options):
        service = EnergyAnalyticsService()
        metrics_created = service.calculate_daily_metrics()
        self.stdout.write(f"Created metrics for {metrics_created} devices")
```

## API Development

### Adding New Endpoints

#### Class-based API View
```python
# discovery/api_views.py
class NewFeatureAPIView(APIView):
    @extend_schema(
        summary="New feature endpoint",
        description="Detailed description of the new feature",
        responses={200: ResponseSerializer}
    )
    def get(self, request):
        # Implementation
        return Response({"success": True, "data": result})
```

#### Serializers
```python
# discovery/serializers.py
class NewFeatureResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = serializers.DictField()
    timestamp = serializers.DateTimeField()
```

#### URL Configuration
```python
# discovery/urls.py
from .api_views import NewFeatureAPIView

urlpatterns = [
    path('api/v2/new-feature/', NewFeatureAPIView.as_view(), name='new-feature-api'),
]
```

### API Documentation

All API endpoints must include:
- OpenAPI schema with drf-spectacular
- Comprehensive docstrings
- Request/response examples
- Error handling documentation

## Frontend Development

### Template Structure
```html
<!-- discovery/templates/discovery/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>BACnet Django</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    {% block content %}{% endblock %}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
```

### JavaScript Guidelines
- Use modern ES6+ syntax
- Implement proper error handling
- Follow async/await patterns
- Include comprehensive comments

```javascript
// Static file: discovery/static/discovery/js/energy-dashboard.js
async function loadEnergyData() {
    try {
        const response = await fetch('/api/energy-dashboard/');
        const data = await response.json();

        if (data.success) {
            updateDashboard(data.data);
        } else {
            showError('Failed to load energy data');
        }
    } catch (error) {
        console.error('Energy data fetch error:', error);
        showError('Network error occurred');
    }
}
```

## Performance Optimization

### Database Optimization
```python
# Use select_related for foreign keys
devices = BACnetDevice.objects.select_related('vendor').filter(is_active=True)

# Use prefetch_related for reverse foreign keys
devices = BACnetDevice.objects.prefetch_related('points').all()

# Add database indexes
class Meta:
    indexes = [
        models.Index(fields=['read_time']),
        models.Index(fields=['is_anomaly', 'read_time']),
    ]
```

### Query Optimization
```python
# Efficient bulk operations
readings = [
    BACnetReading(point=point, value=value, read_time=timestamp)
    for point, value, timestamp in reading_data
]
BACnetReading.objects.bulk_create(readings, batch_size=1000)

# Use annotations for complex queries
from django.db.models import Count, Avg
devices_with_stats = BACnetDevice.objects.annotate(
    point_count=Count('points'),
    avg_temperature=Avg('points__readings__value')
)
```

### Caching Strategy
```python
from django.core.cache import cache

def get_device_status(device_id):
    cache_key = f'device_status_{device_id}'
    status = cache.get(cache_key)

    if status is None:
        status = calculate_device_status(device_id)
        cache.set(cache_key, status, timeout=300)  # 5 minutes

    return status
```

## Deployment and Production

### Production Settings
```python
# bacnet_project/settings_production.py
import os
from .settings import *

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Database configuration
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

### Docker Production
```dockerfile
# Dockerfile.production
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "bacnet_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Contributing Guidelines

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Follow code standards**: Type hints, docstrings, tests
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Run quality checks**: flake8, black, mypy
6. **Submit pull request** with clear description

### Commit Message Format
```
feat: add new energy forecasting algorithm

- Implement LSTM neural network for seasonal forecasting
- Add configuration options for model parameters
- Include comprehensive tests and documentation
- Update API documentation with new endpoints

Fixes #123
```

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] All functions have type hints and docstrings
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

### Release Process

1. **Version bump**: Update version in `__init__.py`
2. **Update changelog**: Document new features and fixes
3. **Create release tag**: `git tag -a v2.4.0 -m "Version 2.4.0"`
4. **Deploy to staging**: Test in staging environment
5. **Deploy to production**: Use blue-green deployment
6. **Monitor metrics**: Check for issues post-deployment

## Debugging and Troubleshooting

### Debug Settings
```python
# Enable debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'discovery': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Common Debug Techniques
```python
# Use Django shell for debugging
python manage.py shell
>>> from discovery.services import BACnetService
>>> service = BACnetService()
>>> devices = service.discover_devices()

# Enable SQL query logging
from django.db import connection
print(connection.queries)

# Use Django debug toolbar
pip install django-debug-toolbar
# Add to INSTALLED_APPS and MIDDLEWARE
```

### Profiling Performance
```python
# Profile view performance
from django.test.utils import override_settings
from django.core.management import execute_from_command_line
import cProfile

def profile_view():
    with override_settings(DEBUG=True):
        pr = cProfile.Profile()
        pr.enable()

        # Execute code to profile
        result = some_expensive_operation()

        pr.disable()
        pr.print_stats(sort='cumulative')

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function implementation
    pass
```

## Security Considerations

### Input Validation
```python
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError

def validate_device_address(address):
    try:
        validate_ipv4_address(address)
    except ValidationError:
        raise ValidationError('Invalid IP address format')
```

### SQL Injection Prevention
```python
# Always use parameterized queries
from django.db import connection

def safe_query(device_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM discovery_bacnetreading WHERE device_id = %s",
            [device_id]
        )
        return cursor.fetchall()
```

### Authentication and Authorization
```python
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated

@login_required
def protected_view(request):
    # View implementation
    pass

class ProtectedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # API implementation
        pass
```

## Future Development

### Planned Enhancements

1. **Advanced ML Features**
   - LSTM neural networks for time series forecasting
   - Isolation Forest for multivariate anomaly detection
   - Automated hyperparameter tuning

2. **Real-time Features**
   - WebSocket integration for live updates
   - Real-time alerting system
   - Streaming data processing

3. **Scalability Improvements**
   - Horizontal scaling with load balancers
   - Database sharding for large datasets
   - Microservices architecture

4. **Integration Capabilities**
   - REST API for third-party integrations
   - Webhook support for external notifications
   - MQTT broker integration

### Technical Debt
- Migrate legacy function-based views to class-based views
- Implement comprehensive caching strategy
- Add comprehensive integration tests
- Improve error handling and recovery mechanisms
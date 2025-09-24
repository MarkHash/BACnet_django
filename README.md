# BACnet Django Discovery Application

A Django web application for discovering, monitoring, and reading BACnet devices on your network. This application provides a user-friendly web interface for BACnet device discovery and real-time sensor data monitoring with optimized batch reading and PostgreSQL data persistence.

## Features

- **Automatic Device Discovery**: Broadcast WhoIs requests to discover BACnet devices
- **Point Discovery**: Read and catalog all BACnet objects from discovered devices
- **Optimized Batch Reading**: High-performance chunked batch reading with 3.7x speedup
- **Real-time Monitoring**: Read current sensor values from analog/binary points
- **Web Dashboard**: Clean, responsive interface for device management
- **PostgreSQL Database**: Robust data persistence with proper indexing
- **Custom Exception Handling**: Professional error management and logging
- **Unit Conversions**: Automatic conversion of engineering units to display format
- **Admin Interface**: Django admin for advanced data management
- **Management Commands**: Database cleanup and maintenance utilities

## Screenshots

### Dashboard
- Overview of all discovered devices
- Device status indicators (online/offline)
- Quick statistics (total devices, points, etc.)
- Discovery controls

### Device Details
- Detailed view of individual devices
- Real-time sensor readings with automatic refresh
- Point lists organized by object type
- Bulk sensor value reading

## Requirements

- Python 3.12+
- Django 5.2+
- PostgreSQL 12+
- BAC0 library (23.07.03+)
- Bootstrap 5.1.3 (loaded via CDN)

## Platform Support

This application now supports **cross-platform deployment** with automatic OS detection:

- **Linux/Mac**: Full Docker containerization with host networking
- **Windows**: Hybrid architecture with native BACnet networking

### Windows Support Features
- ✅ **Automatic platform detection** - no manual configuration needed
- ✅ **Native Windows networking** - accesses real Windows network (192.168.1.x)
- ✅ **Hybrid architecture** - Database/Redis in containers, BACnet discovery native
- ✅ **Zero changes to Linux/Mac workflow** - existing deployments unchanged

## Installation

### Linux/Mac Installation (Docker)

### 1. Clone the repository
```bash
git clone <repository-url>
cd BACnet_django
```

### 2. Start with Docker Compose
```bash
docker-compose up -d
```

That's it! The application will be available at http://localhost:8000

### Windows Installation (Hybrid)

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
# Or manually:
pip install django psycopg2-binary BAC0 celery redis python-dotenv
```

### 4. PostgreSQL Setup & Environment Variables

**Create database and user (choose your own credentials):**
```sql
-- Connect to PostgreSQL as superuser (psql -U postgres)
CREATE DATABASE bacnet_django;
CREATE USER your_chosen_username WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE bacnet_django TO your_chosen_username;
```

**Or using command line:**
```bash
# Create database
createdb -U postgres bacnet_django

# Create user with your chosen credentials
psql -U postgres -c "CREATE USER your_chosen_username WITH PASSWORD 'your_secure_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE bacnet_django TO your_chosen_username;"
```

**Create `.env` file with your credentials:**
```bash
# .env (customize these values with your chosen credentials)
DB_NAME=bacnet_django
DB_USER=your_chosen_username
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=True
```

**Database configuration (uses environment variables):**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

**Security benefits:**
- ✅ No passwords in version control
- ✅ Each developer can use their own credentials
- ✅ Different credentials for dev/staging/production
- ✅ Easy credential rotation

### 5. Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create superuser (optional)
```bash
python manage.py createsuperuser
```

### 4. Start infrastructure services (Windows-specific Docker Compose)
```bash
docker-compose -f docker-compose.windows.yml up -d
```

### 5. Start Django development server
```bash
python manage.py runserver
```

The application automatically detects Windows and enables native BACnet networking.

### 6. Access the application
- Web Interface: http://localhost:8000/
- Admin Interface: http://localhost:8000/admin/

## How the Hybrid Architecture Works (Windows)

### What Runs Where:
```
┌─────────────────────────────────────────┐
│               Windows Host              │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │     Django (python manage.py)      ││  ← Native Windows
│  │  - Web interface                   ││  ← ALL BACnet operations
│  │  - Device discovery                ││  ← Direct network access
│  │  - Point reading                   ││  ← Real Windows network
│  │  - All BACnet functions            ││  ← (192.168.1.x)
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │          Docker Containers          ││
│  │  ┌─────────────────────────────────┐││
│  │  │ PostgreSQL Database (port 5432) │││  ← Containerized
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │ Redis Cache (port 6379)         │││  ← Containerized
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │ Celery Workers                  │││  ← Containerized
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### Why This Works:
- **Django connects to `localhost:5432`** → Docker forwards to PostgreSQL container
- **Django connects to `localhost:6379`** → Docker forwards to Redis container
- **All BACnet operations run in Django** → Direct Windows network access (192.168.1.x)
- **Web interface calls BACnetService directly** → No additional workers needed
- **Best of both worlds**: Reliable containerized services + native Windows networking

## Configuration

### BAC0 Configuration

The application uses BAC0 for BACnet communication with automatic network detection. Key configuration options:

- **Automatic IP Detection**: BAC0 automatically detects network interface
- **Default Port**: UDP 47808 (BACnet standard)
- **Network Timeout**: 10 seconds for device discovery
- **Batch Size**: Maximum 50 points per batch read for optimal performance

### Django Settings

Key settings in `bacnet_project/settings.py`:

- **TIME_ZONE**: Set to your local timezone
- **DEBUG**: Set to False in production
- **ALLOWED_HOSTS**: Add your domain/IP for production
- **DATABASE**: PostgreSQL configuration with connection pooling

### Performance Settings

```python
# Optimized settings for BACnet operations
BACNET_CONSTANTS = {
    'MAX_BATCH_SIZE': 50,
    'REFRESH_THRESHOLD_SECONDS': 300,
    'MAX_READING_LIMIT': 50,
}
```

## Usage

### Discovering Devices

1. Navigate to the dashboard
2. Click "Start Discovery" to send WhoIs broadcasts
3. Discovered devices will appear in the devices list
4. Device status indicators show online/offline state

### Reading Device Points

1. Click device ID to view device details
2. If points haven't been discovered, click "🔍 Discover Points"
3. The application will discover all BACnet objects on the device
4. Points are organized by object type (analogInput, binaryInput, etc.)

### Reading Sensor Values

1. In device details, click "🌡️ Read Sensor Values"
2. Application uses optimized batch reading for better performance
3. Current values display with units and timestamps
4. Values automatically refresh every 30 seconds

### Data Management

```bash
# Clean database for fresh start
python manage.py clean_db

# Use Django admin for advanced data management
# Export data using Django admin
```

## API Endpoints

The application provides REST API endpoints:

- `POST /api/start-discovery/` - Start device discovery
- `POST /api/discover-points/{device_id}/` - Discover device points
- `POST /api/read-values/{device_id}/` - Read all point values from device
- `POST /api/read-point/{device_id}/{object_type}/{instance}/` - Read single point
- `GET /api/device-values/{device_id}/` - Get current device values
- `POST /api/clear-devices/` - Clear all devices

## Database Models

### BACnetDevice
- Device ID, IP address, vendor information
- Online status and timestamps
- Point reading status
- Soft delete with `is_active` field

### BACnetPoint
- Object type, instance number, identifier
- Present value, units, object name
- Data type and readability flags
- Foreign key to device

### BACnetReading
- Historical sensor readings
- Timestamps and quality indicators
- Linked to specific points

### DeviceStatusHistory
- Device online/offline history
- Status change timestamps

## Architecture

### Components

1. **Django Views** (`discovery/views.py`)
   - Web interface and API endpoints
   - Device and point management
   - Error handling with custom exceptions

2. **BACnet Service** (`discovery/services.py`)
   - BAC0 integration with context managers
   - Optimized batch reading with chunking
   - Professional error handling
   - Connection lifecycle management

3. **Models** (`discovery/models.py`)
   - PostgreSQL-optimized database schema
   - Data validation and relationships
   - Soft delete patterns

4. **Constants** (`discovery/constants.py`)
   - BACnet property names
   - Readable object types
   - Unit conversion mappings

5. **Custom Exceptions** (`discovery/exceptions.py`)
   - Structured error hierarchy
   - BACnet-specific error types

6. **Templates** (`discovery/templates/`)
   - Responsive web interface
   - Bootstrap-based design
   - Real-time updates via JavaScript

### BACnet Communication

- Uses BAC0 library (Lite mode) for BACnet protocol support
- Supports BACnet/IP over Ethernet
- Handles WhoIs/IAm for device discovery
- ReadProperty and ReadMultiple requests for data collection
- Context manager pattern for automatic connection management
- Chunked batch reading for large devices (161+ points)

### Performance Optimizations

- **Batch Reading**: ReadMultiple requests with up to 50 points per batch
- **Chunked Processing**: Large devices split into manageable chunks
- **Connection Pooling**: Efficient BAC0 connection management
- **Database Indexing**: Optimized PostgreSQL indexes
- **Error Recovery**: Graceful fallback to individual reads on batch failures

## Troubleshooting

### Platform-Specific Issues

#### Windows-Specific Issues

1. **"Windows detected but no BACnet devices found"**
   - Verify your Windows machine can reach BACnet devices:
     ```bash
     ping 192.168.1.5  # Replace with your BACnet device IP
     ```
   - Check Windows firewall settings for UDP port 47808
   - Ensure you're on the same subnet as BACnet devices

2. **"Double BACnet connection error"**
   - Fixed in current version with connection reuse
   - If you see this error, restart Django server

3. **Docker port conflicts**
   - Make sure you're using `docker-compose.windows.yml`
   - Don't run both `docker-compose.yml` and `docker-compose.windows.yml` simultaneously

#### Linux/Mac-Specific Issues

1. **Docker BACnet worker not finding devices**
   - Check host networking is working: `docker run --rm --net=host busybox ip addr`
   - Verify no firewall blocking UDP 47808

### Common Issues (All Platforms)

1. **No devices discovered**
   - Check network connectivity and subnet
   - Verify firewall settings for UDP port 47808
   - Ensure BACnet devices are accessible
   - **Windows**: Make sure Django is running natively (not in Docker)
   - **Linux/Mac**: Make sure Docker has host networking access

2. **PostgreSQL connection errors**
   - Verify your `.env` file exists and has correct credentials
   - Test connection with your credentials from `.env`:
     ```bash
     # Use your actual credentials from .env file
     psql -h localhost -U your_db_user -d bacnet_django
     ```
   - **Docker users**: Ensure containers are running: `docker-compose ps`
   - Check PostgreSQL service is running: `sudo systemctl status postgresql` (Linux)
   - Ensure database and user exist:
     ```sql
     # Connect as postgres user
     psql -U postgres
     \l  -- List databases (should show bacnet_django)
     \du -- List users (should show your user)
     ```
   - Verify `.env` file is loaded correctly:
     ```bash
     python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB_USER:', os.getenv('DB_USER'))"
     ```

3. **Platform detection issues**
   - Check the startup message:
     - Windows: "🪟 Windows detected: BACnet worker will run natively"
     - Linux/Mac: "🐧 Linux/Mac detected: Using Docker BACnet worker"
   - If incorrect, check `platform.system()` output:
     ```python
     import platform
     print(platform.system())  # Should be 'Windows', 'Linux', or 'Darwin'
     ```

4. **Point reading failures**
   - Some devices may have security restrictions
   - Check device documentation for supported properties
   - Verify device is online and responsive

5. **Performance issues**
   - Monitor batch read success in logs
   - Check network latency to devices
   - Consider adjusting MAX_BATCH_SIZE

### Debug Information

- Enable Django debug mode in settings.py
- Check application logs for BACnet communication
- Use Django admin to inspect database records
- Monitor performance with batch read statistics

### Logging

```python
# Key loggers to monitor:
- discovery.services    # BACnet operations
- discovery.views      # Web interface
- BAC0_Root            # BAC0 library (set to WARNING)
```

## Development

### Project Structure
```
BACnet_django/
├── bacnet_project/          # Django project settings
├── discovery/               # Main application
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   ├── management/         # Custom management commands
│   ├── models.py          # Database models
│   ├── views.py           # Web views and API
│   ├── services.py        # BACnet communication service
│   ├── constants.py       # BACnet constants and mappings
│   ├── exceptions.py      # Custom exception hierarchy
│   └── urls.py           # URL routing
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── .env                   # Environment variables (create from .env.example)
├── .env.example          # Environment variables template
└── README.md             # This file
```

### Management Commands

```bash
# Clean database for fresh start
python manage.py clean_db

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### Testing

```bash
# Run tests
python manage.py test

# Test with logging
python manage.py runserver 2>&1 | tee test_log.txt
```

### Adding Features

1. **New BACnet Properties**
   - Extend `services.py` to read additional properties
   - Update models to store new data
   - Add constants to `constants.py`

2. **Additional Device Types**
   - Update device discovery logic in `services.py`
   - Add support for new object types in constants
   - Extend admin interface

3. **Performance Monitoring**
   - Add metrics collection
   - Implement performance dashboards
   - Monitor batch read efficiency

## Production Deployment

### Database Configuration
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
}
```

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,your-ip-address
DB_NAME=bacnet_production
DB_USER=bacnet_user
DB_PASSWORD=secure-password
```

### Security Checklist
- Change SECRET_KEY in production
- Set DEBUG = False
- Configure proper ALLOWED_HOSTS
- Use environment variables for sensitive data
- Implement authentication for admin access
- Consider network segmentation for BACnet traffic
- Regular database backups

## Performance Metrics

Based on testing with real BACnet devices:

- **Device Discovery**: 3 devices discovered in ~9 seconds
- **Point Discovery**: 161+ points discovered in ~1.5 seconds
- **Batch Reading**: 3.7x faster than individual reads
  - Individual reads: 3.82s for 28 points
  - Batch reads: 1.03s for 28 points
- **Large Device Handling**: 161+ points read in ~4 batches
- **Database Performance**: PostgreSQL with optimized indexes

## Celery Integration

For parallel device processing (already configured):

```python
# Celery is already installed and configured in settings.py
# Current configuration uses PostgreSQL as broker and result backend:

CELERY_BROKER_URL = 'sqlalchemy+postgresql://bacnet_user:password@localhost:5432/bacnet_django'
CELERY_RESULT_BACKEND = 'db+postgresql://bacnet_user:password@localhost:5432/bacnet_django'

# Scheduled tasks configured:
CELERY_BEAT_SCHEDULE = {
    'calculate-hourly-stats': {
        'task': 'discovery.tasks.calculate_hourly_stats',
        'schedule': crontab(minute=0),  # Every hour
    },
    'calculate-daily-stats': {
        'task': 'discovery.tasks.calculate_daily_stats',
        'schedule': crontab(hour=0, minute=5),  # Daily at 00:05
    },
}
```

**To start Celery services:**
```bash
# Start Celery worker
celery -A bacnet_project worker --loglevel=info

# Start Celery beat (scheduler)
celery -A bacnet_project beat --loglevel=info
```

## License

[Add your license information here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues and questions:
- Create GitHub issues for bugs and feature requests
- Check logs for BACnet communication issues
- Review troubleshooting section for common problems

## Files Added for Windows Support

For reference, these are the minimal files added to enable Windows support:

### New Files
- `docker-compose.windows.yml` - Windows-specific Docker configuration (excludes web service)

### Modified Files
- `bacnet_project/settings.py` - Added OS auto-detection (5 lines at end)
- `discovery/services.py` - Fixed BACnet connection reuse in `__enter__` method

### How It Works
- **Web interface already calls BACnetService directly** - no additional workers needed
- **Django runs natively on Windows** - gets real network access (192.168.1.x)
- **Database/Redis run in containers** - reliable infrastructure services
- **Automatic platform detection** - no user configuration required

### Architecture Benefits
- **Zero risk**: Linux/Mac behavior unchanged
- **Minimal changes**: ~10 lines of code modifications
- **Simple**: No trigger files or background workers needed
- **Direct**: Web interface → BACnetService → Windows network
- **Maintainable**: Shared business logic across platforms

## Changelog

### Version 2.1 (Current) - Windows Support
- Added cross-platform support with automatic OS detection
- Implemented hybrid architecture for Windows (native BACnet + containerized services)
- Fixed BACnet connection reuse issues
- Zero changes to existing Linux/Mac functionality
- Created Windows-specific Docker Compose configuration

### Version 2.0
- Migrated from BACpypes to BAC0
- Implemented PostgreSQL database
- Added optimized batch reading
- Custom exception handling
- Context manager pattern
- Unit conversion system
- Performance improvements (3.7x faster)

### Version 1.0
- Initial release with BACpypes
- SQLite database
- Basic device discovery
- Individual point reading
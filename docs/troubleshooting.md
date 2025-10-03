# Troubleshooting Guide

This guide covers common issues and their solutions for the BACnet Django application.

## Platform-Specific Issues

### Windows-Specific Issues

#### 1. "Windows detected but no BACnet devices found"
**Symptoms**: Discovery runs but finds no devices

**Solutions**:
- Verify network connectivity to BACnet devices:
  ```bash
  ping 192.168.1.5  # Replace with your BACnet device IP
  ```
- Check Windows firewall settings for UDP port 47808
- Ensure you're on the same subnet as BACnet devices
- Verify BACnet devices are actually responding to WhoIs broadcasts

#### 2. PostgreSQL Database Conflicts
**Symptoms**: Windows service can't save data to Docker database

**Root Cause**: Local PostgreSQL service using port 5432 conflicts with Docker PostgreSQL

**Check for conflict**:
```bash
netstat -an | findstr ":5432"
# Should show only Docker connections, not local PostgreSQL
```

**Solution**: Stop local PostgreSQL service:
```bash
# As Administrator:
net stop postgresql-x64-15
# Or use Services Manager (services.msc)
```

**Verification**: Test database connection:
```bash
psql -h localhost -U bacnet_user -d bacnet_django -c "SELECT 1;"
```

#### 3. "Empty reply from server" or "localhost:8000 not working" ✅ FIXED
**Symptoms**: Browser shows empty response or connection refused

**Solution**: Use `127.0.0.1:8000` instead of `localhost:8000`
- **Root cause**: Windows resolves `localhost` to IPv6 (`::1`) but server binds to IPv4
- **All documentation updated**: Examples now use `127.0.0.1:8000`

#### 4. "net::ERR_EMPTY_RESPONSE" on API calls ✅ FIXED
**Symptoms**: API calls fail with empty responses

**Solutions**:
- Ensure Windows integrated server is running: `python windows_integrated_server.py`
- Use correct docker-compose file: `docker-compose -f docker-compose.windows.yml up -d`
- **Verification**: Test API with PowerShell:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/status/"
  ```

#### 5. DataQualityAPIView numpy errors ✅ FIXED
**Error**: `ufunc 'subtract' did not contain a loop with signature matching types`

**Solution**: Enhanced data filtering to handle mixed numeric/text BACnet readings
- **Now handles**: "inactive", "offline", and other status text values safely
- **Fixed in**: Version 2.3 with improved data type validation

### Linux/Mac-Specific Issues

#### 1. Docker BACnet worker not finding devices
**Symptoms**: Container runs but no devices discovered

**Solutions**:
- Check host networking is working:
  ```bash
  docker run --rm --net=host busybox ip addr
  ```
- Verify no firewall blocking UDP 47808:
  ```bash
  sudo ufw status  # Ubuntu
  sudo iptables -L  # Other Linux
  ```
- Test BACnet port accessibility:
  ```bash
  sudo netstat -ulnp | grep 47808
  ```

#### 2. Permission denied errors
**Symptoms**: Docker commands fail with permission errors

**Solutions**:
- Add user to docker group:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```
- Fix file permissions:
  ```bash
  sudo chown -R $USER:$USER /path/to/BACnet_django
  ```

## Common Issues (All Platforms)

### 1. No devices discovered

**Diagnostic steps**:
```bash
# Check network connectivity
ping 192.168.1.5  # Replace with known BACnet device IP

# Verify BACnet port is available
netstat -ulnp | grep 47808  # Linux/Mac
netstat -an | findstr ":47808"  # Windows

# Test manual discovery
python manage.py shell
>>> from discovery.services import BACnetService
>>> service = BACnetService()
>>> devices = service.discover_devices()
>>> print(f"Found {len(devices)} devices")
```

**Common solutions**:
- **Network issues**: Ensure same subnet as BACnet devices
- **Firewall**: Allow UDP port 47808 inbound/outbound
- **Device configuration**: Verify BACnet devices support WhoIs requests
- **Timing**: Some devices respond slowly - wait 30+ seconds

### 2. PostgreSQL connection errors

**Diagnostic commands**:
```bash
# Test database connection
psql -h localhost -U bacnet_user -d bacnet_django

# Check if PostgreSQL is running
docker-compose ps  # Docker users
sudo systemctl status postgresql  # Linux native
net start | findstr postgres  # Windows native
```

**Environment verification**:
```bash
# Verify .env file is loaded correctly
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB_USER:', os.getenv('DB_USER'))"
```

**Database setup verification**:
```sql
-- Connect as postgres user
psql -U postgres
\l  -- List databases (should show bacnet_django)
\du -- List users (should show your user)
```

### 3. Point reading failures

**Symptoms**: Devices discovered but point values can't be read

**Diagnostic steps**:
```python
# Test individual point reading
from discovery.models import BACnetDevice, BACnetPoint
device = BACnetDevice.objects.first()
points = device.points.all()[:5]  # Test first 5 points

from discovery.services import BACnetService
service = BACnetService()
for point in points:
    try:
        value = service.read_point_value(device, point)
        print(f"{point.identifier}: {value}")
    except Exception as e:
        print(f"{point.identifier}: ERROR - {e}")
```

**Common solutions**:
- **Security restrictions**: Some devices require authentication
- **Property support**: Not all devices support all BACnet properties
- **Network timeouts**: Increase timeout values in BAC0 configuration
- **Device limitations**: Some devices limit concurrent requests

### 4. Performance issues

**Symptoms**: Slow discovery, timeouts, high memory usage

**Diagnostic tools**:
```bash
# Monitor system resources
top  # Linux/Mac
taskmgr  # Windows

# Check database performance
python manage.py dbshell
\dt+  -- Show table sizes
SELECT COUNT(*) FROM discovery_bacnetreading;  -- Check reading count
```

**Performance solutions**:
- **Batch size tuning**: Adjust `MAX_BATCH_SIZE` in constants
- **Database optimization**: Run `VACUUM ANALYZE` on PostgreSQL
- **Memory management**: Restart services if memory usage high
- **Network optimization**: Check for packet loss or high latency

## API-Specific Issues

### 1. API endpoints returning errors

**Test API health**:
```bash
# Test basic endpoints
curl -v http://127.0.0.1:8000/api/v2/devices/status/
curl -v http://127.0.0.1:8000/api/docs/

# Windows PowerShell testing
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/status/" -Method GET
```

**Common API issues**:
- **CORS errors**: Check `ALLOWED_HOSTS` in settings
- **JSON parsing**: Verify response content-type is `application/json`
- **Rate limiting**: Check if rate limits are being exceeded
- **Authentication**: Some endpoints may require authentication in production

### 2. Data quality API issues

**Symptoms**: DataQualityAPIView returns errors or unexpected results

**Diagnostic checks**:
```python
# Check for mixed data types in readings
from discovery.models import BACnetReading
problematic_readings = BACnetReading.objects.filter(
    value__in=['inactive', 'offline', 'error', 'null']
)
print(f"Non-numeric readings: {problematic_readings.count()}")

# Test data quality calculation
from discovery.api_views import calculate_completeness_score
point = BACnetPoint.objects.first()
completeness = calculate_completeness_score(point, 288)  # Expected daily readings
print(f"Completeness: {completeness}")
```

## Energy Analytics Issues

### 1. No energy data available

**Symptoms**: Energy dashboard shows no data

**Diagnostic steps**:
```python
# Check for temperature sensors
from discovery.models import BACnetPoint
temp_sensors = BACnetPoint.objects.filter(units__icontains='degree')
print(f"Temperature sensors found: {temp_sensors.count()}")

# Check recent temperature readings
from discovery.models import BACnetReading
from django.utils import timezone
from datetime import timedelta

recent_readings = BACnetReading.objects.filter(
    point__in=temp_sensors,
    read_time__gte=timezone.now() - timedelta(hours=24)
).count()
print(f"Recent temperature readings: {recent_readings}")
```

**Solutions**:
- **Sensor identification**: Ensure temperature sensors have units containing "degree"
- **Data collection**: Verify sensors are being read regularly
- **Manual calculation**: Run energy analytics manually:
  ```python
  from discovery.energy_analytics import EnergyAnalyticsService
  service = EnergyAnalyticsService()
  metrics_created = service.calculate_daily_metrics()
  print(f"Metrics created: {metrics_created}")
  ```

### 2. Low efficiency scores

**Symptoms**: All devices show low efficiency scores

**Analysis**:
- **High variance**: Indicates HVAC instability
- **Large temperature deviations**: Away from 22°C comfort zone
- **Poor timing**: Peak demand during expensive hours (12:00-18:00)

**Solutions**:
- **HVAC tuning**: Adjust setpoints for better stability
- **Sensor placement**: Verify sensors are in representative locations
- **Threshold adjustment**: Customize comfort zone center if needed

## Anomaly Detection Issues

### 1. No anomalies detected

**Diagnostic checks**:
```python
# Verify anomaly detection is running
from discovery.models import BACnetReading
anomalies = BACnetReading.objects.filter(is_anomaly=True).count()
print(f"Total anomalies in database: {anomalies}")

# Check Z-score distribution
import statistics
recent_scores = BACnetReading.objects.filter(
    anomaly_score__isnull=False,
    read_time__gte=timezone.now() - timedelta(hours=24)
).values_list('anomaly_score', flat=True)

if recent_scores:
    print(f"Max Z-score: {max(recent_scores):.2f}")
    print(f"Avg Z-score: {statistics.mean(recent_scores):.2f}")
```

**Solutions**:
- **Threshold adjustment**: Lower Z-score threshold from 2.5 to 2.0
- **Data requirements**: Ensure sufficient historical data (5+ readings)
- **Manual testing**: Test anomaly detection with known outliers

### 2. Too many false positives

**Symptoms**: Every reading flagged as anomaly

**Solutions**:
- **Increase threshold**: Try Z-score threshold of 3.0 or higher
- **Data cleaning**: Remove sensors with consistently invalid readings
- **Sensor calibration**: Physical sensors may need adjustment

## Debug Tools and Commands

### System Health Check
```bash
# Check all services
docker-compose ps
python manage.py check
python manage.py check --deploy  # Production readiness

# Database health
python manage.py dbshell
SELECT version();  -- PostgreSQL version
\dt+  -- Table sizes
```

### Application Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test core functionality
from discovery.services import BACnetService
service = BACnetService()

# Test database connectivity
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    print("Database connection: OK")
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats  # Docker containers
htop          # System resources (Linux/Mac)

# Check logs
docker-compose logs web
docker-compose logs db
tail -f /var/log/django/debug.log  # If file logging enabled
```

## Getting Additional Help

### Log Analysis
- **Django logs**: Check console output or log files
- **PostgreSQL logs**: Usually in `/var/log/postgresql/`
- **Docker logs**: `docker-compose logs [service_name]`
- **BAC0 logs**: Look for BACnet communication errors

### Community Support
- **GitHub Issues**: Report bugs with detailed logs
- **Stack Overflow**: Tag questions with `bacnet`, `django`, `bac0`
- **BACnet Community**: Forums for protocol-specific questions

### Professional Support
- **System Integration**: For complex BACnet network issues
- **Performance Tuning**: For large-scale deployments
- **Custom Development**: For specialized features

## Emergency Procedures

### Quick Recovery
```bash
# Reset everything
docker-compose down
docker-compose up -d --build

# Clear database and restart
python manage.py clean_db
python manage.py migrate
python manage.py createsuperuser
```

### Data Backup
```bash
# Backup database
pg_dump -h localhost -U bacnet_user bacnet_django > backup.sql

# Restore database
psql -h localhost -U bacnet_user bacnet_django < backup.sql
```

### Rollback Strategy
```bash
# Revert to previous version
git checkout previous-working-commit
docker-compose down
docker-compose up -d --build
```
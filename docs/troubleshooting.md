# Troubleshooting Guide

This guide covers common issues and solutions for the simplified BACnet Django application.

## Common Issues

### 1. Device Discovery Issues

**Symptoms**: No devices found during discovery

**Possible Causes**:
- BACnet devices not on the same network
- Firewall blocking UDP port 47808
- BACnet devices configured with different port numbers

**Solutions**:
```bash
# Check network connectivity
ping [device_ip_address]

# Verify UDP port 47808 is accessible
nmap -sU -p 47808 [device_ip_address]

# Check firewall settings (Linux)
sudo ufw allow 47808/udp

# Check firewall settings (Windows)
# Add inbound rule for UDP port 47808 in Windows Firewall
```

### 2. Database Connection Issues

**Symptoms**: Database connection errors, migration failures

**Solutions**:
```bash
# Restart database service
docker-compose restart db

# Check database status
docker-compose ps

# Reset database if needed
docker-compose down
docker volume rm bacnet_django_postgres_data
docker-compose up -d

# Run migrations
python manage.py migrate
```

### 3. Point Reading Failures

**Symptoms**: Points discovered but values not reading

**Possible Causes**:
- Points not readable (write-only objects)
- Device communication timeout
- Invalid point identifiers

**Solutions**:
```python
# Check if points are readable
from discovery.models import BACnetPoint
readable_points = BACnetPoint.objects.filter(
    object_type__in=['analogInput', 'analogOutput', 'analogValue']
)

# Test single point reading
python manage.py shell
>>> from discovery.services import BACnetService
>>> service = BACnetService()
>>> # Test specific device communication
```

### 4. Docker Issues

**Symptoms**: Container startup failures, port conflicts

**Solutions**:
```bash
# Check container logs
docker-compose logs web
docker-compose logs db

# Check port availability
lsof -i :8000  # Web port
lsof -i :5432  # Database port

# Clean up Docker resources
docker-compose down
docker system prune -f
docker volume prune -f
```

### 5. Environment Configuration

**Symptoms**: Settings errors, missing environment variables

**Solutions**:
```bash
# Check .env file exists
ls -la .env

# Verify required variables
cat .env | grep -E "(SECRET_KEY|DB_|DEBUG)"

# Use example configuration
cp .env.example .env
# Edit .env with appropriate values
```

### 6. Permission Issues (Linux/Mac)

**Symptoms**: Permission denied errors with Docker

**Solutions**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again

# Fix file permissions
sudo chown -R $USER:$USER .
```

### 7. Windows-Specific Issues

**Symptoms**: BACnet communication failures on Windows

**Solutions**:
- Ensure Windows firewall allows UDP traffic on port 47808
- Check that no antivirus is blocking network connections
- Verify network adapter settings allow broadcast traffic

```powershell
# Check Windows firewall rules
Get-NetFirewallRule -DisplayName "*BACnet*"

# Add firewall rule if needed
New-NetFirewallRule -DisplayName "BACnet UDP" -Direction Inbound -Protocol UDP -LocalPort 47808 -Action Allow
```

## Performance Issues

### 1. Slow Device Discovery

**Solutions**:
- Reduce discovery timeout in services.py
- Use manual device creation for known devices
- Limit discovery to specific IP ranges

### 2. Database Performance

**Solutions**:
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('bacnet_django'));

-- Clean old readings (older than 30 days)
DELETE FROM discovery_bacnetreading
WHERE read_time < NOW() - INTERVAL '30 days';

-- Rebuild indexes
REINDEX DATABASE bacnet_django;
```

## Debugging Commands

### Check System Status
```bash
# View active devices
python manage.py shell
>>> from discovery.models import BACnetDevice
>>> BACnetDevice.objects.filter(is_active=True).count()

# Check recent readings
>>> from discovery.models import BACnetReading
>>> BACnetReading.objects.filter(
...     read_time__gte=timezone.now() - timedelta(hours=1)
... ).count()
```

### Test BACnet Communication
```bash
# Test device discovery
python manage.py discover_devices --mock

# Test reading collection
python manage.py collect_readings

# Clean database
python manage.py clean_db
```

### Check Dependencies
```bash
# Verify Python packages
pip list | grep -E "(Django|BAC0|psycopg2)"

# Check Python version
python --version

# Verify Docker installation
docker --version
docker-compose --version
```

## Log Analysis

### Application Logs
```bash
# View Django logs
docker-compose logs web

# View database logs
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f web
```

### Django Debug Mode
```python
# In settings.py or .env
DEBUG = True

# Check for detailed error pages in browser
# View Django debug toolbar for SQL queries
```

## Network Debugging

### BACnet Network Issues
```bash
# Check network interface
ip addr show  # Linux
ipconfig      # Windows

# Test UDP broadcast
# Install netcat (nc) tool
echo "test" | nc -u -b 255.255.255.255 47808

# Monitor network traffic
sudo tcpdump -i any port 47808  # Linux
# Use Wireshark on Windows
```

### Connectivity Tests
```bash
# Test specific device connectivity
python manage.py shell
>>> from discovery.services import BACnetService
>>> service = BACnetService()
>>> # Manual device communication test
```

## Getting Help

### Error Reporting
When reporting issues, include:
1. **Error message**: Full error text and stack trace
2. **Environment**: OS, Python version, Docker version
3. **Configuration**: .env settings (without sensitive data)
4. **Logs**: Relevant log output from docker-compose logs
5. **Steps**: What you were trying to do when the error occurred

### Debug Information Collection
```bash
# Collect system information
python --version
docker --version
docker-compose --version

# Collect application status
docker-compose ps
docker-compose logs --tail=50 web

# Check database status
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "\dt"
```

### Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| No devices found | Check network/firewall settings |
| Database errors | Restart database container |
| Port conflicts | Change ports in docker-compose.yml |
| Permission denied | Fix Docker permissions |
| Slow performance | Clean old database records |
| Reading failures | Verify point readability |

For additional support, check the main project documentation and ensure you're using the simplified version appropriate for your deployment needs.
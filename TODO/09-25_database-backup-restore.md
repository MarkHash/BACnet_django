# Database Backup and Restore Commands

## Quick Backup Commands

### Create Timestamped Backup (Recommended)
```bash
docker-compose exec -T db pg_dump -U bacnet_user -d bacnet_django > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Create Named Backup
```bash
docker-compose exec -T db pg_dump -U bacnet_user -d bacnet_django > bacnet_backup.sql
```

### Windows PowerShell Version (with timestamp)
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker-compose exec -T db pg_dump -U bacnet_user -d bacnet_django > "backup_$timestamp.sql"
```

## Restore Commands

### Restore from Backup File
```bash
docker-compose exec -T db psql -U bacnet_user -d bacnet_django < backup_filename.sql
```

### Restore with Drop/Create (Clean Restore)
```bash
# Drop and recreate database first
docker-compose exec db psql -U bacnet_user -c "DROP DATABASE bacnet_django;"
docker-compose exec db psql -U bacnet_user -c "CREATE DATABASE bacnet_django;"

# Then restore
docker-compose exec -T db psql -U bacnet_user -d bacnet_django < backup_filename.sql
```

## Database Inspection Commands

### Check Current Database Content
```bash
# List all tables
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "\dt"

# Count devices
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT COUNT(*) FROM discovery_bacnetdevice;"

# Count readings
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT COUNT(*) FROM discovery_bacnetreading;"

# Count points
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT COUNT(*) FROM discovery_bacnetpoint;"

# Show recent readings
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT * FROM discovery_bacnetreading ORDER BY read_time DESC LIMIT 10;"
```

### Database Size Information
```bash
# Database size
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT pg_size_pretty(pg_database_size('bacnet_django'));"

# Table sizes
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Backup Best Practices

### Before Major Changes
```bash
# Always backup before:
# - Database migrations
# - Schema changes
# - Major data imports
# - System updates

docker-compose exec -T db pg_dump -U bacnet_user -d bacnet_django > "before_migration_$(date +%Y%m%d_%H%M%S).sql"
```

### Regular Automated Backup
```bash
# Add to cron or scheduled task
#!/bin/bash
cd /path/to/BACnet_django
docker-compose exec -T db pg_dump -U bacnet_user -d bacnet_django > "daily_backup_$(date +%Y%m%d).sql"

# Keep only last 7 days
find . -name "daily_backup_*.sql" -mtime +7 -delete
```

## Troubleshooting

### If Backup Fails
```bash
# Check database connection
docker-compose exec db psql -U bacnet_user -d bacnet_django -c "SELECT version();"

# Check database status
docker-compose logs db --tail=20

# Restart database if needed
docker-compose restart db
```

### If Restore Fails
```bash
# Check backup file integrity
head -10 backup_filename.sql
tail -10 backup_filename.sql

# Restore with verbose output
docker-compose exec -T db psql -U bacnet_user -d bacnet_django -v ON_ERROR_STOP=1 < backup_filename.sql
```

## Environment Variables Used
- `DB_USER`: bacnet_user
- `DB_NAME`: bacnet_django
- `DB_PASSWORD`: password (from .env file)
- `DB_HOST`: localhost (for host connections) / db (for container connections)
- `DB_PORT`: 5432

## Notes
- Use `-T` flag with `docker-compose exec` to disable TTY allocation for file redirection
- Backup files are created in the current directory
- Always test restore process with a copy of your backup
- Consider compressing large backup files: `gzip backup_filename.sql`
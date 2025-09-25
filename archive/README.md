# Archive

This folder contains legacy code and backup files that have been moved from the active codebase.

## discovery/
- **bacnet_client.py** - Legacy custom BACnet client implementation, replaced by services.py using BAC0 library
- **tests/test_bacnet_client.py** - Tests for the legacy BACnet client

## backups/
- **backup.sql** - PostgreSQL database backup (524KB)
- **bacnet_backup.sql** - Partial BACnet data backup (113KB)
- **db.sqlite3*** - SQLite database files used during development
- **backup_20250924_152656.sql** - Empty backup file

## scripts/
Development and debugging scripts moved from root directory:
- **test_bac0.py** - Service layer testing with mock mode
- **test_bac0_batch.py** - BAC0 library batch reading experiments
- **test_celery_tasks.py** - Celery task testing and validation
- **test_performance.py** - Performance comparison (individual vs batch reads)
- **test_historical_data.py** - Historical data and statistics testing
- **test_network.py** - Windows networking socket binding tests
- **debug_task_logic.py** - Deep debugging for statistical task logic
- **create_fresh_test_data.py** - Test data generator with anomaly detection

## Configuration Files
- **docker-compose.yml.backup** - Backup of Docker compose configuration
- **docker-compose.override.yml** - Redundant override file (settings already in main compose files)
- **pytest.ini** - Pytest configuration for legacy test structure
- **requirements-dev.txt** - Legacy dev requirements (consolidated into main requirements.txt)
- **requirements-test.txt** - Legacy test requirements (consolidated into main requirements.txt)

## Archived on
2025-09-25 - Moved during codebase cleanup as part of services layer refactor
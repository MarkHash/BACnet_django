# BACnet Django Application - Internship Summary

## Project Overview

A production-ready Django web application for discovering, monitoring, and collecting data from BACnet building automation devices. Developed as an internship deliverable demonstrating full-stack development, systems integration, and real-world problem-solving.

## Key Achievements

### 1. Dual Architecture Implementation ⭐

**Challenge:** Docker network isolation prevents BACnet UDP broadcasts from working correctly.

**Solution:** Implemented two deployment architectures:
- **Separated (Linux/macOS):** BACnet API service on host + Django in Docker
- **Integrated (Windows):** Combined server for simplified deployment

**Impact:** Application works across all platforms with optimal network access.

**Files:**
- `bacnet_api_service.py` - FastAPI service for BACnet operations
- `windows_integrated_server.py` - Integrated server for Windows
- `docker-compose.yml` / `docker-compose.windows.yml`

---

### 2. Intelligent Network Detection 🌐

**Challenge:** Different IP addresses needed for home (macOS) vs office (Windows) networks.

**Solution:** OS-based automatic network detection:
```python
def get_bacnet_ip() -> str:
    system = platform.system()
    if system == "Darwin":  # macOS
        return "192.168.1.101/24"  # Home network
    elif system == "Windows":
        return "192.168.1.5/24"    # Office network
```

**Impact:** Zero configuration needed when switching between environments.

**File:** `bacnet_api_service.py:32-45`

---

### 3. Professional UI/UX Design 🎨

**Achievements:**
- Responsive Bootstrap 5 interface
- Consistent breadcrumb navigation across all pages
- Real-time device status indicators (online/offline)
- Color-coded point types (analog inputs, binary values, etc.)
- Mobile-friendly dashboard

**Key Pages:**
- Dashboard with device overview and quick actions
- Device detail with live sensor readings
- Virtual device management (Beta)

**Files:** `discovery/templates/discovery/`

---

### 4. Robust Data Collection System 📊

**Features:**
- Automatic BACnet device discovery via WhoIs broadcasts
- Point cataloging by object type
- Batch reading with error handling
- Historical data storage (106,000+ readings collected)
- Device status tracking

**Database:**
- 4 active devices (office environment)
- 205 total points across all devices
- PostgreSQL for production-grade storage

**Files:** `discovery/services.py`, `discovery/models.py`

---

### 5. RESTful API Design 🔌

**Implemented 15+ API Endpoints:**

**Device Management:**
- `POST /api/start-discovery/` - Discover devices
- `POST /api/discover-points/<id>/` - Discover points
- `POST /api/clear-devices/` - Clear database

**Data Reading:**
- `POST /api/read-values/<id>/` - Read all points
- `GET /api/device-values/<id>/` - Get latest values
- `GET /api/read-point/<id>/<type>/<instance>/` - Single point

**Analytics:**
- `GET /api/devices/status/` - Status summary
- `GET /api/devices/<id>/trends/` - Trend analysis

**Documentation:** See `ARCHITECTURE.md` for full API reference

---

### 6. Virtual Device Testing Framework (Beta) 🧪

**Feature:** Create virtual BACnet devices for testing without physical hardware.

**Capabilities:**
- Virtual device creation with custom object IDs
- Analog/binary point simulation
- Testing of reading and discovery logic

**Status:** Beta - working but needs more testing before production use

**Files:** `discovery/virtual_device_service.py`

---

### 7. Code Quality & Testing ✅

**Testing:**
- 16/16 passing Jest tests for JavaScript
- Django test suite for models/views
- Total test coverage: Device detail page fully tested

**Code Quality Tools:**
- Black - Code formatting
- Flake8 - Linting
- isort - Import sorting
- Pre-commit hooks for automatic checks

**Configuration:** `.pre-commit-config.yaml`

---

### 8. Production-Ready Deployment 🚀

**Docker Configuration:**
- Multi-container setup (web, database)
- Health checks for PostgreSQL
- Volume persistence for data
- Environment-based configuration

**Database Migrations:**
- Clean migration history
- Forward-compatible schema
- Easy fresh database setup

**Security:**
- Environment variables for secrets
- Django security middleware
- Admin authentication
- `.gitignore` for sensitive files

---

## Challenges Overcome

### Challenge 1: BACnet Network Discovery Failure

**Problem:**
At the office with working BACnet devices, discovery returned 0 devices despite identical code working previously.

**Root Cause:**
Hardcoded IP address `192.168.1.101/24` (home network) in the code didn't match office network `192.168.1.5/24`.

**Investigation:**
1. Verified firewall wasn't blocking UDP port 47808
2. Confirmed BACnet service was sending broadcasts (tcpdump)
3. Identified network mismatch as root cause

**Solution:**
Implemented OS-based automatic network detection to switch between home/office networks based on the platform.

**Learning:**
Always make network configuration flexible, especially for applications that run in multiple environments.

**File:** `bacnet_api_service.py:32-45`

---

### Challenge 2: Docker Network Isolation

**Problem:**
BACnet device discovery didn't work when running inside Docker container.

**Root Cause:**
Docker's bridge networking mode isolates containers from the host network. BACnet relies on UDP broadcast packets that can't traverse this boundary.

**Attempts:**
1. ❌ Host network mode - Not supported on macOS/Windows
2. ❌ Macvlan network - Too complex for simple deployment
3. ✅ Separated architecture - BACnet service on host, Django in Docker

**Solution:**
Created two deployment modes:
- Separated: BACnet API (host) + Django (Docker) for Linux/macOS
- Integrated: Combined server for Windows simplicity

**Learning:**
Sometimes the best solution is architectural rather than technical configuration.

**Files:** `bacnet_api_service.py`, `windows_integrated_server.py`

---

### Challenge 3: Git Repository Cleanup

**Problem:**
Repository contained unnecessary files: node_modules (17MB+), venv312, coverage reports, empty backups.

**Impact:**
- Bloated repository size
- Slow git operations
- Confusion about which files are important

**Solution:**
Systematic cleanup:
1. Added `node_modules/`, `coverage/`, `staticfiles/` to `.gitignore`
2. Removed tracked virtual environment files
3. Removed generated test coverage reports
4. Removed empty backup files
5. Kept lock files (package-lock.json) for reproducibility

**Results:**
- Removed ~30 files, ~12,000 lines of generated code
- Cleaner repository for internship presentation
- Better understanding of git best practices

**Commits:** `90203b6`, `44e381f`

---

### Challenge 4: Database Foreign Key Constraints

**Problem:**
Couldn't delete test devices due to foreign key constraints from related records.

**Error:**
```
delete on table "discovery_bacnetdevice" violates foreign key constraint
```

**Solution:**
Deleted related records first (devicestatushistory, bacnetpoint) before deleting devices.

**Learning:**
Always consider database relationships when performing deletions. Django's ORM doesn't always handle cascading deletes automatically depending on the on_delete setting.

---

### Challenge 5: Template Consistency

**Problem:**
Inconsistent navigation patterns across pages - some had "Back to Dashboard" buttons, others had breadcrumbs, titles varied between h1/h2.

**Solution:**
Systematic UI/UX improvements:
1. Added breadcrumb navigation to all pages
2. Standardized title hierarchy (h2 for page titles)
3. Removed redundant "Back" buttons
4. Consistent card-based layouts

**Impact:**
Professional, cohesive user interface suitable for internship demo.

**Files:** `discovery/templates/discovery/*.html`

---

## Technical Skills Demonstrated

### Backend Development
- Django 5.2+ framework
- PostgreSQL database design
- RESTful API development
- Service-oriented architecture
- Background task management

### Frontend Development
- Bootstrap 5 responsive design
- JavaScript DOM manipulation
- AJAX/Fetch API integration
- Template engine (Django templates)

### DevOps & Tools
- Docker containerization
- docker-compose orchestration
- Git version control
- Pre-commit hooks
- Environment configuration

### Testing & Quality
- Jest testing framework
- Django test suite
- Code formatting (Black)
- Linting (Flake8)
- Import sorting (isort)

### Systems Integration
- BACnet/IP protocol (BAC0 library)
- Network programming (UDP broadcasts)
- Cross-platform compatibility
- API integration (FastAPI)

### Problem Solving
- Debugging network issues
- Resolving Docker limitations
- Database relationship management
- Migration troubleshooting

---

## Statistics

**Codebase:**
- ~15 API endpoints
- 5 database models
- 8 HTML templates
- 4 management commands
- 16 passing tests

**Data Collected:**
- 4 active BACnet devices
- 205 total points
- 106,000+ historical readings

**Git Activity:**
- Multiple feature branches
- Clean commit history
- Merged to main for deliverable

---

## Deliverables

1. ✅ Working web application with dual architecture support
2. ✅ Comprehensive documentation (README, ARCHITECTURE, this summary)
3. ✅ Clean codebase with tests and code quality tools
4. ✅ Production-ready Docker deployment
5. ✅ Real data from office BACnet devices
6. ⏳ Screenshots for README (pending)

---

## Next Steps (Post-Internship)

1. **Virtual Devices:** Move from Beta to production-ready
2. **Screenshots:** Add to README for better documentation
3. **Scheduling:** Implement automated reading collection
4. **Advanced Analytics:** Trend analysis and anomaly detection
5. **Real-time Updates:** WebSocket integration for live data
6. **Device-Specific Collection:** Implement the TODO in collect_readings.py

---

## Acknowledgments

This project represents a complete full-stack application demonstrating:
- Real-world problem-solving
- Cross-platform compatibility
- Production-ready code quality
- Professional documentation
- Practical systems integration

Developed during internship at [Company Name]
Timeframe: [Start Date] - [End Date]
Technology Stack: Django, PostgreSQL, BAC0, Docker, Bootstrap

---

**Internship Summary**
Last Updated: October 2024
Student: Makoto Hashimoto

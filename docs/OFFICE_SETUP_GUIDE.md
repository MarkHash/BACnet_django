# Office Machine Setup Guide - Main Branch Migration

## Overview

This guide helps you migrate the office Windows machine from the old `feat/bacnet-api-service` branch to the new simplified `main` branch.

**Time Required:** ~15-20 minutes
**Difficulty:** Easy - just follow the steps in order

---

## Pre-Migration Checklist

- [ ] Office machine is running Windows
- [ ] Has BACnet devices on network (192.168.1.x)
- [ ] Currently on `feat/bacnet-api-service` branch
- [ ] Has PostgreSQL Docker container running

---

## Step-by-Step Migration

### Step 1: Backup Current Data (Optional but Recommended)

```bash
# If you want to keep your current data
docker-compose exec db pg_dump -U postgres bacnet_django > backup_$(date +%Y%m%d).sql
```

**Note:** The new main branch has a clean architecture, so you'll likely start fresh.

---

### Step 2: Stop All Running Services

```bash
# Stop any running Python servers
# Press Ctrl+C in any terminal running bacnet_api_service.py or Django

# Stop Docker containers
docker-compose down
```

**Verify everything stopped:**
```bash
docker ps  # Should show no running containers
```

---

### Step 3: Pull Latest Code from Remote

```bash
# Fetch all remote changes
git fetch origin

# Check current branch
git branch
# Should show: * feat/bacnet-api-service

# Stash any local changes (if any)
git stash

# Switch to main branch
git checkout main

# Pull latest main branch
git pull origin main
```

**Verify you're on main:**
```bash
git branch
# Should show: * main
```

---

### Step 4: Review What Changed

The main branch has a **simpler architecture** for Windows:

**Old (feat/bacnet-api-service):**
- Separated FastAPI service + Django app
- Two different servers to manage
- More complex setup

**New (main):**
- **Integrated server** for Windows: `windows_integrated_server.py`
- Single process handles both Django + BACnet
- Automatic network detection (192.168.1.5/24 for Windows)

---

### Step 5: Update Python Dependencies

```bash
# Activate your virtual environment
# (Assuming you have venv or conda environment)

# Install/update requirements
pip install -r requirements.txt
```

**Key new/updated packages:**
- No FastAPI needed for Windows integrated server
- BAC0 library updated if needed
- Django 5.2+

---

### Step 6: Start PostgreSQL Database

```bash
# Start database container (Windows-specific docker-compose)
docker-compose -f docker-compose.windows.yml up -d

# Verify database is running
docker-compose -f docker-compose.windows.yml ps
# Should show: bacnet_django-db-1 (healthy)
```

**Wait ~10 seconds** for PostgreSQL to fully initialize.

---

### Step 7: Setup Database (Fresh Start)

```bash
# Run migrations to create tables
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Username: bacnet_user
# Password: password
# Email: (can leave blank)
```

**Verify database:**
```bash
# Should connect without errors
python manage.py check --database default
```

---

### Step 8: Start the Integrated Server

```bash
# This is the NEW way for Windows - single command!
python windows_integrated_server.py
```

**Expected Output:**
```
🪟 Detected Windows - Using office network: 192.168.1.5/24
🌐 BACnet service initializing on 192.168.1.5/24...
✅ BACnet service started successfully
🚀 Starting Django server...
Starting development server at http://127.0.0.1:8000/
```

**Important:** Leave this terminal window open!

---

### Step 9: Access the Application

Open your browser and go to:

**Main Application:**
```
http://127.0.0.1:8000
```

**Django Admin:**
```
http://127.0.0.1:8000/admin/
Username: bacnet_user
Password: password
```

---

### Step 10: Test BACnet Discovery

1. **Go to Dashboard:** http://127.0.0.1:8000

2. **Click "Discover Devices"** button

3. **Expected Result:**
   - Should find your office BACnet devices
   - Previously worked with 4 devices on 192.168.1.x network

4. **If devices found:**
   - Click on a device to see details
   - Click "Discover Points" to catalog device points
   - Click "Read Values" to get current sensor readings

---

## Troubleshooting

### Issue 1: "No module named 'X'"

**Solution:**
```bash
pip install -r requirements.txt
```

---

### Issue 2: Database Connection Error

**Solution:**
```bash
# Check if Docker database is running
docker-compose -f docker-compose.windows.yml ps

# If not running, start it
docker-compose -f docker-compose.windows.yml up -d

# Check .env file exists with database credentials
cat .env
# Should have DATABASE_URL=...
```

---

### Issue 3: "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

### Issue 4: BACnet Discovery Finds 0 Devices

**Checklist:**
- [ ] Firewall allows UDP port 47808
- [ ] BACnet devices are powered on
- [ ] Office network is 192.168.1.x
- [ ] Windows machine IP is 192.168.1.5

**Test:**
```bash
# Check network interface
ipconfig
# Should show 192.168.1.5 (or similar)
```

**If different IP:**
Edit `bacnet_api_service.py` line 41:
```python
elif system == "Windows":
    ip = "192.168.1.5/24"  # Change to your actual IP
    return ip
```

---

## Key Differences from Old Branch

### What's REMOVED:
- ❌ Separate `bacnet_api_service.py` running on port 5001 (for Windows)
- ❌ FastAPI dependency for Windows
- ❌ Need to manage two separate servers
- ❌ HTTP API calls between services

### What's NEW:
- ✅ Single `windows_integrated_server.py`
- ✅ Automatic OS-based network detection
- ✅ Simplified one-command startup
- ✅ Better error messages
- ✅ Virtual device support (Beta)
- ✅ Professional UI improvements

### What's SAME:
- ✅ Same device discovery functionality
- ✅ Same point reading capabilities
- ✅ Same database structure
- ✅ Same admin interface
- ✅ Same API endpoints

---

## Quick Reference Commands

### Start Everything:
```bash
# Terminal 1: Start database
docker-compose -f docker-compose.windows.yml up -d

# Terminal 2: Start integrated server
python windows_integrated_server.py
```

### Stop Everything:
```bash
# Press Ctrl+C in server terminal
# Then stop database:
docker-compose -f docker-compose.windows.yml down
```

### Check Status:
```bash
# Check database
docker-compose -f docker-compose.windows.yml ps

# Check web server
# Open: http://127.0.0.1:8000
```

### Useful Management Commands:
```bash
# Discover all devices
python manage.py discover_devices

# Collect readings from all devices
python manage.py collect_readings

# Clean database (remove all data)
python manage.py clean_db
```

---

## File Structure (New Main Branch)

```
BACnet_django/
├── windows_integrated_server.py    # ⭐ NEW: Start this for Windows
├── bacnet_api_service.py           # For Linux/macOS separated mode
├── docker-compose.windows.yml      # Database only for Windows
├── docker-compose.yml              # Full stack for Linux/macOS
├── manage.py                       # Django management
├── discovery/                      # Main Django app
│   ├── models.py                  # Database models
│   ├── views.py                   # Web views
│   ├── services.py                # BACnet integration
│   └── templates/                 # HTML templates
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # System architecture
│   ├── INTERNSHIP_SUMMARY.md      # Project summary
│   └── OFFICE_SETUP_GUIDE.md      # This file!
└── requirements.txt               # Python dependencies
```

---

## Expected Results After Setup

### Dashboard Should Show:
- Device count (initially 0)
- "Discover Devices" button
- "Manage Virtual Devices" button (Beta)

### After Discovery:
- 4+ BACnet devices listed
- Device online/offline status
- Last seen timestamps

### Device Detail Page:
- Device information (ID, name, IP)
- Points organized by type
- "Read Values" functionality
- Real-time sensor readings

---

## Verification Checklist

After completing all steps, verify:

- [ ] `git branch` shows `* main`
- [ ] PostgreSQL container is running (healthy)
- [ ] `windows_integrated_server.py` starts without errors
- [ ] Can access http://127.0.0.1:8000
- [ ] Can login to admin at http://127.0.0.1:8000/admin/
- [ ] Device discovery finds office BACnet devices
- [ ] Can discover points on a device
- [ ] Can read values from device points

---

## Next Steps After Setup

1. **Test Discovery:** Verify all 4 office devices are found
2. **Discover Points:** Catalog all device points (205 total expected)
3. **Read Values:** Collect initial readings
4. **Schedule Collection:** Set up periodic reading collection
5. **Monitor:** Check device status over time

---

## Getting Help

**If something doesn't work:**

1. Check the troubleshooting section above
2. Review logs in the terminal
3. Check `docs/troubleshooting.md` for more help
4. Verify you're using `docker-compose.windows.yml` (not `docker-compose.yml`)

**Common Mistakes:**
- Using `python manage.py runserver` instead of `python windows_integrated_server.py`
- Using `docker-compose.yml` instead of `docker-compose.windows.yml`
- Forgetting to run migrations after fresh checkout

---

## Summary

**Old Way (feat/bacnet-api-service):**
```bash
docker-compose up -d
python bacnet_api_service.py  # Terminal 1
python manage.py runserver    # Terminal 2
```

**New Way (main branch):**
```bash
docker-compose -f docker-compose.windows.yml up -d
python windows_integrated_server.py  # That's it! ✨
```

---

**Office Setup Guide**
Last Updated: October 15, 2024
Branch: main
For: Windows Office Machine

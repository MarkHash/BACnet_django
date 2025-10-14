# BACnet Django Discovery Application - Simplified Core

## 🏢 **Company Internship Version - Essential BACnet Functionality**

A streamlined Django web application focused on core BACnet building automation functionality. This simplified version provides essential device discovery, data collection, and monitoring capabilities suitable for production deployment.

> **Note**: This is the **simplified company version** with core BACnet features only. For advanced ML and analytics, see the portfolio branch.

## 🎯 **Core Features**

### **🔍 BACnet Device Management**
- **Device Discovery**: Automatic BACnet device discovery via WhoIs broadcasts
- **Manual Device Creation**: Add devices manually with IP address and device ID
- **Real-time Monitoring**: Online/offline device status tracking
- **Point Discovery**: Automatic discovery and cataloging of device points

### **📊 Data Collection & Monitoring**
- **Real-time Reading**: Collect sensor values from BACnet points
- **Historical Data**: Store and track readings over time
- **Device Status History**: Monitor device connectivity and performance
- **Basic Dashboard**: Simple web interface for device management

## 📋 Quick Start

### Linux/Mac (Docker)
```bash
git clone <repository-url>
cd BACnet_django
docker-compose up -d
```
**Access**: http://127.0.0.1:8000

### Windows (Database only)
```bash
git clone <repository-url>
cd BACnet_django
docker-compose -f docker-compose.windows.yml up -d
python manage.py runserver
```
**Access**: http://127.0.0.1:8000

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[Installation Guide](docs/installation.md)** | Setup instructions for development |
| **[Troubleshooting](docs/troubleshooting.md)** | Common issues and solutions |
| **[Development](docs/development.md)** | Development workflow and testing |

## 🎯 Core Functionality

### Device Management
- Automatic BACnet device discovery via WhoIs broadcasts
- Manual device creation with IP address and device ID
- Real-time device status monitoring (online/offline)
- Point discovery and cataloging by object type
- Simple batch reading with error handling

### Data Collection
- Real-time sensor value collection from BACnet devices
- Historical data storage in PostgreSQL database
- Device status history tracking
- Basic reading management and monitoring

## 🏗️ Architecture

### Simple Code Organization
- **`models.py`**: Core database models (Device, Point, Reading, StatusHistory)
- **`views.py`**: HTML rendering and basic API endpoints
- **`api_views.py`**: REST API views for device status and trends
- **`services.py`**: BACnet communication with BAC0 integration
- **`forms.py`**: Django forms for manual device creation

### Deployment Options
- **Docker**: Containerized deployment with PostgreSQL
- **Local**: Direct Python development with local database

## 📊 API Overview

### Simple REST API
```bash
# Device status and basic analytics
GET /api/devices/status/
GET /api/devices/{device_id}/trends/

# Device management
POST /api/discover-devices/
POST /api/devices/{device_id}/read-points/
POST /api/devices/{device_id}/discover-points/

# Interactive documentation
GET /api/docs/
```

## 💻 Management Commands

### Useful Commands
```bash
# Discover BACnet devices on network
python manage.py discover_devices

# Collect readings from all devices
python manage.py collect_readings

# Clean database (remove all data)
python manage.py clean_db

# Create admin user
python manage.py createsuperuser
```

## 🛠️ Requirements

- **Python**: 3.12+
- **Django**: 5.2+
- **PostgreSQL**: 12+
- **BAC0**: 23.07.03+ (BACnet communication)
- **Libraries**: Django REST Framework, python-dotenv

## ✨ Features

- **Simple Setup**: Easy Docker deployment with minimal configuration
- **Core Functionality**: Focus on essential BACnet operations
- **Clean Code**: Well-organized Django application structure
- **Basic API**: RESTful endpoints for device management
- **Manual Creation**: Add devices manually when discovery isn't available
- **Status Monitoring**: Track device connectivity and performance

## 📝 Development

### Local Development
```bash
# Clone and setup
git clone <repository-url>
cd BACnet_django
pip install -r requirements.txt

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Code Quality
```bash
# Code formatting
black .

# Linting
flake8

# Type checking
mypy discovery/
```

## 🔗 Admin Access

- **URL**: http://127.0.0.1:8000/admin/
- **Username**: bacnet_user
- **Password**: password

## 🆘 Support

- **Documentation**: Check the docs/ directory for guides
- **Issues**: For bugs and feature requests
- **Development**: See development documentation for setup

---

**Simple BACnet Django Application for Building Automation**
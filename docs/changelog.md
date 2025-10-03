# Changelog

All notable changes to the BACnet Django Discovery Application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2024-10-03

### 🏗️ Enterprise Code Architecture & Energy Analytics

#### Added
- **Enterprise Code Organization**: Complete separation of concerns with dedicated `api_views.py` module
- **Energy Analytics Pipeline**: Advanced HVAC energy consumption analysis and forecasting
- **Interactive Energy Dashboard**: Real-time metrics with Chart.js visualizations and responsive design
- **ML Forecasting**: Linear regression forecasting for next-day energy consumption with confidence scoring
- **Efficiency Scoring**: HVAC efficiency analysis based on stability, comfort, and timing performance
- **Type Safety**: 100% type hints across all modules (`energy_analytics.py`, `ml_utils.py`, `views.py`)
- **Professional Documentation**: Comprehensive module docstrings and enterprise-level code organization

#### Changed
- **Separated API Views**: Moved 7 class-based APIViews from `views.py` to dedicated `api_views.py`
- **Refactored Methods**: Broke down large methods into focused, single-responsibility functions
- **Enhanced Exception Handling**: Custom exception hierarchy with graceful error recovery
- **Improved Code Quality**: Flake8 compliance with proper import organization and line length standards
- **Restructured Documentation**: Organized documentation into modular `docs/` directory with focused README

#### Technical Implementation
- **Energy Metrics Model**: New database table for storing daily energy analytics
- **Constants Integration**: Centralized energy calculation constants in `constants.py`
- **API Endpoints**: RESTful energy dashboard API with JSON data provisioning
- **Frontend Integration**: Modern API-first architecture with JavaScript data loading
- **Production Testing**: Verified with real September 2024 temperature data (200K+ readings)

## [2.3.0] - 2024-09-30

### 🤖 Anomaly Detection Integration

#### Added
- **Real-time Anomaly Detection**: Z-score based statistical anomaly detection for temperature sensors
- **Ensemble Detection**: Combined Z-score and IQR methods for robust anomaly identification
- **Intelligent Sensor Detection**: Automatic identification of temperature sensors by units (°C, °F)
- **Historical Analysis**: 24-hour rolling window for statistical baseline calculation
- **Database Integration**: Anomaly scores and flags stored with each reading
- **ML Utils Module**: Extensible framework for additional detection algorithms
- **API Endpoints**: Complete REST API suite for anomaly querying and statistics

#### Changed
- **Database Schema**: Added `anomaly_score` and `is_anomaly` fields to BACnetReading model
- **Data Filtering**: Enhanced filtering to handle mixed numeric/text BACnet readings safely
- **Service Integration**: Integrated anomaly detection into data collection pipeline

#### Fixed
- **Data Type Handling**: Resolved numpy errors with mixed data types in DataQualityAPIView
- **Invalid Data Filtering**: Automatic exclusion of status text like "inactive", "offline"

## [2.2.0] - 2024-09-15

### 🌐 Django REST Framework Integration

#### Added
- **Django REST Framework**: Professional class-based API views with comprehensive documentation
- **Serializers**: Data validation and documentation for all API responses
- **OpenAPI Documentation**: Auto-generated documentation with Swagger UI at `/api/docs/`
- **Modern v2 API Endpoints**: Professional API design with structured responses
- **Device Performance Analytics API**: Real-time device activity monitoring and performance metrics
- **Data Quality Monitoring API**: Comprehensive analysis with completeness, accuracy, freshness metrics
- **Rate Limiting**: API rate limiting for production deployment

#### Changed
- **API Architecture**: Maintained backward compatibility with legacy function-based endpoints
- **Response Format**: Standardized JSON responses with success/error states
- **Error Handling**: Enhanced error responses with detailed information

#### Enhanced
- **Query Parameters**: Flexible filtering and pagination for API endpoints
- **Documentation**: Interactive API documentation with real-time testing capabilities

## [2.1.0] - 2024-09-01

### 🖥️ Windows Support & Cross-Platform Architecture

#### Added
- **Windows Support**: Native BACnet networking for Windows with hybrid architecture
- **Cross-Platform Detection**: Automatic OS detection and appropriate deployment strategy
- **Windows Integrated Server**: Single-command deployment with `windows_integrated_server.py`
- **Docker Windows Configuration**: Windows-specific Docker Compose setup
- **Native Threading**: Background BACnet worker with native Windows network access

#### Changed
- **Platform Architecture**:
  - Linux/Mac: Full Docker containerization with host networking
  - Windows: Native BACnet networking + containerized database services
- **Connection Management**: Fixed BACnet connection reuse issues in services layer

#### Fixed
- **IPv4/IPv6 Issues**: Updated all documentation to use `127.0.0.1` instead of `localhost`
- **Network Conflicts**: Resolved Docker networking limitations on Windows
- **Database Connectivity**: Fixed PostgreSQL port conflicts with local services

## [2.0.0] - 2024-08-15

### 🚀 Major Architecture Overhaul

#### Added
- **BAC0 Integration**: Migrated from BACpypes to BAC0 for better performance and reliability
- **PostgreSQL Database**: Enterprise-grade database with proper indexing and relationships
- **Optimized Batch Reading**: High-performance chunked batch reading with 3.7x speedup
- **Context Manager Pattern**: Professional connection lifecycle management
- **Unit Conversion System**: Automatic conversion of engineering units to display format
- **Custom Exception Handling**: Professional error management and logging hierarchy

#### Changed
- **Database Backend**: Migrated from SQLite to PostgreSQL for production scalability
- **Reading Strategy**: Implemented intelligent batch vs individual reading selection
- **Performance**: Achieved 3.7x performance improvement (individual: 3.82s → batch: 1.03s for 28 points)

#### Enhanced
- **Error Recovery**: Graceful fallback to individual reads on batch failures
- **Data Persistence**: Robust data storage with proper relationships and constraints
- **Connection Management**: Automatic cleanup and resource management

## [1.0.0] - 2024-07-01

### 🎯 Initial Release

#### Added
- **BACnet Device Discovery**: Automatic device discovery using WhoIs broadcasts
- **Point Discovery**: Comprehensive BACnet object cataloging and management
- **Real-time Monitoring**: Live sensor value reading and display
- **Web Dashboard**: Clean, responsive interface for device management
- **SQLite Database**: Basic data persistence for development
- **Django Admin**: Administrative interface for data management
- **BACpypes Integration**: Initial BACnet protocol support

#### Features
- Device status monitoring (online/offline)
- Point lists organized by object type
- Individual point value reading
- Basic error handling and logging
- Bootstrap-based responsive design

---

## Version History Summary

| Version | Key Features | Performance | Architecture |
|---------|-------------|-------------|--------------|
| **2.4.0** | Enterprise Code + Energy Analytics | Production-ready | API Separation + ML Pipeline |
| **2.3.0** | Anomaly Detection + ML Utils | Real-time processing | Statistical Analysis |
| **2.2.0** | REST Framework + OpenAPI | Enhanced APIs | Professional API Design |
| **2.1.0** | Windows Support + Cross-Platform | Native networking | Hybrid Architecture |
| **2.0.0** | PostgreSQL + BAC0 + Batch Reading | 3.7x performance boost | Enterprise Database |
| **1.0.0** | Basic BACnet + Web Interface | Individual reads | SQLite + BACpypes |

## Migration Guides

### Upgrading from 2.3.x to 2.4.0

#### Code Changes
- Update imports if using moved API views:
  ```python
  # Old
  from discovery.views import DeviceStatusAPIView

  # New
  from discovery.api_views import DeviceStatusAPIView
  ```

#### New Features
- Access energy analytics at `/energy-dashboard/`
- API endpoint: `GET /api/energy-dashboard/`
- New documentation structure in `docs/` directory

### Upgrading from 2.2.x to 2.3.0

#### Database Migration
```bash
python manage.py migrate discovery
```

#### New Features
- Anomaly detection automatically enabled for temperature sensors
- API endpoints: `/api/v2/anomalies/`, `/api/v2/anomalies/stats/`

### Upgrading from 2.1.x to 2.2.0

#### New Dependencies
```bash
pip install djangorestframework drf-spectacular
```

#### New Features
- Modern API endpoints at `/api/v2/`
- Interactive documentation at `/api/docs/`

## Breaking Changes

### Version 2.4.0
- **None**: Fully backward compatible

### Version 2.3.0
- **Database Schema**: Added anomaly detection fields (handled by migrations)

### Version 2.2.0
- **API Responses**: Enhanced error response format (backward compatible)

### Version 2.1.0
- **URLs**: Documentation examples changed from `localhost` to `127.0.0.1` (Windows compatibility)

### Version 2.0.0
- **Database**: Migration from SQLite to PostgreSQL required
- **Dependencies**: BACpypes replaced with BAC0
- **Configuration**: New environment variables for PostgreSQL

## Deprecation Notices

### Version 2.4.0
- **None**: All features maintained for compatibility

### Version 2.3.0
- **Legacy anomaly detection**: Manual anomaly calculation methods deprecated in favor of automated system

### Version 2.2.0
- **Function-based APIs**: Legacy API endpoints maintained but new development should use DRF views

## Security Updates

### Version 2.4.0
- Enhanced input validation in energy analytics calculations
- Improved error handling to prevent information disclosure

### Version 2.3.0
- Secured anomaly detection to prevent data manipulation
- Enhanced data filtering for mixed content types

### Version 2.2.0
- Added rate limiting to prevent API abuse
- Enhanced error responses to prevent information leakage

### Version 2.1.0
- Fixed network binding issues that could expose services unintentionally
- Enhanced Docker security configuration

## Performance Improvements

### Version 2.4.0
- **Energy Analytics**: Optimized database queries for energy calculations
- **Dashboard Loading**: Improved frontend performance with efficient data loading
- **API Response Times**: Sub-second response times for most endpoints

### Version 2.3.0
- **Anomaly Detection**: Efficient statistical calculations with minimal performance impact
- **Database Queries**: Optimized queries for anomaly detection and statistics

### Version 2.2.0
- **API Performance**: Enhanced response times with optimized serializers
- **Query Optimization**: Improved database query efficiency for large datasets

### Version 2.1.0
- **Windows Performance**: Native networking provides better performance than Docker networking
- **Cross-Platform**: Optimized deployment for each platform's strengths

### Version 2.0.0
- **Batch Reading**: 3.7x performance improvement over individual reads
- **Database**: PostgreSQL provides significant performance gains over SQLite
- **Connection Management**: Reduced overhead with proper connection lifecycle
# BACnet Django Discovery Application

A production-ready Django web application for discovering, monitoring, and analyzing BACnet devices on your network. Features advanced energy analytics, anomaly detection, and enterprise-level code architecture.

## 🚀 Key Features

- **🔍 Device Discovery**: Automatic BACnet device discovery with real-time monitoring
- **📊 Energy Analytics**: HVAC energy consumption analysis with ML forecasting
- **🤖 Anomaly Detection**: Real-time statistical anomaly detection for temperature sensors
- **⚡ Performance Optimized**: 3.7x faster batch reading with PostgreSQL persistence
- **🌐 Modern REST API**: Enterprise-grade APIs with OpenAPI documentation
- **🖥️ Cross-Platform**: Supports Linux/Mac (Docker) and Windows (native networking)

## 📋 Quick Start

### Linux/Mac (Docker)
```bash
git clone <repository-url>
cd BACnet_django
docker-compose up -d
```
**Access**: http://127.0.0.1:8000

### Windows (Hybrid)
```bash
git clone <repository-url>
cd BACnet_django
docker-compose -f docker-compose.windows.yml up -d
python windows_integrated_server.py
```
**Access**: http://127.0.0.1:8000

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[Installation Guide](docs/installation.md)** | Detailed setup instructions for all platforms |
| **[API Documentation](docs/api-documentation.md)** | Complete REST API reference with examples |
| **[Energy Analytics](docs/energy-analytics.md)** | HVAC efficiency analysis and dashboard |
| **[Anomaly Detection](docs/anomaly-detection.md)** | Statistical anomaly detection system |
| **[Troubleshooting](docs/troubleshooting.md)** | Platform-specific issues and solutions |
| **[Development](docs/development.md)** | Architecture, testing, and contributing |
| **[Changelog](docs/changelog.md)** | Version history and feature timeline |

## 🎯 Core Functionality

### Device Management
- Automatic BACnet device discovery via WhoIs broadcasts
- Real-time device status monitoring (online/offline)
- Point discovery and cataloging by object type
- Optimized batch reading with error recovery

### Energy Analytics
- HVAC energy consumption estimation based on temperature deviation
- Efficiency scoring with stability, comfort, and timing analysis
- ML forecasting using linear regression with confidence intervals
- Interactive dashboard with Chart.js visualizations

### Data Quality & Monitoring
- Comprehensive data quality metrics (completeness, accuracy, freshness)
- Real-time anomaly detection using Z-score and IQR methods
- Performance analytics with device activity monitoring
- Historical trends analysis with flexible time periods

## 🏗️ Architecture

### Enterprise Code Organization
- **`views.py`**: HTML rendering and function-based API endpoints
- **`api_views.py`**: Class-based API views with comprehensive documentation
- **`energy_analytics.py`**: HVAC energy analysis and ML forecasting
- **`ml_utils.py`**: Anomaly detection algorithms and statistical analysis
- **`services.py`**: BACnet communication with BAC0 integration

### Platform-Specific Architecture
- **Linux/Mac**: Full Docker containerization with host networking
- **Windows**: Native BACnet networking + containerized database services

## 📊 API Overview

### Modern REST API (v2)
```bash
# Device status and performance
GET /api/v2/devices/status/
GET /api/v2/devices/performance/

# Energy analytics
GET /api/energy-dashboard/

# Anomaly detection
GET /api/v2/anomalies/
GET /api/v2/anomalies/stats/

# Interactive documentation
GET /api/docs/
```

## 🛠️ Requirements

- **Python**: 3.12+
- **Django**: 5.2+
- **PostgreSQL**: 12+
- **BAC0**: 23.07.03+ (BACnet communication)
- **Libraries**: DRF, numpy, pandas, scikit-learn

## 🔧 Production Features

- **Type Safety**: 100% type hints across all modules
- **Error Handling**: Custom exception hierarchy with graceful recovery
- **Code Quality**: Flake8 compliance with enterprise standards
- **Documentation**: Comprehensive docstrings and API documentation
- **Testing**: Production-tested with 200K+ real BACnet readings
- **Security**: Environment-based configuration with secure defaults

## 📈 Performance Metrics

- **Device Discovery**: ~3 devices in 9 seconds
- **Point Discovery**: 161+ points in 1.5 seconds
- **Batch Reading**: 3.7x faster than individual reads
- **Database**: Optimized PostgreSQL with proper indexing
- **API Response**: <1s for most endpoints

## 🆕 Version 2.4 Highlights

- **Enterprise Code Architecture**: Complete API separation and type safety
- **Energy Analytics Pipeline**: Advanced HVAC analysis with ML forecasting
- **Production Code Quality**: 100% type hints, comprehensive exception handling
- **Interactive Energy Dashboard**: Real-time metrics with Chart.js visualizations
- **Comprehensive Documentation**: Modular docs with focused README

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Make your changes with tests
4. Follow code quality standards (type hints, Flake8 compliance)
5. Update documentation as needed
6. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory for detailed guides
- **Issues**: Create GitHub issues for bugs and feature requests
- **Troubleshooting**: See [troubleshooting.md](docs/troubleshooting.md) for common problems

---

**Built with ❤️ for the BACnet community**
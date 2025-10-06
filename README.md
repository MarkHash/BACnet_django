# BACnet Django Discovery Application - Portfolio Showcase

## 🎨 **Portfolio Branch - Advanced ML & Enterprise Features**

A production-ready Django web application showcasing advanced machine learning, enterprise architecture, and comprehensive BACnet building automation capabilities. This branch demonstrates sophisticated technical skills including ensemble ML algorithms, energy analytics, and enterprise-level code quality.

> **Note**: This is the **portfolio/showcase version** featuring advanced ML and analytics. For the simplified company version, see other branches.

## 🏆 **Portfolio Highlights - Advanced Technical Skills**

### **🤖 Machine Learning & Data Science**
- **Ensemble Anomaly Detection**: Multi-method ML combining Z-score, IQR, and Isolation Forest
- **Multi-dimensional Analysis**: Temperature, time patterns, and rate-of-change features
- **Energy Analytics Pipeline**: HVAC efficiency analysis with ML forecasting
- **Statistical Analysis**: Production-ready statistical methods with confidence scoring

### **🏗️ Enterprise Architecture & Code Quality**
- **100% Type Safety**: Complete type annotations across all modules
- **API Separation**: Clean separation between HTML views and REST APIs
- **Custom Exception Hierarchy**: Production-quality error handling
- **Enterprise Documentation**: Comprehensive docstrings and architectural guides

### **🚀 Core BACnet Features**
- **🔍 Device Discovery**: Automatic BACnet device discovery with real-time monitoring
- **📊 Energy Analytics**: HVAC energy consumption analysis with ML forecasting
- **🤖 Enhanced Anomaly Detection**: Multi-method ensemble ML system with method transparency
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

### Enhanced Anomaly Detection & Monitoring
- **Multi-method ensemble ML system** combining Z-score, IQR, and Isolation Forest
- **Real-time anomaly detection** with confidence scoring and method transparency
- **Multi-dimensional analysis** using temperature, time patterns, and rate of change
- **Intelligent alerting** with contextual messages and severity classification
- **Production-ready integration** with AlarmHistory and detailed logging
- Comprehensive data quality metrics (completeness, accuracy, freshness)
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

# Enhanced anomaly detection
GET /api/v2/anomalies/
GET /api/v2/anomalies/stats/
GET /api/v2/anomalies/devices/{device_id}/

# Interactive documentation
GET /api/docs/
```

## 🤖 Enhanced Anomaly Detection System

### Multi-Method Ensemble Approach
The system combines three complementary detection methods for superior accuracy:

1. **Z-Score Analysis** (40% weight)
   - Fast statistical outlier detection using standard deviation
   - Excellent for detecting value-based anomalies
   - Works with minimal data (5+ readings)

2. **IQR Method** (30% weight)
   - Quartile-based detection resistant to extreme outliers
   - Robust performance with skewed data distributions
   - Complements Z-score for comprehensive coverage

3. **Isolation Forest** (30% weight)
   - **Multi-dimensional ML algorithm** analyzing:
     - Temperature value
     - Hour of day (daily patterns)
     - Rate of temperature change
   - Detects complex anomalies that single-dimension methods miss
   - Requires 20+ samples for reliable training

### Real-World Example
```python
# Normal reading
22.5°C at 2:00 PM → All methods agree: Normal ✅

# Complex anomaly that only ensemble catches
23.0°C at 3:00 AM with +15°C rate change
├─ Z-score: 0.5 (normal temperature value)
├─ IQR: 0.3 (normal quartile position)
├─ Isolation Forest: 0.9 (wrong time + extreme rate change)
└─ Ensemble: 0.6 → ANOMALY DETECTED! 🚨
```

### Production Integration
- **Real-time processing** during BACnet data collection
- **Intelligent alarm creation** with detailed method contributions
- **Severity classification**: Medium (<0.7) or High (≥0.7) ensemble scores
- **Transparency**: See which methods contributed to each detection

### Test the System
```bash
# Generate realistic test anomalies
docker-compose exec web python manage.py create_test_anomalies --count 10

# View results
http://127.0.0.1:8000/anomaly-dashboard/
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
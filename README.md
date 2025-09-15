# BACnet Django Discovery Application

A Django web application for discovering, monitoring, and reading BACnet devices on your network. This application provides a user-friendly web interface for BACnet device discovery and real-time sensor data monitoring.

## Features

- **Automatic Device Discovery**: Broadcast WhoIs requests to discover BACnet devices
- **Point Discovery**: Read and catalog all BACnet objects from discovered devices
- **Real-time Monitoring**: Read current sensor values from analog/binary points
- **Web Dashboard**: Clean, responsive interface for device management
- **Data Persistence**: Store device information, points, and readings in SQLite database
- **Admin Interface**: Django admin for advanced data management

## Screenshots

### Dashboard
- Overview of all discovered devices
- Device status indicators (online/offline)
- Quick statistics (total devices, points, etc.)
- Discovery controls

### Device Details
- Detailed view of individual devices
- Real-time sensor readings
- Point lists organized by object type
- Individual point value reading

## Requirements

- Python 3.8+
- Django 5.2+
- BACpypes library
- Bootstrap 5.1.3 (loaded via CDN)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BACnet_django
   ```

2. **Create virtual environment**
   ```bash
   python -m venv bacnet_env
   source bacnet_env/bin/activate  # On Windows: bacnet_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django bacpypes
   ```

4. **Configure BACnet settings**
   
   Edit `discovery/BACpypes.ini` with your network configuration:
   ```ini
   [BACpypes]
   objectName: YourDeviceName
   address: 192.168.1.100/24
   objectIdentifier: 599
   maxApduLengthAccepted: 1024
   segmentationSupported: segmentedBoth
   vendorIdentifier: 15
   foreignBBMD: 192.168.1.1
   foreignTTL: 30
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Web Interface: http://localhost:8000/
   - Admin Interface: http://localhost:8000/admin/

## Configuration

### BACnet Configuration

The application uses a configuration file at `discovery/BACpypes.ini`. Key settings:

- **objectName**: Name of your BACnet client device
- **address**: IP address and subnet mask (e.g., 192.168.1.100/24)
- **objectIdentifier**: Unique device ID for your client
- **vendorIdentifier**: BACnet vendor ID
- **foreignBBMD**: BBMD router IP (if using BACnet/IP routing)

### Django Settings

Key settings in `bacnet_project/settings.py`:

- **TIME_ZONE**: Set to "Australia/Melbourne" (adjust as needed)
- **DEBUG**: Set to False in production
- **ALLOWED_HOSTS**: Add your domain/IP for production

## Usage

### Discovering Devices

1. Navigate to the dashboard
2. Click "Discover Devices" to send WhoIs broadcasts
3. Discovered devices will appear in the devices list
4. Device status indicators show online/offline state

### Reading Device Points

1. Click "View Details" on any discovered device
2. If points haven't been read, click "Read Points"
3. The application will discover all BACnet objects on the device
4. Points are organized by object type (analogInput, binaryInput, etc.)

### Reading Sensor Values

1. In device details, click "Read Sensor Values"
2. Current values will be displayed for readable points
3. Individual points can be read using "Read Now" buttons
4. Values automatically refresh every 30 seconds

### Data Management

- Use Django admin interface for advanced data management
- Clear all devices and data using "Clear All Devices"
- Export data using Django admin

## API Endpoints

The application provides REST API endpoints:

- `POST /api/start-discovery/` - Start device discovery
- `POST /api/read-points/{device_id}/` - Read device points
- `POST /api/read-values/{device_id}/` - Read all point values
- `POST /api/read-point/{device_id}/{object_type}/{instance}/` - Read single point
- `GET /api/device-values/{device_id}/` - Get current device values
- `POST /api/clear-devices/` - Clear all devices
- `GET /api/devices/` - List all devices

## Database Models

### BACnetDevice
- Device ID, IP address, vendor information
- Online status and timestamps
- Point reading status

### BACnetPoint
- Object type, instance number, identifier
- Present value, units, object name
- Data type and metadata

### BACnetReading
- Historical sensor readings
- Timestamps and quality indicators
- Linked to specific points

## Architecture

### Components

1. **Django Views** (`discovery/views.py`)
   - Web interface and API endpoints
   - Device and point management

2. **BACnet Client** (`discovery/bacnet_client.py`)
   - BACpypes integration
   - Device discovery and communication
   - Asynchronous request handling

3. **Models** (`discovery/models.py`)
   - Database schema
   - Data validation and relationships

4. **Templates** (`discovery/templates/`)
   - Responsive web interface
   - Bootstrap-based design
   - Real-time updates via JavaScript

### BACnet Communication

- Uses BACpypes library for BACnet protocol support
- Supports BACnet/IP over Ethernet
- Handles WhoIs/IAmI for device discovery
- ReadProperty requests for data collection
- Asynchronous I/O for non-blocking operations

## Troubleshooting

### Common Issues

1. **No devices discovered**
   - Check network connectivity
   - Verify BACpypes.ini configuration
   - Ensure BACnet devices are on same subnet or routing is configured

2. **Permission errors**
   - Run with appropriate network permissions
   - Check firewall settings for UDP port 47808

3. **Point reading failures**
   - Some devices may have security restrictions
   - Check device documentation for supported properties
   - Verify device is online and responsive

4. **Database errors**
   - Run migrations: `python manage.py migrate`
   - Check SQLite file permissions

### Debug Information

- Enable Django debug mode in settings.py
- Check console logs in browser developer tools
- Use Django admin to inspect database records
- Monitor BACnet traffic with Wireshark if needed

## Development

### Project Structure
```
BACnet_django/
├── bacnet_project/          # Django project settings
├── discovery/               # Main application
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   ├── models.py          # Database models
│   ├── views.py           # Web views and API
│   ├── bacnet_client.py   # BACnet communication
│   └── BACpypes.ini       # BACnet configuration
├── manage.py              # Django management script
└── README.md             # This file
```

### Adding Features

1. **New BACnet Properties**
   - Extend `bacnet_client.py` to read additional properties
   - Update models to store new data
   - Modify templates to display information

2. **Additional Device Types**
   - Update device discovery logic
   - Add support for new object types
   - Extend admin interface

3. **Data Export**
   - Add CSV/Excel export functionality
   - Create data visualization features
   - Implement historical trending

## Security Notes

- Change SECRET_KEY in production
- Set DEBUG = False in production
- Use proper database (PostgreSQL/MySQL) for production
- Implement authentication for sensitive operations
- Consider network segmentation for BACnet traffic

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support contact information here]


## How to develop on a new machine 
Basic Requirements on the New Machine

  Install Docker:
  # On macOS (with Homebrew)
  brew install docker docker-compose

  # On Ubuntu/Linux
  sudo apt update
  sudo apt install docker.io docker-compose

  # On Windows
  # Download Docker Desktop from docker.com

  Method 1: Git Clone (Recommended)

  On the new machine:
  # Clone your repository
  git clone https://github.com/your-username/BACnet_django.git
  cd BACnet_django

  # Start all services
  docker-compose up --build

  # In another terminal, run migrations
  docker-compose exec web python manage.py migrate

  # Create superuser
  docker-compose exec web python manage.py createsuperuser

  Method 2: Share Docker Images (Advanced)

  Build and push images to Docker Hub:
  # On your machine, build and tag the image
  docker build -t your-dockerhub-username/bacnet-django .
  docker push your-dockerhub-username/bacnet-django

  # Update docker-compose.yml to use the image
  # Instead of: build: .
  # Use: image: your-dockerhub-username/bacnet-django

  On the new machine:
  # Just pull and run
  docker-compose pull
  docker-compose up
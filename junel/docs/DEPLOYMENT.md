# Deployment Guide

This guide provides detailed instructions for deploying the Face Mask Detection System in various environments.

## Prerequisites

### System Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB available space
- **Network**: Stable internet connection for camera streams
- **OS**: Linux (Ubuntu 20.04+), Windows 10+, or macOS

### Software Requirements
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)

## Installation Methods

### Method 1: Docker Deployment (Recommended)

#### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd face_mask_detection_system

# Copy environment configuration
cp env.example .env

# Edit configuration
nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

#### Manual Docker Setup
```bash
# 1. Build the application
docker-compose build

# 2. Initialize database
docker-compose run --rm face_mask_detection python scripts/init_db.py

# 3. Start services
docker-compose up -d postgres redis mosquitto
docker-compose up -d grafana
docker-compose up -d celery_worker celery_beat
docker-compose up -d face_mask_detection

# 4. Verify deployment
docker-compose logs face_mask_detection
```

### Method 2: Local Installation

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.9 python3.9-dev python3.9-venv \
    postgresql postgresql-contrib \
    redis-server \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 \
    libxrender-dev libgomp1 libgthread-2.0-0 libgtk-3-0 \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev \
    libjpeg-dev libpng-dev libtiff-dev \
    libatlas-base-dev gfortran
```

**CentOS/RHEL:**
```bash
sudo yum update
sudo yum install -y \
    python3.9 python3.9-devel \
    postgresql postgresql-server \
    redis \
    mesa-libGL mesa-libGL-devel \
    gtk3-devel libjpeg-turbo-devel \
    libpng-devel libtiff-devel
```

#### 2. Setup Python Environment
```bash
# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 3. Configure Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE face_mask_detection;
CREATE USER face_mask_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE face_mask_detection TO face_mask_user;
\q

# Initialize database
python scripts/init_db.py
```

#### 4. Configure Redis
```bash
# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test connection
redis-cli ping
```

#### 5. Setup Environment
```bash
# Copy and edit configuration
cp env.example .env
nano .env

# Create necessary directories
mkdir -p logs models config
```

#### 6. Start Services
```bash
# Start Redis (if not already running)
sudo systemctl start redis

# Start Celery worker
celery -A src.workers.celery_app worker --loglevel=info --concurrency=4 &

# Start Celery beat
celery -A src.workers.celery_app beat --loglevel=info &

# Start web application
python src/web_app.py &

# Start main system
python src/main.py
```

### Method 3: Raspberry Pi Deployment

#### 1. Install Raspberry Pi OS
- Download and install Raspberry Pi OS (64-bit recommended)
- Enable SSH and configure network

#### 2. Install Dependencies
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y \
    python3.9 python3.9-dev python3.9-venv \
    libatlas-base-dev gfortran \
    libhdf5-dev libhdf5-serial-dev \
    libqtgui4 libqtwebkit4 libqt4-test \
    python3-pyqt5 libatlas-base-dev \
    libjasper-dev libqtcore4 libqt4-test

# Install OpenCV dependencies
sudo apt-get install -y \
    libopencv-dev python3-opencv \
    libgtk-3-dev libcanberra-gtk3-module
```

#### 3. Setup Camera
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable

# Test camera
vcgencmd get_camera
```

#### 4. Install Application
```bash
# Clone repository
git clone <repository-url>
cd face_mask_detection_system

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
nano .env
```

#### 5. Configure for RPI
```env
# In .env file
RPI_CAMERA_INDEXES=0
CAMERA_RTSP_URLS=
CONFIDENCE_THRESHOLD=0.7
FRAME_SKIP=3
RESIZE_WIDTH=320
RESIZE_HEIGHT=240
```

#### 6. Start System
```bash
# Use startup script
python start_system.py
```

## Configuration

### Environment Variables

#### Database Configuration
```env
DATABASE_URL=postgresql://user:password@localhost/face_mask_detection
```

#### Camera Configuration
```env
# RTSP cameras
CAMERA_RTSP_URLS=rtsp://camera1:554/stream,rtsp://camera2:554/stream

# Raspberry Pi cameras
RPI_CAMERA_INDEXES=0,1
```

#### Performance Tuning
```env
# Processing settings
MAX_WORKERS=4
QUEUE_SIZE=100
BATCH_SIZE=10
FRAME_SKIP=2

# Detection settings
CONFIDENCE_THRESHOLD=0.8
DETECTION_INTERVAL=1.0
```

### Camera Setup

#### IP Camera Configuration
1. **RTSP URL Format**: `rtsp://username:password@ip_address:port/stream`
2. **Common Ports**: 554 (default), 8554, 10554
3. **Stream Paths**: `/stream`, `/live`, `/h264`, `/mjpeg`

#### Raspberry Pi Camera
1. **Enable Camera**: `sudo raspi-config`
2. **Test Camera**: `vcgencmd get_camera`
3. **Camera Index**: Usually 0 for built-in camera

## Monitoring and Maintenance

### Health Checks
```bash
# Check system status
curl http://localhost:5000/health

# Check database
psql -h localhost -U face_mask_user -d face_mask_detection -c "SELECT 1;"

# Check Redis
redis-cli ping

# Check Celery
celery -A src.workers.celery_app inspect active
```

### Logs
```bash
# Application logs
tail -f logs/face_mask_detection.log

# Docker logs
docker-compose logs -f face_mask_detection

# System logs
journalctl -u face_mask_detection -f
```

### Performance Monitoring
- **Grafana Dashboard**: http://localhost:3000
- **Web Dashboard**: http://localhost:5000
- **API Endpoints**: http://localhost:5000/api

### Backup and Recovery
```bash
# Database backup
pg_dump -h localhost -U face_mask_user face_mask_detection > backup.sql

# Restore database
psql -h localhost -U face_mask_user face_mask_detection < backup.sql

# Configuration backup
tar -czf config_backup.tar.gz .env models/ logs/
```

## Troubleshooting

### Common Issues

#### 1. Camera Connection Issues
```bash
# Test RTSP stream
ffplay rtsp://camera_ip:554/stream

# Check network connectivity
ping camera_ip

# Verify camera credentials
curl -u username:password http://camera_ip/onvif/device_service
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U face_mask_user -d face_mask_detection

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Performance Issues
```bash
# Monitor system resources
htop
nvidia-smi  # if using GPU

# Check queue status
redis-cli llen celery

# Optimize settings
# Increase FRAME_SKIP, reduce RESIZE_WIDTH/HEIGHT
```

#### 4. Memory Issues
```bash
# Monitor memory usage
free -h
ps aux --sort=-%mem

# Optimize batch size and queue size
# Reduce MAX_WORKERS if needed
```

## Security Considerations

### Network Security
- Use VPN for remote access
- Configure firewall rules
- Use HTTPS for web interface
- Implement authentication for API endpoints

### Data Privacy
- Encrypt sensitive data
- Implement data retention policies
- Regular security audits
- GDPR compliance considerations

### Access Control
- Use strong passwords
- Implement role-based access
- Regular credential rotation
- Monitor access logs

## Scaling

### Horizontal Scaling
```bash
# Multiple worker instances
docker-compose up -d --scale celery_worker=4

# Load balancer setup
# Use nginx or haproxy for multiple instances
```

### Vertical Scaling
- Increase CPU cores
- Add more RAM
- Use GPU acceleration
- Optimize database queries

## Support

For technical support:
- Check the troubleshooting section
- Review system logs
- Consult the API documentation
- Contact system administrator

## Updates and Maintenance

### Regular Maintenance
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Database maintenance
psql -h localhost -U face_mask_user -d face_mask_detection -c "VACUUM ANALYZE;"

# Log rotation
logrotate /etc/logrotate.d/face_mask_detection

# System updates
sudo apt-get update && sudo apt-get upgrade
```

### Backup Strategy
- Daily database backups
- Weekly configuration backups
- Monthly full system backups
- Test restore procedures regularly

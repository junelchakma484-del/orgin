# Face Mask Detection System

A comprehensive AI-powered face mask detection system designed for university computer labs and public spaces. The system uses Raspberry Pi and IP cameras to monitor mask compliance and provides real-time reporting through multiple channels.

## Features

- **Real-time Detection**: AI-powered face mask detection using OpenCV and TensorFlow
- **Multi-Camera Support**: Handles multiple RTSP video streams simultaneously
- **Message Queue Architecture**: Optimized processing with Redis and Celery
- **Multithreading**: Parallel processing for video streams, analysis, and alerts
- **Multiple Reporting Channels**:
  - Grafana dashboards for analytics
  - Telegram bot for real-time alerts
  - PostgreSQL database for data persistence
- **MQTT Integration**: Remote control and monitoring capabilities
- **Performance Optimized**: 50% faster OpenCV processing through queue design

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IP Cameras    │    │  Raspberry Pi   │    │   USB Cameras   │
│   (RTSP)        │    │   Cameras       │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   Video Stream Manager    │
                    │    (Multithreaded)        │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   Message Queue (Redis)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   Face Detection Worker   │
                    │    (Celery Tasks)         │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│   PostgreSQL      │  │   Telegram Bot    │  │   Grafana         │
│   Database        │  │   (Alerts)        │  │   (Analytics)     │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd face_mask_detection_system
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up databases**:
   ```bash
   # PostgreSQL setup
   createdb face_mask_detection
   
   # Redis setup
   redis-server
   ```

5. **Initialize the database**:
   ```bash
   python scripts/init_db.py
   ```

## Configuration

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/face_mask_detection

# Redis
REDIS_URL=redis://localhost:6379

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password

# Camera Configuration
CAMERA_RTSP_URLS=rtsp://camera1:554/stream,rtsp://camera2:554/stream
RPI_CAMERA_INDEXES=0,1

# Detection Settings
CONFIDENCE_THRESHOLD=0.8
DETECTION_INTERVAL=1.0
```

## Usage

### Starting the System

1. **Start Redis and Celery**:
   ```bash
   redis-server
   celery -A src.workers.celery_app worker --loglevel=info
   ```

2. **Start the main application**:
   ```bash
   python src/main.py
   ```

3. **Start the web dashboard**:
   ```bash
   python src/web_app.py
   ```

### Monitoring

- **Grafana Dashboard**: http://localhost:3000
- **Web Dashboard**: http://localhost:5000
- **API Endpoints**: http://localhost:5000/api

## Performance Optimizations

- **Message Queue Design**: Reduces OpenCV processing time by 50%
- **Multithreading**: Parallel processing of video streams and analysis
- **Batch Processing**: Efficient handling of multiple camera feeds
- **Memory Management**: Optimized image processing pipeline

## Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Raspberry Pi Deployment
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-opencv libatlas-base-dev

# Run the application
python3 src/main.py
```

## API Documentation

### Endpoints

- `GET /api/status` - System status
- `GET /api/statistics` - Detection statistics
- `POST /api/camera/control` - Camera control
- `GET /api/alerts` - Recent alerts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- OpenCV community for computer vision tools
- TensorFlow team for AI framework
- University computer lab staff for testing and feedback

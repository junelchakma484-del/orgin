"""
Configuration module for Face Mask Detection System
Handles environment variables and system settings
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Face Mask Detection System"""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/face_mask_detection')
    
    # Redis Configuration
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')
    
    # MQTT Configuration
    MQTT_BROKER: str = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT: int = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_USERNAME: Optional[str] = os.getenv('MQTT_USERNAME')
    MQTT_PASSWORD: Optional[str] = os.getenv('MQTT_PASSWORD')
    MQTT_CLIENT_ID: str = os.getenv('MQTT_CLIENT_ID', 'face_mask_detector')
    
    # Camera Configuration
    CAMERA_RTSP_URLS: List[str] = os.getenv('CAMERA_RTSP_URLS', '').split(',') if os.getenv('CAMERA_RTSP_URLS') else []
    RPI_CAMERA_INDEXES: List[int] = [int(x) for x in os.getenv('RPI_CAMERA_INDEXES', '0').split(',')]
    
    # Detection Settings
    CONFIDENCE_THRESHOLD: float = float(os.getenv('CONFIDENCE_THRESHOLD', '0.8'))
    DETECTION_INTERVAL: float = float(os.getenv('DETECTION_INTERVAL', '1.0'))
    FACE_DETECTION_MODEL: str = os.getenv('FACE_DETECTION_MODEL', 'models/face_detection_model.pb')
    MASK_DETECTION_MODEL: str = os.getenv('MASK_DETECTION_MODEL', 'models/mask_detection_model.h5')
    
    # Processing Settings
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    QUEUE_SIZE: int = int(os.getenv('QUEUE_SIZE', '100'))
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '10'))
    
    # Alert Settings
    ALERT_COOLDOWN: int = int(os.getenv('ALERT_COOLDOWN', '300'))  # 5 minutes
    MIN_VIOLATIONS_FOR_ALERT: int = int(os.getenv('MIN_VIOLATIONS_FOR_ALERT', '3'))
    
    # Web Server Settings
    WEB_HOST: str = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT: int = int(os.getenv('WEB_PORT', '5000'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/face_mask_detection.log')
    
    # Performance Settings
    FRAME_SKIP: int = int(os.getenv('FRAME_SKIP', '2'))  # Process every nth frame
    RESIZE_WIDTH: int = int(os.getenv('RESIZE_WIDTH', '640'))
    RESIZE_HEIGHT: int = int(os.getenv('RESIZE_HEIGHT', '480'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        required_fields = [
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        for field in required_fields:
            if not getattr(cls, field):
                raise ValueError(f"Required configuration field '{field}' is not set")
        
        return True
    
    @classmethod
    def get_camera_urls(cls) -> List[str]:
        """Get all camera URLs (RTSP + RPI)"""
        urls = cls.CAMERA_RTSP_URLS.copy()
        for index in cls.RPI_CAMERA_INDEXES:
            urls.append(f"rpi://{index}")
        return urls

# Global configuration instance
config = Config()

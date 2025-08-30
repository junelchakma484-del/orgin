"""
Main Application for Face Mask Detection System
Orchestrates all components with multithreading and message queue optimization
"""

import sys
import time
import signal
import threading
import logging
from typing import Dict, Any
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config import config
from camera.stream_manager import create_stream_manager
from workers.celery_app import celery_app
from workers.tasks import process_frame
from database.connection import init_database, create_tables, test_connection
from notifications.telegram_bot import get_telegram_notifier
from mqtt.client import get_mqtt_client
import cv2

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FaceMaskDetectionSystem:
    """Main system class that orchestrates all components"""
    
    def __init__(self):
        self.stream_manager = None
        self.telegram_notifier = None
        self.mqtt_client = None
        self.running = False
        self.stats_thread = None
        self.monitoring_thread = None
        
        # Performance tracking
        self.start_time = time.time()
        self.total_frames_processed = 0
        self.total_violations = 0
        
        # Initialize components
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing Face Mask Detection System...")
            
            # Validate configuration
            config.validate()
            
            # Initialize database
            logger.info("Initializing database...")
            init_database()
            if not test_connection():
                raise Exception("Database connection failed")
            create_tables()
            
            # Initialize stream manager
            logger.info("Initializing stream manager...")
            self.stream_manager = create_stream_manager()
            self.stream_manager.set_frame_callback(self._process_frame_callback)
            
            # Initialize Telegram notifier
            logger.info("Initializing Telegram notifier...")
            self.telegram_notifier = get_telegram_notifier()
            
            # Initialize MQTT client
            logger.info("Initializing MQTT client...")
            self.mqtt_client = get_mqtt_client()
            if not self.mqtt_client.connect():
                logger.warning("MQTT connection failed, continuing without MQTT")
            
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    def _process_frame_callback(self, frame_data: Dict[str, Any]):
        """Callback for processing frames from stream manager"""
        try:
            # Send frame to Celery worker for processing
            task = process_frame.delay(frame_data)
            
            # Update statistics
            self.total_frames_processed += 1
            
            # Log progress every 100 frames
            if self.total_frames_processed % 100 == 0:
                logger.info(f"Processed {self.total_frames_processed} frames")
                
        except Exception as e:
            logger.error(f"Error in frame processing callback: {e}")
    
    def _monitoring_loop(self):
        """Monitoring loop for system health and performance"""
        while self.running:
            try:
                # Get system statistics
                stats = self.stream_manager.get_stats()
                
                # Calculate compliance rate
                uptime = time.time() - self.start_time
                fps = stats['processed_frames'] / uptime if uptime > 0 else 0
                
                # Prepare status data
                status_data = {
                    'timestamp': time.time(),
                    'uptime': uptime,
                    'fps': fps,
                    'active_streams': stats['active_streams'],
                    'queue_size': stats['queue_size'],
                    'total_frames_processed': stats['processed_frames'],
                    'dropped_frames': stats['dropped_frames']
                }
                
                # Send status updates
                if self.mqtt_client and self.mqtt_client.is_connected:
                    self.mqtt_client.publish_metrics(status_data)
                
                if self.telegram_notifier:
                    # Send status update every hour
                    if int(uptime) % 3600 < 60:  # Within first minute of each hour
                        self.telegram_notifier.send_status_update(status_data)
                
                # Sleep for monitoring interval
                time.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _stats_loop(self):
        """Statistics collection loop for Grafana"""
        while self.running:
            try:
                from database.connection import get_db_session
                from database.models import SystemMetrics
                
                # Get system stats
                stats = self.stream_manager.get_stats()
                uptime = time.time() - self.start_time
                
                # Create system metrics record
                with get_db_session() as session:
                    metrics = SystemMetrics(
                        timestamp=time.time(),
                        fps=stats['fps'],
                        queue_size=stats['queue_size'],
                        active_streams=stats['active_streams'],
                        total_frames_processed=stats['processed_frames'],
                        dropped_frames=stats['dropped_frames']
                    )
                    session.add(metrics)
                    session.commit()
                
                # Sleep for stats collection interval
                time.sleep(300)  # Collect stats every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in stats loop: {e}")
                time.sleep(300)
    
    def start(self):
        """Start the face mask detection system"""
        if self.running:
            logger.warning("System is already running")
            return
        
        try:
            logger.info("Starting Face Mask Detection System...")
            
            # Start stream manager
            self.stream_manager.start()
            
            # Start monitoring threads
            self.running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
            
            self.monitoring_thread.start()
            self.stats_thread.start()
            
            logger.info("Face Mask Detection System started successfully")
            logger.info(f"Monitoring {len(self.stream_manager.streams)} camera streams")
            
            # Send startup notification
            if self.telegram_notifier:
                self.telegram_notifier.send_alert(
                    "🚀 Face Mask Detection System Started\n\n"
                    f"Active cameras: {len(self.stream_manager.streams)}\n"
                    f"Location: University Computer Lab\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    {'mask_violations': 0, 'total_faces': 0}
                )
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            raise
    
    def stop(self):
        """Stop the face mask detection system"""
        if not self.running:
            return
        
        try:
            logger.info("Stopping Face Mask Detection System...")
            
            # Stop monitoring threads
            self.running = False
            
            # Stop stream manager
            if self.stream_manager:
                self.stream_manager.stop()
            
            # Disconnect MQTT client
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            
            # Send shutdown notification
            if self.telegram_notifier:
                uptime = time.time() - self.start_time
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                
                self.telegram_notifier.send_alert(
                    "🛑 Face Mask Detection System Stopped\n\n"
                    f"Uptime: {hours}h {minutes}m\n"
                    f"Total frames processed: {self.total_frames_processed}\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    {'mask_violations': 0, 'total_faces': 0}
                )
            
            logger.info("Face Mask Detection System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        if not self.stream_manager:
            return {'status': 'not_initialized'}
        
        stats = self.stream_manager.get_stats()
        uptime = time.time() - self.start_time
        
        return {
            'status': 'running' if self.running else 'stopped',
            'uptime': uptime,
            'fps': stats['fps'],
            'active_streams': stats['active_streams'],
            'queue_size': stats['queue_size'],
            'total_frames_processed': stats['processed_frames'],
            'dropped_frames': stats['dropped_frames'],
            'total_violations': self.total_violations
        }

# Global system instance
system = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if system:
        system.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    global system
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and start system
        system = FaceMaskDetectionSystem()
        system.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            system.stop()
            
    except Exception as e:
        logger.error(f"System error: {e}")
        if system:
            system.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()

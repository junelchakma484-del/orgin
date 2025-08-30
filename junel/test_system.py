#!/usr/bin/env python3
"""
Test Script for Face Mask Detection System
Verifies all system components are working correctly
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import config
from database.connection import test_connection, init_database
from models.face_detector import FaceDetector
from camera.stream_manager import create_stream_manager
from notifications.telegram_bot import get_telegram_notifier
from mqtt.client import get_mqtt_client
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTester:
    """Test all system components"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_configuration(self):
        """Test configuration loading"""
        try:
            logger.info("Testing configuration...")
            config.validate()
            logger.info("✓ Configuration is valid")
            self.test_results['configuration'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Configuration test failed: {e}")
            self.test_results['configuration'] = False
            return False
    
    def test_database(self):
        """Test database connection"""
        try:
            logger.info("Testing database connection...")
            init_database()
            if test_connection():
                logger.info("✓ Database connection successful")
                self.test_results['database'] = True
                return True
            else:
                logger.error("✗ Database connection failed")
                self.test_results['database'] = False
                return False
        except Exception as e:
            logger.error(f"✗ Database test failed: {e}")
            self.test_results['database'] = False
            return False
    
    def test_face_detector(self):
        """Test face detection model"""
        try:
            logger.info("Testing face detector...")
            detector = FaceDetector()
            
            # Create a test image
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            # Test detection
            detections = detector.process_frame(test_image)
            logger.info(f"✓ Face detector processed frame with {len(detections)} detections")
            self.test_results['face_detector'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Face detector test failed: {e}")
            self.test_results['face_detector'] = False
            return False
    
    def test_stream_manager(self):
        """Test stream manager"""
        try:
            logger.info("Testing stream manager...")
            manager = create_stream_manager()
            logger.info(f"✓ Stream manager created with {len(manager.streams)} streams")
            self.test_results['stream_manager'] = True
            return True
        except Exception as e:
            logger.error(f"✗ Stream manager test failed: {e}")
            self.test_results['stream_manager'] = False
            return False
    
    def test_telegram_bot(self):
        """Test Telegram bot"""
        try:
            logger.info("Testing Telegram bot...")
            notifier = get_telegram_notifier()
            if notifier.is_initialized:
                logger.info("✓ Telegram bot initialized successfully")
                self.test_results['telegram_bot'] = True
                return True
            else:
                logger.warning("⚠ Telegram bot not configured (missing token)")
                self.test_results['telegram_bot'] = 'not_configured'
                return True
        except Exception as e:
            logger.error(f"✗ Telegram bot test failed: {e}")
            self.test_results['telegram_bot'] = False
            return False
    
    def test_mqtt_client(self):
        """Test MQTT client"""
        try:
            logger.info("Testing MQTT client...")
            client = get_mqtt_client()
            if client.connect():
                logger.info("✓ MQTT client connected successfully")
                client.disconnect()
                self.test_results['mqtt_client'] = True
                return True
            else:
                logger.warning("⚠ MQTT client connection failed (broker may not be running)")
                self.test_results['mqtt_client'] = 'not_connected'
                return True
        except Exception as e:
            logger.error(f"✗ MQTT client test failed: {e}")
            self.test_results['mqtt_client'] = False
            return False
    
    def test_opencv(self):
        """Test OpenCV installation"""
        try:
            logger.info("Testing OpenCV...")
            # Test basic OpenCV functionality
            test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            logger.info("✓ OpenCV is working correctly")
            self.test_results['opencv'] = True
            return True
        except Exception as e:
            logger.error(f"✗ OpenCV test failed: {e}")
            self.test_results['opencv'] = False
            return False
    
    def test_tensorflow(self):
        """Test TensorFlow installation"""
        try:
            logger.info("Testing TensorFlow...")
            import tensorflow as tf
            logger.info(f"✓ TensorFlow version: {tf.__version__}")
            logger.info(f"✓ Available devices: {tf.config.list_physical_devices()}")
            self.test_results['tensorflow'] = True
            return True
        except Exception as e:
            logger.error(f"✗ TensorFlow test failed: {e}")
            self.test_results['tensorflow'] = False
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        logger.info("Starting Face Mask Detection System Tests")
        logger.info("=" * 50)
        
        tests = [
            ('Configuration', self.test_configuration),
            ('Database', self.test_database),
            ('OpenCV', self.test_opencv),
            ('TensorFlow', self.test_tensorflow),
            ('Face Detector', self.test_face_detector),
            ('Stream Manager', self.test_stream_manager),
            ('Telegram Bot', self.test_telegram_bot),
            ('MQTT Client', self.test_mqtt_client),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\nTesting {test_name}...")
            if test_func():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        
        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        
        for test_name, test_func in tests:
            result = self.test_results.get(test_name.lower().replace(' ', '_'), False)
            status = "✓ PASS" if result is True else "⚠ SKIP" if result == 'not_configured' else "✗ FAIL"
            logger.info(f"{test_name:20} {status}")
        
        logger.info(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! System is ready to run.")
            return True
        else:
            logger.warning("⚠ Some tests failed. Please check the configuration.")
            return False

def main():
    """Main test function"""
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("\nTo start the system, run:")
        logger.info("python start_system.py")
        logger.info("\nOr for Docker deployment:")
        logger.info("docker-compose up -d")
    else:
        logger.error("\nPlease fix the failed tests before running the system.")
        sys.exit(1)

if __name__ == "__main__":
    main()

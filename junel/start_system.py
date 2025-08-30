#!/usr/bin/env python3
"""
Startup Script for Face Mask Detection System
Initializes and runs the entire system with all components
"""

import os
import sys
import time
import subprocess
import threading
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemManager:
    """Manages the startup and shutdown of all system components"""
    
    def __init__(self):
        self.processes = []
        self.running = False
        
    def start_redis(self):
        """Start Redis server"""
        try:
            logger.info("Starting Redis server...")
            # Check if Redis is already running
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Redis is already running")
                return True
            
            # Start Redis
            process = subprocess.Popen(['redis-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('redis', process))
            
            # Wait for Redis to start
            time.sleep(2)
            logger.info("Redis started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            return False
    
    def start_celery_worker(self):
        """Start Celery worker"""
        try:
            logger.info("Starting Celery worker...")
            cmd = [
                sys.executable, '-m', 'celery', 
                '-A', 'src.workers.celery_app', 
                'worker', 
                '--loglevel=info',
                '--concurrency=4'
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('celery_worker', process))
            logger.info("Celery worker started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Celery worker: {e}")
            return False
    
    def start_celery_beat(self):
        """Start Celery beat scheduler"""
        try:
            logger.info("Starting Celery beat scheduler...")
            cmd = [
                sys.executable, '-m', 'celery', 
                '-A', 'src.workers.celery_app', 
                'beat', 
                '--loglevel=info'
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('celery_beat', process))
            logger.info("Celery beat scheduler started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Celery beat: {e}")
            return False
    
    def start_web_app(self):
        """Start Flask web application"""
        try:
            logger.info("Starting web application...")
            cmd = [sys.executable, 'src/web_app.py']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('web_app', process))
            logger.info("Web application started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start web application: {e}")
            return False
    
    def start_main_system(self):
        """Start main face mask detection system"""
        try:
            logger.info("Starting main face mask detection system...")
            cmd = [sys.executable, 'src/main.py']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(('main_system', process))
            logger.info("Main system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start main system: {e}")
            return False
    
    def initialize_database(self):
        """Initialize database"""
        try:
            logger.info("Initializing database...")
            cmd = [sys.executable, 'scripts/init_db.py']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database initialized successfully")
                return True
            else:
                logger.error(f"Database initialization failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def check_dependencies(self):
        """Check if all dependencies are available"""
        try:
            logger.info("Checking dependencies...")
            
            # Check Python packages
            required_packages = [
                'opencv-python', 'tensorflow', 'numpy', 'flask', 
                'celery', 'redis', 'psycopg2-binary', 'paho-mqtt'
            ]
            
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    logger.error(f"Missing package: {package}")
                    return False
            
            # Check system commands
            system_commands = ['redis-server', 'redis-cli']
            for cmd in system_commands:
                result = subprocess.run(['which', cmd], capture_output=True)
                if result.returncode != 0:
                    logger.warning(f"System command not found: {cmd}")
            
            logger.info("Dependencies check completed")
            return True
            
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            return False
    
    def start_system(self):
        """Start the entire system"""
        try:
            logger.info("Starting Face Mask Detection System...")
            
            # Check dependencies
            if not self.check_dependencies():
                logger.error("Dependency check failed")
                return False
            
            # Initialize database
            if not self.initialize_database():
                logger.error("Database initialization failed")
                return False
            
            # Start Redis
            if not self.start_redis():
                logger.error("Failed to start Redis")
                return False
            
            # Start Celery worker
            if not self.start_celery_worker():
                logger.error("Failed to start Celery worker")
                return False
            
            # Start Celery beat
            if not self.start_celery_beat():
                logger.error("Failed to start Celery beat")
                return False
            
            # Start web application
            if not self.start_web_app():
                logger.error("Failed to start web application")
                return False
            
            # Start main system
            if not self.start_main_system():
                logger.error("Failed to start main system")
                return False
            
            self.running = True
            logger.info("All system components started successfully")
            logger.info("System is now running")
            logger.info("Web Dashboard: http://localhost:5000")
            logger.info("Grafana: http://localhost:3000")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            return False
    
    def stop_system(self):
        """Stop all system components"""
        try:
            logger.info("Stopping Face Mask Detection System...")
            
            self.running = False
            
            # Stop all processes
            for name, process in self.processes:
                try:
                    logger.info(f"Stopping {name}...")
                    process.terminate()
                    process.wait(timeout=10)
                    logger.info(f"{name} stopped successfully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
            
            self.processes.clear()
            logger.info("System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    def monitor_processes(self):
        """Monitor running processes"""
        while self.running:
            try:
                for name, process in self.processes:
                    if process.poll() is not None:
                        logger.error(f"Process {name} has stopped unexpectedly")
                        self.running = False
                        break
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error monitoring processes: {e}")
                break

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if system_manager:
        system_manager.stop_system()
    sys.exit(0)

def main():
    """Main entry point"""
    global system_manager
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create system manager
        system_manager = SystemManager()
        
        # Start system
        if not system_manager.start_system():
            logger.error("Failed to start system")
            sys.exit(1)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=system_manager.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while system_manager.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            system_manager.stop_system()
            
    except Exception as e:
        logger.error(f"System error: {e}")
        if system_manager:
            system_manager.stop_system()
        sys.exit(1)

if __name__ == "__main__":
    main()

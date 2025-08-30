#!/usr/bin/env python3
"""
Database Initialization Script for Face Mask Detection System
Creates database tables and initializes the system
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from database.connection import init_database, create_tables, test_connection
from database.models import Detection, Alert, SystemMetrics, CameraStatus, ComplianceReport
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize the database"""
    try:
        logger.info("Initializing database...")
        
        # Initialize database connection
        init_database()
        
        # Test connection
        if not test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        # Create tables
        create_tables()
        
        logger.info("Database initialization completed successfully")
        
        # Print table information
        logger.info("Created tables:")
        logger.info("- detections")
        logger.info("- alerts")
        logger.info("- system_metrics")
        logger.info("- camera_status")
        logger.info("- compliance_reports")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

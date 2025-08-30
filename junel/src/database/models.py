"""
Database Models for Face Mask Detection System
SQLAlchemy models with proper indexing for Grafana analytics
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class Detection(Base):
    """Detection model for storing face mask detection results"""
    
    __tablename__ = 'detections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stream_name = Column(String(100), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    total_faces = Column(Integer, default=0)
    mask_violations = Column(Integer, default=0)
    detection_data = Column(Text)  # JSON string of detection details
    created_at = Column(DateTime, default=func.now())
    
    # Indexes for Grafana analytics
    __table_args__ = (
        Index('idx_detections_timestamp', 'timestamp'),
        Index('idx_detections_stream_timestamp', 'stream_name', 'timestamp'),
        Index('idx_detections_violations', 'mask_violations'),
        Index('idx_detections_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Detection(id={self.id}, stream={self.stream_name}, violations={self.mask_violations})>"
    
    @property
    def compliance_rate(self) -> float:
        """Calculate compliance rate for this detection"""
        if self.total_faces == 0:
            return 100.0
        return round(((self.total_faces - self.mask_violations) / self.total_faces) * 100, 2)

class Alert(Base):
    """Alert model for storing mask violation alerts"""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stream_name = Column(String(100), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    message = Column(Text, nullable=False)
    violation_count = Column(Integer, default=0)
    total_faces = Column(Integer, default=0)
    sent_via_telegram = Column(Boolean, default=False)
    sent_via_mqtt = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Indexes for alert analytics
    __table_args__ = (
        Index('idx_alerts_timestamp', 'timestamp'),
        Index('idx_alerts_stream_timestamp', 'stream_name', 'timestamp'),
        Index('idx_alerts_violation_count', 'violation_count'),
        Index('idx_alerts_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Alert(id={self.id}, stream={self.stream_name}, violations={self.violation_count})>"

class SystemMetrics(Base):
    """System metrics model for monitoring performance"""
    
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Float, nullable=False, index=True)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    gpu_usage = Column(Float)
    fps = Column(Float)
    queue_size = Column(Integer)
    active_streams = Column(Integer)
    total_frames_processed = Column(Integer)
    dropped_frames = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Indexes for system monitoring
    __table_args__ = (
        Index('idx_metrics_timestamp', 'timestamp'),
        Index('idx_metrics_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, fps={self.fps}, cpu={self.cpu_usage})>"

class CameraStatus(Base):
    """Camera status model for monitoring camera health"""
    
    __tablename__ = 'camera_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stream_name = Column(String(100), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # 'online', 'offline', 'error'
    fps = Column(Float)
    resolution = Column(String(20))
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Indexes for camera monitoring
    __table_args__ = (
        Index('idx_camera_status_stream', 'stream_name'),
        Index('idx_camera_status_timestamp', 'timestamp'),
        Index('idx_camera_status_status', 'status'),
    )
    
    def __repr__(self):
        return f"<CameraStatus(stream={self.stream_name}, status={self.status})>"

class ComplianceReport(Base):
    """Compliance report model for storing daily/weekly reports"""
    
    __tablename__ = 'compliance_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    total_detections = Column(Integer, default=0)
    total_faces = Column(Integer, default=0)
    total_violations = Column(Integer, default=0)
    compliance_rate = Column(Float, default=100.0)
    report_data = Column(Text)  # JSON string of detailed report
    created_at = Column(DateTime, default=func.now())
    
    # Indexes for report analytics
    __table_args__ = (
        Index('idx_reports_type', 'report_type'),
        Index('idx_reports_start_date', 'start_date'),
        Index('idx_reports_end_date', 'end_date'),
        Index('idx_reports_compliance_rate', 'compliance_rate'),
    )
    
    def __repr__(self):
        return f"<ComplianceReport(type={self.report_type}, compliance={self.compliance_rate}%)>"

# Utility functions for database operations
def get_detection_stats(session, start_time=None, end_time=None, stream_name=None):
    """Get detection statistics for Grafana"""
    query = session.query(Detection)
    
    if start_time:
        query = query.filter(Detection.timestamp >= start_time)
    if end_time:
        query = query.filter(Detection.timestamp <= end_time)
    if stream_name:
        query = query.filter(Detection.stream_name == stream_name)
    
    return query

def get_compliance_rate(session, start_time=None, end_time=None, stream_name=None):
    """Calculate compliance rate for given period"""
    query = get_detection_stats(session, start_time, end_time, stream_name)
    
    total_faces = query.with_entities(func.sum(Detection.total_faces)).scalar() or 0
    total_violations = query.with_entities(func.sum(Detection.mask_violations)).scalar() or 0
    
    if total_faces == 0:
        return 100.0
    
    return round(((total_faces - total_violations) / total_faces) * 100, 2)

def get_hourly_breakdown(session, start_time, end_time, stream_name=None):
    """Get hourly detection breakdown for Grafana"""
    query = session.query(
        func.date_trunc('hour', func.to_timestamp(Detection.timestamp)).label('hour'),
        func.count(Detection.id).label('detections'),
        func.sum(Detection.total_faces).label('total_faces'),
        func.sum(Detection.mask_violations).label('violations')
    ).filter(
        Detection.timestamp >= start_time,
        Detection.timestamp <= end_time
    )
    
    if stream_name:
        query = query.filter(Detection.stream_name == stream_name)
    
    return query.group_by(
        func.date_trunc('hour', func.to_timestamp(Detection.timestamp))
    ).all()

"""
Flask Web Application for Face Mask Detection System
Real-time monitoring and control dashboard
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Import system components
from config import config
from database.connection import get_db_session
from database.models import Detection, Alert, SystemMetrics, get_compliance_rate, get_hourly_breakdown
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global system reference (will be set by main.py)
system = None

def set_system_reference(system_instance):
    """Set global system reference"""
    global system
    system = system_instance

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        if system:
            status = system.get_status()
        else:
            status = {'status': 'not_initialized'}
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get detection statistics"""
    try:
        with get_db_session() as session:
            # Get today's stats
            today_start = time.time() - (24 * 60 * 60)
            
            # Total detections today
            total_detections = session.query(func.count(Detection.id)).filter(
                Detection.timestamp >= today_start
            ).scalar() or 0
            
            # Total faces today
            total_faces = session.query(func.sum(Detection.total_faces)).filter(
                Detection.timestamp >= today_start
            ).scalar() or 0
            
            # Total violations today
            total_violations = session.query(func.sum(Detection.mask_violations)).filter(
                Detection.timestamp >= today_start
            ).scalar() or 0
            
            # Compliance rate
            compliance_rate = get_compliance_rate(session, today_start, time.time())
            
            # Hourly breakdown
            hourly_stats = get_hourly_breakdown(session, today_start, time.time())
            
            stats = {
                'total_detections': total_detections,
                'total_faces': total_faces,
                'total_violations': total_violations,
                'compliance_rate': compliance_rate,
                'hourly_breakdown': [
                    {
                        'hour': h.hour.strftime('%H:00'),
                        'detections': h.detections,
                        'violations': h.violations
                    }
                    for h in hourly_stats
                ]
            }
            
            return jsonify(stats)
            
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        with get_db_session() as session:
            alerts = session.query(Alert).order_by(
                Alert.timestamp.desc()
            ).limit(limit).all()
            
            alert_data = [
                {
                    'id': alert.id,
                    'stream_name': alert.stream_name,
                    'timestamp': alert.timestamp,
                    'message': alert.message,
                    'violation_count': alert.violation_count,
                    'total_faces': alert.total_faces,
                    'created_at': alert.created_at.isoformat()
                }
                for alert in alerts
            ]
            
            return jsonify(alert_data)
            
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/detections')
def get_detections():
    """Get recent detections"""
    try:
        limit = request.args.get('limit', 50, type=int)
        stream_name = request.args.get('stream')
        
        with get_db_session() as session:
            query = session.query(Detection).order_by(Detection.timestamp.desc())
            
            if stream_name:
                query = query.filter(Detection.stream_name == stream_name)
            
            detections = query.limit(limit).all()
            
            detection_data = [
                {
                    'id': detection.id,
                    'stream_name': detection.stream_name,
                    'timestamp': detection.timestamp,
                    'total_faces': detection.total_faces,
                    'mask_violations': detection.mask_violations,
                    'compliance_rate': detection.compliance_rate,
                    'created_at': detection.created_at.isoformat()
                }
                for detection in detections
            ]
            
            return jsonify(detection_data)
            
    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/control', methods=['POST'])
def camera_control():
    """Control camera operations"""
    try:
        data = request.get_json()
        action = data.get('action')
        camera_id = data.get('camera_id')
        
        if not action or not camera_id:
            return jsonify({'error': 'Missing action or camera_id'}), 400
        
        # Send MQTT command
        if system and system.mqtt_client:
            system.mqtt_client.send_camera_control(camera_id, action)
            return jsonify({'status': 'command_sent'})
        else:
            return jsonify({'error': 'MQTT not available'}), 503
            
    except Exception as e:
        logger.error(f"Error in camera control: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/control', methods=['POST'])
def system_control():
    """Control system operations"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if not action:
            return jsonify({'error': 'Missing action'}), 400
        
        # Send MQTT command
        if system and system.mqtt_client:
            system.mqtt_client.send_system_control(action)
            return jsonify({'status': 'command_sent'})
        else:
            return jsonify({'error': 'MQTT not available'}), 503
            
    except Exception as e:
        logger.error(f"Error in system control: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def get_metrics():
    """Get system metrics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        start_time = time.time() - (hours * 60 * 60)
        
        with get_db_session() as session:
            metrics = session.query(SystemMetrics).filter(
                SystemMetrics.timestamp >= start_time
            ).order_by(SystemMetrics.timestamp.asc()).all()
            
            metrics_data = [
                {
                    'timestamp': metric.timestamp,
                    'fps': metric.fps,
                    'queue_size': metric.queue_size,
                    'active_streams': metric.active_streams,
                    'total_frames_processed': metric.total_frames_processed,
                    'dropped_frames': metric.dropped_frames
                }
                for metric in metrics
            ]
            
            return jsonify(metrics_data)
            
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/compliance')
def get_compliance_report():
    """Get compliance report"""
    try:
        days = request.args.get('days', 7, type=int)
        start_time = time.time() - (days * 24 * 60 * 60)
        
        with get_db_session() as session:
            # Daily breakdown
            daily_stats = session.query(
                func.date_trunc('day', func.to_timestamp(Detection.timestamp)).label('day'),
                func.count(Detection.id).label('detections'),
                func.sum(Detection.total_faces).label('total_faces'),
                func.sum(Detection.mask_violations).label('violations')
            ).filter(
                Detection.timestamp >= start_time
            ).group_by(
                func.date_trunc('day', func.to_timestamp(Detection.timestamp))
            ).order_by(
                func.date_trunc('day', func.to_timestamp(Detection.timestamp))
            ).all()
            
            report_data = [
                {
                    'date': stat.day.strftime('%Y-%m-%d'),
                    'detections': stat.detections,
                    'total_faces': stat.total_faces or 0,
                    'violations': stat.violations or 0,
                    'compliance_rate': round(((stat.total_faces or 0) - (stat.violations or 0)) / (stat.total_faces or 1) * 100, 2)
                }
                for stat in daily_stats
            ]
            
            return jsonify(report_data)
            
    except Exception as e:
        logger.error(f"Error getting compliance report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams')
def get_streams():
    """Get camera stream information"""
    try:
        if system and system.stream_manager:
            streams = []
            for name, stream in system.stream_manager.streams.items():
                streams.append({
                    'name': name,
                    'url': stream.config.url,
                    'running': stream.running,
                    'enabled': stream.config.enabled
                })
            return jsonify(streams)
        else:
            return jsonify([])
            
    except Exception as e:
        logger.error(f"Error getting streams: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        with get_db_session() as session:
            session.execute("SELECT 1")
        
        # Check system status
        if system:
            status = 'healthy'
        else:
            status = 'initializing'
        
        return jsonify({
            'status': status,
            'timestamp': time.time(),
            'version': '1.0.0'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500

if __name__ == '__main__':
    app.run(
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        debug=config.DEBUG
    )

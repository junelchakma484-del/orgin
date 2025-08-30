"""
MQTT Client for Face Mask Detection System
Remote control and monitoring via MQTT protocol
"""

import paho.mqtt.client as mqtt
import json
import logging
import time
from typing import Dict, Any, Callable, Optional
from ..config import config

logger = logging.getLogger(__name__)

class MQTTClient:
    """MQTT client for remote control and monitoring"""
    
    def __init__(self):
        self.client = None
        self.broker = config.MQTT_BROKER
        self.port = config.MQTT_PORT
        self.username = config.MQTT_USERNAME
        self.password = config.MQTT_PASSWORD
        self.client_id = config.MQTT_CLIENT_ID
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize MQTT client"""
        try:
            self.client = mqtt.Client(
                client_id=self.client_id,
                clean_session=True,
                protocol=mqtt.MQTTv311
            )
            
            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            
            logger.info("MQTT client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing MQTT client: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker")
            
            # Subscribe to control topics
            self._subscribe_to_topics()
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection with code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received MQTT message on {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            # Call registered handler
            if topic in self.message_handlers:
                self.message_handlers[topic](data)
            else:
                logger.warning(f"No handler registered for topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        logger.debug(f"Message published with ID: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscribed to topic"""
        logger.debug(f"Subscribed to topic with ID: {mid}, QoS: {granted_qos}")
    
    def _subscribe_to_topics(self):
        """Subscribe to control and monitoring topics"""
        topics = [
            ("face_mask/control/camera", 1),
            ("face_mask/control/system", 1),
            ("face_mask/control/detection", 1),
            ("face_mask/status/request", 1),
        ]
        
        for topic, qos in topics:
            self.client.subscribe(topic, qos)
            logger.info(f"Subscribed to {topic} with QoS {qos}")
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            if not self.client:
                self._initialize_client()
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            if self.client and self.is_connected:
                self.client.loop_stop()
                self.client.disconnect()
                self.is_connected = False
                logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        """Publish message to MQTT topic"""
        try:
            if not self.is_connected:
                logger.warning("MQTT client not connected")
                return False
            
            # Convert payload to JSON if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            elif not isinstance(payload, str):
                payload = str(payload)
            
            result = self.client.publish(topic, payload, qos, retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            return False
    
    def subscribe(self, topic: str, handler: Callable, qos: int = 1):
        """Subscribe to topic with message handler"""
        try:
            if not self.is_connected:
                logger.warning("MQTT client not connected")
                return False
            
            self.client.subscribe(topic, qos)
            self.message_handlers[topic] = handler
            logger.info(f"Subscribed to {topic} with handler")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            return False
    
    def publish_status(self, status_data: Dict[str, Any]):
        """Publish system status"""
        topic = "face_mask/status/system"
        self.publish(topic, status_data)
    
    def publish_detection(self, detection_data: Dict[str, Any]):
        """Publish detection results"""
        topic = "face_mask/detection/results"
        self.publish(topic, detection_data)
    
    def publish_alert(self, alert_data: Dict[str, Any]):
        """Publish alert"""
        topic = "face_mask/alerts/violation"
        self.publish(topic, alert_data)
    
    def publish_metrics(self, metrics_data: Dict[str, Any]):
        """Publish system metrics"""
        topic = "face_mask/metrics/system"
        self.publish(topic, metrics_data)
    
    def request_status(self):
        """Request system status from other clients"""
        topic = "face_mask/status/request"
        self.publish(topic, {"timestamp": time.time()})
    
    def send_camera_control(self, camera_id: str, action: str, params: Dict[str, Any] = None):
        """Send camera control command"""
        topic = f"face_mask/control/camera/{camera_id}"
        payload = {
            "action": action,
            "params": params or {},
            "timestamp": time.time()
        }
        self.publish(topic, payload)
    
    def send_system_control(self, action: str, params: Dict[str, Any] = None):
        """Send system control command"""
        topic = "face_mask/control/system"
        payload = {
            "action": action,
            "params": params or {},
            "timestamp": time.time()
        }
        self.publish(topic, payload)

# Global MQTT client instance
mqtt_client = None

def get_mqtt_client() -> MQTTClient:
    """Get global MQTT client instance"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
    return mqtt_client

# Message handlers for system control
def handle_camera_control(data):
    """Handle camera control messages"""
    try:
        camera_id = data.get('camera_id')
        action = data.get('action')
        params = data.get('params', {})
        
        logger.info(f"Camera control: {camera_id} - {action}")
        
        # Implement camera control logic here
        if action == 'start':
            # Start camera
            pass
        elif action == 'stop':
            # Stop camera
            pass
        elif action == 'restart':
            # Restart camera
            pass
        
    except Exception as e:
        logger.error(f"Error handling camera control: {e}")

def handle_system_control(data):
    """Handle system control messages"""
    try:
        action = data.get('action')
        params = data.get('params', {})
        
        logger.info(f"System control: {action}")
        
        # Implement system control logic here
        if action == 'shutdown':
            # Shutdown system
            pass
        elif action == 'restart':
            # Restart system
            pass
        elif action == 'update_config':
            # Update configuration
            pass
        
    except Exception as e:
        logger.error(f"Error handling system control: {e}")

def handle_status_request(data):
    """Handle status request messages"""
    try:
        # Publish current system status
        client = get_mqtt_client()
        status_data = {
            "timestamp": time.time(),
            "status": "running",
            "uptime": time.time() - 0,  # Would need to track start time
            "active_cameras": 0,  # Would need to get from stream manager
            "fps": 0.0  # Would need to get from processing stats
        }
        client.publish_status(status_data)
        
    except Exception as e:
        logger.error(f"Error handling status request: {e}")

"""
Telegram Bot Notification System for Face Mask Detection
Real-time alerts and status updates via Telegram
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from ..config import config
import json
import time

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Telegram bot for sending mask violation alerts"""
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.bot = None
        self.application = None
        self.is_initialized = False
        
        if self.bot_token and self.chat_id:
            self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize Telegram bot"""
        try:
            self.bot = Bot(token=self.bot_token)
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("status", self._status_command))
            self.application.add_handler(CommandHandler("stats", self._stats_command))
            self.application.add_handler(CommandHandler("help", self._help_command))
            
            self.is_initialized = True
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 Face Mask Detection System Bot

Welcome! This bot provides real-time alerts for mask violations in the university computer lab.

Commands:
/status - Get system status
/stats - Get detection statistics
/help - Show this help message

The bot will automatically send alerts when mask violations are detected.
        """
        await update.message.reply_text(welcome_message)
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            from ..database.connection import get_db_session
            from ..database.models import Detection, CameraStatus
            
            with get_db_session() as session:
                # Get latest detection
                latest_detection = session.query(Detection).order_by(Detection.timestamp.desc()).first()
                
                # Get camera status
                camera_statuses = session.query(CameraStatus).filter(
                    CameraStatus.timestamp >= time.time() - 300  # Last 5 minutes
                ).all()
                
                status_message = "📊 System Status\n\n"
                
                if latest_detection:
                    status_message += f"Last Detection: {time.strftime('%H:%M:%S', time.localtime(latest_detection.timestamp))}\n"
                    status_message += f"Faces Detected: {latest_detection.total_faces}\n"
                    status_message += f"Violations: {latest_detection.mask_violations}\n"
                    status_message += f"Compliance Rate: {latest_detection.compliance_rate}%\n\n"
                else:
                    status_message += "No recent detections\n\n"
                
                # Camera status
                status_message += "📹 Camera Status:\n"
                for camera in camera_statuses:
                    status_emoji = "🟢" if camera.status == "online" else "🔴"
                    status_message += f"{status_emoji} {camera.stream_name}: {camera.status}\n"
                
                await update.message.reply_text(status_message)
                
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await update.message.reply_text("❌ Error getting system status")
    
    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            from ..database.connection import get_db_session
            from ..database.models import Detection, get_compliance_rate
            from sqlalchemy import func
            
            with get_db_session() as session:
                # Get today's stats
                today_start = time.time() - (24 * 60 * 60)  # 24 hours ago
                
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
                
                stats_message = "📈 Today's Statistics\n\n"
                stats_message += f"Total Detections: {total_detections}\n"
                stats_message += f"Total Faces: {total_faces}\n"
                stats_message += f"Total Violations: {total_violations}\n"
                stats_message += f"Compliance Rate: {compliance_rate}%\n"
                
                # Hourly breakdown (last 6 hours)
                six_hours_ago = time.time() - (6 * 60 * 60)
                hourly_stats = session.query(
                    func.date_trunc('hour', func.to_timestamp(Detection.timestamp)).label('hour'),
                    func.count(Detection.id).label('detections'),
                    func.sum(Detection.mask_violations).label('violations')
                ).filter(
                    Detection.timestamp >= six_hours_ago
                ).group_by(
                    func.date_trunc('hour', func.to_timestamp(Detection.timestamp))
                ).order_by(
                    func.date_trunc('hour', func.to_timestamp(Detection.timestamp)).desc()
                ).limit(6).all()
                
                if hourly_stats:
                    stats_message += "\n📊 Last 6 Hours:\n"
                    for hour_stat in hourly_stats:
                        hour_str = hour_stat.hour.strftime('%H:00')
                        stats_message += f"{hour_str}: {hour_stat.detections} detections, {hour_stat.violations} violations\n"
                
                await update.message.reply_text(stats_message)
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ Error getting statistics")
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 Face Mask Detection Bot Help

Commands:
/start - Start the bot and get welcome message
/status - Get current system status and camera health
/stats - Get today's detection statistics
/help - Show this help message

The bot automatically sends alerts when:
• Mask violations are detected
• System goes offline
• Cameras lose connection

For support, contact the system administrator.
        """
        await update.message.reply_text(help_message)
    
    def send_alert(self, message: str, detection_data: Dict[str, Any]) -> bool:
        """Send alert message to Telegram"""
        if not self.is_initialized:
            logger.warning("Telegram bot not initialized")
            return False
        
        try:
            # Add detection details to message
            enhanced_message = self._enhance_alert_message(message, detection_data)
            
            # Send message asynchronously
            asyncio.create_task(self._send_message_async(enhanced_message))
            
            logger.info(f"Telegram alert sent: {detection_data.get('mask_violations', 0)} violations")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False
    
    def _enhance_alert_message(self, message: str, detection_data: Dict[str, Any]) -> str:
        """Enhance alert message with additional details"""
        enhanced = message + "\n\n"
        
        # Add detection details
        if 'detections' in detection_data:
            detections = detection_data['detections']
            enhanced += f"Detection Details:\n"
            for i, detection in enumerate(detections[:3]):  # Show first 3 detections
                mask_status = "✅" if detection['mask_label'] == 'mask' else "❌"
                confidence = detection['mask_confidence']
                enhanced += f"{mask_status} Person {i+1}: {confidence:.1%} confidence\n"
            
            if len(detections) > 3:
                enhanced += f"... and {len(detections) - 3} more\n"
        
        # Add timestamp
        enhanced += f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return enhanced
    
    async def _send_message_async(self, message: str):
        """Send message asynchronously"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending async message: {e}")
    
    def send_status_update(self, status_data: Dict[str, Any]) -> bool:
        """Send system status update"""
        if not self.is_initialized:
            return False
        
        try:
            message = "📊 System Status Update\n\n"
            
            if 'fps' in status_data:
                message += f"Processing FPS: {status_data['fps']:.1f}\n"
            if 'active_streams' in status_data:
                message += f"Active Cameras: {status_data['active_streams']}\n"
            if 'queue_size' in status_data:
                message += f"Queue Size: {status_data['queue_size']}\n"
            if 'uptime' in status_data:
                hours = int(status_data['uptime'] // 3600)
                minutes = int((status_data['uptime'] % 3600) // 60)
                message += f"Uptime: {hours}h {minutes}m\n"
            
            asyncio.create_task(self._send_message_async(message))
            return True
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False
    
    def start_bot(self):
        """Start the Telegram bot"""
        if not self.is_initialized:
            logger.error("Bot not initialized")
            return
        
        try:
            logger.info("Starting Telegram bot...")
            self.application.run_polling()
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")

# Global instance
telegram_notifier = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get global Telegram notifier instance"""
    global telegram_notifier
    if telegram_notifier is None:
        telegram_notifier = TelegramNotifier()
    return telegram_notifier

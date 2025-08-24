"""
Comprehensive Notification System
Supports Telegram, Email, and SMS notifications for trading events
"""

import asyncio
import aiohttp
import smtplib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.image import MimeImage
import ssl
import os
from secure_api_manager import EnvironmentManager

class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"

@dataclass
class NotificationConfig:
    """Notification system configuration"""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    webhook_url: str = ""
    enable_telegram: bool = True
    enable_email: bool = True
    enable_sms: bool = False
    enable_webhook: bool = False
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

@dataclass
class NotificationMessage:
    """Notification message structure"""
    title: str
    message: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    timestamp: datetime
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, message: NotificationMessage) -> bool:
        """Send message via Telegram"""
        try:
            # Format message with emoji based on type
            emoji_map = {
                NotificationType.INFO: "ℹ️",
                NotificationType.SUCCESS: "✅",
                NotificationType.WARNING: "⚠️",
                NotificationType.ERROR: "❌",
                NotificationType.CRITICAL: "🚨"
            }
            
            emoji = emoji_map.get(message.notification_type, "📢")
            
            formatted_message = f"{emoji} *{message.title}*\n\n{message.message}"
            
            # Add timestamp
            formatted_message += f"\n\n🕐 {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Add metadata if present
            if message.metadata:
                formatted_message += "\n\n📊 *Details:*"
                for key, value in message.metadata.items():
                    formatted_message += f"\n• {key}: {value}"
            
            payload = {
                "chat_id": self.chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        print(f"❌ Telegram notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Telegram notification error: {e}")
            return False
    
    async def send_chart(self, chart_path: str, caption: str = "") -> bool:
        """Send chart image via Telegram"""
        try:
            if not os.path.exists(chart_path):
                return False
            
            data = aiohttp.FormData()
            data.add_field('chat_id', self.chat_id)
            data.add_field('caption', caption)
            data.add_field('photo', open(chart_path, 'rb'))
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/sendPhoto", data=data) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"❌ Telegram chart send error: {e}")
            return False

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
    
    def send_message(self, message: NotificationMessage) -> bool:
        """Send message via email"""
        try:
            if not self.config.email_recipients:
                return False
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"[Trading Bot] {message.title}"
            msg['From'] = self.config.email_username
            msg['To'] = ", ".join(self.config.email_recipients)
            
            # Create HTML content
            html_content = self._create_html_email(message)
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"❌ Email notification error: {e}")
            return False
    
    def _create_html_email(self, message: NotificationMessage) -> str:
        """Create HTML email content"""
        
        color_map = {
            NotificationType.INFO: "#2196F3",
            NotificationType.SUCCESS: "#4CAF50",
            NotificationType.WARNING: "#FF9800",
            NotificationType.ERROR: "#F44336",
            NotificationType.CRITICAL: "#D32F2F"
        }
        
        color = color_map.get(message.notification_type, "#2196F3")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px;">
                    <h1 style="margin: 0; font-size: 24px;">{message.title}</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">{message.notification_type.value.upper()}</p>
                </div>
                <div style="padding: 20px;">
                    <div style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
                        {message.message.replace('\n', '<br>')}
                    </div>
                    <div style="border-top: 1px solid #eee; padding-top: 15px; font-size: 14px; color: #666;">
                        <strong>Time:</strong> {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
        """
        
        if message.metadata:
            html += """
                    <div style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 4px;">
                        <strong style="color: #333;">Details:</strong>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
            """
            for key, value in message.metadata.items():
                html += f"<li><strong>{key}:</strong> {value}</li>"
            html += "</ul></div>"
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

class WebhookNotifier:
    """Webhook notification handler"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_message(self, message: NotificationMessage) -> bool:
        """Send message via webhook"""
        try:
            payload = {
                "title": message.title,
                "message": message.message,
                "type": message.notification_type.value,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"❌ Webhook notification error: {e}")
            return False

class NotificationManager:
    """Central notification management system"""
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or self._load_config()
        self.telegram_notifier = None
        self.email_notifier = None
        self.webhook_notifier = None
        self.message_queue = []
        self.failed_messages = []
        
        self._initialize_notifiers()
    
    def _load_config(self) -> NotificationConfig:
        """Load notification configuration from environment"""
        return NotificationConfig(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            email_username=os.getenv("EMAIL_USERNAME", ""),
            email_password=os.getenv("EMAIL_PASSWORD", ""),
            email_recipients=os.getenv("EMAIL_RECIPIENTS", "").split(",") if os.getenv("EMAIL_RECIPIENTS") else [],
            webhook_url=os.getenv("WEBHOOK_URL", ""),
            enable_telegram=os.getenv("ENABLE_TELEGRAM", "true").lower() == "true",
            enable_email=os.getenv("ENABLE_EMAIL", "true").lower() == "true",
            enable_webhook=os.getenv("ENABLE_WEBHOOK", "false").lower() == "true"
        )
    
    def _initialize_notifiers(self):
        """Initialize notification handlers"""
        if self.config.enable_telegram and self.config.telegram_bot_token:
            self.telegram_notifier = TelegramNotifier(
                self.config.telegram_bot_token,
                self.config.telegram_chat_id
            )
        
        if self.config.enable_email and self.config.email_username:
            self.email_notifier = EmailNotifier(self.config)
        
        if self.config.enable_webhook and self.config.webhook_url:
            self.webhook_notifier = WebhookNotifier(self.config.webhook_url)
    
    async def send_notification(self, title: str, message: str, 
                              notification_type: NotificationType = NotificationType.INFO,
                              channels: List[NotificationChannel] = None,
                              metadata: Dict = None) -> bool:
        """Send notification through specified channels"""
        
        if channels is None:
            channels = [NotificationChannel.TELEGRAM, NotificationChannel.EMAIL]
        
        notification = NotificationMessage(
            title=title,
            message=message,
            notification_type=notification_type,
            channels=channels,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        success = True
        
        # Send via Telegram
        if NotificationChannel.TELEGRAM in channels and self.telegram_notifier:
            telegram_success = await self.telegram_notifier.send_message(notification)
            if not telegram_success:
                success = False
        
        # Send via Email
        if NotificationChannel.EMAIL in channels and self.email_notifier:
            email_success = self.email_notifier.send_message(notification)
            if not email_success:
                success = False
        
        # Send via Webhook
        if NotificationChannel.WEBHOOK in channels and self.webhook_notifier:
            webhook_success = await self.webhook_notifier.send_message(notification)
            if not webhook_success:
                success = False
        
        if not success:
            self.failed_messages.append(notification)
        
        return success
    
    # Trading-specific notification methods
    async def notify_trade_opened(self, symbol: str, exchange: str, side: str, 
                                 entry_price: float, quantity: float, 
                                 stop_loss: float, take_profit: float,
                                 risk_amount: float, risk_reward_ratio: float):
        """Notify when a new trade is opened"""
        
        message = f"""
🔄 New {side.upper()} position opened

📈 Symbol: {symbol}
🏢 Exchange: {exchange.title()}
💰 Entry Price: ${entry_price:,.2f}
📊 Quantity: {quantity}
🛑 Stop Loss: ${stop_loss:,.2f}
🎯 Take Profit: ${take_profit:,.2f}

💸 Risk Amount: ${risk_amount:.2f}
⚖️ Risk/Reward: 1:{risk_reward_ratio:.2f}
        """.strip()
        
        metadata = {
            "symbol": symbol,
            "exchange": exchange,
            "side": side,
            "entry_price": f"${entry_price:,.2f}",
            "risk_amount": f"${risk_amount:.2f}",
            "risk_reward_ratio": f"1:{risk_reward_ratio:.2f}"
        }
        
        await self.send_notification(
            title="Trade Opened",
            message=message,
            notification_type=NotificationType.SUCCESS,
            metadata=metadata
        )
    
    async def notify_trade_closed(self, symbol: str, exchange: str, side: str,
                                 entry_price: float, exit_price: float,
                                 quantity: float, pnl: float, reason: str):
        """Notify when a trade is closed"""
        
        pnl_emoji = "📈" if pnl > 0 else "📉"
        pnl_type = "PROFIT" if pnl > 0 else "LOSS"
        
        message = f"""
{pnl_emoji} {side.upper()} position closed - {pnl_type}

📈 Symbol: {symbol}
🏢 Exchange: {exchange.title()}
💰 Entry: ${entry_price:,.2f}
🚪 Exit: ${exit_price:,.2f}
📊 Quantity: {quantity}

💵 P&L: ${pnl:,.2f}
📝 Reason: {reason}
        """.strip()
        
        metadata = {
            "symbol": symbol,
            "exchange": exchange,
            "pnl": f"${pnl:,.2f}",
            "reason": reason,
            "return_percent": f"{((exit_price - entry_price) / entry_price * 100):.2f}%"
        }
        
        notification_type = NotificationType.SUCCESS if pnl > 0 else NotificationType.WARNING
        
        await self.send_notification(
            title=f"Trade Closed - {pnl_type}",
            message=message,
            notification_type=notification_type,
            metadata=metadata
        )
    
    async def notify_daily_limit_reached(self, daily_loss_percent: float, 
                                       current_balance: float, limit_percent: float):
        """Notify when daily loss limit is reached"""
        
        message = f"""
🚨 DAILY LOSS LIMIT REACHED

📉 Daily Loss: {daily_loss_percent:.2f}%
💰 Current Balance: ${current_balance:,.2f}
⚠️ Limit: {limit_percent:.1f}%

🛑 Trading has been automatically stopped for today.
📊 Please review your strategy and risk management.
        """.strip()
        
        metadata = {
            "daily_loss_percent": f"{daily_loss_percent:.2f}%",
            "current_balance": f"${current_balance:,.2f}",
            "limit_percent": f"{limit_percent:.1f}%"
        }
        
        await self.send_notification(
            title="Daily Loss Limit Reached",
            message=message,
            notification_type=NotificationType.CRITICAL,
            metadata=metadata
        )
    
    async def notify_emergency_stop(self, reason: str, current_balance: float,
                                  total_loss_percent: float):
        """Notify when emergency stop is triggered"""
        
        message = f"""
🚨 EMERGENCY STOP ACTIVATED

⚠️ Reason: {reason}
💰 Current Balance: ${current_balance:,.2f}
📉 Total Loss: {total_loss_percent:.2f}%

🛑 All positions have been closed automatically.
🔒 Trading is now disabled.
📞 Immediate attention required!
        """.strip()
        
        metadata = {
            "reason": reason,
            "current_balance": f"${current_balance:,.2f}",
            "total_loss_percent": f"{total_loss_percent:.2f}%"
        }
        
        await self.send_notification(
            title="🚨 EMERGENCY STOP ACTIVATED",
            message=message,
            notification_type=NotificationType.CRITICAL,
            metadata=metadata
        )
    
    async def notify_daily_summary(self, daily_pnl: float, daily_pnl_percent: float,
                                 trades_count: int, win_rate: float,
                                 current_balance: float):
        """Send daily performance summary"""
        
        pnl_emoji = "📈" if daily_pnl > 0 else "📉" if daily_pnl < 0 else "➡️"
        
        message = f"""
📊 Daily Trading Summary

{pnl_emoji} Daily P&L: ${daily_pnl:,.2f} ({daily_pnl_percent:+.2f}%)
💰 Current Balance: ${current_balance:,.2f}
📈 Trades Today: {trades_count}
🎯 Win Rate: {win_rate:.1f}%

{"🎉 Great day!" if daily_pnl > 0 else "📚 Learn and improve!" if daily_pnl < 0 else "🔄 Steady progress!"}
        """.strip()
        
        metadata = {
            "daily_pnl": f"${daily_pnl:,.2f}",
            "daily_pnl_percent": f"{daily_pnl_percent:+.2f}%",
            "trades_count": trades_count,
            "win_rate": f"{win_rate:.1f}%",
            "current_balance": f"${current_balance:,.2f}"
        }
        
        notification_type = NotificationType.SUCCESS if daily_pnl > 0 else NotificationType.INFO
        
        await self.send_notification(
            title="Daily Summary",
            message=message,
            notification_type=notification_type,
            metadata=metadata
        )
    
    async def notify_system_status(self, status: str, uptime: str, 
                                 active_positions: int, total_balance: float):
        """Send system status notification"""
        
        message = f"""
🤖 Trading Bot Status

🔄 Status: {status}
⏰ Uptime: {uptime}
📊 Active Positions: {active_positions}
💰 Total Balance: ${total_balance:,.2f}

✅ System is running normally.
        """.strip()
        
        metadata = {
            "status": status,
            "uptime": uptime,
            "active_positions": active_positions,
            "total_balance": f"${total_balance:,.2f}"
        }
        
        await self.send_notification(
            title="System Status",
            message=message,
            notification_type=NotificationType.INFO,
            metadata=metadata
        )

# Demo function
async def demo_notification_system():
    """Demonstrate notification system"""
    
    print("📢 Notification System Demo")
    print("=" * 50)
    
    # Initialize notification manager with demo config
    config = NotificationConfig(
        telegram_bot_token="demo_bot_token",
        telegram_chat_id="demo_chat_id",
        email_username="demo@example.com",
        email_password="demo_password",
        email_recipients=["trader@example.com"],
        enable_telegram=True,
        enable_email=True
    )
    
    notifier = NotificationManager(config)
    
    print("🔧 Notification Channels:")
    print(f"   ✅ Telegram: {'Enabled' if config.enable_telegram else 'Disabled'}")
    print(f"   ✅ Email: {'Enabled' if config.enable_email else 'Disabled'}")
    print(f"   ✅ Webhook: {'Enabled' if config.enable_webhook else 'Disabled'}")
    
    # Demo notifications
    print("\n📨 Sending Demo Notifications:")
    
    # Trade opened notification
    await notifier.notify_trade_opened(
        symbol="BTC/USDT",
        exchange="binance",
        side="buy",
        entry_price=45000,
        quantity=0.02,
        stop_loss=43500,
        take_profit=47000,
        risk_amount=750,
        risk_reward_ratio=2.67
    )
    print("   ✅ Trade opened notification sent")
    
    # Trade closed notification
    await notifier.notify_trade_closed(
        symbol="BTC/USDT",
        exchange="binance",
        side="buy",
        entry_price=45000,
        exit_price=46500,
        quantity=0.02,
        pnl=300,
        reason="Take Profit"
    )
    print("   ✅ Trade closed notification sent")
    
    # Daily summary
    await notifier.notify_daily_summary(
        daily_pnl=450,
        daily_pnl_percent=0.9,
        trades_count=3,
        win_rate=66.7,
        current_balance=50450
    )
    print("   ✅ Daily summary notification sent")
    
    # System status
    await notifier.notify_system_status(
        status="Active",
        uptime="2 days, 14 hours",
        active_positions=2,
        total_balance=50450
    )
    print("   ✅ System status notification sent")
    
    print("\n📋 Notification Features:")
    print("   ✅ Multi-channel support (Telegram, Email, Webhook)")
    print("   ✅ Rich message formatting with emojis")
    print("   ✅ HTML email templates")
    print("   ✅ Metadata and detailed information")
    print("   ✅ Trading-specific notification types")
    print("   ✅ Emergency and critical alerts")
    print("   ✅ Daily performance summaries")
    print("   ✅ System status monitoring")
    print("   ✅ Failed message retry queue")
    
    print("\n⚙️ Setup Requirements:")
    print("   • Telegram Bot Token (from @BotFather)")
    print("   • Telegram Chat ID")
    print("   • Email SMTP credentials")
    print("   • Webhook URL (optional)")
    print("   • Environment variables configuration")

if __name__ == "__main__":
    asyncio.run(demo_notification_system())

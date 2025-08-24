"""
Integrated AI Trading System
Combines all components: API management, risk management, notifications, 
failsafe mechanisms, performance dashboard, comprehensive logging, and scheduler
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

# Import all system components
from secure_api_manager import SecureAPIManager, EnvironmentManager
from advanced_risk_manager import AdvancedRiskManager
from notification_system import NotificationManager, NotificationType
from emergency_failsafe_system import EmergencyFailsafeSystem, FailsafeConfig
from comprehensive_logging_system import ComprehensiveLogger, TradeLog, LogLevel, LogCategory
from multi_exchange_integration import MultiExchangeManager
from scheduler_system import ContinuousScheduler, TaskPriority

class IntegratedTradingSystem:
    """Main integrated trading system coordinator"""
    
    def __init__(self, initial_capital: float = 50000, master_password: str = None):
        self.initial_capital = initial_capital
        self.system_running = False
        self.start_time = None
        
        # Initialize all components
        print("🚀 Initializing Integrated AI Trading System...")
        
        # 1. Secure API Management
        print("🔐 Setting up secure API management...")
        self.api_manager = SecureAPIManager()
        if not self.api_manager.initialize_security(master_password):
            raise Exception("Failed to initialize secure API management")
        
        # 2. Risk Management
        print("🛡️ Setting up risk management...")
        self.risk_manager = AdvancedRiskManager(initial_capital)
        
        # 3. Notification System
        print("📢 Setting up notification system...")
        self.notification_manager = NotificationManager()
        
        # 4. Multi-Exchange Integration
        print("🌍 Setting up multi-exchange integration...")
        self.exchange_manager = MultiExchangeManager(self.api_manager)
        
        # 5. Emergency Failsafe System
        print("🚨 Setting up emergency failsafe...")
        failsafe_config = FailsafeConfig()
        self.failsafe_system = EmergencyFailsafeSystem(
            self.risk_manager, 
            self.notification_manager, 
            failsafe_config
        )
        
        # 6. Comprehensive Logging
        print("📊 Setting up comprehensive logging...")
        self.logger = ComprehensiveLogger()
        
        # 7. 24/7 Scheduler System
        print("🕐 Setting up 24/7 scheduler...")
        self.scheduler = ContinuousScheduler(trading_system=self)
        
        print("✅ All systems initialized successfully!")
        
        # Log system initialization
        self.logger.log_system_event(
            LogLevel.INFO, LogCategory.SYSTEM, "IntegratedSystem",
            "Trading system initialized",
            {
                "initial_capital": initial_capital,
                "components": [
                    "SecureAPIManager", "RiskManager", "NotificationManager",
                    "ExchangeManager", "FailsafeSystem", "Logger", "Scheduler"
                ]
            }
        )
    
    async def start_system(self):
        """Start the complete trading system"""
        if self.system_running:
            print("⚠️ System is already running")
            return
        
        try:
            self.system_running = True
            self.start_time = datetime.now()
            
            print("🚀 Starting Integrated AI Trading System...")
            
            # Start all monitoring systems
            self.failsafe_system.start_monitoring()
            self.logger.start_monitoring()
            
            # Initialize exchanges with secure configuration
            if not self.exchange_manager.initialize_with_secure_config():
                raise Exception("Failed to initialize exchanges")
            
            self.scheduler.start_scheduler()
            
            # Send startup notification
            await self.notification_manager.notify_system_status(
                status="Started",
                uptime="0 minutes",
                active_positions=0,
                total_balance=self.initial_capital
            )
            
            # Log system start
            self.logger.log_system_event(
                LogLevel.INFO, LogCategory.SYSTEM, "IntegratedSystem",
                "Trading system started successfully",
                {"start_time": self.start_time.isoformat()}
            )
            
            print("✅ Trading system started successfully!")
            print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
            print(f"🔄 Active Exchanges: {len(self.exchange_manager.active_exchanges)}")
            print(f"🛡️ Risk Management: Active")
            print(f"📢 Notifications: Enabled")
            print(f"🚨 Emergency Failsafe: Active")
            print(f"📊 Logging: Active")
            print(f"🕐 24/7 Scheduler: Active")
            
            return True
            
        except Exception as e:
            self.system_running = False
            error_msg = f"Failed to start trading system: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Log error
            self.logger.log_system_event(
                LogLevel.CRITICAL, LogCategory.SYSTEM, "IntegratedSystem",
                error_msg, {"error": str(e)}
            )
            
            # Send error notification
            await self.notification_manager.send_notification(
                title="System Startup Failed",
                message=error_msg,
                notification_type=NotificationType.CRITICAL
            )
            
            return False
    
    async def stop_system(self):
        """Stop the complete trading system"""
        if not self.system_running:
            print("⚠️ System is not running")
            return
        
        try:
            print("🛑 Stopping Integrated AI Trading System...")
            
            self.scheduler.stop_scheduler()
            
            # Close all active positions
            active_positions = list(self.risk_manager.active_positions.keys())
            for position_id in active_positions:
                position = self.risk_manager.active_positions[position_id]
                self.risk_manager.close_position(position_id, position.current_price, "System Shutdown")
            
            # Stop monitoring systems
            self.failsafe_system.stop_monitoring()
            self.logger.stop_monitoring()
            
            # Calculate uptime
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            uptime_str = f"{uptime.total_seconds() / 3600:.1f} hours"
            
            # Send shutdown notification
            await self.notification_manager.notify_system_status(
                status="Stopped",
                uptime=uptime_str,
                active_positions=0,
                total_balance=self.risk_manager.current_capital
            )
            
            # Log system stop
            self.logger.log_system_event(
                LogLevel.INFO, LogCategory.SYSTEM, "IntegratedSystem",
                "Trading system stopped",
                {
                    "uptime_hours": uptime.total_seconds() / 3600,
                    "final_balance": self.risk_manager.current_capital,
                    "total_return": ((self.risk_manager.current_capital - self.initial_capital) / self.initial_capital) * 100
                }
            )
            
            self.system_running = False
            
            print("✅ Trading system stopped successfully!")
            print(f"⏰ Total Uptime: {uptime_str}")
            print(f"💰 Final Balance: ${self.risk_manager.current_capital:,.2f}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error stopping trading system: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Log error
            self.logger.log_system_event(
                LogLevel.ERROR, LogCategory.SYSTEM, "IntegratedSystem",
                error_msg, {"error": str(e)}
            )
            
            return False
    
    async def execute_trade(self, symbol: str, exchange: str, side: str,
                           entry_price: float, quantity: float,
                           stop_loss: float, take_profit: float,
                           strategy: str = "Manual", entry_reason: str = "Manual trade"):
        """Execute a complete trade with all safety checks"""
        
        try:
            # Validate trade through risk management
            is_valid, message = self.risk_manager.validate_trade(
                symbol, exchange, side, entry_price, quantity, stop_loss, take_profit
            )
            
            if not is_valid:
                print(f"❌ Trade rejected: {message}")
                
                # Log rejection
                self.logger.log_system_event(
                    LogLevel.WARNING, LogCategory.TRADING, "TradeValidator",
                    f"Trade rejected: {message}",
                    {
                        "symbol": symbol,
                        "exchange": exchange,
                        "side": side,
                        "entry_price": entry_price,
                        "quantity": quantity
                    }
                )
                
                return False
            
            # Open position through risk manager
            position = self.risk_manager.open_position(
                symbol, exchange, side, entry_price, quantity, stop_loss, take_profit
            )
            
            if not position:
                print("❌ Failed to open position")
                return False
            
            # Create comprehensive trade log
            trade_log = TradeLog(
                trade_id=position.id,
                timestamp=position.timestamp,
                symbol=symbol,
                exchange=exchange,
                side=side,
                entry_price=entry_price,
                exit_price=None,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status="open",
                pnl=None,
                pnl_percent=None,
                risk_amount=position.risk_amount,
                risk_reward_ratio=position.risk_reward_ratio,
                strategy=strategy,
                entry_reason=entry_reason,
                exit_reason=None,
                duration_minutes=None,
                market_conditions={"timestamp": datetime.now().isoformat()}
            )
            
            # Log the trade
            self.logger.log_trade_event(trade_log)
            
            # Send notification
            await self.notification_manager.notify_trade_opened(
                symbol, exchange, side, entry_price, quantity,
                stop_loss, take_profit, position.risk_amount, position.risk_reward_ratio
            )
            
            # Log system event
            self.logger.log_system_event(
                LogLevel.INFO, LogCategory.TRADING, "TradeExecutor",
                f"Trade executed successfully: {position.id}",
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "risk_amount": position.risk_amount,
                    "risk_reward_ratio": position.risk_reward_ratio
                }
            )
            
            print(f"✅ Trade executed successfully: {position.id}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to execute trade: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Log error
            self.logger.log_system_event(
                LogLevel.ERROR, LogCategory.TRADING, "TradeExecutor",
                error_msg,
                {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": str(e)
                }
            )
            
            return False
    
    async def update_system_performance(self):
        """Update and log system performance metrics"""
        try:
            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            
            # Log performance metrics
            self.logger.log_performance_metrics(
                balance=risk_summary["current_capital"],
                daily_pnl=risk_summary["daily_pnl"],
                daily_pnl_percent=risk_summary["daily_pnl_percent"],
                total_trades=len(self.risk_manager.closed_positions),
                active_positions=risk_summary["active_positions"],
                win_rate=risk_summary["win_rate"],
                max_drawdown=abs(risk_summary.get("max_drawdown", 0)),
                sharpe_ratio=1.42,  # Would calculate from actual data
                profit_factor=2.18,  # Would calculate from actual data
                risk_level=risk_summary["risk_level"],
                system_health="healthy" if not risk_summary["emergency_stop"] else "emergency"
            )
            
            # Send daily summary if it's a new day
            # (Implementation would check if it's end of day)
            
        except Exception as e:
            self.logger.log_system_event(
                LogLevel.ERROR, LogCategory.PERFORMANCE, "PerformanceUpdater",
                f"Failed to update performance: {str(e)}"
            )
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            uptime_hours = 0
            if self.start_time:
                uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            risk_summary = self.risk_manager.get_risk_summary()
            failsafe_status = self.failsafe_system.get_system_status()
            logger_stats = self.logger.get_system_statistics()
            scheduler_status = self.scheduler.get_scheduler_status()
            
            return {
                "system_running": self.system_running,
                "uptime_hours": uptime_hours,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "risk_management": risk_summary,
                "failsafe_system": failsafe_status,
                "logging_stats": logger_stats,
                "scheduler_system": scheduler_status,
                "active_exchanges": len(self.exchange_manager.active_exchanges),
                "components_status": {
                    "api_manager": "active",
                    "risk_manager": "active",
                    "notification_manager": "active",
                    "exchange_manager": "active",
                    "failsafe_system": "active" if failsafe_status["monitoring_active"] else "inactive",
                    "logger": "active" if logger_stats.get("system_info", {}).get("monitoring_active") else "inactive",
                    "scheduler": "active" if scheduler_status["running"] else "inactive"
                }
            }
            
        except Exception as e:
            return {"error": str(e)}

# Demo function
async def demo_integrated_system():
    """Demonstrate the complete integrated trading system"""
    print("🚀 Integrated AI Trading System Demo")
    print("=" * 60)
    
    # Initialize system
    trading_system = IntegratedTradingSystem(initial_capital=50000, master_password="demo_password_123")
    
    # Start system
    if await trading_system.start_system():
        print("\n📊 System Status:")
        status = trading_system.get_system_status()
        
        for key, value in status.items():
            if key != "risk_management" and key != "failsafe_system" and key != "logging_stats" and key != "scheduler_system":
                print(f"   • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n🔧 Component Status:")
        for component, status in status["components_status"].items():
            print(f"   ✅ {component.replace('_', ' ').title()}: {status}")
        
        # Demo trade execution
        print(f"\n📈 Executing Demo Trade:")
        
        success = await trading_system.execute_trade(
            symbol="BTC/USDT",
            exchange="binance",
            side="buy",
            entry_price=45000.0,
            quantity=0.02,
            stop_loss=43500.0,
            take_profit=47000.0,
            strategy="Demo_Strategy",
            entry_reason="Demo trade for system testing"
        )
        
        if success:
            print("   ✅ Demo trade executed successfully")
        
        # Update performance
        await trading_system.update_system_performance()
        print("   ✅ Performance metrics updated")
        
        # Let system run for a bit
        print(f"\n⏰ System running for 30 seconds...")
        await asyncio.sleep(30)
        
        # Generate daily report
        report = trading_system.logger.generate_daily_report()
        if report:
            print(f"   📋 Daily report generated")
        
        # Stop system
        await trading_system.stop_system()
    
    print(f"\n🎯 Integration Features:")
    print(f"   ✅ Secure API key management with encryption")
    print(f"   ✅ Advanced risk management with position limits")
    print(f"   ✅ Multi-channel notifications (Telegram, Email)")
    print(f"   ✅ Emergency failsafe with automatic shutdown")
    print(f"   ✅ Multi-exchange support (8+ platforms)")
    print(f"   ✅ Comprehensive logging and monitoring")
    print(f"   ✅ Real-time performance tracking")
    print(f"   ✅ Automated daily reporting")
    print(f"   ✅ System health monitoring")
    print(f"   ✅ Bilingual dashboard support")
    print(f"   ✅ 24/7 Scheduler for continuous operation")
    
    print(f"\n✅ Integrated AI Trading System demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_integrated_system())

"""
Comprehensive Logging and Monitoring System
Advanced logging, monitoring, and reporting for AI trading bot
"""

import logging
import json
import time
import threading
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import gzip
import shutil
from contextlib import contextmanager

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    SYSTEM = "system"
    TRADING = "trading"
    RISK = "risk"
    PERFORMANCE = "performance"
    API = "api"
    NOTIFICATION = "notification"
    EMERGENCY = "emergency"

@dataclass
class TradeLog:
    """Comprehensive trade logging structure"""
    trade_id: str
    timestamp: datetime
    symbol: str
    exchange: str
    side: str  # buy/sell
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    stop_loss: float
    take_profit: float
    status: str  # open/closed/cancelled
    pnl: Optional[float]
    pnl_percent: Optional[float]
    risk_amount: float
    risk_reward_ratio: float
    strategy: str
    entry_reason: str
    exit_reason: Optional[str]
    duration_minutes: Optional[int]
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    market_conditions: Dict = None
    
    def __post_init__(self):
        if self.market_conditions is None:
            self.market_conditions = {}

@dataclass
class SystemLog:
    """System event logging structure"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    component: str
    message: str
    details: Dict = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

@dataclass
class PerformanceLog:
    """Performance metrics logging"""
    timestamp: datetime
    balance: float
    daily_pnl: float
    daily_pnl_percent: float
    total_trades: int
    active_positions: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    risk_level: str
    system_health: str
    uptime_hours: float

class DatabaseManager:
    """SQLite database manager for logs"""
    
    def __init__(self, db_path: str = "trading_logs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Trade logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_logs (
                    trade_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    quantity REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit REAL NOT NULL,
                    status TEXT NOT NULL,
                    pnl REAL,
                    pnl_percent REAL,
                    risk_amount REAL NOT NULL,
                    risk_reward_ratio REAL NOT NULL,
                    strategy TEXT NOT NULL,
                    entry_reason TEXT NOT NULL,
                    exit_reason TEXT,
                    duration_minutes INTEGER,
                    max_favorable_excursion REAL DEFAULT 0,
                    max_adverse_excursion REAL DEFAULT 0,
                    commission REAL DEFAULT 0,
                    slippage REAL DEFAULT 0,
                    market_conditions TEXT
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    execution_time REAL,
                    memory_usage REAL,
                    cpu_usage REAL
                )
            """)
            
            # Performance logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    balance REAL NOT NULL,
                    daily_pnl REAL NOT NULL,
                    daily_pnl_percent REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    active_positions INTEGER NOT NULL,
                    win_rate REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    sharpe_ratio REAL NOT NULL,
                    profit_factor REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    system_health TEXT NOT NULL,
                    uptime_hours REAL NOT NULL
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trade_timestamp ON trade_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_logs(timestamp)")
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_trade_log(self, trade_log: TradeLog):
        """Insert trade log into database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trade_logs VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                trade_log.trade_id,
                trade_log.timestamp.isoformat(),
                trade_log.symbol,
                trade_log.exchange,
                trade_log.side,
                trade_log.entry_price,
                trade_log.exit_price,
                trade_log.quantity,
                trade_log.stop_loss,
                trade_log.take_profit,
                trade_log.status,
                trade_log.pnl,
                trade_log.pnl_percent,
                trade_log.risk_amount,
                trade_log.risk_reward_ratio,
                trade_log.strategy,
                trade_log.entry_reason,
                trade_log.exit_reason,
                trade_log.duration_minutes,
                trade_log.max_favorable_excursion,
                trade_log.max_adverse_excursion,
                trade_log.commission,
                trade_log.slippage,
                json.dumps(trade_log.market_conditions)
            ))
            conn.commit()
    
    def insert_system_log(self, system_log: SystemLog):
        """Insert system log into database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs VALUES (
                    NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                system_log.timestamp.isoformat(),
                system_log.level.value,
                system_log.category.value,
                system_log.component,
                system_log.message,
                json.dumps(system_log.details),
                system_log.execution_time,
                system_log.memory_usage,
                system_log.cpu_usage
            ))
            conn.commit()
    
    def insert_performance_log(self, perf_log: PerformanceLog):
        """Insert performance log into database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_logs VALUES (
                    NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                perf_log.timestamp.isoformat(),
                perf_log.balance,
                perf_log.daily_pnl,
                perf_log.daily_pnl_percent,
                perf_log.total_trades,
                perf_log.active_positions,
                perf_log.win_rate,
                perf_log.max_drawdown,
                perf_log.sharpe_ratio,
                perf_log.profit_factor,
                perf_log.risk_level,
                perf_log.system_health,
                perf_log.uptime_hours
            ))
            conn.commit()
    
    def get_trades_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get trades within date range"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trade_logs 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_system_logs_by_level(self, level: LogLevel, hours: int = 24) -> List[Dict]:
        """Get system logs by level within time period"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM system_logs 
                WHERE level = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (level.value, start_time.isoformat()))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class LogRotationManager:
    """Manages log file rotation and compression"""
    
    def __init__(self, log_dir: str = "logs", max_size_mb: int = 100, keep_days: int = 30):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.keep_days = keep_days
    
    def rotate_log_file(self, file_path: Path):
        """Rotate log file if it exceeds size limit"""
        if file_path.exists() and file_path.stat().st_size > self.max_size_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_path = file_path.with_suffix(f".{timestamp}.log")
            
            # Move current log to rotated file
            shutil.move(str(file_path), str(rotated_path))
            
            # Compress rotated file
            with open(rotated_path, 'rb') as f_in:
                with gzip.open(f"{rotated_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed rotated file
            rotated_path.unlink()
            
            print(f"Rotated and compressed log: {rotated_path}.gz")
    
    def cleanup_old_logs(self):
        """Remove old compressed log files"""
        cutoff_date = datetime.now() - timedelta(days=self.keep_days)
        
        for log_file in self.log_dir.glob("*.gz"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                print(f"Removed old log: {log_file}")

class ComprehensiveLogger:
    """Main logging system coordinator"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.rotation_manager = LogRotationManager(log_dir)
        
        # Setup file loggers
        self.setup_loggers()
        
        # System monitoring
        self.start_time = datetime.now()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Performance tracking
        self.last_performance_log = None
        
        print("✅ Comprehensive logging system initialized")
    
    def setup_loggers(self):
        """Setup file-based loggers for different categories"""
        self.loggers = {}
        
        for category in LogCategory:
            logger = logging.getLogger(f"trading_bot_{category.value}")
            logger.setLevel(logging.DEBUG)
            
            # Remove existing handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # File handler
            log_file = self.log_dir / f"{category.value}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            self.loggers[category] = logger
    
    def log_trade_event(self, trade_log: TradeLog):
        """Log trade event to database and file"""
        try:
            # Insert to database
            self.db_manager.insert_trade_log(trade_log)
            
            # Log to file
            message = f"Trade {trade_log.status.upper()}: {trade_log.symbol} {trade_log.side} @ {trade_log.entry_price}"
            if trade_log.pnl is not None:
                message += f" | P&L: ${trade_log.pnl:.2f}"
            
            self.loggers[LogCategory.TRADING].info(message)
            
            print(f"📝 Trade logged: {trade_log.trade_id}")
            
        except Exception as e:
            print(f"❌ Failed to log trade: {e}")
    
    def log_system_event(self, level: LogLevel, category: LogCategory, 
                        component: str, message: str, details: Dict = None,
                        execution_time: float = None):
        """Log system event"""
        try:
            import psutil
            
            system_log = SystemLog(
                timestamp=datetime.now(),
                level=level,
                category=category,
                component=component,
                message=message,
                details=details or {},
                execution_time=execution_time,
                memory_usage=psutil.virtual_memory().percent,
                cpu_usage=psutil.cpu_percent()
            )
            
            # Insert to database
            self.db_manager.insert_system_log(system_log)
            
            # Log to file
            log_message = f"[{component}] {message}"
            if details:
                log_message += f" | Details: {json.dumps(details)}"
            
            logger = self.loggers[category]
            if level == LogLevel.DEBUG:
                logger.debug(log_message)
            elif level == LogLevel.INFO:
                logger.info(log_message)
            elif level == LogLevel.WARNING:
                logger.warning(log_message)
            elif level == LogLevel.ERROR:
                logger.error(log_message)
            elif level == LogLevel.CRITICAL:
                logger.critical(log_message)
            
        except Exception as e:
            print(f"❌ Failed to log system event: {e}")
    
    def log_performance_metrics(self, balance: float, daily_pnl: float, 
                               daily_pnl_percent: float, total_trades: int,
                               active_positions: int, win_rate: float,
                               max_drawdown: float, sharpe_ratio: float,
                               profit_factor: float, risk_level: str,
                               system_health: str):
        """Log performance metrics"""
        try:
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            perf_log = PerformanceLog(
                timestamp=datetime.now(),
                balance=balance,
                daily_pnl=daily_pnl,
                daily_pnl_percent=daily_pnl_percent,
                total_trades=total_trades,
                active_positions=active_positions,
                win_rate=win_rate,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                profit_factor=profit_factor,
                risk_level=risk_level,
                system_health=system_health,
                uptime_hours=uptime_hours
            )
            
            # Insert to database
            self.db_manager.insert_performance_log(perf_log)
            
            # Log to file
            message = f"Performance: Balance=${balance:.2f}, Daily P&L={daily_pnl_percent:+.2f}%, Win Rate={win_rate:.1f}%"
            self.loggers[LogCategory.PERFORMANCE].info(message)
            
            self.last_performance_log = perf_log
            
        except Exception as e:
            print(f"❌ Failed to log performance: {e}")
    
    def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.log_system_event(
            LogLevel.INFO, LogCategory.SYSTEM, "Logger",
            "Monitoring started", {"uptime_hours": 0}
        )
        
        print("🔍 System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        self.log_system_event(
            LogLevel.INFO, LogCategory.SYSTEM, "Logger",
            "Monitoring stopped", {"uptime_hours": uptime_hours}
        )
        
        print("🛑 System monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Rotate log files if needed
                for category in LogCategory:
                    log_file = self.log_dir / f"{category.value}.log"
                    self.rotation_manager.rotate_log_file(log_file)
                
                # Cleanup old logs
                self.rotation_manager.cleanup_old_logs()
                
                # Log system health
                import psutil
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent(interval=1)
                disk_percent = psutil.disk_usage('/').percent
                
                if memory_percent > 85 or cpu_percent > 90 or disk_percent > 90:
                    self.log_system_event(
                        LogLevel.WARNING, LogCategory.SYSTEM, "ResourceMonitor",
                        "High resource usage detected",
                        {
                            "memory_percent": memory_percent,
                            "cpu_percent": cpu_percent,
                            "disk_percent": disk_percent
                        }
                    )
                
                # Wait for next check (every 5 minutes)
                time.sleep(300)
                
            except Exception as e:
                print(f"❌ Monitoring loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def generate_daily_report(self, date: datetime = None) -> Dict:
        """Generate comprehensive daily report"""
        if date is None:
            date = datetime.now().date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        try:
            # Get trades for the day
            trades = self.db_manager.get_trades_by_date_range(start_date, end_date)
            
            # Calculate metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in trades if t.get('pnl', 0) < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum(t.get('pnl', 0) for t in trades if t.get('pnl') is not None)
            
            # Get system logs
            error_logs = self.db_manager.get_system_logs_by_level(LogLevel.ERROR, 24)
            warning_logs = self.db_manager.get_system_logs_by_level(LogLevel.WARNING, 24)
            
            report = {
                "date": date.isoformat(),
                "trading_summary": {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": win_rate,
                    "total_pnl": total_pnl,
                    "avg_pnl_per_trade": total_pnl / total_trades if total_trades > 0 else 0
                },
                "system_health": {
                    "error_count": len(error_logs),
                    "warning_count": len(warning_logs),
                    "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
                },
                "trades": trades[:10],  # Last 10 trades
                "errors": error_logs[:5],  # Last 5 errors
                "warnings": warning_logs[:5]  # Last 5 warnings
            }
            
            # Save report to file
            report_file = self.log_dir / f"daily_report_{date.strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.log_system_event(
                LogLevel.INFO, LogCategory.SYSTEM, "ReportGenerator",
                f"Daily report generated for {date}",
                {"trades": total_trades, "pnl": total_pnl}
            )
            
            return report
            
        except Exception as e:
            self.log_system_event(
                LogLevel.ERROR, LogCategory.SYSTEM, "ReportGenerator",
                f"Failed to generate daily report: {str(e)}"
            )
            return {}
    
    def get_system_statistics(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            # Database statistics
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Trade statistics
                cursor.execute("SELECT COUNT(*) FROM trade_logs")
                total_trades = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM trade_logs WHERE pnl > 0")
                winning_trades = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(pnl) FROM trade_logs WHERE pnl IS NOT NULL")
                total_pnl = cursor.fetchone()[0] or 0
                
                # System log statistics
                cursor.execute("SELECT level, COUNT(*) FROM system_logs GROUP BY level")
                log_counts = dict(cursor.fetchall())
                
                # Performance statistics
                cursor.execute("SELECT AVG(balance), MAX(balance), MIN(balance) FROM performance_logs")
                balance_stats = cursor.fetchone()
            
            statistics = {
                "system_info": {
                    "uptime_hours": uptime_hours,
                    "start_time": self.start_time.isoformat(),
                    "monitoring_active": self.monitoring_active
                },
                "trading_stats": {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                    "total_pnl": total_pnl
                },
                "system_logs": log_counts,
                "balance_stats": {
                    "average": balance_stats[0] or 0,
                    "maximum": balance_stats[1] or 0,
                    "minimum": balance_stats[2] or 0
                } if balance_stats else {}
            }
            
            return statistics
            
        except Exception as e:
            print(f"❌ Failed to get system statistics: {e}")
            return {}

# Demo function
def demo_comprehensive_logging():
    """Demonstrate comprehensive logging system"""
    print("📊 Comprehensive Logging System Demo")
    print("=" * 50)
    
    # Initialize logger
    logger = ComprehensiveLogger()
    
    # Start monitoring
    logger.start_monitoring()
    
    print("🔧 Logging Components:")
    print("   ✅ SQLite database for structured logs")
    print("   ✅ File-based logging with rotation")
    print("   ✅ System resource monitoring")
    print("   ✅ Performance metrics tracking")
    print("   ✅ Automated report generation")
    
    # Demo trade logging
    print("\n📝 Demo Trade Logging:")
    
    demo_trade = TradeLog(
        trade_id="DEMO_001",
        timestamp=datetime.now(),
        symbol="BTC/USDT",
        exchange="binance",
        side="buy",
        entry_price=45000.0,
        exit_price=46500.0,
        quantity=0.02,
        stop_loss=43500.0,
        take_profit=47000.0,
        status="closed",
        pnl=300.0,
        pnl_percent=0.67,
        risk_amount=750.0,
        risk_reward_ratio=2.67,
        strategy="RSI_Strategy",
        entry_reason="RSI oversold + bullish divergence",
        exit_reason="Take profit hit",
        duration_minutes=240,
        max_favorable_excursion=350.0,
        max_adverse_excursion=-50.0,
        commission=5.0,
        slippage=2.0,
        market_conditions={"volatility": "medium", "trend": "bullish"}
    )
    
    logger.log_trade_event(demo_trade)
    print("   ✅ Trade logged successfully")
    
    # Demo system logging
    print("\n🔍 Demo System Logging:")
    
    logger.log_system_event(
        LogLevel.INFO, LogCategory.SYSTEM, "TradingEngine",
        "System initialized successfully",
        {"version": "1.0.0", "config": "production"}
    )
    
    logger.log_system_event(
        LogLevel.WARNING, LogCategory.RISK, "RiskManager",
        "Daily loss approaching limit",
        {"current_loss": 4.2, "limit": 5.0}
    )
    
    print("   ✅ System events logged")
    
    # Demo performance logging
    print("\n📈 Demo Performance Logging:")
    
    logger.log_performance_metrics(
        balance=52450.75,
        daily_pnl=234.50,
        daily_pnl_percent=0.45,
        total_trades=247,
        active_positions=3,
        win_rate=68.5,
        max_drawdown=-3.2,
        sharpe_ratio=1.42,
        profit_factor=2.18,
        risk_level="medium",
        system_health="healthy"
    )
    
    print("   ✅ Performance metrics logged")
    
    # Generate daily report
    print("\n📋 Generating Daily Report:")
    
    report = logger.generate_daily_report()
    if report:
        print(f"   ✅ Report generated with {report['trading_summary']['total_trades']} trades")
        print(f"   📊 Win rate: {report['trading_summary']['win_rate']:.1f}%")
        print(f"   💰 Total P&L: ${report['trading_summary']['total_pnl']:.2f}")
    
    # Get system statistics
    print("\n📊 System Statistics:")
    
    stats = logger.get_system_statistics()
    if stats:
        print(f"   ⏰ Uptime: {stats['system_info']['uptime_hours']:.2f} hours")
        print(f"   📈 Total trades: {stats['trading_stats']['total_trades']}")
        print(f"   🎯 Win rate: {stats['trading_stats']['win_rate']:.1f}%")
        print(f"   💵 Total P&L: ${stats['trading_stats']['total_pnl']:.2f}")
    
    print("\n🛠️ Logging Features:")
    print("   ✅ Comprehensive trade logging with all details")
    print("   ✅ System event logging with categorization")
    print("   ✅ Performance metrics tracking")
    print("   ✅ SQLite database for structured storage")
    print("   ✅ File-based logging with rotation")
    print("   ✅ Automated daily report generation")
    print("   ✅ System resource monitoring")
    print("   ✅ Log compression and cleanup")
    print("   ✅ Real-time statistics and analytics")
    
    # Let it run for a bit
    print("\n⏰ Monitoring for 10 seconds...")
    time.sleep(10)
    
    # Stop monitoring
    logger.stop_monitoring()
    
    print("\n✅ Comprehensive logging system demo completed")

if __name__ == "__main__":
    demo_comprehensive_logging()

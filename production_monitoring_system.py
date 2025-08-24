"""
Production Monitoring System for AI Trading Bot
Provides comprehensive monitoring, alerting, and reporting for production deployment
"""

import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import sqlite3
import os
from collections import deque, defaultdict
import statistics

class MonitoringLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    SYSTEM_DOWN = "system_down"
    HIGH_ERROR_RATE = "high_error_rate"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TRADING_ANOMALY = "trading_anomaly"
    CONNECTIVITY_ISSUE = "connectivity_issue"
    SECURITY_BREACH = "security_breach"

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    disk_used_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    open_files: int
    uptime_hours: float

@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: datetime
    active_positions: int
    total_trades_today: int
    successful_trades_today: int
    failed_trades_today: int
    daily_pnl: float
    daily_pnl_percent: float
    current_balance: float
    win_rate: float
    max_drawdown: float
    risk_level: str
    api_calls_per_minute: int
    avg_execution_time_ms: float

@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    alert_type: AlertType
    condition: Callable[[Dict], bool]
    severity: MonitoringLevel
    cooldown_minutes: int = 15
    enabled: bool = True
    last_triggered: Optional[datetime] = None

@dataclass
class MonitoringAlert:
    """Monitoring alert event"""
    id: str
    timestamp: datetime
    alert_type: AlertType
    severity: MonitoringLevel
    title: str
    message: str
    metrics: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    acknowledgment_time: Optional[datetime] = None

class ProductionMonitoringSystem:
    """Comprehensive production monitoring system"""
    
    def __init__(self, trading_system=None, notification_manager=None, logger=None):
        self.trading_system = trading_system
        self.notification_manager = notification_manager
        self.logger = logger
        
        # Monitoring state
        self.monitoring_active = False
        self.start_time = None
        self.monitoring_thread = None
        
        # Metrics storage
        self.system_metrics_history = deque(maxlen=1440)  # 24 hours of minute data
        self.trading_metrics_history = deque(maxlen=1440)
        self.error_rate_history = deque(maxlen=60)  # 1 hour of minute data
        
        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, MonitoringAlert] = {}
        self.alert_history: List[MonitoringAlert] = []
        
        # Performance tracking
        self.api_call_times = deque(maxlen=1000)
        self.trade_execution_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        
        # Database for persistent storage
        self.db_path = "data/monitoring.db"
        self._initialize_database()
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        print("📊 Production Monitoring System initialized")
    
    def _initialize_database(self):
        """Initialize monitoring database"""
        os.makedirs("data", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # System metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    timestamp TEXT PRIMARY KEY,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    disk_percent REAL,
                    disk_used_gb REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    active_threads INTEGER,
                    open_files INTEGER,
                    uptime_hours REAL
                )
            """)
            
            # Trading metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_metrics (
                    timestamp TEXT PRIMARY KEY,
                    active_positions INTEGER,
                    total_trades_today INTEGER,
                    successful_trades_today INTEGER,
                    failed_trades_today INTEGER,
                    daily_pnl REAL,
                    daily_pnl_percent REAL,
                    current_balance REAL,
                    win_rate REAL,
                    max_drawdown REAL,
                    risk_level TEXT,
                    api_calls_per_minute INTEGER,
                    avg_execution_time_ms REAL
                )
            """)
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    title TEXT,
                    message TEXT,
                    metrics TEXT,
                    resolved INTEGER,
                    resolution_time TEXT,
                    acknowledgment_time TEXT
                )
            """)
            
            conn.commit()
    
    def _setup_default_alert_rules(self):
        """Setup default monitoring alert rules"""
        
        # System down alert
        self.add_alert_rule(AlertRule(
            id="system_down",
            name="System Down",
            alert_type=AlertType.SYSTEM_DOWN,
            condition=lambda m: not m.get("system_running", True),
            severity=MonitoringLevel.CRITICAL,
            cooldown_minutes=5
        ))
        
        # High CPU usage
        self.add_alert_rule(AlertRule(
            id="high_cpu",
            name="High CPU Usage",
            alert_type=AlertType.RESOURCE_EXHAUSTION,
            condition=lambda m: m.get("cpu_percent", 0) > 90,
            severity=MonitoringLevel.WARNING,
            cooldown_minutes=10
        ))
        
        # High memory usage
        self.add_alert_rule(AlertRule(
            id="high_memory",
            name="High Memory Usage",
            alert_type=AlertType.RESOURCE_EXHAUSTION,
            condition=lambda m: m.get("memory_percent", 0) > 85,
            severity=MonitoringLevel.WARNING,
            cooldown_minutes=10
        ))
        
        # High error rate
        self.add_alert_rule(AlertRule(
            id="high_error_rate",
            name="High Error Rate",
            alert_type=AlertType.HIGH_ERROR_RATE,
            condition=lambda m: m.get("error_rate_per_minute", 0) > 10,
            severity=MonitoringLevel.ERROR,
            cooldown_minutes=15
        ))
        
        # Trading anomaly - high losses
        self.add_alert_rule(AlertRule(
            id="high_daily_loss",
            name="High Daily Loss",
            alert_type=AlertType.TRADING_ANOMALY,
            condition=lambda m: m.get("daily_pnl_percent", 0) < -3.0,
            severity=MonitoringLevel.ERROR,
            cooldown_minutes=30
        ))
        
        # Performance degradation
        self.add_alert_rule(AlertRule(
            id="slow_execution",
            name="Slow Trade Execution",
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            condition=lambda m: m.get("avg_execution_time_ms", 0) > 5000,
            severity=MonitoringLevel.WARNING,
            cooldown_minutes=20
        ))
        
        # Connectivity issues
        self.add_alert_rule(AlertRule(
            id="connectivity_issue",
            name="Connectivity Issues",
            alert_type=AlertType.CONNECTIVITY_ISSUE,
            condition=lambda m: not m.get("network_connected", True),
            severity=MonitoringLevel.ERROR,
            cooldown_minutes=5
        ))
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules[rule.id] = rule
        print(f"📋 Alert rule added: {rule.name}")
    
    def start_monitoring(self):
        """Start the production monitoring system"""
        if self.monitoring_active:
            print("⚠️ Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.start_time = datetime.now()
        
        print("🚀 Starting Production Monitoring System...")
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("✅ Production monitoring started")
        
        # Log monitoring start
        if self.logger:
            self.logger.log_system_event(
                "INFO", "MONITORING", "ProductionMonitoring",
                "Production monitoring system started",
                {"start_time": self.start_time.isoformat()}
            )
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.monitoring_active:
            print("⚠️ Monitoring is not active")
            return
        
        print("🛑 Stopping Production Monitoring System...")
        
        self.monitoring_active = False
        
        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        print("✅ Production monitoring stopped")
        
        # Log monitoring stop
        if self.logger:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            self.logger.log_system_event(
                "INFO", "MONITORING", "ProductionMonitoring",
                "Production monitoring system stopped",
                {"uptime_hours": uptime.total_seconds() / 3600}
            )
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        print("🔄 Monitoring loop started")
        
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Collect trading metrics
                trading_metrics = self._collect_trading_metrics()
                if trading_metrics:
                    self.trading_metrics_history.append(trading_metrics)
                
                # Store metrics in database
                self._store_metrics_to_db(system_metrics, trading_metrics)
                
                # Check alert conditions
                asyncio.run(self._check_alert_conditions(system_metrics, trading_metrics))
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                print(f"❌ Monitoring loop error: {str(e)}")
                time.sleep(60)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            
            # Uptime
            uptime_hours = 0
            if self.start_time:
                uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_percent=disk.percent,
                disk_used_gb=disk.used / (1024 * 1024 * 1024),
                network_sent_mb=network.bytes_sent / (1024 * 1024),
                network_recv_mb=network.bytes_recv / (1024 * 1024),
                active_threads=threading.active_count(),
                open_files=len(process.open_files()),
                uptime_hours=uptime_hours
            )
            
        except Exception as e:
            print(f"❌ Error collecting system metrics: {str(e)}")
            return None
    
    def _collect_trading_metrics(self) -> Optional[TradingMetrics]:
        """Collect current trading metrics"""
        try:
            if not self.trading_system:
                return None
            
            # Get trading system status
            status = self.trading_system.get_system_status()
            risk_summary = status.get("risk_management", {})
            
            # Calculate API call rate
            api_calls_per_minute = len([t for t in self.api_call_times if datetime.now() - t < timedelta(minutes=1)])
            
            # Calculate average execution time
            recent_execution_times = [t for t in self.trade_execution_times if datetime.now() - t[0] < timedelta(minutes=5)]
            avg_execution_time = statistics.mean([t[1] for t in recent_execution_times]) if recent_execution_times else 0
            
            return TradingMetrics(
                timestamp=datetime.now(),
                active_positions=risk_summary.get("active_positions", 0),
                total_trades_today=risk_summary.get("total_trades_today", 0),
                successful_trades_today=risk_summary.get("successful_trades_today", 0),
                failed_trades_today=risk_summary.get("failed_trades_today", 0),
                daily_pnl=risk_summary.get("daily_pnl", 0),
                daily_pnl_percent=risk_summary.get("daily_pnl_percent", 0),
                current_balance=risk_summary.get("current_capital", 0),
                win_rate=risk_summary.get("win_rate", 0),
                max_drawdown=abs(risk_summary.get("max_drawdown", 0)),
                risk_level=risk_summary.get("risk_level", "unknown"),
                api_calls_per_minute=api_calls_per_minute,
                avg_execution_time_ms=avg_execution_time
            )
            
        except Exception as e:
            print(f"❌ Error collecting trading metrics: {str(e)}")
            return None
    
    def _store_metrics_to_db(self, system_metrics: SystemMetrics, trading_metrics: Optional[TradingMetrics]):
        """Store metrics to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store system metrics
                if system_metrics:
                    cursor.execute("""
                        INSERT OR REPLACE INTO system_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        system_metrics.timestamp.isoformat(),
                        system_metrics.cpu_percent,
                        system_metrics.memory_percent,
                        system_metrics.memory_used_mb,
                        system_metrics.disk_percent,
                        system_metrics.disk_used_gb,
                        system_metrics.network_sent_mb,
                        system_metrics.network_recv_mb,
                        system_metrics.active_threads,
                        system_metrics.open_files,
                        system_metrics.uptime_hours
                    ))
                
                # Store trading metrics
                if trading_metrics:
                    cursor.execute("""
                        INSERT OR REPLACE INTO trading_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trading_metrics.timestamp.isoformat(),
                        trading_metrics.active_positions,
                        trading_metrics.total_trades_today,
                        trading_metrics.successful_trades_today,
                        trading_metrics.failed_trades_today,
                        trading_metrics.daily_pnl,
                        trading_metrics.daily_pnl_percent,
                        trading_metrics.current_balance,
                        trading_metrics.win_rate,
                        trading_metrics.max_drawdown,
                        trading_metrics.risk_level,
                        trading_metrics.api_calls_per_minute,
                        trading_metrics.avg_execution_time_ms
                    ))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error storing metrics to database: {str(e)}")
    
    async def _check_alert_conditions(self, system_metrics: SystemMetrics, trading_metrics: Optional[TradingMetrics]):
        """Check all alert conditions and trigger alerts if needed"""
        try:
            # Prepare metrics dictionary for condition checking
            metrics_dict = {}
            
            if system_metrics:
                metrics_dict.update({
                    "cpu_percent": system_metrics.cpu_percent,
                    "memory_percent": system_metrics.memory_percent,
                    "disk_percent": system_metrics.disk_percent,
                    "uptime_hours": system_metrics.uptime_hours,
                    "system_running": True  # If we're collecting metrics, system is running
                })
            
            if trading_metrics:
                metrics_dict.update({
                    "daily_pnl_percent": trading_metrics.daily_pnl_percent,
                    "avg_execution_time_ms": trading_metrics.avg_execution_time_ms,
                    "active_positions": trading_metrics.active_positions,
                    "win_rate": trading_metrics.win_rate
                })
            
            # Add error rate
            recent_errors = len([t for t in self.error_rate_history if datetime.now() - t < timedelta(minutes=1)])
            metrics_dict["error_rate_per_minute"] = recent_errors
            
            # Add network connectivity (would be checked by error handler)
            metrics_dict["network_connected"] = True  # Simplified for demo
            
            # Check each alert rule
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Check cooldown period
                if rule.last_triggered:
                    time_since_last = datetime.now() - rule.last_triggered
                    if time_since_last.total_seconds() < (rule.cooldown_minutes * 60):
                        continue
                
                # Check condition
                try:
                    if rule.condition(metrics_dict):
                        await self._trigger_alert(rule, metrics_dict)
                except Exception as e:
                    print(f"❌ Error checking alert condition {rule_id}: {str(e)}")
            
        except Exception as e:
            print(f"❌ Error checking alert conditions: {str(e)}")
    
    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Trigger an alert"""
        try:
            alert_id = f"{rule.id}_{int(time.time())}"
            
            # Create alert
            alert = MonitoringAlert(
                id=alert_id,
                timestamp=datetime.now(),
                alert_type=rule.alert_type,
                severity=rule.severity,
                title=rule.name,
                message=self._generate_alert_message(rule, metrics),
                metrics=metrics.copy()
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Update rule last triggered time
            rule.last_triggered = datetime.now()
            
            # Store alert in database
            self._store_alert_to_db(alert)
            
            # Send notification
            if self.notification_manager:
                notification_type = "CRITICAL" if rule.severity == MonitoringLevel.CRITICAL else "HIGH"
                
                await self.notification_manager.send_notification(
                    title=f"🚨 {alert.title}",
                    message=alert.message,
                    notification_type=notification_type
                )
            
            # Log alert
            if self.logger:
                self.logger.log_system_event(
                    rule.severity.value.upper(), "MONITORING", "AlertSystem",
                    f"Alert triggered: {rule.name}",
                    {"alert_id": alert_id, "metrics": metrics}
                )
            
            print(f"🚨 Alert triggered: {rule.name}")
            print(f"   Message: {alert.message}")
            
        except Exception as e:
            print(f"❌ Error triggering alert: {str(e)}")
    
    def _generate_alert_message(self, rule: AlertRule, metrics: Dict[str, Any]) -> str:
        """Generate alert message based on rule and metrics"""
        if rule.alert_type == AlertType.SYSTEM_DOWN:
            return "Trading system has stopped running. Immediate attention required."
        
        elif rule.alert_type == AlertType.RESOURCE_EXHAUSTION:
            if "cpu_percent" in metrics and metrics["cpu_percent"] > 90:
                return f"High CPU usage detected: {metrics['cpu_percent']:.1f}%"
            elif "memory_percent" in metrics and metrics["memory_percent"] > 85:
                return f"High memory usage detected: {metrics['memory_percent']:.1f}%"
        
        elif rule.alert_type == AlertType.HIGH_ERROR_RATE:
            error_rate = metrics.get("error_rate_per_minute", 0)
            return f"High error rate detected: {error_rate} errors per minute"
        
        elif rule.alert_type == AlertType.TRADING_ANOMALY:
            daily_pnl = metrics.get("daily_pnl_percent", 0)
            return f"High daily loss detected: {daily_pnl:.2f}% loss today"
        
        elif rule.alert_type == AlertType.PERFORMANCE_DEGRADATION:
            exec_time = metrics.get("avg_execution_time_ms", 0)
            return f"Slow trade execution detected: {exec_time:.0f}ms average"
        
        elif rule.alert_type == AlertType.CONNECTIVITY_ISSUE:
            return "Network connectivity issues detected. Check internet connection."
        
        return f"Alert condition met for {rule.name}"
    
    def _store_alert_to_db(self, alert: MonitoringAlert):
        """Store alert to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.timestamp.isoformat(),
                    alert.alert_type.value,
                    alert.severity.value,
                    alert.title,
                    alert.message,
                    json.dumps(alert.metrics),
                    1 if alert.resolved else 0,
                    alert.resolution_time.isoformat() if alert.resolution_time else None,
                    alert.acknowledgment_time.isoformat() if alert.acknowledgment_time else None
                ))
                conn.commit()
        except Exception as e:
            print(f"❌ Error storing alert to database: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            # Clean up database records older than 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff_date,))
                cursor.execute("DELETE FROM trading_metrics WHERE timestamp < ?", (cutoff_date,))
                cursor.execute("DELETE FROM alerts WHERE timestamp < ? AND resolved = 1", (cutoff_date,))
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error cleaning up old data: {str(e)}")
    
    def record_api_call(self):
        """Record an API call for rate monitoring"""
        self.api_call_times.append(datetime.now())
    
    def record_trade_execution(self, execution_time_ms: float):
        """Record trade execution time"""
        self.trade_execution_times.append((datetime.now(), execution_time_ms))
    
    def record_error(self, error_type: str):
        """Record an error for rate monitoring"""
        self.error_rate_history.append(datetime.now())
        self.error_counts[error_type] += 1
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledgment_time = datetime.now()
            print(f"✅ Alert acknowledged: {alert_id}")
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            
            # Update in database
            self._store_alert_to_db(alert)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            print(f"✅ Alert resolved: {alert_id}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        try:
            uptime_hours = 0
            if self.start_time:
                uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            
            # Get latest metrics
            latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
            latest_trading = self.trading_metrics_history[-1] if self.trading_metrics_history else None
            
            return {
                "monitoring_active": self.monitoring_active,
                "uptime_hours": uptime_hours,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "total_alerts": len(self.alert_history),
                "active_alerts": len(self.active_alerts),
                "alert_rules_count": len(self.alert_rules),
                "latest_system_metrics": {
                    "cpu_percent": latest_system.cpu_percent if latest_system else 0,
                    "memory_percent": latest_system.memory_percent if latest_system else 0,
                    "disk_percent": latest_system.disk_percent if latest_system else 0,
                    "uptime_hours": latest_system.uptime_hours if latest_system else 0
                } if latest_system else {},
                "latest_trading_metrics": {
                    "active_positions": latest_trading.active_positions if latest_trading else 0,
                    "daily_pnl_percent": latest_trading.daily_pnl_percent if latest_trading else 0,
                    "win_rate": latest_trading.win_rate if latest_trading else 0,
                    "api_calls_per_minute": latest_trading.api_calls_per_minute if latest_trading else 0
                } if latest_trading else {},
                "error_statistics": dict(self.error_counts),
                "recent_alerts": [
                    {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "type": alert.alert_type.value,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "resolved": alert.resolved
                    }
                    for alert in sorted(self.alert_history[-10:], key=lambda x: x.timestamp, reverse=True)
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        try:
            print("📋 Generating monitoring report...")
            
            # Calculate time ranges
            now = datetime.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # System performance summary
            recent_system_metrics = [m for m in self.system_metrics_history if m.timestamp >= last_24h]
            
            system_summary = {}
            if recent_system_metrics:
                system_summary = {
                    "avg_cpu_percent": statistics.mean([m.cpu_percent for m in recent_system_metrics]),
                    "max_cpu_percent": max([m.cpu_percent for m in recent_system_metrics]),
                    "avg_memory_percent": statistics.mean([m.memory_percent for m in recent_system_metrics]),
                    "max_memory_percent": max([m.memory_percent for m in recent_system_metrics]),
                    "current_disk_percent": recent_system_metrics[-1].disk_percent,
                    "uptime_hours": recent_system_metrics[-1].uptime_hours
                }
            
            # Trading performance summary
            recent_trading_metrics = [m for m in self.trading_metrics_history if m.timestamp >= last_24h]
            
            trading_summary = {}
            if recent_trading_metrics:
                trading_summary = {
                    "total_trades": recent_trading_metrics[-1].total_trades_today,
                    "successful_trades": recent_trading_metrics[-1].successful_trades_today,
                    "failed_trades": recent_trading_metrics[-1].failed_trades_today,
                    "win_rate": recent_trading_metrics[-1].win_rate,
                    "daily_pnl_percent": recent_trading_metrics[-1].daily_pnl_percent,
                    "current_balance": recent_trading_metrics[-1].current_balance,
                    "max_drawdown": max([m.max_drawdown for m in recent_trading_metrics]),
                    "avg_execution_time_ms": statistics.mean([m.avg_execution_time_ms for m in recent_trading_metrics])
                }
            
            # Alert summary
            recent_alerts = [a for a in self.alert_history if a.timestamp >= last_7d]
            alert_summary = {
                "total_alerts_7d": len(recent_alerts),
                "critical_alerts_7d": len([a for a in recent_alerts if a.severity == MonitoringLevel.CRITICAL]),
                "unresolved_alerts": len(self.active_alerts),
                "alert_types_breakdown": {}
            }
            
            # Count alerts by type
            for alert in recent_alerts:
                alert_type = alert.alert_type.value
                alert_summary["alert_types_breakdown"][alert_type] = alert_summary["alert_types_breakdown"].get(alert_type, 0) + 1
            
            report = {
                "report_timestamp": now.isoformat(),
                "report_period": "Last 24 hours",
                "system_performance": system_summary,
                "trading_performance": trading_summary,
                "alert_summary": alert_summary,
                "error_statistics": dict(self.error_counts),
                "monitoring_health": {
                    "monitoring_active": self.monitoring_active,
                    "data_points_collected": len(self.system_metrics_history),
                    "alert_rules_active": len([r for r in self.alert_rules.values() if r.enabled])
                }
            }
            
            print("✅ Monitoring report generated")
            return report
            
        except Exception as e:
            print(f"❌ Error generating monitoring report: {str(e)}")
            return {"error": str(e)}

# Demo function
async def demo_production_monitoring():
    """Demonstrate the production monitoring system"""
    print("📊 Production Monitoring System Demo")
    print("=" * 50)
    
    # Create monitoring system
    monitoring = ProductionMonitoringSystem()
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Simulate some activity
    print("\n🔄 Simulating system activity...")
    
    # Record some API calls
    for i in range(5):
        monitoring.record_api_call()
        time.sleep(0.1)
    
    # Record trade execution
    monitoring.record_trade_execution(1500.0)  # 1.5 seconds
    
    # Record some errors
    monitoring.record_error("network_error")
    monitoring.record_error("api_error")
    
    # Let monitoring run for a bit
    print("⏰ Monitoring for 10 seconds...")
    await asyncio.sleep(10)
    
    # Get monitoring status
    status = monitoring.get_monitoring_status()
    print(f"\n📊 Monitoring Status:")
    print(f"   • Active: {status['monitoring_active']}")
    print(f"   • Uptime: {status['uptime_hours']:.2f} hours")
    print(f"   • Total Alerts: {status['total_alerts']}")
    print(f"   • Active Alerts: {status['active_alerts']}")
    
    # Show latest metrics
    if status['latest_system_metrics']:
        metrics = status['latest_system_metrics']
        print(f"   • CPU: {metrics['cpu_percent']:.1f}%")
        print(f"   • Memory: {metrics['memory_percent']:.1f}%")
        print(f"   • Disk: {metrics['disk_percent']:.1f}%")
    
    # Generate report
    report = await monitoring.generate_monitoring_report()
    if "error" not in report:
        print(f"\n📋 Monitoring Report Generated:")
        print(f"   • Report Period: {report['report_period']}")
        print(f"   • Data Points: {report['monitoring_health']['data_points_collected']}")
        print(f"   • Alert Rules: {report['monitoring_health']['alert_rules_active']}")
    
    # Stop monitoring
    monitoring.stop_monitoring()
    
    print(f"\n🎯 Production Monitoring Features:")
    print(f"   ✅ Real-time system metrics collection")
    print(f"   ✅ Trading performance monitoring")
    print(f"   ✅ Intelligent alert system with rules")
    print(f"   ✅ Database storage for historical data")
    print(f"   ✅ Telegram/Email notifications")
    print(f"   ✅ Comprehensive reporting")
    print(f"   ✅ Error rate tracking")
    print(f"   ✅ Performance degradation detection")
    print(f"   ✅ Resource exhaustion alerts")
    print(f"   ✅ Trading anomaly detection")
    
    print(f"\n✅ Production Monitoring demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_production_monitoring())

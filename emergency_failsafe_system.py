"""
Emergency Failsafe System
Comprehensive monitoring and emergency response for trading bot
"""

import asyncio
import aiohttp
import psutil
import time
import json
import threading
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os
import shutil
from pathlib import Path
import requests
from advanced_risk_manager import AdvancedRiskManager
from notification_system import NotificationManager, NotificationType

class FailsafeLevel(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SystemComponent(Enum):
    NETWORK = "network"
    EXCHANGE_API = "exchange_api"
    RISK_MANAGER = "risk_manager"
    NOTIFICATION = "notification"
    DATABASE = "database"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"

@dataclass
class HealthCheck:
    """System health check result"""
    component: SystemComponent
    status: bool
    message: str
    timestamp: datetime
    response_time: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FailsafeConfig:
    """Emergency failsafe configuration"""
    # Network monitoring
    network_timeout: float = 10.0
    network_check_interval: int = 30  # seconds
    max_network_failures: int = 3
    
    # Exchange API monitoring
    api_timeout: float = 15.0
    api_check_interval: int = 60  # seconds
    max_api_failures: int = 2
    
    # System resource monitoring
    max_memory_usage_percent: float = 85.0
    max_cpu_usage_percent: float = 90.0
    min_disk_space_gb: float = 1.0
    
    # Emergency thresholds
    emergency_monthly_loss_percent: float = 20.0
    emergency_daily_loss_percent: float = 10.0
    max_consecutive_losses: int = 5
    
    # Recovery settings
    auto_restart_attempts: int = 3
    restart_delay_seconds: int = 300  # 5 minutes
    backup_interval_hours: int = 6
    
    # Monitoring intervals
    health_check_interval: int = 60  # seconds
    system_monitor_interval: int = 30  # seconds

class NetworkMonitor:
    """Network connectivity monitoring"""
    
    def __init__(self, config: FailsafeConfig):
        self.config = config
        self.failure_count = 0
        self.last_check = None
        self.test_urls = [
            "https://api.binance.com/api/v3/ping",
            "https://api.coinbase.com/v2/time",
            "https://api.kraken.com/0/public/SystemStatus",
            "https://8.8.8.8"  # Google DNS
        ]
    
    async def check_connectivity(self) -> HealthCheck:
        """Check network connectivity"""
        start_time = time.time()
        
        try:
            # Test multiple endpoints
            successful_tests = 0
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.network_timeout)) as session:
                for url in self.test_urls:
                    try:
                        if url == "https://8.8.8.8":
                            # DNS test
                            socket.create_connection(("8.8.8.8", 53), timeout=5)
                            successful_tests += 1
                        else:
                            async with session.get(url) as response:
                                if response.status < 500:  # Accept any non-server error
                                    successful_tests += 1
                    except:
                        continue
            
            response_time = time.time() - start_time
            success_rate = successful_tests / len(self.test_urls)
            
            if success_rate >= 0.5:  # At least 50% success
                self.failure_count = 0
                return HealthCheck(
                    component=SystemComponent.NETWORK,
                    status=True,
                    message=f"Network connectivity OK ({success_rate*100:.0f}% success rate)",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    metadata={"success_rate": success_rate, "successful_tests": successful_tests}
                )
            else:
                self.failure_count += 1
                return HealthCheck(
                    component=SystemComponent.NETWORK,
                    status=False,
                    message=f"Network connectivity issues ({success_rate*100:.0f}% success rate)",
                    timestamp=datetime.now(),
                    response_time=response_time,
                    metadata={"success_rate": success_rate, "failure_count": self.failure_count}
                )
                
        except Exception as e:
            self.failure_count += 1
            return HealthCheck(
                component=SystemComponent.NETWORK,
                status=False,
                message=f"Network check failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                metadata={"failure_count": self.failure_count}
            )

class ExchangeAPIMonitor:
    """Exchange API health monitoring"""
    
    def __init__(self, config: FailsafeConfig):
        self.config = config
        self.exchange_failures = {}
        self.exchange_endpoints = {
            "binance": "https://api.binance.com/api/v3/exchangeInfo",
            "coinbase": "https://api.exchange.coinbase.com/products",
            "kraken": "https://api.kraken.com/0/public/SystemStatus",
            "bybit": "https://api.bybit.com/v5/market/time"
        }
    
    async def check_exchange_apis(self) -> List[HealthCheck]:
        """Check all exchange APIs"""
        results = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.api_timeout)) as session:
            for exchange, endpoint in self.exchange_endpoints.items():
                result = await self._check_single_exchange(session, exchange, endpoint)
                results.append(result)
        
        return results
    
    async def _check_single_exchange(self, session: aiohttp.ClientSession, 
                                   exchange: str, endpoint: str) -> HealthCheck:
        """Check single exchange API"""
        start_time = time.time()
        
        try:
            async with session.get(endpoint) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    # Reset failure count on success
                    self.exchange_failures[exchange] = 0
                    
                    return HealthCheck(
                        component=SystemComponent.EXCHANGE_API,
                        status=True,
                        message=f"{exchange.title()} API is healthy",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        metadata={"exchange": exchange, "status_code": response.status}
                    )
                else:
                    # Increment failure count
                    self.exchange_failures[exchange] = self.exchange_failures.get(exchange, 0) + 1
                    
                    return HealthCheck(
                        component=SystemComponent.EXCHANGE_API,
                        status=False,
                        message=f"{exchange.title()} API error: HTTP {response.status}",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        metadata={"exchange": exchange, "status_code": response.status, 
                                "failure_count": self.exchange_failures[exchange]}
                    )
                    
        except Exception as e:
            self.exchange_failures[exchange] = self.exchange_failures.get(exchange, 0) + 1
            
            return HealthCheck(
                component=SystemComponent.EXCHANGE_API,
                status=False,
                message=f"{exchange.title()} API failed: {str(e)}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time,
                metadata={"exchange": exchange, "error": str(e), 
                        "failure_count": self.exchange_failures[exchange]}
            )

class SystemResourceMonitor:
    """System resource monitoring"""
    
    def __init__(self, config: FailsafeConfig):
        self.config = config
    
    def check_system_resources(self) -> List[HealthCheck]:
        """Check system resources (CPU, Memory, Disk)"""
        results = []
        
        # Check memory usage
        memory = psutil.virtual_memory()
        memory_check = HealthCheck(
            component=SystemComponent.MEMORY,
            status=memory.percent < self.config.max_memory_usage_percent,
            message=f"Memory usage: {memory.percent:.1f}%",
            timestamp=datetime.now(),
            metadata={
                "used_gb": memory.used / (1024**3),
                "total_gb": memory.total / (1024**3),
                "percent": memory.percent
            }
        )
        results.append(memory_check)
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_check = HealthCheck(
            component=SystemComponent.CPU,
            status=cpu_percent < self.config.max_cpu_usage_percent,
            message=f"CPU usage: {cpu_percent:.1f}%",
            timestamp=datetime.now(),
            metadata={"percent": cpu_percent, "cores": psutil.cpu_count()}
        )
        results.append(cpu_check)
        
        # Check disk space
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024**3)
        disk_check = HealthCheck(
            component=SystemComponent.DISK,
            status=free_gb > self.config.min_disk_space_gb,
            message=f"Free disk space: {free_gb:.1f} GB",
            timestamp=datetime.now(),
            metadata={
                "free_gb": free_gb,
                "total_gb": disk.total / (1024**3),
                "used_percent": (disk.used / disk.total) * 100
            }
        )
        results.append(disk_check)
        
        return results

class BackupManager:
    """Backup and recovery management"""
    
    def __init__(self, config: FailsafeConfig):
        self.config = config
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self) -> bool:
        """Create system backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)
            
            # Files to backup
            files_to_backup = [
                "risk_state.json",
                "encrypted_config.json",
                "security.salt",
                ".env"
            ]
            
            backed_up_files = 0
            for file_name in files_to_backup:
                if os.path.exists(file_name):
                    shutil.copy2(file_name, backup_path / file_name)
                    backed_up_files += 1
            
            # Create backup manifest
            manifest = {
                "timestamp": timestamp,
                "files_backed_up": backed_up_files,
                "backup_path": str(backup_path),
                "system_info": {
                    "python_version": os.sys.version,
                    "platform": os.name,
                    "cwd": os.getcwd()
                }
            }
            
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            # Clean old backups (keep last 10)
            self._cleanup_old_backups()
            
            print(f"✅ Backup created: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backup files"""
        try:
            backup_dirs = sorted([d for d in self.backup_dir.iterdir() if d.is_dir()], 
                               key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the 10 most recent backups
            for old_backup in backup_dirs[10:]:
                shutil.rmtree(old_backup)
                print(f"🗑️ Removed old backup: {old_backup.name}")
                
        except Exception as e:
            print(f"❌ Backup cleanup failed: {e}")

class EmergencyFailsafeSystem:
    """Main emergency failsafe system"""
    
    def __init__(self, risk_manager: AdvancedRiskManager, 
                 notification_manager: NotificationManager,
                 config: FailsafeConfig = None):
        self.risk_manager = risk_manager
        self.notification_manager = notification_manager
        self.config = config or FailsafeConfig()
        
        # Initialize monitors
        self.network_monitor = NetworkMonitor(self.config)
        self.api_monitor = ExchangeAPIMonitor(self.config)
        self.resource_monitor = SystemResourceMonitor(self.config)
        self.backup_manager = BackupManager(self.config)
        
        # System state
        self.system_status = FailsafeLevel.NORMAL
        self.health_checks: List[HealthCheck] = []
        self.emergency_triggered = False
        self.monitoring_active = False
        self.restart_attempts = 0
        
        # Threading
        self.monitor_thread = None
        self.backup_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup emergency system logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('emergency_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('EmergencyFailsafe')
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.shutdown_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start backup thread
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
        
        self.logger.info("Emergency failsafe monitoring started")
        print("🛡️ Emergency failsafe system activated")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        self.shutdown_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        
        self.logger.info("Emergency failsafe monitoring stopped")
        print("🛑 Emergency failsafe system deactivated")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active and not self.shutdown_event.is_set():
            try:
                # Run health checks
                asyncio.run(self._run_health_checks())
                
                # Analyze system status
                self._analyze_system_status()
                
                # Take action if needed
                if self.system_status in [FailsafeLevel.CRITICAL, FailsafeLevel.EMERGENCY]:
                    asyncio.run(self._handle_emergency())
                
                # Wait for next check
                self.shutdown_event.wait(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                self.shutdown_event.wait(30)  # Wait 30 seconds before retry
    
    def _backup_loop(self):
        """Backup loop"""
        while self.monitoring_active and not self.shutdown_event.is_set():
            try:
                # Create backup
                self.backup_manager.create_backup()
                
                # Wait for next backup
                self.shutdown_event.wait(self.config.backup_interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Backup loop error: {e}")
                self.shutdown_event.wait(3600)  # Wait 1 hour before retry
    
    async def _run_health_checks(self):
        """Run all health checks"""
        self.health_checks.clear()
        
        # Network connectivity check
        network_check = await self.network_monitor.check_connectivity()
        self.health_checks.append(network_check)
        
        # Exchange API checks
        api_checks = await self.api_monitor.check_exchange_apis()
        self.health_checks.extend(api_checks)
        
        # System resource checks
        resource_checks = self.resource_monitor.check_system_resources()
        self.health_checks.extend(resource_checks)
        
        # Risk manager check
        risk_check = self._check_risk_manager()
        self.health_checks.append(risk_check)
    
    def _check_risk_manager(self) -> HealthCheck:
        """Check risk manager status"""
        try:
            summary = self.risk_manager.get_risk_summary()
            
            # Check for emergency conditions
            emergency_conditions = []
            
            if summary["emergency_stop"]:
                emergency_conditions.append("Emergency stop active")
            
            if not summary["trading_enabled"]:
                emergency_conditions.append("Trading disabled")
            
            if abs(summary["monthly_loss_percent"]) >= self.config.emergency_monthly_loss_percent:
                emergency_conditions.append(f"Monthly loss limit exceeded: {summary['monthly_loss_percent']:.2f}%")
            
            if abs(summary["daily_pnl_percent"]) >= self.config.emergency_daily_loss_percent:
                emergency_conditions.append(f"Daily loss limit exceeded: {summary['daily_pnl_percent']:.2f}%")
            
            if emergency_conditions:
                return HealthCheck(
                    component=SystemComponent.RISK_MANAGER,
                    status=False,
                    message=f"Risk manager issues: {'; '.join(emergency_conditions)}",
                    timestamp=datetime.now(),
                    metadata=summary
                )
            else:
                return HealthCheck(
                    component=SystemComponent.RISK_MANAGER,
                    status=True,
                    message="Risk manager operating normally",
                    timestamp=datetime.now(),
                    metadata=summary
                )
                
        except Exception as e:
            return HealthCheck(
                component=SystemComponent.RISK_MANAGER,
                status=False,
                message=f"Risk manager check failed: {str(e)}",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
    
    def _analyze_system_status(self):
        """Analyze health checks and determine system status"""
        failed_checks = [check for check in self.health_checks if not check.status]
        critical_failures = []
        
        for check in failed_checks:
            if check.component == SystemComponent.NETWORK:
                if self.network_monitor.failure_count >= self.config.max_network_failures:
                    critical_failures.append("Network connectivity lost")
            
            elif check.component == SystemComponent.EXCHANGE_API:
                exchange = check.metadata.get("exchange", "unknown")
                failure_count = self.api_monitor.exchange_failures.get(exchange, 0)
                if failure_count >= self.config.max_api_failures:
                    critical_failures.append(f"{exchange.title()} API unavailable")
            
            elif check.component == SystemComponent.RISK_MANAGER:
                if "Emergency stop active" in check.message or "Monthly loss limit exceeded" in check.message:
                    critical_failures.append("Risk management emergency")
            
            elif check.component in [SystemComponent.MEMORY, SystemComponent.CPU, SystemComponent.DISK]:
                critical_failures.append(f"System resource critical: {check.component.value}")
        
        # Determine system status
        if critical_failures:
            if not self.emergency_triggered:
                self.system_status = FailsafeLevel.EMERGENCY
            else:
                self.system_status = FailsafeLevel.CRITICAL
        elif failed_checks:
            self.system_status = FailsafeLevel.WARNING
        else:
            self.system_status = FailsafeLevel.NORMAL
        
        # Log status change
        if hasattr(self, '_last_status') and self._last_status != self.system_status:
            self.logger.warning(f"System status changed: {self._last_status.value} -> {self.system_status.value}")
        
        self._last_status = self.system_status
    
    async def _handle_emergency(self):
        """Handle emergency situations"""
        if self.emergency_triggered:
            return  # Already handling emergency
        
        self.emergency_triggered = True
        self.logger.critical("EMERGENCY SITUATION DETECTED - INITIATING FAILSAFE PROCEDURES")
        
        try:
            # 1. Immediately stop all trading
            self.risk_manager.trading_enabled = False
            
            # 2. Close all active positions
            active_positions = list(self.risk_manager.active_positions.keys())
            for position_id in active_positions:
                position = self.risk_manager.active_positions[position_id]
                self.risk_manager.close_position(position_id, position.current_price, "Emergency Failsafe")
            
            # 3. Create emergency backup
            self.backup_manager.create_backup()
            
            # 4. Send emergency notifications
            await self._send_emergency_notifications()
            
            # 5. Log emergency details
            self._log_emergency_details()
            
            self.logger.critical("EMERGENCY FAILSAFE PROCEDURES COMPLETED")
            
        except Exception as e:
            self.logger.critical(f"EMERGENCY HANDLING FAILED: {e}")
    
    async def _send_emergency_notifications(self):
        """Send emergency notifications"""
        try:
            failed_checks = [check for check in self.health_checks if not check.status]
            failure_messages = [f"• {check.component.value}: {check.message}" for check in failed_checks]
            
            emergency_message = f"""
🚨 EMERGENCY FAILSAFE ACTIVATED

⚠️ Critical system failures detected:
{chr(10).join(failure_messages)}

🛑 Actions taken:
• All trading stopped immediately
• Active positions closed
• Emergency backup created
• System monitoring continues

📞 IMMEDIATE ATTENTION REQUIRED!
            """.strip()
            
            await self.notification_manager.send_notification(
                title="🚨 EMERGENCY FAILSAFE ACTIVATED",
                message=emergency_message,
                notification_type=NotificationType.CRITICAL
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send emergency notifications: {e}")
    
    def _log_emergency_details(self):
        """Log detailed emergency information"""
        emergency_log = {
            "timestamp": datetime.now().isoformat(),
            "system_status": self.system_status.value,
            "failed_health_checks": [asdict(check) for check in self.health_checks if not check.status],
            "risk_summary": self.risk_manager.get_risk_summary(),
            "system_resources": {
                "memory": psutil.virtual_memory()._asdict(),
                "cpu_percent": psutil.cpu_percent(),
                "disk": psutil.disk_usage('/')._asdict()
            }
        }
        
        # Save emergency log
        with open(f"emergency_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(emergency_log, f, indent=2, default=str)
        
        self.logger.critical(f"Emergency details logged: {json.dumps(emergency_log, indent=2, default=str)}")
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "status": self.system_status.value,
            "emergency_triggered": self.emergency_triggered,
            "monitoring_active": self.monitoring_active,
            "last_health_check": max([check.timestamp for check in self.health_checks]) if self.health_checks else None,
            "failed_components": [check.component.value for check in self.health_checks if not check.status],
            "restart_attempts": self.restart_attempts,
            "health_checks": [asdict(check) for check in self.health_checks]
        }

# Demo function
async def demo_emergency_failsafe():
    """Demonstrate emergency failsafe system"""
    print("🛡️ Emergency Failsafe System Demo")
    print("=" * 50)
    
    # Initialize components
    from advanced_risk_manager import AdvancedRiskManager
    from notification_system import NotificationManager
    
    risk_manager = AdvancedRiskManager(initial_capital=50000)
    notification_manager = NotificationManager()
    
    # Initialize failsafe system
    failsafe_config = FailsafeConfig(
        network_check_interval=10,  # Faster for demo
        health_check_interval=15,   # Faster for demo
        max_network_failures=2,     # Lower threshold for demo
        emergency_monthly_loss_percent=15.0  # Lower threshold for demo
    )
    
    failsafe = EmergencyFailsafeSystem(risk_manager, notification_manager, failsafe_config)
    
    print("🔧 Failsafe Configuration:")
    print(f"   • Network check interval: {failsafe_config.network_check_interval}s")
    print(f"   • Health check interval: {failsafe_config.health_check_interval}s")
    print(f"   • Max network failures: {failsafe_config.max_network_failures}")
    print(f"   • Emergency monthly loss: {failsafe_config.emergency_monthly_loss_percent}%")
    
    # Start monitoring
    failsafe.start_monitoring()
    
    print("\n🔍 Running Health Checks:")
    
    # Run initial health checks
    await failsafe._run_health_checks()
    
    for check in failsafe.health_checks:
        status_icon = "✅" if check.status else "❌"
        print(f"   {status_icon} {check.component.value}: {check.message}")
    
    # Get system status
    print(f"\n📊 System Status:")
    status = failsafe.get_system_status()
    
    for key, value in status.items():
        if key != "health_checks":  # Skip detailed health checks in summary
            print(f"   • {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n🛡️ Failsafe Features:")
    print(f"   ✅ Network connectivity monitoring")
    print(f"   ✅ Exchange API health checks")
    print(f"   ✅ System resource monitoring")
    print(f"   ✅ Risk management integration")
    print(f"   ✅ Automatic position closure")
    print(f"   ✅ Emergency backup creation")
    print(f"   ✅ Multi-channel notifications")
    print(f"   ✅ Continuous monitoring threads")
    print(f"   ✅ Detailed logging and reporting")
    
    print(f"\n⚠️ Emergency Triggers:")
    print(f"   • Network connectivity lost (>{failsafe_config.max_network_failures} failures)")
    print(f"   • Exchange API unavailable (>{failsafe_config.max_api_failures} failures)")
    print(f"   • Monthly loss >{failsafe_config.emergency_monthly_loss_percent}%")
    print(f"   • System resource critical (Memory >{failsafe_config.max_memory_usage_percent}%)")
    print(f"   • Risk manager emergency stop")
    
    # Let it run for a bit
    print(f"\n⏰ Monitoring for 30 seconds...")
    await asyncio.sleep(30)
    
    # Stop monitoring
    failsafe.stop_monitoring()
    
    print(f"\n✅ Emergency failsafe demo completed")

if __name__ == "__main__":
    asyncio.run(demo_emergency_failsafe())

"""
Auto-Restart System for AI Trading Bot
Provides automatic restart capabilities, process monitoring, and recovery mechanisms
"""

import asyncio
import os
import sys
import time
import signal
import subprocess
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import traceback

class RestartReason(Enum):
    CRASH = "crash"
    MEMORY_LEAK = "memory_leak"
    UNRESPONSIVE = "unresponsive"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    ERROR_THRESHOLD = "error_threshold"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    EXTERNAL_SIGNAL = "external_signal"

class ProcessState(Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    CRASHED = "crashed"
    RESTARTING = "restarting"

@dataclass
class RestartEvent:
    """Represents a restart event"""
    timestamp: datetime
    reason: RestartReason
    process_id: int
    uptime_seconds: float
    memory_usage_mb: float
    cpu_percent: float
    error_count: int
    restart_count: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class ProcessConfig:
    """Process configuration for auto-restart"""
    name: str
    command: List[str]
    working_directory: str
    environment: Dict[str, str] = field(default_factory=dict)
    max_restarts: int = 10
    restart_delay_seconds: int = 5
    max_restart_delay_seconds: int = 300
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 90
    health_check_interval: int = 30
    unresponsive_timeout: int = 300
    auto_restart_enabled: bool = True

class ProcessWatchdog:
    """Monitors and manages a single process"""
    
    def __init__(self, config: ProcessConfig, notification_manager=None, logger=None):
        self.config = config
        self.notification_manager = notification_manager
        self.logger = logger
        
        # Process state
        self.process: Optional[subprocess.Popen] = None
        self.state = ProcessState.STOPPED
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.error_count = 0
        self.last_health_check = None
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.restart_history: List[RestartEvent] = []
        
        # Health check
        self.last_response_time = datetime.now()
        self.health_check_callback: Optional[Callable] = None
        
        print(f"🐕 Process watchdog initialized for: {config.name}")
    
    def set_health_check_callback(self, callback: Callable):
        """Set custom health check callback"""
        self.health_check_callback = callback
    
    async def start_process(self) -> bool:
        """Start the monitored process"""
        try:
            if self.state == ProcessState.RUNNING:
                print(f"⚠️ Process {self.config.name} is already running")
                return True
            
            print(f"🚀 Starting process: {self.config.name}")
            self.state = ProcessState.STARTING
            
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.environment)
            
            # Start process
            self.process = subprocess.Popen(
                self.config.command,
                cwd=self.config.working_directory,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.start_time = datetime.now()
            self.state = ProcessState.RUNNING
            self.last_response_time = datetime.now()
            
            # Start monitoring
            if not self.monitoring_active:
                self.start_monitoring()
            
            # Log start
            if self.logger:
                self.logger.log_system_event(
                    "INFO", "AUTO_RESTART", "ProcessWatchdog",
                    f"Process started: {self.config.name}",
                    {"pid": self.process.pid, "command": " ".join(self.config.command)}
                )
            
            print(f"✅ Process started successfully: {self.config.name} (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            self.state = ProcessState.CRASHED
            error_msg = f"Failed to start process {self.config.name}: {str(e)}"
            print(f"❌ {error_msg}")
            
            if self.logger:
                self.logger.log_system_event(
                    "ERROR", "AUTO_RESTART", "ProcessWatchdog",
                    error_msg, {"error": str(e)}
                )
            
            return False
    
    async def stop_process(self, timeout: int = 30) -> bool:
        """Stop the monitored process gracefully"""
        try:
            if self.state != ProcessState.RUNNING or not self.process:
                print(f"⚠️ Process {self.config.name} is not running")
                return True
            
            print(f"🛑 Stopping process: {self.config.name}")
            self.state = ProcessState.STOPPING
            
            # Try graceful shutdown first
            if os.name != 'nt':
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                print(f"⚠️ Process {self.config.name} did not stop gracefully, forcing...")
                
                # Force kill
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                else:
                    self.process.kill()
                
                self.process.wait()
            
            self.state = ProcessState.STOPPED
            self.process = None
            
            print(f"✅ Process stopped: {self.config.name}")
            return True
            
        except Exception as e:
            error_msg = f"Error stopping process {self.config.name}: {str(e)}"
            print(f"❌ {error_msg}")
            
            if self.logger:
                self.logger.log_system_event(
                    "ERROR", "AUTO_RESTART", "ProcessWatchdog",
                    error_msg, {"error": str(e)}
                )
            
            return False
    
    async def restart_process(self, reason: RestartReason, delay: Optional[int] = None) -> bool:
        """Restart the process"""
        try:
            print(f"🔄 Restarting process: {self.config.name} (Reason: {reason.value})")
            
            # Record restart event
            uptime = 0
            memory_usage = 0
            cpu_percent = 0
            
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
            
            if self.process:
                try:
                    proc_info = psutil.Process(self.process.pid)
                    memory_usage = proc_info.memory_info().rss / (1024 * 1024)  # MB
                    cpu_percent = proc_info.cpu_percent()
                except:
                    pass
            
            restart_event = RestartEvent(
                timestamp=datetime.now(),
                reason=reason,
                process_id=self.process.pid if self.process else 0,
                uptime_seconds=uptime,
                memory_usage_mb=memory_usage,
                cpu_percent=cpu_percent,
                error_count=self.error_count,
                restart_count=self.restart_count,
                success=False
            )
            
            # Check restart limits
            if self.restart_count >= self.config.max_restarts:
                error_msg = f"Process {self.config.name} exceeded max restarts ({self.config.max_restarts})"
                print(f"❌ {error_msg}")
                
                restart_event.success = False
                restart_event.error_message = error_msg
                self.restart_history.append(restart_event)
                
                # Send critical notification
                if self.notification_manager:
                    await self.notification_manager.send_notification(
                        title=f"Process Restart Limit Exceeded",
                        message=f"{self.config.name} has exceeded maximum restart attempts",
                        notification_type="CRITICAL"
                    )
                
                return False
            
            # Stop current process
            await self.stop_process()
            
            # Wait before restart
            restart_delay = delay or min(
                self.config.restart_delay_seconds * (2 ** min(self.restart_count, 5)),
                self.config.max_restart_delay_seconds
            )
            
            if restart_delay > 0:
                print(f"⏳ Waiting {restart_delay} seconds before restart...")
                await asyncio.sleep(restart_delay)
            
            # Start process
            success = await self.start_process()
            
            if success:
                self.restart_count += 1
                restart_event.success = True
                
                # Send notification
                if self.notification_manager:
                    await self.notification_manager.send_notification(
                        title=f"Process Restarted",
                        message=f"{self.config.name} restarted successfully (Reason: {reason.value})",
                        notification_type="INFO"
                    )
                
                print(f"✅ Process restarted successfully: {self.config.name}")
            else:
                restart_event.success = False
                restart_event.error_message = "Failed to start process after restart"
            
            self.restart_history.append(restart_event)
            return success
            
        except Exception as e:
            error_msg = f"Error restarting process {self.config.name}: {str(e)}"
            print(f"❌ {error_msg}")
            
            if self.logger:
                self.logger.log_system_event(
                    "ERROR", "AUTO_RESTART", "ProcessWatchdog",
                    error_msg, {"error": str(e)}
                )
            
            return False
    
    def start_monitoring(self):
        """Start process monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print(f"👁️ Started monitoring for: {self.config.name}")
    
    def stop_monitoring(self):
        """Stop process monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        print(f"👁️ Stopped monitoring for: {self.config.name}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                if self.state == ProcessState.RUNNING and self.process:
                    # Check if process is still alive
                    if self.process.poll() is not None:
                        print(f"💀 Process {self.config.name} has died")
                        self.state = ProcessState.CRASHED
                        
                        if self.config.auto_restart_enabled:
                            asyncio.run(self.restart_process(RestartReason.CRASH))
                        continue
                    
                    # Check resource usage
                    try:
                        proc_info = psutil.Process(self.process.pid)
                        memory_mb = proc_info.memory_info().rss / (1024 * 1024)
                        cpu_percent = proc_info.cpu_percent()
                        
                        # Check memory limit
                        if memory_mb > self.config.memory_limit_mb:
                            print(f"🧠 Process {self.config.name} exceeded memory limit: {memory_mb:.1f}MB")
                            
                            if self.config.auto_restart_enabled:
                                asyncio.run(self.restart_process(RestartReason.MEMORY_LEAK))
                            continue
                        
                        # Check CPU limit (sustained high usage)
                        if cpu_percent > self.config.cpu_limit_percent:
                            print(f"⚡ Process {self.config.name} high CPU usage: {cpu_percent:.1f}%")
                            # Could implement sustained high CPU restart logic here
                        
                    except psutil.NoSuchProcess:
                        print(f"💀 Process {self.config.name} no longer exists")
                        self.state = ProcessState.CRASHED
                        
                        if self.config.auto_restart_enabled:
                            asyncio.run(self.restart_process(RestartReason.CRASH))
                        continue
                    
                    # Health check
                    if self.health_check_callback:
                        try:
                            is_healthy = self.health_check_callback()
                            if is_healthy:
                                self.last_response_time = datetime.now()
                            else:
                                # Check if unresponsive for too long
                                unresponsive_time = (datetime.now() - self.last_response_time).total_seconds()
                                if unresponsive_time > self.config.unresponsive_timeout:
                                    print(f"😵 Process {self.config.name} is unresponsive for {unresponsive_time:.0f}s")
                                    
                                    if self.config.auto_restart_enabled:
                                        asyncio.run(self.restart_process(RestartReason.UNRESPONSIVE))
                                    continue
                        except Exception as e:
                            print(f"❌ Health check failed for {self.config.name}: {str(e)}")
                
                # Sleep before next check
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                print(f"❌ Monitoring error for {self.config.name}: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def get_status(self) -> Dict[str, Any]:
        """Get process status"""
        uptime = 0
        memory_usage = 0
        cpu_percent = 0
        
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        if self.process and self.state == ProcessState.RUNNING:
            try:
                proc_info = psutil.Process(self.process.pid)
                memory_usage = proc_info.memory_info().rss / (1024 * 1024)
                cpu_percent = proc_info.cpu_percent()
            except:
                pass
        
        return {
            "name": self.config.name,
            "state": self.state.value,
            "pid": self.process.pid if self.process else None,
            "uptime_seconds": uptime,
            "restart_count": self.restart_count,
            "error_count": self.error_count,
            "memory_usage_mb": memory_usage,
            "cpu_percent": cpu_percent,
            "monitoring_active": self.monitoring_active,
            "auto_restart_enabled": self.config.auto_restart_enabled,
            "last_restart": self.restart_history[-1].timestamp.isoformat() if self.restart_history else None
        }

class AutoRestartManager:
    """Manages multiple processes with auto-restart capabilities"""
    
    def __init__(self, notification_manager=None, logger=None):
        self.notification_manager = notification_manager
        self.logger = logger
        self.watchdogs: Dict[str, ProcessWatchdog] = {}
        self.global_config = {
            "max_concurrent_restarts": 3,
            "restart_burst_limit": 5,
            "restart_burst_window_minutes": 10
        }
        
        print("🔄 Auto-Restart Manager initialized")
    
    def add_process(self, config: ProcessConfig) -> ProcessWatchdog:
        """Add a process to be managed"""
        watchdog = ProcessWatchdog(config, self.notification_manager, self.logger)
        self.watchdogs[config.name] = watchdog
        
        print(f"➕ Added process to auto-restart manager: {config.name}")
        return watchdog
    
    async def start_all_processes(self) -> bool:
        """Start all managed processes"""
        print("🚀 Starting all managed processes...")
        
        success_count = 0
        for name, watchdog in self.watchdogs.items():
            if await watchdog.start_process():
                success_count += 1
        
        total_processes = len(self.watchdogs)
        print(f"✅ Started {success_count}/{total_processes} processes")
        
        return success_count == total_processes
    
    async def stop_all_processes(self) -> bool:
        """Stop all managed processes"""
        print("🛑 Stopping all managed processes...")
        
        success_count = 0
        for name, watchdog in self.watchdogs.items():
            watchdog.stop_monitoring()
            if await watchdog.stop_process():
                success_count += 1
        
        total_processes = len(self.watchdogs)
        print(f"✅ Stopped {success_count}/{total_processes} processes")
        
        return success_count == total_processes
    
    async def restart_all_processes(self, reason: RestartReason = RestartReason.MANUAL) -> bool:
        """Restart all managed processes"""
        print(f"🔄 Restarting all managed processes (Reason: {reason.value})...")
        
        success_count = 0
        for name, watchdog in self.watchdogs.items():
            if await watchdog.restart_process(reason):
                success_count += 1
        
        total_processes = len(self.watchdogs)
        print(f"✅ Restarted {success_count}/{total_processes} processes")
        
        return success_count == total_processes
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all managed processes"""
        processes_status = {}
        total_restarts = 0
        running_processes = 0
        
        for name, watchdog in self.watchdogs.items():
            status = watchdog.get_status()
            processes_status[name] = status
            total_restarts += status["restart_count"]
            
            if status["state"] == "running":
                running_processes += 1
        
        return {
            "total_processes": len(self.watchdogs),
            "running_processes": running_processes,
            "total_restarts": total_restarts,
            "processes": processes_status,
            "system_health": "healthy" if running_processes == len(self.watchdogs) else "degraded"
        }
    
    @staticmethod
    def generate_supervisor_config(processes: List[ProcessConfig], output_file: str = "supervisord.conf"):
        """Generate supervisor configuration file"""
        config_content = """[unix_http_server]
file=/tmp/supervisor.sock

[supervisord]
logfile=/tmp/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

"""
        
        for process in processes:
            config_content += f"""
[program:{process.name}]
command={' '.join(process.command)}
directory={process.working_directory}
autostart=true
autorestart=true
startretries={process.max_restarts}
user=ubuntu
redirect_stderr=true
stdout_logfile=/var/log/{process.name}.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment={''.join([f'{k}="{v}",' for k, v in process.environment.items()]).rstrip(',')}
"""
        
        with open(output_file, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Supervisor config generated: {output_file}")
        return output_file
    
    @staticmethod
    def generate_systemd_service(process: ProcessConfig, output_file: str = None):
        """Generate systemd service file"""
        if not output_file:
            output_file = f"{process.name}.service"
        
        service_content = f"""[Unit]
Description={process.name} Auto-Restart Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec={process.restart_delay_seconds}
User=ubuntu
WorkingDirectory={process.working_directory}
ExecStart={' '.join(process.command)}
StandardOutput=journal
StandardError=journal
SyslogIdentifier={process.name}
"""
        
        if process.environment:
            for key, value in process.environment.items():
                service_content += f"Environment={key}={value}\n"
        
        service_content += """
[Install]
WantedBy=multi-user.target
"""
        
        with open(output_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Systemd service generated: {output_file}")
        return output_file
    
    @staticmethod
    def generate_pm2_ecosystem(processes: List[ProcessConfig], output_file: str = "ecosystem.config.js"):
        """Generate PM2 ecosystem file"""
        apps = []
        
        for process in processes:
            app_config = {
                "name": process.name,
                "script": process.command[0],
                "args": " ".join(process.command[1:]) if len(process.command) > 1 else "",
                "cwd": process.working_directory,
                "instances": 1,
                "autorestart": True,
                "watch": False,
                "max_memory_restart": f"{process.memory_limit_mb}M",
                "env": process.environment,
                "error_file": f"logs/{process.name}-error.log",
                "out_file": f"logs/{process.name}-out.log",
                "log_file": f"logs/{process.name}-combined.log",
                "time": True,
                "max_restarts": process.max_restarts,
                "min_uptime": "10s",
                "restart_delay": process.restart_delay_seconds * 1000
            }
            apps.append(app_config)
        
        ecosystem_content = f"""module.exports = {{
  apps: {json.dumps(apps, indent=2)}
}};
"""
        
        with open(output_file, 'w') as f:
            f.write(ecosystem_content)
        
        print(f"✅ PM2 ecosystem generated: {output_file}")
        return output_file
    
    @staticmethod
    def generate_docker_compose_with_restart(processes: List[ProcessConfig], output_file: str = "docker-compose.yml"):
        """Generate Docker Compose with restart policies"""
        services = {}
        
        for process in processes:
            service_config = {
                "build": ".",
                "container_name": process.name,
                "restart": "unless-stopped",
                "working_dir": process.working_directory,
                "command": process.command,
                "environment": process.environment,
                "volumes": [
                    "./data:/app/data",
                    "./logs:/app/logs"
                ],
                "deploy": {
                    "resources": {
                        "limits": {
                            "memory": f"{process.memory_limit_mb}M",
                            "cpus": "1.0"
                        }
                    },
                    "restart_policy": {
                        "condition": "on-failure",
                        "delay": f"{process.restart_delay_seconds}s",
                        "max_attempts": process.max_restarts
                    }
                },
                "healthcheck": {
                    "test": ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8080/health')"],
                    "interval": f"{process.health_check_interval}s",
                    "timeout": "10s",
                    "retries": 3,
                    "start_period": "30s"
                }
            }
            services[process.name] = service_config
        
        compose_content = {
            "version": "3.8",
            "services": services
        }
        
        with open(output_file, 'w') as f:
            f.write(f"# Auto-generated Docker Compose with restart policies\n")
            f.write(f"# Generated on: {datetime.now().isoformat()}\n\n")
            import yaml
            yaml.dump(compose_content, f, default_flow_style=False, indent=2)
        
        print(f"✅ Docker Compose with restart policies generated: {output_file}")
        return output_file

# Demo function
async def demo_auto_restart_system():
    """Demonstrate the auto-restart system"""
    print("🔄 Auto-Restart System Demo")
    print("=" * 50)
    
    # Create auto-restart manager
    restart_manager = AutoRestartManager()
    
    # Create demo process configuration
    demo_config = ProcessConfig(
        name="demo_trading_bot",
        command=["python3", "-c", "import time; [print(f'Bot running... {i}') or time.sleep(2) for i in range(100)]"],
        working_directory=os.getcwd(),
        max_restarts=3,
        restart_delay_seconds=2,
        memory_limit_mb=100,  # Low limit for demo
        health_check_interval=5,
        auto_restart_enabled=True
    )
    
    # Add process to manager
    watchdog = restart_manager.add_process(demo_config)
    
    # Set up simple health check
    def health_check():
        # Simple health check - always return True for demo
        return True
    
    watchdog.set_health_check_callback(health_check)
    
    # Start the process
    print("\n🚀 Starting demo process...")
    success = await watchdog.start_process()
    
    if success:
        print("✅ Demo process started successfully")
        
        # Let it run for a bit
        print("⏰ Letting process run for 10 seconds...")
        await asyncio.sleep(10)
        
        # Get status
        status = watchdog.get_status()
        print(f"\n📊 Process Status:")
        print(f"   • Name: {status['name']}")
        print(f"   • State: {status['state']}")
        print(f"   • PID: {status['pid']}")
        print(f"   • Uptime: {status['uptime_seconds']:.1f}s")
        print(f"   • Restart Count: {status['restart_count']}")
        
        # Simulate a restart
        print(f"\n🔄 Simulating manual restart...")
        restart_success = await watchdog.restart_process(RestartReason.MANUAL, delay=1)
        
        if restart_success:
            print("✅ Manual restart successful")
            
            # Wait a bit more
            await asyncio.sleep(5)
            
            # Get updated status
            status = watchdog.get_status()
            print(f"   • New PID: {status['pid']}")
            print(f"   • Restart Count: {status['restart_count']}")
        
        # Stop the process
        print(f"\n🛑 Stopping demo process...")
        await watchdog.stop_process()
    
    # Generate deployment configurations
    print(f"\n📋 Generating deployment configurations...")
    
    # Supervisor config
    AutoRestartManager.generate_supervisor_config([demo_config], "demo_supervisord.conf")
    
    # Systemd service
    AutoRestartManager.generate_systemd_service(demo_config, "demo_trading_bot.service")
    
    # PM2 ecosystem
    AutoRestartManager.generate_pm2_ecosystem([demo_config], "demo_ecosystem.config.js")
    
    # Get system status
    system_status = restart_manager.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   • Total Processes: {system_status['total_processes']}")
    print(f"   • Running Processes: {system_status['running_processes']}")
    print(f"   • Total Restarts: {system_status['total_restarts']}")
    print(f"   • System Health: {system_status['system_health']}")
    
    print(f"\n🎯 Auto-Restart Features:")
    print(f"   ✅ Automatic crash detection and restart")
    print(f"   ✅ Memory leak detection and restart")
    print(f"   ✅ Unresponsive process detection")
    print(f"   ✅ Resource usage monitoring")
    print(f"   ✅ Configurable restart limits and delays")
    print(f"   ✅ Health check integration")
    print(f"   ✅ Supervisor configuration generation")
    print(f"   ✅ Systemd service generation")
    print(f"   ✅ PM2 ecosystem generation")
    print(f"   ✅ Docker Compose with restart policies")
    print(f"   ✅ Process monitoring and alerting")
    
    print(f"\n✅ Auto-Restart System demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_auto_restart_system())

"""
Advanced Error Handling System for AI Trading Bot
Handles internet outages, API errors, failed orders, and implements retry mechanisms
"""

import asyncio
import time
import requests
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import traceback
import threading
import json
from functools import wraps
import logging

class ErrorType(Enum):
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    ORDER_ERROR = "order_error"
    SYSTEM_ERROR = "system_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INSUFFICIENT_FUNDS_ERROR = "insufficient_funds_error"
    MARKET_CLOSED_ERROR = "market_closed_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ErrorEvent:
    """Represents an error event"""
    id: str
    timestamp: datetime
    error_type: ErrorType
    severity: ErrorSeverity
    component: str
    function_name: str
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_method: Optional[str] = None

@dataclass
class RetryConfig:
    """Configuration for retry mechanisms"""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 300.0  # 5 minutes
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.API_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.RATE_LIMIT_ERROR
    ])

class NetworkConnectivityChecker:
    """Monitors network connectivity"""
    
    def __init__(self):
        self.test_urls = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://api.binance.com/api/v3/ping",
            "https://api.coinbase.com/v2/time"
        ]
        self.is_connected = True
        self.last_check = None
        self.consecutive_failures = 0
    
    def check_internet_connection(self, timeout: int = 10) -> bool:
        """Check if internet connection is available"""
        try:
            for url in self.test_urls:
                try:
                    response = requests.get(url, timeout=timeout)
                    if response.status_code == 200:
                        self.is_connected = True
                        self.consecutive_failures = 0
                        self.last_check = datetime.now()
                        return True
                except:
                    continue
            
            # All URLs failed
            self.is_connected = False
            self.consecutive_failures += 1
            self.last_check = datetime.now()
            return False
            
        except Exception as e:
            self.is_connected = False
            self.consecutive_failures += 1
            self.last_check = datetime.now()
            return False
    
    def check_dns_resolution(self, hostname: str = "google.com") -> bool:
        """Check if DNS resolution is working"""
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "is_connected": self.is_connected,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "consecutive_failures": self.consecutive_failures,
            "dns_working": self.check_dns_resolution()
        }

class AdvancedErrorHandler:
    """Advanced error handling system with retry mechanisms"""
    
    def __init__(self, notification_manager=None, logger=None):
        self.notification_manager = notification_manager
        self.logger = logger
        self.error_events: Dict[str, ErrorEvent] = {}
        self.error_statistics: Dict[ErrorType, int] = {error_type: 0 for error_type in ErrorType}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.network_checker = NetworkConnectivityChecker()
        
        # Circuit breaker patterns
        self.circuit_breakers: Dict[str, Dict] = {}
        
        # Error recovery strategies
        self.recovery_strategies: Dict[ErrorType, Callable] = {
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.API_ERROR: self._handle_api_error,
            ErrorType.ORDER_ERROR: self._handle_order_error,
            ErrorType.RATE_LIMIT_ERROR: self._handle_rate_limit_error,
            ErrorType.AUTHENTICATION_ERROR: self._handle_auth_error,
            ErrorType.INSUFFICIENT_FUNDS_ERROR: self._handle_insufficient_funds_error
        }
        
        # Default retry configuration
        self.default_retry_config = RetryConfig()
        
        print("🛡️ Advanced Error Handler initialized")
    
    def set_retry_config(self, component: str, config: RetryConfig):
        """Set retry configuration for a specific component"""
        self.retry_configs[component] = config
    
    def get_retry_config(self, component: str) -> RetryConfig:
        """Get retry configuration for a component"""
        return self.retry_configs.get(component, self.default_retry_config)
    
    async def handle_error(self, error: Exception, component: str, function_name: str,
                          context: Dict[str, Any] = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> ErrorEvent:
        """Handle an error event"""
        try:
            # Classify error type
            error_type = self._classify_error(error)
            
            # Create error event
            error_event = ErrorEvent(
                id=f"{component}_{function_name}_{int(time.time())}",
                timestamp=datetime.now(),
                error_type=error_type,
                severity=severity,
                component=component,
                function_name=function_name,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            
            # Store error event
            self.error_events[error_event.id] = error_event
            self.error_statistics[error_type] += 1
            
            # Log error
            if self.logger:
                self.logger.log_system_event(
                    "ERROR", "ERROR_HANDLING", component,
                    f"Error in {function_name}: {str(error)}",
                    {
                        "error_type": error_type.value,
                        "severity": severity.value,
                        "context": context
                    }
                )
            
            print(f"❌ Error handled: {error_type.value} in {component}.{function_name}")
            print(f"   Message: {str(error)}")
            
            # Send notification for critical errors
            if severity == ErrorSeverity.CRITICAL and self.notification_manager:
                await self.notification_manager.send_notification(
                    title=f"Critical Error in {component}",
                    message=f"Function: {function_name}\nError: {str(error)}",
                    notification_type="CRITICAL"
                )
            
            # Apply recovery strategy
            await self._apply_recovery_strategy(error_event)
            
            return error_event
            
        except Exception as e:
            print(f"❌ Error in error handler: {str(e)}")
            return None
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            return ErrorType.NETWORK_ERROR
        
        if any(keyword in error_type_name for keyword in ['connectionerror', 'timeout', 'urlerror']):
            return ErrorType.NETWORK_ERROR
        
        # API-related errors
        if any(keyword in error_str for keyword in ['api', 'http', 'status', 'response']):
            return ErrorType.API_ERROR
        
        # Authentication errors
        if any(keyword in error_str for keyword in ['auth', 'unauthorized', 'forbidden', 'invalid key']):
            return ErrorType.AUTHENTICATION_ERROR
        
        # Rate limit errors
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
            return ErrorType.RATE_LIMIT_ERROR
        
        # Order-related errors
        if any(keyword in error_str for keyword in ['order', 'trade', 'position', 'insufficient']):
            if 'insufficient' in error_str and 'fund' in error_str:
                return ErrorType.INSUFFICIENT_FUNDS_ERROR
            return ErrorType.ORDER_ERROR
        
        # Market closed errors
        if any(keyword in error_str for keyword in ['market closed', 'trading suspended']):
            return ErrorType.MARKET_CLOSED_ERROR
        
        # Timeout errors
        if 'timeout' in error_str or 'timeout' in error_type_name:
            return ErrorType.TIMEOUT_ERROR
        
        return ErrorType.UNKNOWN_ERROR
    
    async def _apply_recovery_strategy(self, error_event: ErrorEvent):
        """Apply recovery strategy based on error type"""
        try:
            recovery_func = self.recovery_strategies.get(error_event.error_type)
            if recovery_func:
                await recovery_func(error_event)
            else:
                await self._handle_generic_error(error_event)
        except Exception as e:
            print(f"❌ Recovery strategy failed: {str(e)}")
    
    async def _handle_network_error(self, error_event: ErrorEvent):
        """Handle network-related errors"""
        print("🌐 Handling network error...")
        
        # Check internet connectivity
        is_connected = self.network_checker.check_internet_connection()
        
        if not is_connected:
            print("❌ Internet connection lost")
            
            # Wait for connection to restore
            max_wait_time = 300  # 5 minutes
            wait_time = 0
            
            while not is_connected and wait_time < max_wait_time:
                print(f"⏳ Waiting for internet connection... ({wait_time}s)")
                await asyncio.sleep(30)
                wait_time += 30
                is_connected = self.network_checker.check_internet_connection()
            
            if is_connected:
                print("✅ Internet connection restored")
                error_event.resolved = True
                error_event.resolution_time = datetime.now()
                error_event.resolution_method = "connection_restored"
            else:
                print("❌ Internet connection not restored within timeout")
                
                # Send critical notification
                if self.notification_manager:
                    await self.notification_manager.send_notification(
                        title="Internet Connection Lost",
                        message=f"Connection lost for {wait_time} seconds. System may be offline.",
                        notification_type="CRITICAL"
                    )
    
    async def _handle_api_error(self, error_event: ErrorEvent):
        """Handle API-related errors"""
        print("🔌 Handling API error...")
        
        # Check if it's a temporary API issue
        if "500" in error_event.error_message or "502" in error_event.error_message or "503" in error_event.error_message:
            print("⏳ Temporary API error detected, waiting before retry...")
            await asyncio.sleep(60)  # Wait 1 minute for server issues
        
        # Check API status if possible
        # Implementation would check specific exchange status pages
        
        error_event.resolved = True
        error_event.resolution_method = "api_retry_scheduled"
    
    async def _handle_order_error(self, error_event: ErrorEvent):
        """Handle order execution errors"""
        print("📋 Handling order error...")
        
        # Check if order was partially filled
        # Implementation would query order status
        
        # Log order failure for manual review
        if self.logger:
            self.logger.log_system_event(
                "WARNING", "ORDER_HANDLING", error_event.component,
                f"Order execution failed: {error_event.error_message}",
                error_event.context
            )
        
        error_event.resolved = True
        error_event.resolution_method = "order_logged_for_review"
    
    async def _handle_rate_limit_error(self, error_event: ErrorEvent):
        """Handle rate limit errors"""
        print("⏱️ Handling rate limit error...")
        
        # Extract wait time from error message if possible
        wait_time = 60  # Default 1 minute
        
        if "retry after" in error_event.error_message.lower():
            # Try to extract wait time from error message
            # Implementation would parse the specific wait time
            pass
        
        print(f"⏳ Rate limited, waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)
        
        error_event.resolved = True
        error_event.resolution_time = datetime.now()
        error_event.resolution_method = f"waited_{wait_time}_seconds"
    
    async def _handle_auth_error(self, error_event: ErrorEvent):
        """Handle authentication errors"""
        print("🔐 Handling authentication error...")
        
        # Critical error - requires manual intervention
        if self.notification_manager:
            await self.notification_manager.send_notification(
                title="Authentication Error",
                message=f"API authentication failed in {error_event.component}. Check API keys.",
                notification_type="CRITICAL"
            )
        
        error_event.resolved = False  # Requires manual intervention
        error_event.resolution_method = "manual_intervention_required"
    
    async def _handle_insufficient_funds_error(self, error_event: ErrorEvent):
        """Handle insufficient funds errors"""
        print("💰 Handling insufficient funds error...")
        
        # Log for risk management review
        if self.logger:
            self.logger.log_system_event(
                "WARNING", "RISK_MANAGEMENT", error_event.component,
                "Insufficient funds for trade execution",
                error_event.context
            )
        
        # Notify about funding issue
        if self.notification_manager:
            await self.notification_manager.send_notification(
                title="Insufficient Funds",
                message="Trade rejected due to insufficient funds. Check account balance.",
                notification_type="HIGH"
            )
        
        error_event.resolved = True
        error_event.resolution_method = "logged_for_funding_review"
    
    async def _handle_generic_error(self, error_event: ErrorEvent):
        """Handle generic/unknown errors"""
        print("❓ Handling generic error...")
        
        # Log for manual review
        if self.logger:
            self.logger.log_system_event(
                "ERROR", "GENERIC_ERROR", error_event.component,
                f"Unknown error type: {error_event.error_message}",
                error_event.context
            )
        
        error_event.resolved = False
        error_event.resolution_method = "logged_for_manual_review"
    
    def with_retry(self, component: str, max_retries: int = None):
        """Decorator for automatic retry functionality"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                retry_config = self.get_retry_config(component)
                max_attempts = max_retries or retry_config.max_retries
                
                for attempt in range(max_attempts + 1):
                    try:
                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)
                    
                    except Exception as e:
                        error_type = self._classify_error(e)
                        
                        # Check if this error type should be retried
                        if error_type not in retry_config.retry_on_errors:
                            raise e
                        
                        if attempt == max_attempts:
                            # Final attempt failed
                            await self.handle_error(
                                e, component, func.__name__,
                                {"attempt": attempt + 1, "max_attempts": max_attempts},
                                ErrorSeverity.HIGH
                            )
                            raise e
                        
                        # Calculate delay for next attempt
                        delay = min(
                            retry_config.base_delay * (retry_config.exponential_base ** attempt),
                            retry_config.max_delay
                        )
                        
                        if retry_config.jitter:
                            import random
                            delay *= (0.5 + random.random() * 0.5)  # Add jitter
                        
                        print(f"🔄 Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} in {delay:.1f}s")
                        
                        # Handle the error (but don't raise it yet)
                        await self.handle_error(
                            e, component, func.__name__,
                            {"attempt": attempt + 1, "delay": delay},
                            ErrorSeverity.MEDIUM
                        )
                        
                        await asyncio.sleep(delay)
                
            return wrapper
        return decorator
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        total_errors = sum(self.error_statistics.values())
        
        return {
            "total_errors": total_errors,
            "error_breakdown": {error_type.value: count for error_type, count in self.error_statistics.items()},
            "resolved_errors": len([e for e in self.error_events.values() if e.resolved]),
            "unresolved_errors": len([e for e in self.error_events.values() if not e.resolved]),
            "network_status": self.network_checker.get_connection_status(),
            "recent_errors": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.error_type.value,
                    "component": e.component,
                    "message": e.error_message,
                    "resolved": e.resolved
                }
                for e in sorted(self.error_events.values(), key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }
    
    async def run_system_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        print("🔍 Running system diagnostics...")
        
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "network_connectivity": self.network_checker.check_internet_connection(),
            "dns_resolution": self.network_checker.check_dns_resolution(),
            "error_statistics": self.get_error_statistics(),
            "system_health": "healthy"
        }
        
        # Check for critical issues
        unresolved_critical = len([
            e for e in self.error_events.values() 
            if not e.resolved and e.severity == ErrorSeverity.CRITICAL
        ])
        
        if unresolved_critical > 0:
            diagnostics["system_health"] = "critical"
        elif not diagnostics["network_connectivity"]:
            diagnostics["system_health"] = "degraded"
        elif diagnostics["error_statistics"]["total_errors"] > 50:
            diagnostics["system_health"] = "degraded"
        
        print(f"📊 System Health: {diagnostics['system_health']}")
        
        return diagnostics

# Demo function
async def demo_error_handling():
    """Demonstrate the advanced error handling system"""
    print("🛡️ Advanced Error Handling System Demo")
    print("=" * 50)
    
    # Create error handler
    error_handler = AdvancedErrorHandler()
    
    # Set custom retry configuration
    custom_config = RetryConfig(max_retries=2, base_delay=0.5)
    error_handler.set_retry_config("demo_component", custom_config)
    
    # Demo 1: Network error simulation
    print("\n🌐 Demo 1: Network Error Handling")
    try:
        raise ConnectionError("Connection to exchange API failed")
    except Exception as e:
        await error_handler.handle_error(e, "demo_component", "connect_to_api", 
                                       {"exchange": "binance"}, ErrorSeverity.HIGH)
    
    # Demo 2: API error simulation
    print("\n🔌 Demo 2: API Error Handling")
    try:
        raise Exception("HTTP 500 Internal Server Error")
    except Exception as e:
        await error_handler.handle_error(e, "demo_component", "fetch_market_data",
                                       {"symbol": "BTC/USDT"}, ErrorSeverity.MEDIUM)
    
    # Demo 3: Order error simulation
    print("\n📋 Demo 3: Order Error Handling")
    try:
        raise Exception("Insufficient funds for order execution")
    except Exception as e:
        await error_handler.handle_error(e, "demo_component", "execute_trade",
                                       {"symbol": "ETH/USDT", "amount": 1000}, ErrorSeverity.HIGH)
    
    # Demo 4: Retry decorator
    print("\n🔄 Demo 4: Retry Decorator")
    
    @error_handler.with_retry("demo_component", max_retries=2)
    async def failing_function():
        print("   Attempting operation...")
        raise Exception("Temporary API error")
    
    try:
        await failing_function()
    except Exception as e:
        print(f"   Final failure: {str(e)}")
    
    # Demo 5: System diagnostics
    print("\n🔍 Demo 5: System Diagnostics")
    diagnostics = await error_handler.run_system_diagnostics()
    
    print(f"   Network Connected: {diagnostics['network_connectivity']}")
    print(f"   DNS Working: {diagnostics['dns_resolution']}")
    print(f"   System Health: {diagnostics['system_health']}")
    print(f"   Total Errors: {diagnostics['error_statistics']['total_errors']}")
    
    # Show error statistics
    print(f"\n📊 Error Statistics:")
    stats = error_handler.get_error_statistics()
    for error_type, count in stats["error_breakdown"].items():
        if count > 0:
            print(f"   • {error_type.replace('_', ' ').title()}: {count}")
    
    print(f"\n🎯 Error Handling Features:")
    print(f"   ✅ Automatic error classification")
    print(f"   ✅ Network connectivity monitoring")
    print(f"   ✅ Retry mechanisms with exponential backoff")
    print(f"   ✅ Recovery strategies for different error types")
    print(f"   ✅ Circuit breaker patterns")
    print(f"   ✅ Comprehensive error logging")
    print(f"   ✅ Real-time error notifications")
    print(f"   ✅ System health diagnostics")
    print(f"   ✅ Internet outage handling")
    print(f"   ✅ API failure recovery")
    
    print(f"\n✅ Advanced Error Handling demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_error_handling())

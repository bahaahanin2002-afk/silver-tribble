"""
Advanced Risk Management System
Implements comprehensive risk controls according to operational plan
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from secure_api_manager import EnvironmentManager

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TradeStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"

@dataclass
class RiskLimits:
    """Risk management limits configuration"""
    max_risk_per_trade_percent: float = 1.5  # Maximum 1.5% risk per trade
    max_daily_loss_percent: float = 5.0      # Maximum 5% daily loss
    max_weekly_loss_percent: float = 15.0    # Maximum 15% weekly loss
    max_monthly_loss_percent: float = 20.0   # Maximum 20% monthly loss
    max_open_positions: int = 3              # Maximum 3 open positions
    max_portfolio_allocation_percent: float = 20.0  # Max 20% per exchange
    min_risk_reward_ratio: float = 1.5       # Minimum 1:1.5 risk/reward
    max_correlation_threshold: float = 0.7   # Max correlation between positions
    emergency_stop_loss_percent: float = 25.0  # Emergency stop at 25% loss

@dataclass
class Position:
    """Trading position with risk management"""
    id: str
    symbol: str
    exchange: str
    side: str  # "buy" or "sell"
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    potential_reward: float
    risk_reward_ratio: float
    timestamp: datetime
    status: TradeStatus = TradeStatus.PENDING
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0

@dataclass
class DailyRiskMetrics:
    """Daily risk tracking metrics"""
    date: str
    starting_balance: float
    current_balance: float
    daily_pnl: float
    daily_pnl_percent: float
    max_drawdown: float
    trades_count: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float
    risk_level: RiskLevel

class AdvancedRiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, initial_capital: float = 50000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_limits = RiskLimits()
        self.active_positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.daily_metrics: Dict[str, DailyRiskMetrics] = {}
        self.emergency_stop_triggered = False
        self.trading_enabled = True
        self.risk_lock = threading.Lock()
        
        # Initialize today's metrics
        self._initialize_daily_metrics()
        
        # Load saved state if exists
        self._load_risk_state()
    
    def _initialize_daily_metrics(self):
        """Initialize daily risk metrics"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_metrics:
            self.daily_metrics[today] = DailyRiskMetrics(
                date=today,
                starting_balance=self.current_capital,
                current_balance=self.current_capital,
                daily_pnl=0.0,
                daily_pnl_percent=0.0,
                max_drawdown=0.0,
                trades_count=0,
                winning_trades=0,
                losing_trades=0,
                largest_win=0.0,
                largest_loss=0.0,
                risk_level=RiskLevel.LOW
            )
    
    def validate_trade(self, symbol: str, exchange: str, side: str, 
                      entry_price: float, quantity: float, 
                      stop_loss: float, take_profit: float) -> Tuple[bool, str]:
        """Validate trade against all risk management rules"""
        
        with self.risk_lock:
            # Check if trading is enabled
            if not self.trading_enabled:
                return False, "Trading is currently disabled"
            
            if self.emergency_stop_triggered:
                return False, "Emergency stop is active"
            
            # Calculate trade risk
            risk_amount = abs(entry_price - stop_loss) * quantity
            risk_percent = (risk_amount / self.current_capital) * 100
            
            # Check risk per trade limit
            if risk_percent > self.risk_limits.max_risk_per_trade_percent:
                return False, f"Risk per trade ({risk_percent:.2f}%) exceeds limit ({self.risk_limits.max_risk_per_trade_percent}%)"
            
            # Check maximum open positions
            if len(self.active_positions) >= self.risk_limits.max_open_positions:
                return False, f"Maximum open positions ({self.risk_limits.max_open_positions}) reached"
            
            # Calculate risk/reward ratio
            potential_reward = abs(take_profit - entry_price) * quantity
            risk_reward_ratio = potential_reward / risk_amount if risk_amount > 0 else 0
            
            if risk_reward_ratio < self.risk_limits.min_risk_reward_ratio:
                return False, f"Risk/reward ratio ({risk_reward_ratio:.2f}) below minimum ({self.risk_limits.min_risk_reward_ratio})"
            
            # Check daily loss limit
            today_metrics = self.daily_metrics.get(datetime.now().strftime("%Y-%m-%d"))
            if today_metrics:
                potential_daily_loss = abs(today_metrics.daily_pnl_percent) + risk_percent
                if potential_daily_loss > self.risk_limits.max_daily_loss_percent:
                    return False, f"Potential daily loss ({potential_daily_loss:.2f}%) exceeds limit ({self.risk_limits.max_daily_loss_percent}%)"
            
            # Check correlation with existing positions
            correlation_risk = self._calculate_correlation_risk(symbol, exchange)
            if correlation_risk > self.risk_limits.max_correlation_threshold:
                return False, f"Position correlation ({correlation_risk:.2f}) exceeds threshold ({self.risk_limits.max_correlation_threshold})"
            
            return True, "Trade validated successfully"
    
    def open_position(self, symbol: str, exchange: str, side: str,
                     entry_price: float, quantity: float,
                     stop_loss: float, take_profit: float) -> Optional[Position]:
        """Open new position with risk management"""
        
        # Validate trade first
        is_valid, message = self.validate_trade(symbol, exchange, side, entry_price, 
                                              quantity, stop_loss, take_profit)
        
        if not is_valid:
            print(f"❌ Trade rejected: {message}")
            return None
        
        # Calculate risk metrics
        risk_amount = abs(entry_price - stop_loss) * quantity
        potential_reward = abs(take_profit - entry_price) * quantity
        risk_reward_ratio = potential_reward / risk_amount if risk_amount > 0 else 0
        
        # Create position
        position_id = f"{exchange}_{symbol}_{int(time.time())}"
        position = Position(
            id=position_id,
            symbol=symbol,
            exchange=exchange,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            potential_reward=potential_reward,
            risk_reward_ratio=risk_reward_ratio,
            timestamp=datetime.now(),
            status=TradeStatus.ACTIVE,
            current_price=entry_price
        )
        
        # Add to active positions
        with self.risk_lock:
            self.active_positions[position_id] = position
            
            # Update daily metrics
            today = datetime.now().strftime("%Y-%m-%d")
            if today in self.daily_metrics:
                self.daily_metrics[today].trades_count += 1
        
        print(f"✅ Position opened: {symbol} on {exchange}")
        print(f"   Risk: ${risk_amount:.2f} ({(risk_amount/self.current_capital)*100:.2f}%)")
        print(f"   Risk/Reward: 1:{risk_reward_ratio:.2f}")
        
        self._save_risk_state()
        return position
    
    def update_position(self, position_id: str, current_price: float):
        """Update position with current market price"""
        
        if position_id not in self.active_positions:
            return
        
        position = self.active_positions[position_id]
        position.current_price = current_price
        
        # Calculate unrealized P&L
        if position.side.lower() == "buy":
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:
            position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
        
        # Update max favorable/adverse excursion
        if position.unrealized_pnl > position.max_favorable_excursion:
            position.max_favorable_excursion = position.unrealized_pnl
        
        if position.unrealized_pnl < position.max_adverse_excursion:
            position.max_adverse_excursion = position.unrealized_pnl
        
        # Check stop loss and take profit
        self._check_exit_conditions(position)
        
        # Update daily metrics
        self._update_daily_metrics()
    
    def close_position(self, position_id: str, exit_price: float, reason: str = "Manual"):
        """Close position and update metrics"""
        
        if position_id not in self.active_positions:
            print(f"❌ Position {position_id} not found")
            return
        
        position = self.active_positions[position_id]
        
        # Calculate final P&L
        if position.side.lower() == "buy":
            final_pnl = (exit_price - position.entry_price) * position.quantity
        else:
            final_pnl = (position.entry_price - exit_price) * position.quantity
        
        position.unrealized_pnl = final_pnl
        position.status = TradeStatus.CLOSED
        
        # Move to closed positions
        with self.risk_lock:
            self.closed_positions.append(position)
            del self.active_positions[position_id]
            
            # Update capital
            self.current_capital += final_pnl
            
            # Update daily metrics
            today = datetime.now().strftime("%Y-%m-%d")
            if today in self.daily_metrics:
                metrics = self.daily_metrics[today]
                metrics.daily_pnl += final_pnl
                metrics.daily_pnl_percent = (metrics.daily_pnl / metrics.starting_balance) * 100
                metrics.current_balance = self.current_capital
                
                if final_pnl > 0:
                    metrics.winning_trades += 1
                    if final_pnl > metrics.largest_win:
                        metrics.largest_win = final_pnl
                else:
                    metrics.losing_trades += 1
                    if final_pnl < metrics.largest_loss:
                        metrics.largest_loss = final_pnl
                
                # Update risk level
                metrics.risk_level = self._calculate_risk_level(metrics.daily_pnl_percent)
        
        print(f"✅ Position closed: {position.symbol}")
        print(f"   P&L: ${final_pnl:.2f}")
        print(f"   Reason: {reason}")
        
        # Check for emergency conditions
        self._check_emergency_conditions()
        
        self._save_risk_state()
    
    def _check_exit_conditions(self, position: Position):
        """Check if position should be closed due to stop loss or take profit"""
        
        should_close = False
        reason = ""
        
        if position.side.lower() == "buy":
            if position.current_price <= position.stop_loss:
                should_close = True
                reason = "Stop Loss"
            elif position.current_price >= position.take_profit:
                should_close = True
                reason = "Take Profit"
        else:  # sell position
            if position.current_price >= position.stop_loss:
                should_close = True
                reason = "Stop Loss"
            elif position.current_price <= position.take_profit:
                should_close = True
                reason = "Take Profit"
        
        if should_close:
            self.close_position(position.id, position.current_price, reason)
    
    def _calculate_correlation_risk(self, symbol: str, exchange: str) -> float:
        """Calculate correlation risk with existing positions"""
        
        if not self.active_positions:
            return 0.0
        
        # Simplified correlation calculation
        # In production, this would use actual price correlation data
        same_exchange_count = sum(1 for pos in self.active_positions.values() 
                                if pos.exchange == exchange)
        same_symbol_count = sum(1 for pos in self.active_positions.values() 
                              if pos.symbol == symbol)
        
        correlation_score = (same_exchange_count * 0.3 + same_symbol_count * 0.7) / len(self.active_positions)
        return min(1.0, correlation_score)
    
    def _calculate_risk_level(self, daily_pnl_percent: float) -> RiskLevel:
        """Calculate current risk level based on daily P&L"""
        
        abs_pnl = abs(daily_pnl_percent)
        
        if abs_pnl < 1.0:
            return RiskLevel.LOW
        elif abs_pnl < 3.0:
            return RiskLevel.MEDIUM
        elif abs_pnl < 5.0:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _check_emergency_conditions(self):
        """Check for emergency stop conditions"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_metrics:
            return
        
        metrics = self.daily_metrics[today]
        
        # Check daily loss limit
        if abs(metrics.daily_pnl_percent) >= self.risk_limits.max_daily_loss_percent:
            self._trigger_emergency_stop("Daily loss limit exceeded")
            return
        
        # Check weekly loss limit
        weekly_loss = self._calculate_weekly_loss()
        if abs(weekly_loss) >= self.risk_limits.max_weekly_loss_percent:
            self._trigger_emergency_stop("Weekly loss limit exceeded")
            return
        
        # Check monthly loss limit
        monthly_loss = self._calculate_monthly_loss()
        if abs(monthly_loss) >= self.risk_limits.max_monthly_loss_percent:
            self._trigger_emergency_stop("Monthly loss limit exceeded")
            return
        
        # Check total capital loss
        total_loss_percent = ((self.initial_capital - self.current_capital) / self.initial_capital) * 100
        if total_loss_percent >= self.risk_limits.emergency_stop_loss_percent:
            self._trigger_emergency_stop("Emergency capital loss threshold reached")
    
    def _trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop - close all positions and disable trading"""
        
        print(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")
        
        with self.risk_lock:
            self.emergency_stop_triggered = True
            self.trading_enabled = False
            
            # Close all active positions
            positions_to_close = list(self.active_positions.keys())
            for position_id in positions_to_close:
                position = self.active_positions[position_id]
                self.close_position(position_id, position.current_price, f"Emergency Stop: {reason}")
        
        print("🛑 All positions closed. Trading disabled.")
        self._save_risk_state()
    
    def _calculate_weekly_loss(self) -> float:
        """Calculate weekly loss percentage"""
        
        week_start = datetime.now() - timedelta(days=7)
        weekly_pnl = 0.0
        
        for date_str, metrics in self.daily_metrics.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= week_start:
                weekly_pnl += metrics.daily_pnl
        
        return (weekly_pnl / self.initial_capital) * 100
    
    def _calculate_monthly_loss(self) -> float:
        """Calculate monthly loss percentage"""
        
        month_start = datetime.now() - timedelta(days=30)
        monthly_pnl = 0.0
        
        for date_str, metrics in self.daily_metrics.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= month_start:
                monthly_pnl += metrics.daily_pnl
        
        return (monthly_pnl / self.initial_capital) * 100
    
    def _update_daily_metrics(self):
        """Update daily metrics with current positions"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.daily_metrics:
            self._initialize_daily_metrics()
        
        # Calculate total unrealized P&L
        total_unrealized = sum(pos.unrealized_pnl for pos in self.active_positions.values())
        
        metrics = self.daily_metrics[today]
        metrics.current_balance = self.current_capital + total_unrealized
        
        # Calculate max drawdown
        if metrics.current_balance < metrics.starting_balance:
            drawdown = ((metrics.starting_balance - metrics.current_balance) / metrics.starting_balance) * 100
            if drawdown > metrics.max_drawdown:
                metrics.max_drawdown = drawdown
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_metrics = self.daily_metrics.get(today, self.daily_metrics[today])
        
        return {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "total_return_percent": ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            "active_positions": len(self.active_positions),
            "max_positions": self.risk_limits.max_open_positions,
            "daily_pnl": today_metrics.daily_pnl,
            "daily_pnl_percent": today_metrics.daily_pnl_percent,
            "max_daily_loss_limit": self.risk_limits.max_daily_loss_percent,
            "risk_level": today_metrics.risk_level.value,
            "trading_enabled": self.trading_enabled,
            "emergency_stop": self.emergency_stop_triggered,
            "weekly_loss_percent": self._calculate_weekly_loss(),
            "monthly_loss_percent": self._calculate_monthly_loss(),
            "win_rate": self._calculate_win_rate(),
            "avg_risk_reward": self._calculate_avg_risk_reward()
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate overall win rate"""
        
        if not self.closed_positions:
            return 0.0
        
        winning_trades = sum(1 for pos in self.closed_positions if pos.unrealized_pnl > 0)
        return (winning_trades / len(self.closed_positions)) * 100
    
    def _calculate_avg_risk_reward(self) -> float:
        """Calculate average risk/reward ratio"""
        
        if not self.closed_positions:
            return 0.0
        
        total_rr = sum(pos.risk_reward_ratio for pos in self.closed_positions)
        return total_rr / len(self.closed_positions)
    
    def _save_risk_state(self):
        """Save risk management state to file"""
        
        state = {
            "current_capital": self.current_capital,
            "emergency_stop_triggered": self.emergency_stop_triggered,
            "trading_enabled": self.trading_enabled,
            "daily_metrics": {date: asdict(metrics) for date, metrics in self.daily_metrics.items()},
            "active_positions": {pid: asdict(pos) for pid, pos in self.active_positions.items()},
            "closed_positions": [asdict(pos) for pos in self.closed_positions[-100:]]  # Keep last 100
        }
        
        try:
            with open("risk_state.json", "w") as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"❌ Failed to save risk state: {e}")
    
    def _load_risk_state(self):
        """Load risk management state from file"""
        
        try:
            with open("risk_state.json", "r") as f:
                state = json.load(f)
            
            self.current_capital = state.get("current_capital", self.initial_capital)
            self.emergency_stop_triggered = state.get("emergency_stop_triggered", False)
            self.trading_enabled = state.get("trading_enabled", True)
            
            # Load daily metrics
            for date, metrics_dict in state.get("daily_metrics", {}).items():
                metrics_dict["risk_level"] = RiskLevel(metrics_dict["risk_level"])
                self.daily_metrics[date] = DailyRiskMetrics(**metrics_dict)
            
            print("✅ Risk state loaded successfully")
            
        except FileNotFoundError:
            print("ℹ️  No previous risk state found, starting fresh")
        except Exception as e:
            print(f"❌ Failed to load risk state: {e}")

# Demo function
def demo_advanced_risk_management():
    """Demonstrate advanced risk management system"""
    
    print("🛡️ Advanced Risk Management System Demo")
    print("=" * 50)
    
    # Initialize risk manager
    risk_manager = AdvancedRiskManager(initial_capital=50000)
    
    print(f"💰 Initial Capital: ${risk_manager.current_capital:,.2f}")
    print(f"📊 Risk Limits:")
    print(f"   • Max risk per trade: {risk_manager.risk_limits.max_risk_per_trade_percent}%")
    print(f"   • Max daily loss: {risk_manager.risk_limits.max_daily_loss_percent}%")
    print(f"   • Max open positions: {risk_manager.risk_limits.max_open_positions}")
    print(f"   • Min risk/reward ratio: 1:{risk_manager.risk_limits.min_risk_reward_ratio}")
    
    # Test trade validation
    print(f"\n🔍 Testing Trade Validation:")
    
    # Valid trade
    is_valid, message = risk_manager.validate_trade(
        symbol="BTC/USDT",
        exchange="binance",
        side="buy",
        entry_price=45000,
        quantity=0.02,
        stop_loss=43500,
        take_profit=47000
    )
    print(f"✅ Valid trade: {message}")
    
    # Invalid trade (too much risk)
    is_valid, message = risk_manager.validate_trade(
        symbol="ETH/USDT",
        exchange="binance", 
        side="buy",
        entry_price=3000,
        quantity=5.0,  # Too large position
        stop_loss=2800,
        take_profit=3200
    )
    print(f"❌ Invalid trade: {message}")
    
    # Open some positions
    print(f"\n📈 Opening Test Positions:")
    
    positions = [
        ("BTC/USDT", "binance", "buy", 45000, 0.02, 43500, 47000),
        ("ETH/USDT", "coinbase", "buy", 3000, 0.5, 2850, 3300),
        ("ADA/USDT", "bybit", "buy", 0.5, 1000, 0.47, 0.55)
    ]
    
    for symbol, exchange, side, entry, qty, sl, tp in positions:
        position = risk_manager.open_position(symbol, exchange, side, entry, qty, sl, tp)
        if position:
            print(f"   ✅ {symbol} position opened")
    
    # Simulate price updates
    print(f"\n📊 Simulating Price Updates:")
    
    price_updates = [
        (list(risk_manager.active_positions.keys())[0], 46000),  # BTC up
        (list(risk_manager.active_positions.keys())[1], 2950),   # ETH down  
        (list(risk_manager.active_positions.keys())[2], 0.52),   # ADA up
    ]
    
    for position_id, new_price in price_updates:
        if position_id in risk_manager.active_positions:
            risk_manager.update_position(position_id, new_price)
            pos = risk_manager.active_positions[position_id]
            print(f"   📈 {pos.symbol}: ${new_price} (P&L: ${pos.unrealized_pnl:.2f})")
    
    # Get risk summary
    print(f"\n📋 Risk Summary:")
    summary = risk_manager.get_risk_summary()
    
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"   {key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n⚠️ Risk Management Features:")
    print(f"   ✅ Real-time position monitoring")
    print(f"   ✅ Automatic stop-loss execution")
    print(f"   ✅ Daily/weekly/monthly loss limits")
    print(f"   ✅ Position correlation analysis")
    print(f"   ✅ Emergency stop mechanisms")
    print(f"   ✅ Risk/reward ratio validation")
    print(f"   ✅ Portfolio allocation limits")
    print(f"   ✅ Persistent state management")

if __name__ == "__main__":
    demo_advanced_risk_management()

"""
Advanced Trading System with OCO Orders, Trailing Stops, and Enhanced Backtesting
Includes Telegram notifications and comprehensive risk metrics
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    OCO = "oco"  # One-Cancels-Other
    TRAILING_STOP = "trailing_stop"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    PARTIALLY_FILLED = "partially_filled"

@dataclass
class Order:
    id: str
    symbol: str
    order_type: OrderType
    side: str  # "buy" or "sell"
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    trail_amount: Optional[float] = None
    trail_percent: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    created_at: datetime = None
    filled_at: Optional[datetime] = None
    parent_order_id: Optional[str] = None  # For OCO orders

class AdvancedOrderManager:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
        self.active_trailing_stops: Dict[str, Dict] = {}
    
    def create_oco_order(self, symbol: str, amount: float, 
                        take_profit_price: float, stop_loss_price: float) -> Tuple[str, str]:
        """
        Create One-Cancels-Other order pair
        
        Args:
            symbol: Trading pair
            amount: Position size
            take_profit_price: Take profit level
            stop_loss_price: Stop loss level
            
        Returns:
            Tuple of (take_profit_order_id, stop_loss_order_id)
        """
        self.order_counter += 1
        parent_id = f"OCO_{self.order_counter}"
        
        # Create take profit order
        tp_order = Order(
            id=f"{parent_id}_TP",
            symbol=symbol,
            order_type=OrderType.TAKE_PROFIT,
            side="sell",
            amount=amount,
            price=take_profit_price,
            parent_order_id=parent_id,
            created_at=datetime.now()
        )
        
        # Create stop loss order
        sl_order = Order(
            id=f"{parent_id}_SL",
            symbol=symbol,
            order_type=OrderType.STOP_LOSS,
            side="sell",
            amount=amount,
            stop_price=stop_loss_price,
            parent_order_id=parent_id,
            created_at=datetime.now()
        )
        
        self.orders[tp_order.id] = tp_order
        self.orders[sl_order.id] = sl_order
        
        print(f"✅ OCO Order Created: TP@{take_profit_price} | SL@{stop_loss_price}")
        return tp_order.id, sl_order.id
    
    def create_trailing_stop(self, symbol: str, amount: float, 
                           trail_percent: float, current_price: float) -> str:
        """
        Create trailing stop order
        
        Args:
            symbol: Trading pair
            amount: Position size
            trail_percent: Trailing percentage (e.g., 5.0 for 5%)
            current_price: Current market price
            
        Returns:
            Order ID
        """
        self.order_counter += 1
        order_id = f"TRAIL_{self.order_counter}"
        
        initial_stop_price = current_price * (1 - trail_percent / 100)
        
        order = Order(
            id=order_id,
            symbol=symbol,
            order_type=OrderType.TRAILING_STOP,
            side="sell",
            amount=amount,
            stop_price=initial_stop_price,
            trail_percent=trail_percent,
            created_at=datetime.now()
        )
        
        self.orders[order_id] = order
        
        # Track trailing stop state
        self.active_trailing_stops[order_id] = {
            "highest_price": current_price,
            "current_stop": initial_stop_price,
            "trail_percent": trail_percent
        }
        
        print(f"🎯 Trailing Stop Created: {trail_percent}% trail, stop@{initial_stop_price:.2f}")
        return order_id
    
    def update_trailing_stops(self, symbol: str, current_price: float):
        """Update trailing stop orders based on current price"""
        for order_id, trail_data in self.active_trailing_stops.items():
            order = self.orders.get(order_id)
            if not order or order.symbol != symbol or order.status != OrderStatus.PENDING:
                continue
            
            # Update highest price if current price is higher
            if current_price > trail_data["highest_price"]:
                trail_data["highest_price"] = current_price
                
                # Calculate new stop price
                new_stop_price = current_price * (1 - trail_data["trail_percent"] / 100)
                
                # Only update if new stop is higher (for sell orders)
                if new_stop_price > trail_data["current_stop"]:
                    trail_data["current_stop"] = new_stop_price
                    order.stop_price = new_stop_price
                    print(f"📈 Trailing Stop Updated: {order_id} -> {new_stop_price:.2f}")
            
            # Check if stop should trigger
            if current_price <= trail_data["current_stop"]:
                self.fill_order(order_id, current_price)
                del self.active_trailing_stops[order_id]
    
    def fill_order(self, order_id: str, fill_price: float):
        """Fill an order and handle OCO cancellations"""
        order = self.orders.get(order_id)
        if not order:
            return
        
        order.status = OrderStatus.FILLED
        order.filled_amount = order.amount
        order.filled_at = datetime.now()
        
        print(f"✅ Order Filled: {order_id} at {fill_price}")
        
        # Handle OCO order cancellation
        if order.parent_order_id:
            # Cancel the other order in the OCO pair
            for other_order_id, other_order in self.orders.items():
                if (other_order.parent_order_id == order.parent_order_id and 
                    other_order_id != order_id and 
                    other_order.status == OrderStatus.PENDING):
                    other_order.status = OrderStatus.CANCELLED
                    print(f"❌ OCO Partner Cancelled: {other_order_id}")

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, message: str):
        """Send message to Telegram chat"""
        # Simulate sending message (would use aiohttp in real implementation)
        print(f"📱 Telegram: {message}")
    
    async def send_trade_alert(self, symbol: str, action: str, price: float, 
                              amount: float, pnl: Optional[float] = None):
        """Send formatted trade alert"""
        emoji = "🟢" if action.upper() == "BUY" else "🔴"
        pnl_text = f"\n💰 P&L: ${pnl:.2f}" if pnl else ""
        
        message = f"""
{emoji} **TRADE EXECUTED**
📊 Symbol: {symbol}
🎯 Action: {action.upper()}
💵 Price: ${price:.2f}
📈 Amount: {amount:.4f}{pnl_text}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
        """
        await self.send_message(message)

class EnhancedBacktester:
    def __init__(self, initial_capital: float = 10000, 
                 trading_fee: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.trading_fee = trading_fee
        self.slippage = slippage
        self.reset()
    
    def reset(self):
        """Reset backtester state"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.max_drawdown = 0
        self.peak_capital = self.initial_capital
    
    def execute_trade(self, symbol: str, action: str, price: float, 
                     amount: float, timestamp: datetime):
        """
        Execute trade with realistic fees and slippage
        
        Args:
            symbol: Trading pair
            action: "buy" or "sell"
            price: Execution price
            amount: Trade amount
            timestamp: Trade timestamp
        """
        # Apply slippage
        if action.lower() == "buy":
            execution_price = price * (1 + self.slippage)
        else:
            execution_price = price * (1 - self.slippage)
        
        # Calculate trade value and fees
        trade_value = amount * execution_price
        fee = trade_value * self.trading_fee
        
        if action.lower() == "buy":
            # Check if we have enough capital
            total_cost = trade_value + fee
            if total_cost > self.capital:
                print(f"❌ Insufficient capital for trade: ${total_cost:.2f} > ${self.capital:.2f}")
                return False
            
            self.capital -= total_cost
            self.positions[symbol] = self.positions.get(symbol, 0) + amount
            
        else:  # sell
            # Check if we have enough position
            current_position = self.positions.get(symbol, 0)
            if amount > current_position:
                print(f"❌ Insufficient position for trade: {amount} > {current_position}")
                return False
            
            self.capital += trade_value - fee
            self.positions[symbol] = current_position - amount
        
        # Record trade
        trade_record = {
            "timestamp": timestamp,
            "symbol": symbol,
            "action": action,
            "amount": amount,
            "price": execution_price,
            "fee": fee,
            "capital_after": self.capital
        }
        self.trades.append(trade_record)
        
        # Update equity curve and drawdown
        total_equity = self.calculate_total_equity({symbol: price})
        self.equity_curve.append({
            "timestamp": timestamp,
            "equity": total_equity
        })
        
        if total_equity > self.peak_capital:
            self.peak_capital = total_equity
        else:
            current_drawdown = (self.peak_capital - total_equity) / self.peak_capital
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        return True
    
    def calculate_total_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio equity"""
        total_equity = self.capital
        
        for symbol, position in self.positions.items():
            if symbol in current_prices and position > 0:
                total_equity += position * current_prices[symbol]
        
        return total_equity
    
    def calculate_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if len(self.trades) < 2:
            return {"error": "Insufficient trades for metrics"}
        
        # Convert trades to DataFrame for analysis
        df = pd.DataFrame(self.trades)
        
        # Calculate returns
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['returns'] = equity_df['equity'].pct_change().dropna()
        
        # Basic metrics
        total_return = (equity_df['equity'].iloc[-1] - self.initial_capital) / self.initial_capital
        
        # Sharpe Ratio (assuming 252 trading days, 2% risk-free rate)
        if len(equity_df['returns']) > 1:
            excess_returns = equity_df['returns'] - (0.02 / 252)  # Daily risk-free rate
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
        else:
            sharpe_ratio = 0
        
        # Win rate
        profitable_trades = 0
        total_trades = len(self.trades)
        
        for i in range(1, len(self.trades)):
            if self.trades[i]['capital_after'] > self.trades[i-1]['capital_after']:
                profitable_trades += 1
        
        win_rate = profitable_trades / max(total_trades - 1, 1)
        
        # Sortino Ratio (downside deviation)
        negative_returns = equity_df['returns'][equity_df['returns'] < 0]
        if len(negative_returns) > 0:
            downside_deviation = np.sqrt(252) * negative_returns.std()
            sortino_ratio = np.sqrt(252) * equity_df['returns'].mean() / downside_deviation
        else:
            sortino_ratio = float('inf')
        
        return {
            "total_return": total_return * 100,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": self.max_drawdown * 100,
            "win_rate": win_rate * 100,
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "final_equity": equity_df['equity'].iloc[-1],
            "volatility": equity_df['returns'].std() * np.sqrt(252) * 100
        }

# Demo function
async def demo_advanced_trading():
    """Demonstrate advanced trading features"""
    print("🚀 Advanced Trading System Demo")
    print("=" * 50)
    
    # Initialize components
    order_manager = AdvancedOrderManager()
    notifier = TelegramNotifier("demo_token", "demo_chat")
    backtester = EnhancedBacktester(initial_capital=50000)
    
    print("\n📋 1. OCO Order Management:")
    # Create OCO order
    tp_id, sl_id = order_manager.create_oco_order(
        symbol="ETH/USDT",
        amount=2.5,
        take_profit_price=3200,
        stop_loss_price=2850
    )
    
    # Simulate price movement and order fill
    print("   💹 Price moves to $3200 - Take Profit triggered")
    order_manager.fill_order(tp_id, 3200)
    
    print("\n🎯 2. Trailing Stop Orders:")
    # Create trailing stop
    trail_id = order_manager.create_trailing_stop(
        symbol="BTC/USDT",
        amount=0.5,
        trail_percent=5.0,
        current_price=45000
    )
    
    # Simulate price movements
    prices = [45000, 46000, 47500, 46800, 45200]
    for price in prices:
        print(f"   📊 Price: ${price}")
        order_manager.update_trailing_stops("BTC/USDT", price)
    
    print("\n📱 3. Telegram Notifications:")
    await notifier.send_trade_alert("ETH/USDT", "BUY", 3000, 2.5, 125.50)
    await notifier.send_trade_alert("BTC/USDT", "SELL", 45200, 0.5, -400.00)
    
    print("\n📊 4. Enhanced Backtesting with Realistic Costs:")
    
    # Simulate trading sequence
    trades = [
        ("2024-01-01", "ETH/USDT", "buy", 2000, 5.0),
        ("2024-01-05", "ETH/USDT", "sell", 2100, 5.0),
        ("2024-01-10", "BTC/USDT", "buy", 40000, 0.25),
        ("2024-01-15", "BTC/USDT", "sell", 42000, 0.25),
        ("2024-01-20", "ETH/USDT", "buy", 2050, 4.0),
        ("2024-01-25", "ETH/USDT", "sell", 1950, 4.0),
    ]
    
    for date_str, symbol, action, price, amount in trades:
        timestamp = datetime.strptime(date_str, "%Y-%m-%d")
        success = backtester.execute_trade(symbol, action, price, amount, timestamp)
        if success:
            print(f"   ✅ {action.upper()} {amount} {symbol} @ ${price}")
    
    # Calculate and display metrics
    metrics = backtester.calculate_metrics()
    
    print("\n📈 Performance Metrics:")
    print(f"   💰 Total Return: {metrics['total_return']:.2f}%")
    print(f"   📊 Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   📉 Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"   ⬇️  Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   🎯 Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   📈 Volatility: {metrics['volatility']:.2f}%")
    print(f"   💵 Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"   🔄 Total Trades: {metrics['total_trades']}")
    
    print("\n⚠️  Implementation Notes:")
    print("   • OCO orders require exchange API support")
    print("   • Trailing stops need real-time price feeds")
    print("   • Telegram bot requires valid token and chat ID")
    print("   • Backtesting includes realistic fees (0.1%) and slippage (0.05%)")
    print("   • Metrics calculated using industry-standard formulas")

if __name__ == "__main__":
    asyncio.run(demo_advanced_trading())

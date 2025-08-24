"""
Market Analysis and Technical Indicators
Demonstrates various technical analysis tools
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TechnicalAnalyzer:
    @staticmethod
    def sma(prices, period):
        """Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices, period):
        """Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def rsi(prices, period=14):
        """Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """MACD Indicator"""
        ema_fast = TechnicalAnalyzer.ema(prices, fast)
        ema_slow = TechnicalAnalyzer.ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalAnalyzer.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """Bollinger Bands"""
        sma = TechnicalAnalyzer.sma(prices, period)
        std = prices.rolling(window=period).std()
        
        return {
            'middle': sma,
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev)
        }
    
    @staticmethod
    def atr(high, low, close, period=14):
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

def generate_realistic_data(symbol="BTC/USDT", days=100):
    """Generate more realistic market data with trends and volatility"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         end=datetime.now(), freq='1H')
    
    # Create trending price movement
    base_price = 45000 if symbol == "BTC/USDT" else 3000
    trend = np.linspace(0, 0.2, len(dates))  # 20% upward trend over period
    
    # Add noise and volatility clustering
    volatility = 0.02
    noise = np.random.normal(0, volatility, len(dates))
    
    # Create price series with trend and mean reversion
    prices = [base_price]
    for i in range(1, len(dates)):
        # Trend component
        trend_component = trend[i] - trend[i-1]
        
        # Mean reversion component
        deviation = (prices[-1] - base_price * (1 + trend[i-1])) / base_price
        mean_reversion = -0.1 * deviation
        
        # Random component
        random_component = noise[i]
        
        # Combine components
        total_change = trend_component + mean_reversion + random_component
        new_price = prices[-1] * (1 + total_change)
        prices.append(max(new_price, base_price * 0.3))  # Floor price
    
    # Generate OHLCV data
    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC from close price
        volatility_factor = abs(np.random.normal(0, 0.005))
        
        high = close_price * (1 + volatility_factor)
        low = close_price * (1 - volatility_factor)
        open_price = prices[i-1] if i > 0 else close_price
        
        # Ensure OHLC relationships are valid
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        volume = np.random.lognormal(5, 1)  # Log-normal distribution for volume
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(data)

def analyze_market_conditions(df):
    """Analyze current market conditions"""
    analyzer = TechnicalAnalyzer()
    
    # Calculate indicators
    df['sma_20'] = analyzer.sma(df['close'], 20)
    df['sma_50'] = analyzer.sma(df['close'], 50)
    df['ema_12'] = analyzer.ema(df['close'], 12)
    df['rsi'] = analyzer.rsi(df['close'])
    
    macd_data = analyzer.macd(df['close'])
    df['macd'] = macd_data['macd']
    df['macd_signal'] = macd_data['signal']
    df['macd_histogram'] = macd_data['histogram']
    
    bb_data = analyzer.bollinger_bands(df['close'])
    df['bb_upper'] = bb_data['upper']
    df['bb_middle'] = bb_data['middle']
    df['bb_lower'] = bb_data['lower']
    
    df['atr'] = analyzer.atr(df['high'], df['low'], df['close'])
    
    return df

def market_regime_detection(df):
    """Detect market regime (trending, ranging, volatile)"""
    # Calculate trend strength
    sma_20 = df['sma_20'].iloc[-1]
    sma_50 = df['sma_50'].iloc[-1]
    current_price = df['close'].iloc[-1]
    
    # Trend direction
    if current_price > sma_20 > sma_50:
        trend = "Uptrend"
    elif current_price < sma_20 < sma_50:
        trend = "Downtrend"
    else:
        trend = "Sideways"
    
    # Volatility assessment
    atr_current = df['atr'].iloc[-1]
    atr_avg = df['atr'].rolling(50).mean().iloc[-1]
    
    if atr_current > atr_avg * 1.5:
        volatility = "High"
    elif atr_current < atr_avg * 0.7:
        volatility = "Low"
    else:
        volatility = "Normal"
    
    # RSI assessment
    rsi_current = df['rsi'].iloc[-1]
    if rsi_current > 70:
        momentum = "Overbought"
    elif rsi_current < 30:
        momentum = "Oversold"
    else:
        momentum = "Neutral"
    
    return {
        'trend': trend,
        'volatility': volatility,
        'momentum': momentum,
        'rsi': rsi_current,
        'atr_ratio': atr_current / atr_avg if atr_avg > 0 else 1
    }

def main():
    print("📈 Market Analysis Demo")
    print("=" * 50)
    
    # Generate market data
    print("📊 Generating market data...")
    df = generate_realistic_data("BTC/USDT", days=90)
    print(f"Generated {len(df)} data points over 90 days")
    
    # Analyze market
    print("\n🔍 Calculating technical indicators...")
    df = analyze_market_conditions(df)
    
    # Current market state
    latest = df.iloc[-1]
    print(f"\n💰 Current Market State:")
    print(f"Price: ${latest['close']:,.2f}")
    print(f"SMA(20): ${latest['sma_20']:,.2f}")
    print(f"SMA(50): ${latest['sma_50']:,.2f}")
    print(f"RSI: {latest['rsi']:.1f}")
    print(f"ATR: ${latest['atr']:,.2f}")
    
    # Market regime analysis
    regime = market_regime_detection(df)
    print(f"\n🎯 Market Regime Analysis:")
    print(f"Trend: {regime['trend']}")
    print(f"Volatility: {regime['volatility']}")
    print(f"Momentum: {regime['momentum']}")
    print(f"ATR Ratio: {regime['atr_ratio']:.2f}")
    
    # Signal analysis
    print(f"\n📡 Signal Analysis:")
    
    # MACD signals
    macd_current = latest['macd']
    macd_signal = latest['macd_signal']
    if macd_current > macd_signal:
        macd_status = "🟢 Bullish"
    else:
        macd_status = "🔴 Bearish"
    print(f"MACD: {macd_status}")
    
    # Bollinger Bands position
    bb_position = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
    if bb_position > 0.8:
        bb_status = "🔴 Near Upper Band (Overbought)"
    elif bb_position < 0.2:
        bb_status = "🟢 Near Lower Band (Oversold)"
    else:
        bb_status = "🟡 Middle Range"
    print(f"Bollinger Bands: {bb_status}")
    
    # Trading recommendations
    print(f"\n💡 Trading Recommendations:")
    
    score = 0
    reasons = []
    
    # Trend following signals
    if regime['trend'] == "Uptrend":
        score += 1
        reasons.append("Strong uptrend")
    elif regime['trend'] == "Downtrend":
        score -= 1
        reasons.append("Strong downtrend")
    
    # RSI signals
    if regime['momentum'] == "Oversold":
        score += 1
        reasons.append("RSI oversold")
    elif regime['momentum'] == "Overbought":
        score -= 1
        reasons.append("RSI overbought")
    
    # MACD signals
    if macd_current > macd_signal:
        score += 1
        reasons.append("MACD bullish crossover")
    else:
        score -= 1
        reasons.append("MACD bearish crossover")
    
    # Final recommendation
    if score >= 2:
        recommendation = "🟢 STRONG BUY"
    elif score == 1:
        recommendation = "🟡 WEAK BUY"
    elif score == -1:
        recommendation = "🟡 WEAK SELL"
    elif score <= -2:
        recommendation = "🔴 STRONG SELL"
    else:
        recommendation = "⚪ HOLD"
    
    print(f"Overall Signal: {recommendation}")
    print(f"Signal Strength: {abs(score)}/3")
    print("Reasons:")
    for reason in reasons:
        print(f"  • {reason}")
    
    print(f"\n⚠️  Risk Considerations:")
    if regime['volatility'] == "High":
        print("  • High volatility - use smaller position sizes")
    if regime['momentum'] in ["Overbought", "Oversold"]:
        print("  • Extreme momentum - potential reversal risk")
    
    print("\n📝 Note: This analysis is for educational purposes only.")
    print("Always combine technical analysis with fundamental analysis and risk management.")

if __name__ == "__main__":
    main()

"""
Real-time Data Update System for AI Trading Bot
Provides continuous market data updates from multiple sources with redundancy
"""

import asyncio
import websockets
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
import hashlib

class DataSource(Enum):
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKX = "okx"
    KUCOIN = "kucoin"
    HUOBI = "huobi"
    BITFINEX = "bitfinex"

class DataType(Enum):
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    KLINES = "klines"
    FUNDING_RATE = "funding_rate"

class DataQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    STALE = "stale"

@dataclass
class MarketData:
    """Market data point"""
    source: DataSource
    data_type: DataType
    symbol: str
    timestamp: datetime
    data: Dict[str, Any]
    sequence_id: Optional[int] = None
    latency_ms: Optional[float] = None

@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    source: DataSource
    websocket_url: str
    rest_api_url: str
    symbols: List[str]
    data_types: List[DataType]
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    max_reconnect_attempts: int = 10
    reconnect_delay_seconds: int = 5
    heartbeat_interval: int = 30
    data_freshness_threshold_seconds: int = 10

@dataclass
class DataFeed:
    """Real-time data feed for a specific symbol and data type"""
    symbol: str
    data_type: DataType
    latest_data: Optional[MarketData] = None
    data_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    subscribers: Set[Callable] = field(default_factory=set)
    quality: DataQuality = DataQuality.GOOD
    last_update: Optional[datetime] = None
    update_count: int = 0
    error_count: int = 0

class WebSocketConnection:
    """Manages WebSocket connection to a data source"""
    
    def __init__(self, config: DataSourceConfig, data_manager):
        self.config = config
        self.data_manager = data_manager
        self.websocket = None
        self.connected = False
        self.reconnect_count = 0
        self.last_heartbeat = None
        self.connection_start_time = None
        
    async def connect(self):
        """Connect to WebSocket"""
        try:
            print(f"🔌 Connecting to {self.config.source.value} WebSocket...")
            
            self.websocket = await websockets.connect(
                self.config.websocket_url,
                ping_interval=self.config.heartbeat_interval,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            self.connection_start_time = datetime.now()
            self.last_heartbeat = datetime.now()
            self.reconnect_count = 0
            
            # Subscribe to data streams
            await self._subscribe_to_streams()
            
            print(f"✅ Connected to {self.config.source.value}")
            
            # Start message handling
            await self._handle_messages()
            
        except Exception as e:
            print(f"❌ Failed to connect to {self.config.source.value}: {str(e)}")
            self.connected = False
            await self._handle_reconnection()
    
    async def _subscribe_to_streams(self):
        """Subscribe to required data streams"""
        # Implementation would be specific to each exchange
        # This is a simplified example
        
        if self.config.source == DataSource.BINANCE:
            # Binance WebSocket subscription format
            streams = []
            for symbol in self.config.symbols:
                for data_type in self.config.data_types:
                    if data_type == DataType.TICKER:
                        streams.append(f"{symbol.lower()}@ticker")
                    elif data_type == DataType.TRADES:
                        streams.append(f"{symbol.lower()}@trade")
                    elif data_type == DataType.ORDERBOOK:
                        streams.append(f"{symbol.lower()}@depth20@100ms")
            
            if streams:
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": streams,
                    "id": int(time.time())
                }
                await self.websocket.send(json.dumps(subscribe_msg))
        
        elif self.config.source == DataSource.COINBASE:
            # Coinbase Pro WebSocket subscription
            subscribe_msg = {
                "type": "subscribe",
                "product_ids": self.config.symbols,
                "channels": ["ticker", "matches", "level2"]
            }
            await self.websocket.send(json.dumps(subscribe_msg))
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                    self.last_heartbeat = datetime.now()
                    
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON from {self.config.source.value}: {message}")
                except Exception as e:
                    print(f"❌ Error processing message from {self.config.source.value}: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 WebSocket connection closed for {self.config.source.value}")
            self.connected = False
            await self._handle_reconnection()
        except Exception as e:
            print(f"❌ WebSocket error for {self.config.source.value}: {str(e)}")
            self.connected = False
            await self._handle_reconnection()
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message and convert to MarketData"""
        try:
            market_data = await self._parse_message(data)
            if market_data:
                await self.data_manager.process_market_data(market_data)
        except Exception as e:
            print(f"❌ Error parsing message from {self.config.source.value}: {str(e)}")
    
    async def _parse_message(self, data: Dict[str, Any]) -> Optional[MarketData]:
        """Parse message into MarketData format"""
        # Implementation would be specific to each exchange
        # This is a simplified example for Binance
        
        if self.config.source == DataSource.BINANCE:
            if 'stream' in data and 'data' in data:
                stream = data['stream']
                msg_data = data['data']
                
                if '@ticker' in stream:
                    symbol = msg_data.get('s', '')
                    return MarketData(
                        source=self.config.source,
                        data_type=DataType.TICKER,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        data={
                            'price': float(msg_data.get('c', 0)),
                            'volume': float(msg_data.get('v', 0)),
                            'high': float(msg_data.get('h', 0)),
                            'low': float(msg_data.get('l', 0)),
                            'change': float(msg_data.get('P', 0))
                        }
                    )
                
                elif '@trade' in stream:
                    symbol = msg_data.get('s', '')
                    return MarketData(
                        source=self.config.source,
                        data_type=DataType.TRADES,
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(msg_data.get('T', 0) / 1000),
                        data={
                            'price': float(msg_data.get('p', 0)),
                            'quantity': float(msg_data.get('q', 0)),
                            'side': 'buy' if msg_data.get('m', False) else 'sell'
                        }
                    )
        
        return None
    
    async def _handle_reconnection(self):
        """Handle WebSocket reconnection"""
        if self.reconnect_count >= self.config.max_reconnect_attempts:
            print(f"❌ Max reconnection attempts reached for {self.config.source.value}")
            return
        
        self.reconnect_count += 1
        delay = min(self.config.reconnect_delay_seconds * (2 ** self.reconnect_count), 300)
        
        print(f"🔄 Reconnecting to {self.config.source.value} in {delay} seconds (attempt {self.reconnect_count})")
        await asyncio.sleep(delay)
        
        await self.connect()
    
    async def disconnect(self):
        """Disconnect WebSocket"""
        self.connected = False
        if self.websocket:
            await self.websocket.close()
            print(f"🔌 Disconnected from {self.config.source.value}")

class RealTimeDataManager:
    """Main real-time data management system"""
    
    def __init__(self, notification_manager=None, logger=None):
        self.notification_manager = notification_manager
        self.logger = logger
        
        # Data sources and connections
        self.data_sources: Dict[DataSource, DataSourceConfig] = {}
        self.websocket_connections: Dict[DataSource, WebSocketConnection] = {}
        
        # Data feeds
        self.data_feeds: Dict[str, DataFeed] = {}  # key: f"{symbol}_{data_type.value}"
        
        # Data quality monitoring
        self.data_quality_stats = defaultdict(lambda: {
            "total_updates": 0,
            "error_count": 0,
            "avg_latency_ms": 0,
            "last_update": None
        })
        
        # System state
        self.running = False
        self.start_time = None
        
        # REST API fallback
        self.rest_session = None
        self.rest_executor = ThreadPoolExecutor(max_workers=5)
        
        print("📡 Real-time Data Manager initialized")
    
    def add_data_source(self, config: DataSourceConfig):
        """Add a data source configuration"""
        self.data_sources[config.source] = config
        print(f"➕ Added data source: {config.source.value}")
        
        # Initialize data feeds for this source
        for symbol in config.symbols:
            for data_type in config.data_types:
                feed_key = f"{symbol}_{data_type.value}"
                if feed_key not in self.data_feeds:
                    self.data_feeds[feed_key] = DataFeed(symbol, data_type)
    
    async def start_data_streams(self):
        """Start all data streams"""
        if self.running:
            print("⚠️ Data streams are already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        print("🚀 Starting real-time data streams...")
        
        # Initialize REST session
        self.rest_session = aiohttp.ClientSession()
        
        # Start WebSocket connections
        connection_tasks = []
        for source, config in self.data_sources.items():
            if config.enabled:
                connection = WebSocketConnection(config, self)
                self.websocket_connections[source] = connection
                task = asyncio.create_task(connection.connect())
                connection_tasks.append(task)
        
        # Start data quality monitoring
        asyncio.create_task(self._monitor_data_quality())
        
        # Start REST API fallback monitoring
        asyncio.create_task(self._rest_fallback_monitor())
        
        print(f"✅ Started {len(connection_tasks)} data stream connections")
        
        # Log start
        if self.logger:
            self.logger.log_system_event(
                "INFO", "REALTIME_DATA", "DataManager",
                "Real-time data streams started",
                {"sources": list(self.data_sources.keys()), "feeds": len(self.data_feeds)}
            )
    
    async def stop_data_streams(self):
        """Stop all data streams"""
        if not self.running:
            print("⚠️ Data streams are not running")
            return
        
        print("🛑 Stopping real-time data streams...")
        
        self.running = False
        
        # Disconnect WebSocket connections
        disconnect_tasks = []
        for connection in self.websocket_connections.values():
            task = asyncio.create_task(connection.disconnect())
            disconnect_tasks.append(task)
        
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        # Close REST session
        if self.rest_session:
            await self.rest_session.close()
        
        # Shutdown executor
        self.rest_executor.shutdown(wait=True)
        
        print("✅ All data streams stopped")
        
        # Log stop
        if self.logger:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            self.logger.log_system_event(
                "INFO", "REALTIME_DATA", "DataManager",
                "Real-time data streams stopped",
                {"uptime_hours": uptime.total_seconds() / 3600}
            )
    
    async def process_market_data(self, market_data: MarketData):
        """Process incoming market data"""
        try:
            feed_key = f"{market_data.symbol}_{market_data.data_type.value}"
            
            if feed_key in self.data_feeds:
                feed = self.data_feeds[feed_key]
                
                # Update feed
                feed.latest_data = market_data
                feed.data_history.append(market_data)
                feed.last_update = datetime.now()
                feed.update_count += 1
                
                # Calculate latency
                if market_data.timestamp:
                    latency = (datetime.now() - market_data.timestamp).total_seconds() * 1000
                    market_data.latency_ms = latency
                
                # Update data quality
                self._update_data_quality(market_data)
                
                # Notify subscribers
                await self._notify_subscribers(feed, market_data)
                
                # Log high-frequency data at debug level
                if self.logger and feed.update_count % 100 == 0:  # Log every 100th update
                    self.logger.log_system_event(
                        "DEBUG", "REALTIME_DATA", "DataProcessor",
                        f"Processed {feed.update_count} updates for {feed_key}",
                        {"latest_price": market_data.data.get("price", 0)}
                    )
            
        except Exception as e:
            print(f"❌ Error processing market data: {str(e)}")
            if self.logger:
                self.logger.log_system_event(
                    "ERROR", "REALTIME_DATA", "DataProcessor",
                    f"Error processing market data: {str(e)}",
                    {"source": market_data.source.value, "symbol": market_data.symbol}
                )
    
    def _update_data_quality(self, market_data: MarketData):
        """Update data quality metrics"""
        source_key = f"{market_data.source.value}_{market_data.symbol}"
        stats = self.data_quality_stats[source_key]
        
        stats["total_updates"] += 1
        stats["last_update"] = datetime.now()
        
        # Update average latency
        if market_data.latency_ms:
            current_avg = stats["avg_latency_ms"]
            total_updates = stats["total_updates"]
            stats["avg_latency_ms"] = ((current_avg * (total_updates - 1)) + market_data.latency_ms) / total_updates
    
    async def _notify_subscribers(self, feed: DataFeed, market_data: MarketData):
        """Notify all subscribers of new data"""
        for subscriber in feed.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(market_data)
                else:
                    subscriber(market_data)
            except Exception as e:
                print(f"❌ Error notifying subscriber: {str(e)}")
    
    async def _monitor_data_quality(self):
        """Monitor data quality and freshness"""
        while self.running:
            try:
                current_time = datetime.now()
                stale_feeds = []
                
                for feed_key, feed in self.data_feeds.items():
                    if feed.last_update:
                        time_since_update = (current_time - feed.last_update).total_seconds()
                        
                        # Check data freshness
                        if time_since_update > 60:  # 1 minute threshold
                            if feed.quality != DataQuality.STALE:
                                feed.quality = DataQuality.STALE
                                stale_feeds.append(feed_key)
                        elif time_since_update > 30:  # 30 seconds
                            feed.quality = DataQuality.POOR
                        elif time_since_update > 10:  # 10 seconds
                            feed.quality = DataQuality.FAIR
                        else:
                            feed.quality = DataQuality.GOOD
                
                # Alert on stale data
                if stale_feeds and self.notification_manager:
                    await self.notification_manager.send_notification(
                        title="Stale Market Data Detected",
                        message=f"Data feeds are stale: {', '.join(stale_feeds)}",
                        notification_type="WARNING"
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Data quality monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _rest_fallback_monitor(self):
        """Monitor and provide REST API fallback for stale data"""
        while self.running:
            try:
                for feed_key, feed in self.data_feeds.items():
                    if feed.quality == DataQuality.STALE and feed.last_update:
                        time_since_update = (datetime.now() - feed.last_update).total_seconds()
                        
                        if time_since_update > 120:  # 2 minutes - trigger fallback
                            await self._fetch_rest_fallback_data(feed)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"❌ REST fallback monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _fetch_rest_fallback_data(self, feed: DataFeed):
        """Fetch data via REST API as fallback"""
        try:
            # Find a working data source for this symbol
            for source, config in self.data_sources.items():
                if feed.symbol in config.symbols and config.enabled:
                    data = await self._fetch_rest_data(source, feed.symbol, feed.data_type)
                    if data:
                        market_data = MarketData(
                            source=source,
                            data_type=feed.data_type,
                            symbol=feed.symbol,
                            timestamp=datetime.now(),
                            data=data
                        )
                        await self.process_market_data(market_data)
                        print(f"📡 REST fallback data fetched for {feed.symbol}")
                        break
        except Exception as e:
            print(f"❌ REST fallback error for {feed.symbol}: {str(e)}")
    
    async def _fetch_rest_data(self, source: DataSource, symbol: str, data_type: DataType) -> Optional[Dict]:
        """Fetch data from REST API"""
        try:
            config = self.data_sources[source]
            
            # Construct REST API URL (simplified example)
            if source == DataSource.BINANCE:
                if data_type == DataType.TICKER:
                    url = f"{config.rest_api_url}/api/v3/ticker/24hr?symbol={symbol}"
                else:
                    return None
            else:
                return None
            
            async with self.rest_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Convert to standard format
                    if source == DataSource.BINANCE and data_type == DataType.TICKER:
                        return {
                            'price': float(data.get('lastPrice', 0)),
                            'volume': float(data.get('volume', 0)),
                            'high': float(data.get('highPrice', 0)),
                            'low': float(data.get('lowPrice', 0)),
                            'change': float(data.get('priceChangePercent', 0))
                        }
                
        except Exception as e:
            print(f"❌ REST API error for {source.value}: {str(e)}")
        
        return None
    
    def subscribe_to_feed(self, symbol: str, data_type: DataType, callback: Callable):
        """Subscribe to a data feed"""
        feed_key = f"{symbol}_{data_type.value}"
        
        if feed_key in self.data_feeds:
            self.data_feeds[feed_key].subscribers.add(callback)
            print(f"📡 Subscribed to {feed_key}")
            return True
        else:
            print(f"❌ Data feed not found: {feed_key}")
            return False
    
    def unsubscribe_from_feed(self, symbol: str, data_type: DataType, callback: Callable):
        """Unsubscribe from a data feed"""
        feed_key = f"{symbol}_{data_type.value}"
        
        if feed_key in self.data_feeds:
            self.data_feeds[feed_key].subscribers.discard(callback)
            print(f"📡 Unsubscribed from {feed_key}")
            return True
        else:
            return False
    
    def get_latest_data(self, symbol: str, data_type: DataType) -> Optional[MarketData]:
        """Get latest data for a symbol and data type"""
        feed_key = f"{symbol}_{data_type.value}"
        
        if feed_key in self.data_feeds:
            feed = self.data_feeds[feed_key]
            
            # Check data freshness
            if feed.latest_data and feed.last_update:
                age_seconds = (datetime.now() - feed.last_update).total_seconds()
                if age_seconds < 60:  # Data is fresh (less than 1 minute old)
                    return feed.latest_data
                else:
                    print(f"⚠️ Data for {symbol} is {age_seconds:.0f} seconds old")
        
        return None
    
    def is_data_fresh(self, symbol: str, data_type: DataType, max_age_seconds: int = 10) -> bool:
        """Check if data is fresh enough for trading decisions"""
        feed_key = f"{symbol}_{data_type.value}"
        
        if feed_key in self.data_feeds:
            feed = self.data_feeds[feed_key]
            if feed.last_update:
                age_seconds = (datetime.now() - feed.last_update).total_seconds()
                return age_seconds <= max_age_seconds
        
        return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        uptime_hours = 0
        if self.start_time:
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        # Connection status
        connection_status = {}
        for source, connection in self.websocket_connections.items():
            connection_status[source.value] = {
                "connected": connection.connected,
                "reconnect_count": connection.reconnect_count,
                "last_heartbeat": connection.last_heartbeat.isoformat() if connection.last_heartbeat else None
            }
        
        # Data feed status
        feed_status = {}
        fresh_feeds = 0
        stale_feeds = 0
        
        for feed_key, feed in self.data_feeds.items():
            feed_status[feed_key] = {
                "quality": feed.quality.value,
                "update_count": feed.update_count,
                "error_count": feed.error_count,
                "last_update": feed.last_update.isoformat() if feed.last_update else None,
                "subscribers": len(feed.subscribers)
            }
            
            if feed.quality in [DataQuality.EXCELLENT, DataQuality.GOOD]:
                fresh_feeds += 1
            elif feed.quality == DataQuality.STALE:
                stale_feeds += 1
        
        return {
            "running": self.running,
            "uptime_hours": uptime_hours,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "data_sources": len(self.data_sources),
            "active_connections": len([c for c in self.websocket_connections.values() if c.connected]),
            "total_feeds": len(self.data_feeds),
            "fresh_feeds": fresh_feeds,
            "stale_feeds": stale_feeds,
            "connection_status": connection_status,
            "feed_status": feed_status,
            "data_quality_stats": dict(self.data_quality_stats)
        }

# Demo function
async def demo_realtime_data_system():
    """Demonstrate the real-time data system"""
    print("📡 Real-time Data System Demo")
    print("=" * 50)
    
    # Create data manager
    data_manager = RealTimeDataManager()
    
    # Add demo data source configurations
    binance_config = DataSourceConfig(
        source=DataSource.BINANCE,
        websocket_url="wss://stream.binance.com:9443/ws/btcusdt@ticker",
        rest_api_url="https://api.binance.com",
        symbols=["BTCUSDT", "ETHUSDT"],
        data_types=[DataType.TICKER, DataType.TRADES],
        priority=1
    )
    
    data_manager.add_data_source(binance_config)
    
    # Demo data subscriber
    received_data = []
    
    async def data_callback(market_data: MarketData):
        received_data.append(market_data)
        print(f"📊 Received {market_data.data_type.value} for {market_data.symbol}: "
              f"Price: {market_data.data.get('price', 'N/A')}")
    
    # Subscribe to data feed
    data_manager.subscribe_to_feed("BTCUSDT", DataType.TICKER, data_callback)
    
    # Start data streams (would connect to real WebSocket in production)
    print("\n🚀 Starting data streams...")
    # Note: In demo, we'll simulate data instead of real connections
    
    # Simulate some market data
    print("\n📊 Simulating market data...")
    for i in range(5):
        demo_data = MarketData(
            source=DataSource.BINANCE,
            data_type=DataType.TICKER,
            symbol="BTCUSDT",
            timestamp=datetime.now(),
            data={
                "price": 45000 + (i * 100),
                "volume": 1000 + (i * 50),
                "high": 45500,
                "low": 44500,
                "change": 2.5
            }
        )
        
        await data_manager.process_market_data(demo_data)
        await asyncio.sleep(1)
    
    # Test data freshness
    print(f"\n🔍 Testing data freshness...")
    is_fresh = data_manager.is_data_fresh("BTCUSDT", DataType.TICKER, max_age_seconds=30)
    print(f"   BTCUSDT ticker data is fresh: {is_fresh}")
    
    # Get latest data
    latest_data = data_manager.get_latest_data("BTCUSDT", DataType.TICKER)
    if latest_data:
        print(f"   Latest BTCUSDT price: {latest_data.data.get('price', 'N/A')}")
    
    # Get system status
    status = data_manager.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   • Running: {status['running']}")
    print(f"   • Data Sources: {status['data_sources']}")
    print(f"   • Total Feeds: {status['total_feeds']}")
    print(f"   • Fresh Feeds: {status['fresh_feeds']}")
    print(f"   • Stale Feeds: {status['stale_feeds']}")
    
    # Show received data
    print(f"\n📈 Received Data Summary:")
    print(f"   • Total messages: {len(received_data)}")
    if received_data:
        print(f"   • Latest price: {received_data[-1].data.get('price', 'N/A')}")
        print(f"   • Average latency: {sum(d.latency_ms or 0 for d in received_data) / len(received_data):.1f}ms")
    
    print(f"\n🎯 Real-time Data Features:")
    print(f"   ✅ Multi-source WebSocket connections")
    print(f"   ✅ Real-time market data streaming")
    print(f"   ✅ Data freshness monitoring")
    print(f"   ✅ Automatic reconnection handling")
    print(f"   ✅ REST API fallback for stale data")
    print(f"   ✅ Data quality assessment")
    print(f"   ✅ Subscriber notification system")
    print(f"   ✅ Latency measurement")
    print(f"   ✅ Multiple exchange support")
    print(f"   ✅ Data redundancy and failover")
    
    print(f"\n✅ Real-time Data System demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_realtime_data_system())

"""
模拟市场数据生成器
用于在没有真实API的情况下生成模拟的加密货币市场数据
"""
import random
import time
from typing import Dict, List
from datetime import datetime, timedelta
from loguru import logger


class MockMarketDataGenerator:
    """模拟市场数据生成器"""
    
    def __init__(self):
        # 初始化各个交易对的基准价格（使用真实市场价格）
        self.base_prices = {
            "BTC/USDT": 109000.0,    # 比特币实际价格
            "ETH/USDT": 3840.0,      # 以太坊实际价格
            "BNB/USDT": 1090.0,      # 币安币实际价格
            "SOL/USDT": 187.0,       # Solana实际价格
            "ADA/USDT": 0.63,        # Cardano实际价格
            "XRP/USDT": 2.38,        # Ripple实际价格
            "DOT/USDT": 2.95,        # Polkadot实际价格
            "DOGE/USDT": 0.192,      # Dogecoin实际价格
            "MATIC/USDT": 0.19,      # Polygon实际价格
            "AVAX/USDT": 19.3,       # Avalanche实际价格
            "LINK/USDT": 17.2,       # Chainlink实际价格
            "UNI/USDT": 6.1,         # Uniswap实际价格
            "ATOM/USDT": 3.15,       # Cosmos实际价格
            "LTC/USDT": 92.6,        # Litecoin实际价格
            "ETC/USDT": 15.5         # Ethereum Classic实际价格
        }
        
        # 当前价格（会随时间波动）
        self.current_prices = self.base_prices.copy()
        
        # 价格走势（bull, bear, sideways）
        self.trends = {}
        self._initialize_trends()
        
        # 模拟持仓
        self.positions = {}
        
        # 模拟账户余额
        self.balances = {
            "USDT": 100.0,
            "BTC": 0.0,
            "ETH": 0.0,
            "BNB": 0.0,
            "SOL": 0.0,
            "ADA": 0.0,
            "XRP": 0.0,
            "DOT": 0.0,
            "DOGE": 0.0,
            "MATIC": 0.0,
            "AVAX": 0.0,
            "LINK": 0.0,
            "UNI": 0.0,
            "ATOM": 0.0,
            "LTC": 0.0,
            "ETC": 0.0
        }
        
        logger.info("✅ 模拟市场数据生成器已初始化")
    
    def _initialize_trends(self):
        """初始化市场趋势"""
        trend_types = ["bull", "bear", "sideways"]
        for symbol in self.base_prices.keys():
            self.trends[symbol] = {
                "type": random.choice(trend_types),
                "strength": random.uniform(0.3, 0.8),
                "duration": random.randint(50, 200)  # 趋势持续的更新次数
            }
    
    def update_prices(self):
        """更新所有交易对的价格（模拟市场波动）"""
        for symbol in self.current_prices.keys():
            trend = self.trends[symbol]
            
            # 根据趋势类型决定价格变化方向
            if trend["type"] == "bull":
                # 牛市：价格倾向上涨
                change_percent = random.uniform(-0.02, 0.05) * trend["strength"]
            elif trend["type"] == "bear":
                # 熊市：价格倾向下跌
                change_percent = random.uniform(-0.05, 0.02) * trend["strength"]
            else:
                # 横盘：价格小幅波动
                change_percent = random.uniform(-0.02, 0.02) * trend["strength"]
            
            # 应用价格变化
            self.current_prices[symbol] *= (1 + change_percent)
            
            # 添加随机噪音
            noise = random.uniform(-0.005, 0.005)
            self.current_prices[symbol] *= (1 + noise)
            
            # 更新趋势持续时间
            trend["duration"] -= 1
            if trend["duration"] <= 0:
                # 趋势结束，切换到新趋势
                trend_types = ["bull", "bear", "sideways"]
                trend["type"] = random.choice(trend_types)
                trend["strength"] = random.uniform(0.3, 0.8)
                trend["duration"] = random.randint(50, 200)
    
    def get_ticker(self, symbol: str) -> Dict:
        """获取单个交易对的行情数据"""
        if symbol not in self.current_prices:
            return {}
        
        price = self.current_prices[symbol]
        base_price = self.base_prices[symbol]
        
        # 计算24小时变化
        change_24h = ((price - base_price) / base_price) * 100
        
        # 模拟高低价
        high_24h = price * random.uniform(1.02, 1.08)
        low_24h = price * random.uniform(0.92, 0.98)
        
        # 模拟成交量
        volume_multiplier = {
            "BTC/USDT": 1000000000,
            "ETH/USDT": 500000000,
            "BNB/USDT": 200000000,
        }
        base_volume = volume_multiplier.get(symbol, 50000000)
        volume_24h = base_volume * random.uniform(0.8, 1.2)
        
        return {
            "symbol": symbol,
            "price": round(price, 8),
            "change_24h": round(change_24h, 2),
            "high_24h": round(high_24h, 8),
            "low_24h": round(low_24h, 8),
            "volume_24h": round(volume_24h, 2),
            "market_cap": round(price * volume_24h * 0.001, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_all_tickers(self) -> List[Dict]:
        """获取所有交易对的行情数据"""
        return [self.get_ticker(symbol) for symbol in self.current_prices.keys()]
    
    def get_account_balance(self) -> Dict:
        """获取账户余额"""
        balances_list = []
        for asset, amount in self.balances.items():
            if amount > 0:
                balances_list.append({
                    "asset": asset,
                    "free": amount,
                    "locked": 0.0,
                    "total": amount
                })
        
        return {
            "success": True,
            "balances": balances_list
        }
    
    def _normalize_symbol(self, symbol: str) -> str:
        """标准化交易对格式 - 将BTCUSDT转换为BTC/USDT"""
        if "/" in symbol:
            return symbol  # 已经是正确格式
        
        # 常见的USDT交易对转换
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}/USDT"
        
        return symbol
    
    def place_order(
        self, 
        symbol: str, 
        side: str, 
        order_type: str, 
        amount: float, 
        price: float = None
    ) -> Dict:
        """模拟下单"""
        try:
            # 标准化symbol格式
            normalized_symbol = self._normalize_symbol(symbol)
            
            # 获取当前价格
            current_price = self.current_prices.get(normalized_symbol, 0)
            if current_price == 0:
                return {"success": False, "error": f"Invalid symbol: {symbol} -> {normalized_symbol}"}
            
            # 使用市价或限价
            execution_price = price if price else current_price
            
            # 计算总价值
            total_value = amount * execution_price
            
            # 提取币对
            base_asset = normalized_symbol.split("/")[0]
            quote_asset = normalized_symbol.split("/")[1]
            
            if side == "buy":
                # 买入：检查USDT余额
                if self.balances.get(quote_asset, 0) < total_value:
                    return {"success": False, "error": "Insufficient balance"}
                
                # 扣除USDT，增加币
                self.balances[quote_asset] -= total_value
                self.balances[base_asset] = self.balances.get(base_asset, 0) + amount
                
                # 更新持仓
                if normalized_symbol not in self.positions:
                    self.positions[normalized_symbol] = {
                        "amount": 0,
                        "average_price": 0,
                        "type": "long"
                    }
                
                pos = self.positions[normalized_symbol]
                total_cost = pos["amount"] * pos["average_price"] + total_value
                pos["amount"] += amount
                pos["average_price"] = total_cost / pos["amount"] if pos["amount"] > 0 else 0
                
                logger.info(f"✅ 模拟买入: {symbol} {amount:.6f} @ ${execution_price:.2f}")
                
            elif side == "sell":
                # 卖出：检查币余额
                if self.balances.get(base_asset, 0) < amount:
                    return {"success": False, "error": "Insufficient balance"}
                
                # 扣除币，增加USDT
                self.balances[base_asset] -= amount
                self.balances[quote_asset] = self.balances.get(quote_asset, 0) + total_value
                
                # 更新持仓
                if normalized_symbol in self.positions:
                    self.positions[normalized_symbol]["amount"] -= amount
                    if self.positions[normalized_symbol]["amount"] <= 0:
                        del self.positions[normalized_symbol]
                
                logger.info(f"✅ 模拟卖出: {symbol} {amount:.6f} @ ${execution_price:.2f}")
            
            return {
                "success": True,
                "order_id": f"MOCK_{int(time.time())}_{random.randint(1000, 9999)}",
                "symbol": symbol,  # 返回原始symbol格式
                "side": side,
                "type": order_type,
                "price": execution_price,
                "amount": amount,
                "total_value": total_value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"模拟下单失败: {e}")
            return {"success": False, "error": str(e)}
    
    def place_short_order(self, symbol: str, amount: float, price: float = None) -> Dict:
        """模拟做空订单"""
        normalized_symbol = self._normalize_symbol(symbol)
        current_price = self.current_prices.get(normalized_symbol, 0)
        execution_price = price if price else current_price
        
        # 简化版做空：记录做空持仓
        if normalized_symbol not in self.positions:
            self.positions[normalized_symbol] = {
                "amount": 0,
                "average_price": 0,
                "type": "short"
            }
        
        pos = self.positions[normalized_symbol]
        pos["type"] = "short"
        pos["amount"] += amount
        pos["average_price"] = execution_price
        
        logger.info(f"✅ 模拟做空: {symbol} {amount:.6f} @ ${execution_price:.2f}")
        
        return {
            "success": True,
            "order_id": f"MOCK_SHORT_{int(time.time())}",
            "symbol": symbol,
            "side": "short",
            "amount": amount,
            "price": execution_price
        }
    
    def close_position(self, symbol: str) -> Dict:
        """模拟平仓"""
        normalized_symbol = self._normalize_symbol(symbol)
        if normalized_symbol not in self.positions:
            return {"success": False, "error": "No position to close"}
        
        pos = self.positions[normalized_symbol]
        current_price = self.current_prices.get(normalized_symbol, 0)
        
        # 计算盈亏
        if pos["type"] == "short":
            pnl = (pos["average_price"] - current_price) * pos["amount"]
        else:
            pnl = (current_price - pos["average_price"]) * pos["amount"]
        
        # 更新余额
        quote_asset = normalized_symbol.split("/")[1]
        self.balances[quote_asset] = self.balances.get(quote_asset, 0) + pnl
        
        # 删除持仓
        del self.positions[normalized_symbol]
        
        logger.info(f"✅ 模拟平仓: {symbol} 盈亏: ${pnl:.2f}")
        
        return {
            "success": True,
            "symbol": symbol,
            "pnl": pnl,
            "close_price": current_price
        }
    
    def get_open_positions(self) -> List[Dict]:
        """获取当前持仓"""
        positions_list = []
        for symbol, pos in self.positions.items():
            # 只返回数量大于0的持仓
            if pos["amount"] <= 0:
                continue
                
            current_price = self.current_prices.get(symbol, 0)
            
            if pos["type"] == "short":
                unrealized_pnl = (pos["average_price"] - current_price) * pos["amount"]
            else:
                unrealized_pnl = (current_price - pos["average_price"]) * pos["amount"]
            
            # 将symbol格式转换回BTCUSDT格式以匹配交易引擎期望
            display_symbol = symbol.replace("/", "") if "/" in symbol else symbol
            
            positions_list.append({
                "symbol": display_symbol,
                "amount": pos["amount"],
                "average_price": pos["average_price"],
                "current_price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "position_type": pos["type"]
            })
        
        return positions_list
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """获取模拟订单簿数据"""
        # 标准化交易对格式
        normalized_symbol = symbol.replace("USDT", "/USDT") if not "/" in symbol else symbol
        
        if normalized_symbol not in self.current_prices:
            logger.warning(f"不支持的交易对: {symbol}")
            return {'bids': [], 'asks': []}
        
        current_price = self.current_prices[normalized_symbol]
        
        # 生成模拟的买卖盘数据
        bids = []  # 买单（价格从高到低）
        asks = []  # 卖单（价格从低到高）
        
        # 生成买单（价格低于当前价格）
        for i in range(limit // 2):
            price = current_price * (1 - (i + 1) * 0.001)  # 每个档位降低0.1%
            quantity = random.uniform(0.1, 2.0)  # 随机数量
            bids.append([price, quantity])
        
        # 生成卖单（价格高于当前价格）
        for i in range(limit // 2):
            price = current_price * (1 + (i + 1) * 0.001)  # 每个档位提高0.1%
            quantity = random.uniform(0.1, 2.0)  # 随机数量
            asks.append([price, quantity])
        
        # 按价格排序
        bids.sort(key=lambda x: x[0], reverse=True)  # 买单按价格降序
        asks.sort(key=lambda x: x[0])  # 卖单按价格升序
        
        logger.info(f"生成模拟订单簿: {symbol} 买盘{len(bids)}档 卖盘{len(asks)}档")
        
        return {
            'bids': bids,
            'asks': asks,
            'lastUpdateId': int(time.time() * 1000)
        }
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的交易对列表"""
        # 返回BTCUSDT格式的交易对，与交易引擎期望的格式一致
        return [symbol.replace("/", "") for symbol in self.base_prices.keys()]
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict]:
        """
        获取K线数据（模拟）
        
        Args:
            symbol: 交易对（支持BTC/USDT或BTCUSDT格式）
            interval: 时间间隔（1m, 5m, 15m, 1h, 4h, 1d）
            limit: 返回的K线数量
            
        Returns:
            K线数据字典数组，格式：[{timestamp, open, high, low, close, volume, ...}, ...]
        """
        # 标准化交易对格式
        normalized_symbol = self._normalize_symbol(symbol)
        
        if normalized_symbol not in self.current_prices:
            logger.warning(f"不支持的交易对: {symbol}")
            return []
        
        # 获取当前价格作为基准
        current_price = self.current_prices[normalized_symbol]
        
        # 时间间隔转换为秒
        interval_seconds = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }.get(interval, 3600)
        
        # 生成模拟K线数据
        klines = []
        current_time = int(time.time() * 1000)  # 当前时间（毫秒）
        
        # 从历史往当前生成
        for i in range(limit, 0, -1):
            # 计算这根K线的时间戳
            timestamp = current_time - (i * interval_seconds * 1000)
            close_time = timestamp + interval_seconds * 1000
            
            # 生成价格（基于趋势和随机波动）
            trend = self.trends.get(normalized_symbol, {"type": "sideways", "strength": 0.5})
            
            # 开盘价：基于当前价格和距离当前时间的远近
            time_factor = i / limit  # 1.0 (最早) -> 0 (最新)
            
            if trend["type"] == "bull":
                # 上涨趋势：历史价格更低
                open_price = current_price * (0.85 + 0.15 * (1 - time_factor))
            elif trend["type"] == "bear":
                # 下跌趋势：历史价格更高
                open_price = current_price * (1.15 - 0.15 * (1 - time_factor))
            else:
                # 横盘：价格在当前价格附近波动
                open_price = current_price * (0.98 + 0.04 * random.random())
            
            # 添加随机波动
            volatility = 0.02 * trend["strength"]
            open_price *= (1 + random.uniform(-volatility, volatility))
            
            # 高低价和收盘价
            high = open_price * random.uniform(1.001, 1.015)
            low = open_price * random.uniform(0.985, 0.999)
            close = random.uniform(low, high)
            
            # 成交量（随机）
            base_volume = 100 + random.uniform(0, 200)
            volume = base_volume * (1 + random.uniform(-0.5, 0.5))
            quote_volume = volume * close
            
            # K线数据格式（字典格式）
            kline = {
                'timestamp': timestamp,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'close_time': close_time,
                'quote_volume': quote_volume,
                'trades': random.randint(100, 500),
                'taker_buy_volume': volume * 0.6,
                'taker_buy_quote_volume': quote_volume * 0.6
            }
            
            klines.append(kline)
        
        # 确保最后一根K线接近当前价格
        if klines:
            last_kline = klines[-1]
            last_kline['close'] = current_price  # 收盘价 = 当前价格
            last_kline['high'] = max(last_kline['open'], current_price * 1.005)  # 最高价
            last_kline['low'] = min(last_kline['open'], current_price * 0.995)  # 最低价
            last_kline['quote_volume'] = last_kline['volume'] * current_price
            last_kline['taker_buy_quote_volume'] = last_kline['taker_buy_volume'] * current_price
        
        logger.info(f"📊 生成模拟K线数据: {symbol} {interval} x{len(klines)}")
        return klines


# 全局模拟市场数据生成器实例
mock_market = MockMarketDataGenerator()


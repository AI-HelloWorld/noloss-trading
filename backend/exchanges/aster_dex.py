"""
Aster DEX 交易所接口 - 使用官方SDK
"""
import time
import asyncio
from typing import Dict, List, Optional
from loguru import logger

# 官方SDK导入
from aster.rest_api import Client as AsterClient
from aster.error import ClientError, ServerError

from backend.config import settings
from backend.exchanges.mock_market_data import mock_market


class AsterDEXClient:
    """Aster DEX API客户端 - 使用官方SDK"""
    
    def __init__(self):
        # 根据官方SDK文档，配置说明：
        # WALLET_ADDRESS = 主钱包地址（user）
        # ASTER_DEX_API_KEY = API Key (对应官方SDK的key参数)
        # ASTER_DEX_API_SECRET = API Secret (对应官方SDK的secret参数)
        
        self.user = settings.wallet_address  # 主钱包地址
        self.api_key = settings.aster_dex_api_key  # API Key
        self.api_secret = settings.aster_dex_api_secret  # API Secret
        self.base_url = "https://fapi.asterdex.com"  # Futures API
        self.position_mode_initialized = False  # 持仓模式初始化标志
        self.time_offset = 0  # 服务器时间偏移量
        
        # 检查配置
        if self.api_key and self.api_secret:
            self.use_mock_data = False
            # 初始化官方SDK客户端，增加recvWindow配置
            self.client = AsterClient(
                key=self.api_key,
                secret=self.api_secret,
                base_url=self.base_url,
                timeout=60000  # 增加超时时间到60秒
            )
            logger.info(f"✅ AsterDEX官方SDK客户端初始化成功")
            logger.info(f"🔗 Base URL: {self.base_url}")
            logger.info(f"🔑 API Key: {self.api_key[:10]}...{self.api_key[-4:]}")
            logger.info(f"🔐 API Secret: {'*' * 20}")
            if self.user:
                logger.info(f"💳 钱包地址: {self.user[:6]}...{self.user[-4:]}")
            
            # 同步服务器时间
            try:
                self._sync_server_time()
            except Exception as e:
                logger.warning(f"⚠️ 同步服务器时间失败: {e}，将使用本地时间")
        else:
            self.use_mock_data = True
            self.client = None
            logger.warning("⚠️  未配置AsterDEX API，使用模拟数据模式")
            logger.warning(f"   需要配置:")
            logger.warning(f"   - ASTER_DEX_API_KEY (API密钥)")
            logger.warning(f"   - ASTER_DEX_API_SECRET (API秘密)")
            logger.warning(f"   - WALLET_ADDRESS (钱包地址，可选)")
    
    def _run_sync(self, coro):
        """在同步上下文中运行异步方法（官方SDK是同步的，我们需要在异步环境中包装）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建新的任务
                return asyncio.create_task(asyncio.to_thread(lambda: coro))
            else:
                # 如果没有运行的循环，直接运行
                return loop.run_until_complete(asyncio.to_thread(lambda: coro))
        except RuntimeError:
            # 如果没有事件循环，创建新的
            return asyncio.run(asyncio.to_thread(lambda: coro))
    
    def _sync_server_time(self):
        """同步服务器时间，计算时间偏移量"""
        try:
            # 获取服务器时间
            server_time_response = self.client.time()
            if isinstance(server_time_response, dict) and 'serverTime' in server_time_response:
                server_time = server_time_response['serverTime']
                local_time = int(time.time() * 1000)
                self.time_offset = server_time - local_time
                logger.info(f"⏰ 时间同步完成: 服务器时间偏移 {self.time_offset}ms")
            else:
                logger.warning(f"⚠️ 无法获取服务器时间: {server_time_response}")
        except Exception as e:
            logger.warning(f"⚠️ 同步服务器时间失败: {e}")
            self.time_offset = 0
    
    def _get_timestamp(self):
        """获取带偏移量的时间戳"""
        return int(time.time() * 1000) + self.time_offset
    
    def _format_symbol_for_mock(self, symbol: str) -> str:
        """将symbol格式从BTCUSDT转换为BTC/USDT以匹配mock数据"""
        if "/" in symbol:
            return symbol
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}/USDT"
        return symbol
    
    async def get_account_balance(self) -> Dict:
        """获取账户余额 - 使用官方SDK"""
        if self.use_mock_data:
            logger.debug("📊 模拟模式：从mock_market获取余额")
            return mock_market.get_account_balance()
        
        try:
            
            # 在线程池中运行同步SDK调用
            def get_balance():
                return self.client.account()
            
            result = await asyncio.to_thread(get_balance)
            
            # 检查API是否返回错误
            if isinstance(result, dict) and 'code' in result:
                error_code = result.get('code')
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ AsterDEX API错误: [{error_code}] {error_msg}")
                return {
                    "success": False,
                    "balances": [],
                    "error": f"API错误 [{error_code}]: {error_msg}"
                }
            
            # 根据官方SDK文档，account()返回格式：
            # Futures API 返回 'assets' 字段，Spot API 返回 'balances' 字段
            # {
            #   "assets": [{"asset": "BTC", "walletBalance": "xxx", ...}, ...],
            #   "canTrade": true,
            #   ...
            # }
            
            if isinstance(result, dict) and 'assets' in result:
                # Futures API格式：返回assets字段
                assets = result['assets']
                
                # 转换为标准格式
                balances = []
                for asset in assets:
                    wallet_balance = float(asset.get('walletBalance', 0))
                    if wallet_balance > 0:  # 只返回有余额的资产
                        balances.append({
                            "asset": asset.get('asset'),
                            "free": asset.get('availableBalance', asset.get('walletBalance')),
                            "locked": str(wallet_balance - float(asset.get('availableBalance', 0)))
                        })
                
                # 显示USDT余额
                usdt_asset = next((a for a in assets if a.get('asset') == 'USDT'), None)
                if usdt_asset:
                    wallet = float(usdt_asset.get('walletBalance', 0))
                    available = float(usdt_asset.get('availableBalance', 0))
                    locked = wallet - available
                
                return {
                    "success": True,
                    "balances": balances,
                    "canTrade": result.get('canTrade', False)
                }
            elif isinstance(result, dict) and 'balances' in result:
                # Spot API格式：返回balances字段
                balances = result['balances']
                
                # 显示USDT余额
                usdt_balance = next((b for b in balances if b.get('asset') == 'USDT'), None)
                if usdt_balance:
                    free = float(usdt_balance.get('free', 0))
                    locked = float(usdt_balance.get('locked', 0))
                    total = free + locked
                    logger.info(f"💵 USDT余额: 可用={free:.2f}, 锁定={locked:.2f}, 总计={total:.2f}")
                
                return {
                    "success": True,
                    "balances": balances,
                    "canTrade": result.get('canTrade', False)
                }
            elif isinstance(result, list):
                logger.info(f"✅ 成功获取钱包余额，共{len(result)}项")
                return {
                    "success": True,
                    "balances": result
                }
            else:
                logger.warning(f"⚠️ API响应格式未知: {result}")
                return {
                    "success": False,
                    "balances": [],
                    "error": "响应格式不匹配"
                }
        except ClientError as e:
            logger.error(f"❌ 客户端错误: {e.error_message}")
            return {
                "success": False,
                "balances": [],
                "error": f"客户端错误: {e.error_message}"
            }
        except ServerError as e:
            logger.error(f"❌ 服务器错误: {e}")
            return {
                "success": False,
                "balances": [],
                "error": f"服务器错误: {str(e)}"
            }
        except Exception as e:
            logger.error(f"获取钱包余额失败: {e}")
            return {
                "success": False,
                "balances": [],
                "error": str(e)
            }
    
    async def get_ticker(self, symbol: str) -> Dict:
        """获取交易对行情 - 使用官方SDK"""
        if self.use_mock_data:
            # 更新价格（模拟市场波动）
            mock_market.update_prices()
            # 转换symbol格式：BTCUSDT -> BTC/USDT
            formatted_symbol = self._format_symbol_for_mock(symbol)
            ticker = mock_market.get_ticker(formatted_symbol)
            # 将返回的symbol改回原格式
            if ticker and 'symbol' in ticker:
                ticker['symbol'] = symbol
            return ticker
        
        try:
            # 在线程池中运行同步SDK调用
            def get_ticker_data():
                return self.client.ticker_24hr_price_change(symbol=symbol)
            
            result = await asyncio.to_thread(get_ticker_data)
            
            # 将真实API字段映射到我们的标准字段
            if result:
                return {
                    "symbol": result.get("symbol", symbol),
                    "price": float(result.get("lastPrice", 0)),
                    "change_24h": float(result.get("priceChangePercent", 0)),
                    "high_24h": float(result.get("highPrice", 0)),
                    "low_24h": float(result.get("lowPrice", 0)),
                    "volume_24h": float(result.get("quoteVolume", 0)),
                    "market_cap": 0,
                    "timestamp": result.get("closeTime", int(time.time() * 1000))
                }
            return {}
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {e}")
            return {}
    
    async def get_all_tickers(self) -> List[Dict]:
        """获取所有交易对行情 - 使用官方SDK"""
        if self.use_mock_data:
            mock_market.update_prices()
            return mock_market.get_all_tickers()
        
        try:
            # 在线程池中运行同步SDK调用
            def get_all_ticker_data():
                return self.client.ticker_24hr_price_change()
            
            result = await asyncio.to_thread(get_all_ticker_data)
            
            # 转换字段格式
            tickers = []
            if isinstance(result, list):
                for item in result:
                    tickers.append({
                        "symbol": item.get("symbol"),
                        "price": float(item.get("lastPrice", 0)),
                        "change_24h": float(item.get("priceChangePercent", 0)),
                        "high_24h": float(item.get("highPrice", 0)),
                        "low_24h": float(item.get("lowPrice", 0)),
                        "volume_24h": float(item.get("quoteVolume", 0)),
                        "market_cap": 0,
                        "timestamp": item.get("closeTime", int(time.time() * 1000))
                    })
            return tickers
        except Exception as e:
            logger.error(f"获取所有行情失败: {e}")
            return []
    
    async def _ensure_hedge_mode(self):
        """确保账户设置为双向持仓模式（支持同时做多和做空）"""
        if self.use_mock_data or self.position_mode_initialized:
            return True
        
        try:
            logger.info("🔧 检查持仓模式设置...")
            
            # 在线程池中运行同步SDK调用
            def change_position_mode():
                try:
                    # 尝试设置为双向持仓模式（Hedge Mode）
                    # 参数: dualSidePosition = "true" 表示双向持仓模式
                    return self.client.change_position_mode(dualSidePosition="true")
                except Exception as e:
                    # 如果已经是双向持仓模式，会返回错误，这是正常的
                    logger.debug(f"设置持仓模式返回: {e}")
                    return {"success": True, "msg": "Already in hedge mode or mode set successfully"}
            
            result = await asyncio.to_thread(change_position_mode)
            
            # 标记为已初始化
            self.position_mode_initialized = True
            
            logger.info("✅ 持仓模式已设置为双向模式（支持同时做多做空）")
            return True
            
        except ClientError as e:
            # 如果错误是"已经是双向模式"，这是正常的
            error_msg = str(e.error_message).lower() if hasattr(e, 'error_message') else str(e).lower()
            if 'no need' in error_msg or 'already' in error_msg:
                logger.info("✅ 持仓模式已经是双向模式")
                self.position_mode_initialized = True
                return True
            else:
                logger.warning(f"⚠️  设置持仓模式时出现问题: {e.error_message if hasattr(e, 'error_message') else e}")
                # 即使失败也标记为已尝试，避免重复尝试
                self.position_mode_initialized = True
                return False
        except Exception as e:
            logger.warning(f"⚠️  设置持仓模式失败: {e}")
            self.position_mode_initialized = True
            return False
    
    def _adjust_precision(self, symbol: str, amount: float) -> float:
        """调整交易数量精度，避免精度错误（统一精度配置）"""
        # 根据交易对设置合适的精度（基于AsterDEX的严格要求）
        precision_rules = {
            # BTC相关 - 通常3-4位小数
            "BTC/USDT": 3,
            "BTCUSDT": 3,
            # ETH相关 - 通常3-4位小数
            "ETH/USDT": 3,
            "ETHUSDT": 3,
            # BNB相关 - 通常2-3位小数
            "BNB/USDT": 2,
            "BNBUSDT": 2,
            # SOL相关 - 通常1-2位小数
            "SOL/USDT": 1,
            "SOLUSDT": 1,
            # ADA相关 - 通常0-1位小数（数量较大）
            "ADA/USDT": 0,
            "ADAUSDT": 0,
            # XRP相关 - 通常0-1位小数（数量较大）
            "XRP/USDT": 0,
            "XRPUSDT": 0,
            # DOT相关 - 通常1-2位小数
            "DOT/USDT": 1,
            "DOTUSDT": 1,
            # DOGE相关 - 通常0位小数（数量很大）
            "DOGE/USDT": 0,
            "DOGEUSDT": 0,
            # MATIC相关 - 通常0-1位小数（数量较大）
            "MATIC/USDT": 0,
            "MATICUSDT": 0,
            # AVAX相关 - 通常1-2位小数
            "AVAX/USDT": 1,
            "AVAXUSDT": 1,
            # LINK相关 - 通常1-2位小数
            "LINK/USDT": 1,
            "LINKUSDT": 1,
            # UNI相关 - 通常1-2位小数
            "UNI/USDT": 1,
            "UNIUSDT": 1,
            # ATOM相关 - 通常1-2位小数
            "ATOM/USDT": 1,
            "ATOMUSDT": 1,
            # LTC相关 - 通常2-3位小数
            "LTC/USDT": 2,
            "LTCUSDT": 2,
            # ETC相关 - 通常1-2位小数
            "ETC/USDT": 1,
            "ETCUSDT": 1,
            # ASTER相关 - 通常0-1位小数
            "ASTER/USDT": 0,
            "ASTERUSDT": 0,
            # 默认精度 - 非常保守，整数
            "default": 0
        }
        
        # 获取精度
        precision = precision_rules.get(symbol, precision_rules.get("default"))
        
        # 四舍五入到指定精度
        adjusted = round(amount, precision)
        
        # 确保不为0（如果原值大于最小值）
        if adjusted == 0 and amount > 0:
            # 如果四舍五入后为0，使用最小精度值
            adjusted = 10 ** (-precision) if precision > 0 else 1
        
        logger.info(f"🔧 精度调整: {symbol} {amount:.8f} -> {adjusted:.{precision}f} ({precision}位小数)")
        
        return adjusted
    
    async def place_order(
        self, 
        symbol: str, 
        side: str,  # buy, sell
        order_type: str,  # market, limit
        amount: float,
        price: Optional[float] = None
    ) -> Dict:
        """下单 - 使用官方SDK"""
        if self.use_mock_data:
            result = mock_market.place_order(symbol, side, order_type, amount, price)
            logger.info(f"模拟订单已提交: {symbol} {side} {amount}")
            return result
        
        # 调整精度（在构建参数之前）
        amount = self._adjust_precision(symbol, amount)
        
        # 构建订单参数（参考官方SDK示例）
        params = {
            "symbol": symbol,
            "side": side.upper(),  # BUY 或 SELL
            "type": order_type.upper(),  # MARKET 或 LIMIT
            "quantity": amount,
        }
        
        # 限价单需要价格和timeInForce
        if order_type.upper() == "LIMIT":
            if price is None:
                logger.error("限价单必须指定价格")
                return {"success": False, "error": "限价单必须指定价格"}
            params["price"] = price
            params["timeInForce"] = "GTC"
        
        try:
            logger.info(f"📤 提交订单: {symbol} {side} {amount} ({order_type})")
            
            # 在线程池中运行同步SDK调用
            def submit_order():
                return self.client.new_order(**params)
            
            result = await asyncio.to_thread(submit_order)
            
            # 检查是否成功
            if isinstance(result, dict) and 'orderId' in result:
                logger.info(f"✅ 订单提交成功: {symbol} {side} {amount}")
                logger.info(f"   订单ID: {result.get('orderId')}")
                logger.info(f"   状态: {result.get('status')}")
                return {
                    "success": True,
                    "order_id": str(result.get('orderId')),
                    **result
                }
            elif isinstance(result, dict) and 'code' in result:
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ 下单失败: {error_msg}")
                return {"success": False, "error": error_msg}
            else:
                logger.warning(f"⚠️  下单响应格式未知: {result}")
                return result
        except ClientError as e:
            logger.error(f"❌ 客户端错误: {e.error_message}")
            return {"success": False, "error": f"客户端错误: {e.error_message}"}
        except ServerError as e:
            logger.error(f"❌ 服务器错误: {e}")
            return {"success": False, "error": f"服务器错误: {str(e)}"}
        except Exception as e:
            logger.error(f"下单异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def place_short_order(self, symbol: str, amount: float, price: Optional[float] = None) -> Dict:
        """
        做空订单 - 使用官方SDK
        
        关键说明：
        - 单向持仓模式：做空使用 side="SELL"，不能使用 positionSide 参数
        - 双向持仓模式：做空使用 side="SELL" + positionSide="SHORT"
        """
        if self.use_mock_data:
            return mock_market.place_short_order(symbol, amount, price)
        
        # 调整精度
        amount = self._adjust_precision(symbol, amount)
        
        # 方案1：尝试使用标准下单接口（SELL方向）
        # 注意：某些交易所不支持positionSide参数，只需要side="SELL"即可做空
        params = {
            "symbol": symbol,
            "side": "SELL",                    # 卖出方向（做空）
            "type": "MARKET" if price is None else "LIMIT",
            "quantity": amount,
        }
        
        # 如果交易所支持positionSide，可以取消注释
        # params["positionSide"] = "SHORT"
        
        # 限价单需要价格
        if price is not None:
            params["price"] = price
            params["timeInForce"] = "GTC"
        
        try:
            logger.info(f"📉 提交做空订单: {symbol} {amount}")
            logger.debug(f"   参数: {params}")
            
            # 在线程池中运行同步SDK调用
            def submit_short_order():
                return self.client.new_order(**params)
            
            result = await asyncio.to_thread(submit_short_order)
            
            logger.debug(f"   API响应: {result}")
            
            # 检查是否成功
            if isinstance(result, dict) and 'orderId' in result:
                logger.info(f"✅ 做空订单提交成功: {symbol} {amount}")
                logger.info(f"   订单ID: {result.get('orderId')}")
                logger.info(f"   状态: {result.get('status')}")
                return {
                    "success": True,
                    "order_id": str(result.get('orderId')),
                    "side": "short",
                    **result
                }
            elif isinstance(result, dict) and 'code' in result:
                error_code = result.get('code')
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ 做空失败 [{error_code}]: {error_msg}")
                
                # 如果是持仓模式不匹配错误，尝试另一种方式
                if 'position side' in error_msg.lower():
                    logger.warning("⚠️  检测到持仓模式不匹配，尝试使用双向模式参数...")
                    params["positionSide"] = "SHORT"
                    
                    def retry_with_position_side():
                        return self.client.new_order(**params)
                    
                    retry_result = await asyncio.to_thread(retry_with_position_side)
                    
                    if isinstance(retry_result, dict) and 'orderId' in retry_result:
                        logger.info(f"✅ 做空订单提交成功（重试）: {symbol} {amount}")
                        return {
                            "success": True,
                            "order_id": str(retry_result.get('orderId')),
                            "side": "short",
                            **retry_result
                        }
                
                return {"success": False, "error": error_msg}
            else:
                logger.warning(f"⚠️  做空响应格式未知: {result}")
                return {"success": False, "error": "响应格式未知", "response": result}
        except ClientError as e:
            logger.error(f"❌ 做空客户端错误: {e.error_message}")
            logger.error(f"   错误代码: {e.error_code}")
            logger.error(f"   参数: {params}")
            return {"success": False, "error": f"客户端错误[{e.error_code}]: {e.error_message}"}
        except ServerError as e:
            logger.error(f"❌ 做空服务器错误: {e}")
            logger.error(f"   状态码: {e.status_code}")
            logger.error(f"   参数: {params}")
            return {"success": False, "error": f"服务器错误[{e.status_code}]: {str(e)}"}
        except Exception as e:
            logger.error(f"❌ 做空异常: {e}")
            logger.error(f"   异常类型: {type(e).__name__}")
            logger.error(f"   参数: {params}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
            return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
    
    async def close_position(self, symbol: str) -> Dict:
        """平仓 - 使用官方SDK或手动平仓"""
        if self.use_mock_data:
            return mock_market.close_position(symbol)
        
        try:
            logger.info(f"📤 提交平仓请求: {symbol}")
            
            # 检查SDK是否有close_position方法
            if hasattr(self.client, 'close_position'):
                def submit_close():
                    return self.client.close_position(symbol=symbol)
                
                result = await asyncio.to_thread(submit_close)
                
                if isinstance(result, dict) and result.get('success') is not False:
                    logger.info(f"✅ 平仓成功: {symbol}")
                    return {"success": True, **result}
                else:
                    error_msg = result.get('error', '未知错误')
                    logger.error(f"❌ 平仓失败: {error_msg}")
                    return {"success": False, "error": error_msg}
            else:
                # SDK没有close_position方法，使用手动平仓方案
                logger.info("ℹ️  SDK没有close_position方法，使用手动平仓")
                
                # 1. 获取当前持仓
                positions = await self.get_open_positions(symbol=symbol)
                
                # 2. 找到对应symbol的持仓
                target_position = None
                for pos in positions:
                    if pos.get('symbol') == symbol:
                        target_position = pos
                        break
                
                if not target_position:
                    logger.warning(f"⚠️  未找到持仓: {symbol}")
                    return {"success": False, "error": f"未找到持仓: {symbol}"}
                
                # 3. 确定平仓方向和数量
                position_type = target_position.get('position_type')
                position_amount = target_position.get('amount', 0)
                
                if position_amount == 0:
                    logger.warning(f"⚠️  持仓数量为0: {symbol}")
                    return {"success": False, "error": f"持仓数量为0: {symbol}"}
                
                # 多仓用SELL平仓，空仓用BUY平仓
                close_side = "SELL" if position_type == "long" else "BUY"
                
                logger.info(f"📊 持仓信息: {position_type} {position_amount} {symbol}")
                logger.info(f"📤 执行平仓: {close_side} {position_amount} {symbol}")
                
                # 4. 使用市价单平仓
                result = await self.place_order(
                    symbol=symbol,
                    side=close_side.lower(),
                    order_type="market",
                    amount=position_amount
                )
                
                if result.get('success'):
                    logger.info(f"✅ 平仓成功: {symbol}")
                    return {"success": True, "order_id": result.get('order_id'), "position_type": position_type}
                else:
                    error_msg = result.get('error', '未知错误')
                    logger.error(f"❌ 平仓失败: {error_msg}")
                    return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ 平仓异常: {e}")
            import traceback
            logger.error(f"   堆栈: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    async def get_order_status(self, order_id: str) -> Dict:
        """查询订单状态 - 使用官方SDK"""
        if self.use_mock_data:
            return {"success": True, "status": "FILLED"}
        
        try:
            logger.debug(f"📊 查询订单状态: {order_id}")
            
            # 在线程池中运行同步SDK调用
            def query_order():
                return self.client.query_order(orderId=order_id)
            
            result = await asyncio.to_thread(query_order)
            
            if isinstance(result, dict) and 'orderId' in result:
                logger.debug(f"✅ 订单查询成功: {order_id}")
                return {"success": True, **result}
            else:
                logger.warning(f"⚠️  订单查询响应格式未知: {result}")
                return result
        except Exception as e:
            logger.error(f"❌ 查询订单失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_open_positions(self, symbol: str = None) -> List[Dict]:
        """获取当前持仓 - 使用官方SDK"""
        if self.use_mock_data:
            return mock_market.get_open_positions()
        
        try:
            
            # 在线程池中运行同步SDK调用
            def get_positions():
                # 根据官方SDK文档，使用get_position_risk()获取持仓风险信息
                return self.client.get_position_risk(symbol=symbol)
            
            result = await asyncio.to_thread(get_positions)
            
            # 检查是否返回错误
            if isinstance(result, dict) and 'code' in result:
                error_code = result.get('code')
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ 持仓查询错误: [{error_code}] {error_msg}")
                return []
            
            # 解析持仓数据
            if isinstance(result, list):
                # 过滤出实际有持仓的（数量不为0）
                positions_data = []
                for pos in result:
                    pos_amt = float(pos.get('positionAmt', 0))
                    if pos_amt != 0:
                        # 转换为我们的标准格式
                        entry_price_value = float(pos.get('entryPrice', 0))
                        positions_data.append({
                            "symbol": pos.get('symbol'),
                            "amount": abs(pos_amt),
                            "average_price": entry_price_value,
                            "entry_price": entry_price_value,  # 记录入场价格
                            "current_price": float(pos.get('markPrice', 0)),
                            "unrealized_pnl": float(pos.get('unRealizedProfit', 0)),
                            "position_type": "short" if pos_amt < 0 else "long",
                            "total_value": entry_price_value * float(pos.get('positionAmt', 0))
                        })
                
                if positions_data:
                    logger.info(f"✅ 获取到{len(positions_data)}个持仓")
                    for pos in positions_data:
                        logger.info(f"   {pos['symbol']}: {pos['amount']:.4f} @ ${pos['average_price']:.2f} (未实现盈亏: ${pos['unrealized_pnl']:.2f})")
                else:
                    logger.info("ℹ️  当前无持仓")
                
                return positions_data
            else:
                logger.warning(f"⚠️ 持仓响应格式未知: {result}")
                return []
        except ClientError as e:
            logger.error(f"❌ 客户端错误: {e.error_message}")
            return []
        except ServerError as e:
            logger.error(f"❌ 服务器错误: {e}")
            return []
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """获取订单簿数据"""
        if self.use_mock_data:
            return mock_market.get_order_book(symbol, limit)
        
        try:
            def get_depth():
                return self.client.depth(symbol=symbol, limit=limit)
            
            result = await asyncio.to_thread(get_depth)
            
            if isinstance(result, dict) and 'bids' in result and 'asks' in result:
                logger.info(f"获取订单簿成功: {symbol}")
                return result
            else:
                logger.warning(f"订单簿数据格式异常: {result}")
                return {'bids': [], 'asks': []}
                
        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return {'bids': [], 'asks': []}

    async def get_supported_symbols(self) -> List[str]:
        """获取所有支持的交易对 - 使用官方SDK"""
        if self.use_mock_data:
            return mock_market.get_supported_symbols()
        
        try:
            # 在线程池中运行同步SDK调用
            def get_exchange_info():
                return self.client.exchange_info()
            
            result = await asyncio.to_thread(get_exchange_info)
            
            # exchangeInfo 返回的 symbols 数组包含详细信息
            if 'symbols' in result:
                return [s for s in result['symbols'] if s.get('status') == 'TRADING']
            return result.get('symbols', [])
        except Exception as e:
            logger.error(f"获取交易对列表失败: {e}")
            # 返回一些常见的加密货币作为默认值
            return [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT",
                "XRP/USDT", "DOT/USDT", "DOGE/USDT", "MATIC/USDT", "AVAX/USDT",
                "LINK/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "ETC/USDT"
            ]
    
    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict]:
        """
        获取K线数据 - 使用官方SDK
        
        Args:
            symbol: 交易对（如BTCUSDT）
            interval: 时间间隔（1m, 5m, 15m, 1h, 4h, 1d）
            limit: 返回的K线数量（默认100，最大1500）
            
        Returns:
            K线数据字典数组，格式：[{timestamp, open, high, low, close, volume, ...}, ...]
        """
        if self.use_mock_data:
            logger.debug(f"📊 模拟模式：生成K线数据 {symbol} {interval} x{limit}")
            return mock_market.get_klines(symbol, interval, limit)
        
        try:
            logger.info(f"📊 真实模式：使用官方SDK获取K线数据 {symbol} {interval} x{limit}")
            
            # 在线程池中运行同步SDK调用
            def get_kline_data():
                # 根据官方SDK文档，使用klines()方法获取K线数据
                # 参数：symbol, interval, limit
                return self.client.klines(symbol=symbol, interval=interval, limit=limit)
            
            result = await asyncio.to_thread(get_kline_data)
            
            # 检查API是否返回错误
            if isinstance(result, dict) and 'code' in result:
                error_code = result.get('code')
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ AsterDEX API错误: [{error_code}] {error_msg}")
                logger.warning(f"⚠️  使用模拟数据作为后备")
                return mock_market.get_klines(symbol, interval, limit)
            
            # 检查返回的数据格式并转换为字典格式
            if isinstance(result, list) and len(result) > 0:
                logger.info(f"✅ 成功获取K线数据: {symbol} {interval} x{len(result)}")
                
                # 将列表格式转换为字典格式
                klines_dict = []
                for kline in result:
                    if isinstance(kline, list) and len(kline) >= 6:
                        # Binance/AsterDEX 标准格式：
                        # [timestamp, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_volume, taker_buy_quote_volume, ignore]
                        klines_dict.append({
                            'timestamp': kline[0],
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5]),
                            'close_time': kline[6] if len(kline) > 6 else 0,
                            'quote_volume': float(kline[7]) if len(kline) > 7 else 0.0,
                            'trades': int(kline[8]) if len(kline) > 8 else 0,
                            'taker_buy_volume': float(kline[9]) if len(kline) > 9 else 0.0,
                            'taker_buy_quote_volume': float(kline[10]) if len(kline) > 10 else 0.0
                        })
                    elif isinstance(kline, dict):
                        # 已经是字典格式，直接使用
                        klines_dict.append(kline)
                
                return klines_dict
            else:
                logger.warning(f"⚠️  K线数据为空或格式异常，使用模拟数据")
                return mock_market.get_klines(symbol, interval, limit)
                
        except ClientError as e:
            logger.error(f"❌ 客户端错误: {e.error_message if hasattr(e, 'error_message') else e}")
            logger.warning(f"⚠️  使用模拟数据作为后备")
            return mock_market.get_klines(symbol, interval, limit)
        except ServerError as e:
            logger.error(f"❌ 服务器错误: {e}")
            logger.warning(f"⚠️  使用模拟数据作为后备")
            return mock_market.get_klines(symbol, interval, limit)
        except Exception as e:
            logger.error(f"❌ 获取K线数据失败: {e}")
            logger.warning(f"⚠️  使用模拟数据作为后备")
            return mock_market.get_klines(symbol, interval, limit)
    
    async def get_commission_rate(self, symbol: str) -> Dict:
        """
        获取交易对手续费率 - 使用官方SDK
        
        Args:
            symbol: 交易对（如BTCUSDT）
            
        Returns:
            手续费率信息字典，格式：{
                "symbol": "BTCUSDT",
                "makerCommissionRate": "0.0002",
                "takerCommissionRate": "0.0004"
            }
        """
        if self.use_mock_data:
            logger.debug(f"📊 模拟模式：返回默认手续费率 {symbol}")
            return {
                "symbol": symbol,
                "makerCommissionRate": "0.0002",
                "takerCommissionRate": "0.0004"
            }
        
        try:
            logger.info(f"📊 获取手续费率: {symbol}")
            
            # 在线程池中运行同步SDK调用
            def get_commission():
                return self.client.commission_rate(symbol=symbol)
            
            result = await asyncio.to_thread(get_commission)
            
            # 检查API是否返回错误
            if isinstance(result, dict) and 'code' in result:
                error_code = result.get('code')
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ 获取手续费率错误: [{error_code}] {error_msg}")
                # 返回默认值
                return {
                    "symbol": symbol,
                    "makerCommissionRate": "0.0002",
                    "takerCommissionRate": "0.0004"
                }
            
            # 返回手续费率信息
            if isinstance(result, dict):
                logger.info(f"✅ 成功获取手续费率: {symbol}")
                logger.debug(f"   Maker: {result.get('makerCommissionRate', 'N/A')}")
                logger.debug(f"   Taker: {result.get('takerCommissionRate', 'N/A')}")
                return result
            else:
                logger.warning(f"⚠️  手续费率响应格式异常，使用默认值")
                return {
                    "symbol": symbol,
                    "makerCommissionRate": "0.0002",
                    "takerCommissionRate": "0.0004"
                }
                
        except ClientError as e:
            logger.error(f"❌ 客户端错误: {e.error_message if hasattr(e, 'error_message') else e}")
            return {
                "symbol": symbol,
                "makerCommissionRate": "0.0002",
                "takerCommissionRate": "0.0004"
            }
        except ServerError as e:
            logger.error(f"❌ 服务器错误: {e}")
            return {
                "symbol": symbol,
                "makerCommissionRate": "0.0002",
                "takerCommissionRate": "0.0004"
            }
        except Exception as e:
            logger.error(f"❌ 获取手续费率失败: {e}")
            return {
                "symbol": symbol,
                "makerCommissionRate": "0.0002",
                "takerCommissionRate": "0.0004"
            }
    
    async def close(self):
        """关闭连接"""
        # 官方SDK不需要显式关闭连接
        pass


# 全局客户端实例
aster_client = AsterDEXClient()


"""
新闻分析师智能体
"""
import datetime
import json
import re
from typing import Dict, Optional, List
from loguru import logger
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import NEWS_ANALYST_PROMPT, get_risk_control_context
from backend.config import settings


class NewsAnalyst(BaseAgent):
    """新闻分析师 - 监控全球新闻、宏观经济与名人推文（特朗普/马斯克/CZ）"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.NEWS_ANALYST, ai_model, api_key)
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.tracked_celebrities = ["Donald Trump", "Elon Musk", "CZ", "赵长鹏", "@elonmusk", "@cz_binance"]
        self.news_api_url = settings.news_api_url
        self.last_new_id = 0
        self.last_result = {}
    
    async def _fetch_news_from_api(self) -> List[Dict]:
        """从配置的新闻API获取新闻数据"""
        try:
            logger.info(f"📰 正在从新闻API获取数据: {self.news_api_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.news_api_url, timeout=30) as response:
                    if response.status == 200:
                        news_data = await response.json()
                        logger.info(f"✅ 成功获取 {len(news_data)} 条新闻")
                        return news_data
                    else:
                        logger.warning(f"⚠️ 新闻API响应异常: {response.status}")
                        return []
        except aiohttp.ClientTimeout:
            logger.warning("⏰ 新闻API请求超时")
            return []
        except Exception as e:
            logger.exception(f"❌ 获取新闻数据失败: {e}")
            return []
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict,
        additional_data: Optional[Dict] = None
    ) -> AgentAnalysis:
        """分析新闻、宏观经济和指定名人推文影响"""
        try:
            # 优先使用传入的新闻数据，如果没有则从API获取
            news_data = additional_data.get('news', []) if additional_data else []
            positions = additional_data.get('positions', [])
            
            tweet_data = additional_data.get('tweets', []) if additional_data else []

            # 过滤：仅保留来自关注人物的推文
            tweet_data = [
                tweet for tweet in tweet_data
                if any(name.lower() in (tweet.get("author", "") + tweet.get("username", "")).lower()
                       for name in self.tracked_celebrities)
            ]

            role_context = self._build_role_context(symbol, news_data, tweet_data)
            
            # 构建完整的提示词（注入风控配置）
            prompt = f"""
当前交易对: {symbol}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

{role_context}
{self._analyze_position_status(symbol, positions, market_data)}
请分析并提供建议，返回标准的JSON格式分析。
注意：建议必须符合系统风控规则！
"""
            logger.info(f"新闻分析师提示词: {NEWS_ANALYST_PROMPT}\n {prompt}")
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": NEWS_ANALYST_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                }
                
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    # 检查API响应格式
                    if 'choices' not in data:
                        logger.error(f"API响应格式错误: {data}")
                        raise Exception(f"API响应缺少choices字段: {data}")
                    
                    if not data['choices'] or len(data['choices']) == 0:
                        logger.error(f"API响应choices为空: {data}")
                        raise Exception("API响应choices为空")
                    
                    content = data['choices'][0]['message']['content']
            
            result = self._parse_response(content)
            return AgentAnalysis(
                agent_role=self.role,
                recommendation=result.get('recommendation', 'hold'),
                confidence=float(result.get('confidence', 0.5)),
                reasoning=result.get('reasoning', '新闻分析'),
                key_metrics=result.get('key_metrics', {}),
                risk_score=float(result.get('risk_score', 0.5)),
                priority=4
            )
            # return self.last_result
            
        except Exception as e:
            logger.exception(f"新闻分析失败: {e}")
            return AgentAnalysis(
                agent_role=self.role,
                recommendation="hold",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                key_metrics={},
                risk_score=0.5,
                priority=4
            )

    def _build_role_context(self, symbol: str, news: List[Dict], tweets: List[Dict]) -> str:
        """构建分析上下文，包括新闻与名人推文以及负面新闻分级"""
        # 处理新闻数据，提取关键信息
        processed_news = []
        for item in news:
            if item.get("sentiment_score") == 0.5:
                continue
            news_time = item.get("received_at")
            # 超过一小时 过滤
            if news_time:
                try:
                    # 尝试解析ISO格式时间（支持多种格式）
                    if isinstance(news_time, str):
                        # 去掉微秒部分，统一处理
                        if 'T' in news_time:
                            # ISO格式: 2025-11-03T12:31:23.153883
                            news_time = news_time.split('.')[0]  # 去掉微秒
                            news_datetime = datetime.datetime.strptime(news_time, "%Y-%m-%dT%H:%M:%S")
                        else:
                            # 标准格式: 2025-11-03 12:31:23
                            news_datetime = datetime.datetime.strptime(news_time, "%Y-%m-%d %H:%M:%S")
                        
                        # 检查是否超过1小时
                        if datetime.datetime.now() - news_datetime > datetime.timedelta(hours=3):
                            continue
                except Exception as e:
                    logger.warning(f"解析新闻时间失败: {news_time}, 错误: {e}")
                    # 时间解析失败，保留该新闻
                    pass
            
            processed_item = {
                "id": item.get("id", ""),
                "summary": item.get("summary", ""),
                "sentiment": item.get("sentiment", "neutral"),
                "sentiment_score": item.get("sentiment_score", 0.5),
                "mentioned_coins": item.get("mentioned_coins", []),
                "is_major": item.get("is_major", False),
                "received_at": item.get("received_at", ""),
                "source_url": item.get("source_url", "")
            }
            # 如果是重大新闻，包含原文内容
            if item.get("is_major") and item.get("original_content"):
                processed_item["original_content"] = item.get("original_content")
            processed_news.append(processed_item.get("summary"))
        
        news_json = json.dumps(processed_news, ensure_ascii=False, indent=2) if processed_news else "无"
        tweet_json = json.dumps(tweets, ensure_ascii=False, indent=2) if tweets else "无"

        return f"""
作为新闻分析师，请重点关注以下三类信息：

1. 加密货币相关新闻：
   - 项目重大公告、合作伙伴关系
   - 技术升级、代币经济变动
   - 监管政策、突发新闻事件
   - 重点关注新闻中提及的币种：{symbol}

2. 宏观经济环境：
   - 美联储利率、通胀数据
   - 地缘政治风险、全球金融市场动态

3. 名人推文影响：
   请特别关注以下人物是否对加密货币发表了观点：
   - Elon Musk（马斯克）
   - Donald Trump（特朗普）
   - CZ（赵长鹏）

他们的发言可能影响市场情绪与方向。

新闻分析重点：
- 情绪评分：positive(>0.6) 利好，negative(<0.4) 利空，neutral(0.4-0.6) 中性
- 重大新闻：需要重点关注
- 提及币种：mentioned_coins 中包含相关币种的新闻更相关
- 时间因素：最近一个小时内的新闻比旧新闻影响更大

强烈做空信号（负面新闻）：
1. 监管打击新闻（SEC诉讼、禁令等）
2. 项目安全漏洞或黑客攻击
3. 团队内部分裂或创始人离职
4. 技术重大缺陷被曝光
5. 竞争对手推出颠覆性产品
6. 宏观经济恶化（加息、流动性收紧）

名人推文做空影响：
- Elon Musk: 对加密货币的负面评论
- Donald Trump: 对加密货币的监管立场
- CZ: 交易所下架代币、监管合规问题

负面新闻严重程度分级：
- 严重：直接影响项目生存（如监管禁令、重大安全事故）
- 中等：影响短期价格但可恢复（如团队成员离职、技术bug）
- 轻微：暂时性负面情绪（如市场流言、小规模批评）

以下是最近新闻内容（过去3小时）和近期推文：
{news_json}



请综合分析正面和负面因素对 {symbol} 的潜在影响，给出平衡的交易建议（包括做空机会）。
特别关注新闻的情绪评分和是否提及相关币种。
"""
    def _analyze_position_status(self, symbol: str, positions: Optional[List[Dict]], market_data: Dict) -> str:
        """分析持仓状态"""
        # 从持仓列表中找到对应symbol的持仓
        position = None
        if positions:
            for pos in positions:
                if pos.get('symbol') == symbol:
                    position = pos
                    break
        
        if not position:
            return f"""
当前{symbol}持仓状态：
- 无持仓
- 可执行操作：buy(做多), short(做空), hold(观望)
"""
        
        position_type = position.get('position_type', 'buy')  # 'buy'表示多仓, 'short'表示空仓
        amount = position.get('amount', 0)
        # 优先使用entry_price，如果不存在则使用average_price
        entry_price = position.get('entry_price') if position.get('entry_price') else position.get('average_price', 0)
        current_price = market_data.get('price', 0)
        
        if position_type == 'buy' or position_type == 'long':
            # 多仓
            unrealized_pnl = (current_price - entry_price) * amount if entry_price > 0 else 0
            unrealized_pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            return f"""
当前{symbol}持仓状态：
- 持仓类型：多仓（做多）
- 持仓数量：{amount:.6f}
- 入场价格：${entry_price:.4f}
- 当前价格：${current_price:.4f}
- 未实现盈亏：${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)
- 可执行操作：sell(平多仓), hold(继续持有)
- **如果团队分析看跌，应考虑sell平仓止损或止盈**
"""
        else:
            # 空仓
            unrealized_pnl = (entry_price - current_price) * amount if entry_price > 0 else 0
            unrealized_pnl_pct = ((entry_price - current_price) / entry_price * 100) if entry_price > 0 else 0
            return f"""
当前{symbol}持仓状态：
- 持仓类型：空仓（做空）
- 持仓数量：{amount:.6f}
- 入场价格：${entry_price:.4f}
- 当前价格：${current_price:.4f}
- 未实现盈亏：${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)
- 可执行操作：cover(平空仓), hold(继续持有)
- **如果团队分析看涨，应考虑cover平仓止损或止盈**
"""
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}


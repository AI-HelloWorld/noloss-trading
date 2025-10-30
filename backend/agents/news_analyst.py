"""
新闻分析师智能体
"""
import json
import re
from typing import Dict, Optional, List
from loguru import logger
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import get_risk_control_context
from backend.config import settings


class NewsAnalyst(BaseAgent):
    """新闻分析师 - 监控全球新闻、宏观经济与名人推文（特朗普/马斯克/CZ）"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.NEWS_ANALYST, ai_model, api_key)
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.tracked_celebrities = ["Donald Trump", "Elon Musk", "CZ", "赵长鹏", "@elonmusk", "@cz_binance"]
        self.news_api_url = settings.news_api_url
    
    async def _fetch_news_from_api(self) -> List[Dict]:
        """从配置的新闻API获取新闻数据"""
        try:
            logger.info(f"📰 正在从新闻API获取数据: {self.news_api_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.news_api_url, timeout=10) as response:
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
            logger.error(f"❌ 获取新闻数据失败: {e}")
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
            if not news_data:
                logger.info("📰 未提供新闻数据，从API获取最新新闻")
                news_data = await self._fetch_news_from_api()
            
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
{get_risk_control_context()}

当前交易对: {symbol}
市场数据：{json.dumps(market_data, ensure_ascii=False, indent=2)}

{role_context}

请分析并提供建议，返回标准的JSON格式分析。
注意：建议必须符合系统风控规则！
"""
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "grok-beta",
                    "messages": [
                        {"role": "system", "content": f"你是一个专业的{self.name}，擅长解读新闻、宏观事件和社交动态对市场的影响。"},
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
            
        except Exception as e:
            logger.error(f"新闻分析失败: {e}")
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
            processed_news.append(processed_item)
        
        news_json = json.dumps(processed_news, ensure_ascii=False, indent=2) if processed_news else "无"
        tweet_json = json.dumps(tweets, ensure_ascii=False, indent=2) if tweets else "无"

        return f"""
作为新闻分析师，请重点关注以下三类信息：

1. 加密货币相关新闻：
   - 项目重大公告、合作伙伴关系
   - 技术升级、代币经济变动
   - 监管政策、突发新闻事件
   - 重点关注新闻中提及的币种：{symbol.replace('USDT', '').replace('USD', '')}

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
- 重大新闻：is_major=true 的新闻影响更大，需要重点关注
- 提及币种：mentioned_coins 中包含相关币种的新闻更相关
- 时间因素：recent news 比旧新闻影响更大

强烈做空信号（负面新闻）：
1. 监管打击新闻（SEC诉讼、禁令等）
2. 项目安全漏洞或黑客攻击
3. 团队内部分裂或创始人离职
4. 技术重大缺陷被曝光
5. 竞争对手推出颠覆性产品
6. 宏观经济恶化（加息、流动性收紧）

名人推文做空影响：
- Elon Musk: 对狗狗币等meme币的负面评论
- Donald Trump: 对加密货币的监管立场
- CZ: 交易所下架代币、监管合规问题

负面新闻严重程度分级：
- 严重：直接影响项目生存（如监管禁令、重大安全事故）
- 中等：影响短期价格但可恢复（如团队成员离职、技术bug）
- 轻微：暂时性负面情绪（如市场流言、小规模批评）

以下是最近新闻内容（过去1小时）和近期推文：
{news_json}



请综合分析正面和负面因素对 {symbol} 的潜在影响，给出平衡的交易建议（包括做空机会）。
特别关注新闻的情绪评分和是否提及相关币种。
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


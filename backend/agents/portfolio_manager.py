"""
投资组合经理智能体
"""
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import openai
import aiohttp

from backend.agents.base_agent import BaseAgent, AgentRole, AgentAnalysis
from backend.agents.prompts import PORTFOLIO_MANAGER_PROMPT, get_risk_control_context
from backend.agents.intelligent_stop_strategy import intelligent_stop_strategy


class PortfolioManager(BaseAgent):
    """投资组合经理 - 综合所有分析师意见做出最终交易决策（使用DeepSeek-R1推理模型）"""
    
    def __init__(self, ai_model: str, api_key: str):
        super().__init__(AgentRole.PORTFOLIO_MANAGER, ai_model, api_key)
        if "GPT" in ai_model.upper():
            openai.api_key = self.api_key
        
        # 强制使用DeepSeek-R1推理模型
        # R1是DeepSeek的推理增强模型，特别适合复杂决策
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model_name = "deepseek-reasoner"  # DeepSeek-R1推理模型
        self.use_reasoning = True  # 启用推理模式
        
        logger.info(f"🧠 投资组合经理使用DeepSeek-R1推理模型（deepseek-reasoner）")
        
        # 备用：根据不同的AI模型设置API URL（保留向后兼容）
        if "R1" in ai_model or "Reasoner" in ai_model or "DeepSeek-R1" in ai_model:
            self.model_name = "deepseek-reasoner"
        elif "DeepSeek" in ai_model:
            # 即使指定DeepSeek，也优先使用R1
            self.model_name = "deepseek-reasoner"
        elif "Grok" in ai_model:
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.model_name = "grok-beta"
            self.use_reasoning = False
        elif "Qwen" in ai_model or "千问" in ai_model:
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            self.model_name = "qwen-plus"
            self.use_reasoning = False
    
    async def make_final_decision(
        self,
        symbol: str,
        market_data: Dict,
        team_analyses: List[AgentAnalysis],
        portfolio: Dict
    ) -> Dict:
        """
        综合团队分析做出最终决策
        
        Args:
            symbol: 交易对
            market_data: 市场数据
            team_analyses: 所有分析师的分析结果
            portfolio: 投资组合信息
        
        Returns:
            最终决策
        """
        try:
            # 整理团队意见
            team_summary = self._summarize_team_analyses(team_analyses)
            
            # 新增：多空投票统计
            long_short_balance = self._calculate_long_short_balance(team_analyses)
            
            # 新增：市场环境适配
            market_regime = self._identify_market_regime(market_data)
            
            # 检查风险管理否决权
            risk_analysis = next(
                (a for a in team_analyses if a.agent_role == AgentRole.RISK_MANAGER),
                None
            )
            
            # 分析当前持仓状态
            positions = portfolio.get('positions', [])
            current_position = self._get_current_position(symbol, positions)
            position_analysis = self._analyze_position_status(symbol, current_position, market_data)
            
            # 计算持仓时长和准确盈亏
            position_duration = self._calculate_position_duration(current_position) if current_position else "无持仓"
            position_pnl_details = self._calculate_accurate_pnl(current_position, market_data) if current_position else ""
            
            # 历史表现分析（最近20个周期）
            performance_analysis = self._analyze_trading_performance()
            
            # 动态风险状态
            risk_context = self._get_dynamic_risk_context(performance_analysis)
            
            # 获取当前买卖盘口信息
            order_book_info = await self._get_order_book_summary(symbol)
            
            # 构建决策上下文（注入风控配置）
            decision_context = f"""
{get_risk_control_context()}

【系统状态与强制规则】
{risk_context}
- 当前市场环境: {market_regime}
- 强制刷新时间: {datetime.now().strftime('%H:%M:%S')}
- 订单类型: 市价单 (永续合约)
- 资金费率周期: 每8小时结算

【账户与持仓状态】
- 总资产: ${portfolio.get('total_balance', 0):,.2f}
- 可用保证金: ${portfolio.get('available_balance', portfolio.get('cash_balance', 0)):,.2f}
- 保证金使用率: {(portfolio.get('positions_value', 0) / portfolio.get('total_balance', 1) * 100) if portfolio.get('total_balance', 0) > 0 else 0:.1f}%
- 持仓价值: ${portfolio.get('positions_value', 0):,.2f}

{position_analysis}
{position_pnl_details}
{position_duration}

【当前市场深度】
{order_book_info.get('info', '盘口数据不可用')}

【市场多空情绪】
- 做多倾向: {long_short_balance['long_ratio']:.2%}
- 做空倾向: {long_short_balance['short_ratio']:.2%}
- 净偏向: {long_short_balance['net_bias']:.2f} (正值偏多，负值偏空)

【历史表现分析】
{performance_analysis}

【团队分析汇总】
{team_summary}

【市价单交易特别注意事项】
🚨 重要提醒：我们使用市价单交易永续合约，请特别注意：

1. 📊 价格执行风险
   - 市价单不保证成交价格，可能因滑点产生额外成本
   - 当前买卖价差: {order_book_info.get('spread_percentage', 'N/A')}
   - 大额市价单可能对市场产生冲击，导致成交价格劣化

2. ⚡ 永续合约特性
   - 注意资金费率影响：当前费率 {market_data.get('funding_rate', 'N/A')}
   - 高资金费率时做多需谨慎，可能增加持仓成本
   - 自动资金费率结算每8小时一次

3. 🎯 入场时机选择
   - 避免在市场剧烈波动时入场（如大阳线/大阴线刚形成）
   - 考虑在价格回调至关键支撑/阻力位时入场
   - 关注成交量配合：放量突破时入场更安全

【强制交易规则与优先级】
1. 🚨 风险管理经理具有绝对否决权 (风险评分 > 0.7 必须拒绝交易)
2. ⚠️ 置信度要求: 所有交易必须标注 confidence 分数 (0.0-1.0)，低于 0.65 不执行
3. 🔒 同方向防重复: 已有 {symbol}_long 持仓时禁止新开多仓，已有 {symbol}_short 持仓时禁止新开空仓
4. 🔄 执行顺序: 先平仓后开仓 - 换方向时必须先平现有持仓
5. ⏱️ 持仓时长考量: 避免过早平仓 (持仓<5分钟需更高置信度)
6. 💰 动态仓位: {risk_context.get('position_size_note', '标准仓位')}
7. 🎯 必须设定: 所有开仓必须提供明确的 stop_loss 和 take_profit 水平

【持仓操作规范】
- 已有持仓时: 团队建议看跌 → 执行 sell(平多仓)；团队建议看涨 → 执行 cover(平空仓)
- 无持仓时: 按团队建议方向开仓，但必须满足置信度要求
- 禁止操作: 无多仓时执行sell，无空仓时执行cover

【决策输出要求】
请基于以上信息，按照以下JSON格式输出决策：
{{
    "action": "buy|sell|short|cover|hold",
    "confidence": 0.85,
    "reasoning": "详细的分析逻辑，特别说明对市价单执行价格的考量...",
    "leverage": 10,
    "position_size": 0.1,
    "stop_loss": 50000,
    "take_profit": 52000,
    "price_consideration": "已考虑市价单执行风险和当前买卖盘口",
    "funding_rate_impact": "已考虑资金费率影响: {market_data.get('funding_rate', 'N/A')}",
    "duration_consideration": "已考虑持仓时长因素"
}}

请严格遵守所有风控规则，特别关注市价单执行风险，只在有足够信心时交易。
"""
            
            prompt = decision_context
            
            # 使用DeepSeek-R1推理模型
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # R1推理模型的配置
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": PORTFOLIO_MANAGER_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.6,  # R1推荐温度
                    "max_tokens": 2000  # R1需要更多token进行推理
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
                    
                    message = data['choices'][0]['message']
                    content = message.get('content', '')
                    
                    # DeepSeek-R1会返回推理过程
                    reasoning_content = message.get('reasoning_content', '')
                    
                    if reasoning_content and self.use_reasoning:
                        logger.info(f"🧠 DeepSeek-R1推理过程（前500字符）:\n{reasoning_content[:500]}...")
                        # 将推理过程记录到日志中供分析
                        logger.debug(f"完整推理过程:\n{reasoning_content}")
            
            result = self._parse_response(content)
            
            # 计算智能止盈止损（如果决策是买入或做空）
            if result.get('action') in ['buy', 'short']:
                stop_levels = self._calculate_intelligent_stop_levels(
                    result.get('action'),
                    market_data.get('price', 0),
                    market_data,
                    result.get('position_size', 0.1),
                    result.get('confidence', 0.5),
                    team_analyses
                )
                
                # 更新结果
                result['stop_loss'] = stop_levels['stop_loss']
                result['take_profit'] = stop_levels['take_profit']
                result['stop_strategy'] = stop_levels
                
                logger.info(f"💡 智能止盈止损设置完成:")
                logger.info(f"   止损: ${stop_levels['stop_loss']:.4f} ({stop_levels['risk_pct']:+.2f}%)")
                logger.info(f"   止盈: ${stop_levels['take_profit']:.4f} ({stop_levels['reward_pct']:+.2f}%)")
                logger.info(f"   风险回报比: 1:{stop_levels['risk_reward_ratio']:.2f}")
                logger.info(f"   策略类型: {stop_levels['strategy_type']}")
            
            # 新增：市场环境调整
            # 确保result是字典类型
            if not isinstance(result, dict):
                logger.error(f"AI响应解析结果不是字典: {type(result)}, 内容: {result}")
                result = {}
            
            adjusted_decision = self._adjust_decision_for_market_regime(result, market_regime)
            
            # 新增：做空特定风控
            if adjusted_decision.get('action') == 'short':
                adjusted_decision = self._apply_short_specific_controls(adjusted_decision, market_data, portfolio)
            
            # 应用风险管理规则（风险管理经理拥有否决权）
            if risk_analysis:
                # 如果风险评分过高，自动否决
                if risk_analysis.risk_score > 0.7:
                    logger.warning(f"风险管理警告: {symbol} 风险评分 {risk_analysis.risk_score}")
                    if adjusted_decision.get('final_decision') == 'approve' and adjusted_decision.get('action') in ['buy', 'short']:
                        adjusted_decision['final_decision'] = 'reject'
                        adjusted_decision['action'] = 'hold'
                        adjusted_decision['reasoning'] = f"风险管理否决（风险评分{risk_analysis.risk_score:.2f}）: {risk_analysis.reasoning}\n\n原决策: {adjusted_decision.get('reasoning', '')}"
                
                # 如果风险经理明确建议reject，直接否决
                if risk_analysis.recommendation == 'reject':
                    logger.warning(f"风险管理否决: {symbol} - {risk_analysis.reasoning}")
                    adjusted_decision['final_decision'] = 'reject'
                    adjusted_decision['action'] = 'hold'
                    adjusted_decision['reasoning'] = f"风险管理经理明确否决: {risk_analysis.reasoning}"
            
            return {
                "final_decision": adjusted_decision.get('final_decision', adjusted_decision.get('decision', 'reject')),
                "action": adjusted_decision.get('action', 'hold'),
                "confidence": float(adjusted_decision.get('confidence', 0.5)),
                "position_size": float(adjusted_decision.get('position_size', 0.0)),
                "reasoning": adjusted_decision.get('reasoning', '投资组合经理决策'),
                "stop_loss": float(adjusted_decision.get('stop_loss', 0)),
                "take_profit": float(adjusted_decision.get('take_profit', 0)),
                "key_considerations": adjusted_decision.get('key_considerations', []),
                "long_short_balance": long_short_balance,
                "market_regime": market_regime,
                "team_analyses": [
                    {
                        "role": a.agent_role.value,
                        "recommendation": a.recommendation,
                        "confidence": a.confidence,
                        "reasoning": a.reasoning[:200]  # 截取前200字符
                    }
                    for a in team_analyses
                ]
            }
            
        except Exception as e:
            logger.error(f"投资组合经理决策失败: {e}")
            return {
                "final_decision": "reject",
                "action": "hold",
                "confidence": 0.0,
                "position_size": 0.0,
                "reasoning": f"决策失败: {str(e)}",
                "stop_loss": 0,
                "take_profit": 0,
                "key_considerations": [],
                "team_analyses": []
            }
    
    def _summarize_team_analyses(self, team_analyses: List[AgentAnalysis]) -> str:
        """整理团队分析摘要"""
        summary_parts = []
        
        for analysis in sorted(team_analyses, key=lambda x: x.priority, reverse=True):
            role_names = {
                AgentRole.TECHNICAL_ANALYST: "技术分析师",
                AgentRole.SENTIMENT_ANALYST: "情绪分析师",
                AgentRole.FUNDAMENTAL_ANALYST: "基本面分析师",
                AgentRole.NEWS_ANALYST: "新闻分析师",
                AgentRole.RISK_MANAGER: "风险管理经理"
            }
            
            role_name = role_names.get(analysis.agent_role, "未知")
            
            summary_parts.append(f"""
{role_name} (优先级{analysis.priority}, 风险评分{analysis.risk_score:.2f}):
- 建议: {analysis.recommendation}
- 置信度: {analysis.confidence:.2f}
- 理由: {analysis.reasoning[:150]}...
- 关键指标: {json.dumps(analysis.key_metrics, ensure_ascii=False)}
""")
        
        return "\n".join(summary_parts)
    
    def _calculate_long_short_balance(self, analyses: List[AgentAnalysis]) -> Dict:
        """计算多空平衡"""
        long_votes = 0
        short_votes = 0
        hold_votes = 0
        
        for analysis in analyses:
            if analysis.recommendation == 'buy':
                long_votes += analysis.confidence
            elif analysis.recommendation == 'short' or analysis.recommendation == 'sell':
                short_votes += analysis.confidence
            else:
                hold_votes += analysis.confidence
        
        total = long_votes + short_votes + hold_votes
        return {
            "long_ratio": long_votes / total if total > 0 else 0,
            "short_ratio": short_votes / total if total > 0 else 0,
            "hold_ratio": hold_votes / total if total > 0 else 0,
            "net_bias": (long_votes - short_votes) / total if total > 0 else 0
        }
    
    def _get_current_position(self, symbol: str, positions: List[Dict]) -> Optional[Dict]:
        """获取当前持仓"""
        for pos in positions:
            if pos.get('symbol') == symbol:
                return pos
        return None
    
    def _analyze_position_status(self, symbol: str, position: Optional[Dict], market_data: Dict) -> str:
        """分析持仓状态"""
        if not position:
            return f"""
当前{symbol}持仓状态：
- 无持仓
- 可执行操作：buy(做多), short(做空), hold(观望)
"""
        
        position_type = position.get('position_type', 'buy')  # 'buy'表示多仓, 'short'表示空仓
        amount = position.get('amount', 0)
        entry_price = position.get('average_price', 0)
        current_price = market_data.get('price', 0)
        
        if position_type == 'buy':
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
    
    def _identify_market_regime(self, market_data: Dict) -> str:
        """识别市场环境"""
        change = market_data.get('change_24h', 0)
        volatility = ((market_data.get('high_24h', 0) - market_data.get('low_24h', 0)) / 
                     market_data.get('price', 1)) * 100
        
        if volatility > 15:
            return "极端波动"
        elif volatility > 10:
            return "高波动"
        elif change > 10:
            return "强势上涨"
        elif change < -10:
            return "强势下跌"
        elif abs(change) < 2:
            return "横盘整理"
        else:
            return "正常波动"
    
    def _calculate_intelligent_stop_levels(
        self,
        action: str,
        entry_price: float,
        market_data: Dict,
        position_size: float,
        confidence: float,
        team_analyses: List[AgentAnalysis]
    ) -> Dict:
        """计算智能止盈止损水平"""
        # 计算波动率
        volatility = ((market_data.get('high_24h', entry_price) - 
                      market_data.get('low_24h', entry_price)) / entry_price * 100)
        
        # 从技术分析中获取支撑阻力位
        technical_analysis = next(
            (a for a in team_analyses if a.agent_role == AgentRole.TECHNICAL_ANALYST),
            None
        )
        
        additional_factors = {}
        if technical_analysis and technical_analysis.key_metrics:
            additional_factors = technical_analysis.key_metrics
        
        # 使用智能止盈止损策略
        stop_levels = intelligent_stop_strategy.calculate_stop_levels(
            action=action,
            entry_price=entry_price,
            market_data=market_data,
            position_size=position_size,
            confidence=confidence,
            volatility=volatility,
            additional_factors=additional_factors
        )
        
        return stop_levels
    
    def _adjust_decision_for_market_regime(self, decision: Dict, market_regime: str) -> Dict:
        """根据市场环境调整决策"""
        # 在极端波动市场中降低仓位
        if market_regime == "极端波动":
            original_size = decision.get('position_size', 0.1)
            decision['position_size'] = original_size * 0.5
            decision['reasoning'] = f"[市场极端波动，仓位减半] {decision.get('reasoning', '')}"
        
        # 在高波动市场中适度降低仓位
        elif market_regime == "高波动":
            original_size = decision.get('position_size', 0.1)
            decision['position_size'] = original_size * 0.7
            decision['reasoning'] = f"[市场高波动，仓位调降30%] {decision.get('reasoning', '')}"
        
        return decision
    
    def _apply_short_specific_controls(self, decision: Dict, market_data: Dict, portfolio: Dict) -> Dict:
        """应用做空特定风控"""
        # 做空仓位通常更小
        original_size = decision.get('position_size', 0.1)
        decision['position_size'] = original_size * 0.7  # 做空仓位减少30%
        
        # 做空止损更紧
        current_price = market_data.get('price', 0)
        if decision.get('action') == 'short':
            # 做空止损设置在阻力位上方
            decision['stop_loss'] = current_price * 1.08  # 8%止损
            decision['take_profit'] = current_price * 0.92  # 8%止盈
            
            # 添加做空风控说明
            decision['reasoning'] = f"[做空风控：仓位-30%，止损8%] {decision.get('reasoning', '')}"
        
        return decision
    
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            # 确保content是字符串
            if not isinstance(content, str):
                logger.warning(f"AI响应不是字符串类型: {type(content)}")
                return {}
            
            # 尝试直接解析JSON
            result = json.loads(content)
            if isinstance(result, dict):
                return result
            else:
                logger.warning(f"AI响应不是字典类型: {type(result)}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"无法解析AI响应为JSON: {content[:200]}...")
            return {}
    
    async def analyze(
        self,
        symbol: str,
        market_data: Dict,
        additional_data: Optional[Dict] = None
    ) -> AgentAnalysis:
        """实现基类的抽象方法（投资组合经理使用make_final_decision）"""
        raise NotImplementedError("投资组合经理应使用make_final_decision方法")
    
    def _calculate_position_duration(self, position: Optional[Dict]) -> str:
        """计算持仓时长"""
        if not position:
            return "无持仓"
        
        created_at = position.get('created_at')
        if not created_at:
            return "持仓时长: 未知"
        
        try:
            if isinstance(created_at, str):
                from dateutil import parser
                created_at = parser.parse(created_at)
            
            duration = datetime.now() - created_at
            minutes = duration.total_seconds() / 60
            
            if minutes < 60:
                return f"持仓时长: {int(minutes)}分钟"
            elif minutes < 1440:  # 24小时
                hours = minutes / 60
                return f"持仓时长: {hours:.1f}小时"
            else:
                days = minutes / 1440
                return f"持仓时长: {days:.1f}天"
        except Exception as e:
            logger.warning(f"计算持仓时长失败: {e}")
            return "持仓时长: 未知"
    
    def _calculate_accurate_pnl(self, position: Optional[Dict], market_data: Dict) -> str:
        """计算准确的盈亏信息"""
        if not position:
            return ""
        
        position_type = position.get('position_type', 'buy')
        amount = abs(position.get('amount', 0))
        entry_price = position.get('average_price', 0)
        current_price = market_data.get('price', 0)
        
        if entry_price == 0 or current_price == 0:
            return "盈亏详情: 数据不足"
        
        if position_type == 'buy' or position_type == 'long':
            # 多仓盈亏
            pnl = (current_price - entry_price) * amount
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            # 空仓盈亏
            pnl = (entry_price - current_price) * amount
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        status = "盈利" if pnl > 0 else "亏损"
        emoji = "💰" if pnl > 0 else "💸"
        
        return f"""
盈亏详情:
- {emoji} {status}: ${pnl:.2f} ({pnl_pct:+.2f}%)
- 入场价: ${entry_price:.4f}
- 当前价: ${current_price:.4f}
- 价格变动: ${abs(current_price - entry_price):.4f}
"""
    
    def _analyze_trading_performance(self) -> str:
        """分析历史交易表现"""
        # 这里可以从数据库查询最近的交易记录
        # 简化版本：返回占位符
        return """
最近交易表现 (最近20个周期):
- 总交易次数: 待实现
- 胜率: 待实现
- 平均盈亏: 待实现
- 最大回撤: 待实现
"""
    
    def _get_dynamic_risk_context(self, performance_analysis: str) -> str:
        """获取动态风险状态"""
        # 根据历史表现动态调整风险参数
        # 简化版本：返回标准风控
        return """
风险状态: 标准模式
- 最大仓位: 10%
- 单笔损失上限: 2%
- 最大回撤限制: 10%
"""
    
    async def _get_order_book_summary(self, symbol: str) -> Dict:
        """获取当前买卖盘口摘要信息"""
        try:
            # 尝试从交易所获取订单簿
            from backend.exchanges.aster_dex import aster_client
            
            order_book = await aster_client.get_order_book(symbol)
            
            if not order_book or 'bids' not in order_book or 'asks' not in order_book:
                return {
                    'info': '盘口数据不可用',
                    'spread_percentage': 'N/A'
                }
            
            best_bid = order_book['bids'][0][0] if order_book['bids'] else 0
            best_ask = order_book['asks'][0][0] if order_book['asks'] else 0
            
            if best_bid == 0 or best_ask == 0:
                return {
                    'info': '买卖价数据不完整',
                    'spread_percentage': 'N/A'
                }
            
            spread = best_ask - best_bid
            spread_percentage = (spread / best_bid * 100) if best_bid > 0 else 0
            
            info = f"""
- 买一价: ${best_bid:.4f}
- 卖一价: ${best_ask:.4f}
- 买卖价差: ${spread:.4f} ({spread_percentage:.4f}%)
- 建议入场参考: 多单接近买一价，空单接近卖一价
"""
            
            return {
                'info': info,
                'spread_percentage': f'{spread_percentage:.4f}%',
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread
            }
            
        except Exception as e:
            logger.warning(f"获取盘口数据失败: {e}")
            return {
                'info': f'盘口数据获取失败: {str(e)}',
                'spread_percentage': 'N/A'
            }


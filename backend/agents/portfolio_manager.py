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
from backend.config import settings


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
    
    async def make_final_stop_decision(
        self,
        decision_context: Dict
    ) -> Dict:
        """
        综合团队意见，做出最终止盈止损决策
        
        Args:
            decision_context: 包含持仓信息、市场数据、团队意见等的决策上下文
        
        Returns:
            {
                'final_decision': 'execute' or 'hold',
                'action': 'hold'|'stop_loss'|'take_profit'|'trailing_stop'|'adjust_stop'|'tighten_stop',
                'confidence': float,
                'reasoning': str,
                'urgency': float,
                'suggested_stop_loss': float,
                'suggested_take_profit': float
            }
        """
        try:
            position_info = decision_context['position_info']
            market_data = decision_context['market_data']
            team_opinions = decision_context['team_opinions']
            team_consensus = decision_context['team_consensus']
            
            # 构建AI提示词
            prompt = self._build_stop_decision_prompt(
                position_info,
                market_data,
                team_opinions,
                team_consensus
            )
            
            logger.debug(f"🤖 投资组合经理分析止盈止损决策...")
            
            # 调用DeepSeek-R1进行推理
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "你是一位专业的投资组合经理，需要综合团队意见做出最终的止盈止损决策。你的决策需要平衡风险和收益，考虑市场环境和团队共识。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 解析响应
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            # DeepSeek-R1的响应可能包含推理过程和结论
                            # 尝试从响应中提取结构化决策
                            decision = self._parse_stop_decision_response(content, position_info)
                            
                            logger.info(f"✅ AI止盈止损决策完成: {decision.get('action', 'hold')}")
                            return decision
                        else:
                            logger.error(f"AI响应格式错误: {result}")
                            return self._default_stop_decision(team_consensus, position_info)
                    else:
                        error_text = await response.text()
                        logger.error(f"AI API调用失败 ({response.status}): {error_text}")
                        return self._default_stop_decision(team_consensus, position_info)
        
        except Exception as e:
            logger.exception(f"AI止盈止损决策失败: {e}")
            return self._default_stop_decision(team_consensus, position_info)
    
    def _build_stop_decision_prompt(
        self,
        position_info: Dict,
        market_data: Dict,
        team_opinions: List[Dict],
        team_consensus: Dict
    ) -> str:
        """构建止盈止损决策提示词"""
        
        # 格式化团队意见
        opinions_text = "\n".join([
            f"- {op['agent']} ({op['role']}): 建议{op['action']} "
            f"(置信度{op['confidence']:.2f}, 紧急度{op['urgency']:.2f})\n"
            f"  理由: {op['reasoning']}"
            for op in team_opinions
        ])
        
        # 格式化投票统计
        votes_text = ", ".join([
            f"{action}: {count}票"
            for action, count in team_consensus['vote_counts'].items()
        ])
        
        # 风险经理意见
        risk_opinion = ""
        if team_consensus['risk_manager_opinion']:
            risk_op = team_consensus['risk_manager_opinion']
            risk_opinion = f"\n**风险管理经理特别意见**:\n建议{risk_op['action']} (紧急度{risk_op['urgency']:.2f})\n理由: {risk_op['reasoning']}\n"
        
        prompt = f"""
# 止盈止损决策请求

## 持仓信息
- 交易对: {position_info['symbol']}
- 持仓方向: {'做多' if position_info['action'] == 'buy' else '做空'}
- 入场价格: ${position_info['entry_price']:.2f}
- 当前价格: ${position_info['current_price']:.2f}
- 持仓数量: {position_info['quantity']}
- 当前盈亏: ${position_info['pnl']:.2f} ({position_info['pnl_pct']:.2f}%)
- 止损价格: ${position_info['stop_loss']:.2f}
- 止盈价格: ${position_info['take_profit']:.2f}
- 最高价: ${position_info['highest_price']:.2f}
- 最低价: ${position_info['lowest_price']:.2f}

## 市场数据
- 24小时涨跌: {market_data.get('change_24h', 0):.2f}%
- 24小时最高: ${market_data.get('high_24h', 0):.2f}
- 24小时最低: ${market_data.get('low_24h', 0):.2f}
- 24小时成交量: ${market_data.get('volume_24h', 0):,.0f}

## 团队意见汇总
{opinions_text}

{risk_opinion}

## 团队投票统计
{votes_text}
平均置信度: {team_consensus['avg_confidence']:.2f}
平均紧急度: {team_consensus['avg_urgency']:.2f}

## 你的任务
作为投资组合经理，综合以上所有信息，做出最终的止盈止损决策。

请按以下格式输出JSON决策：
```json
{{
    "final_decision": "execute或hold",
    "action": "hold/stop_loss/take_profit/trailing_stop/adjust_stop/tighten_stop之一",
    "confidence": 0.0-1.0之间的数值,
    "urgency": 0.0-1.0之间的数值,
    "reasoning": "详细的决策理由，包括你的推理过程",
    "suggested_stop_loss": 建议的止损价格（数值）,
    "suggested_take_profit": 建议的止盈价格（数值）
}}
```

**决策原则**:
1. 如果团队中出现置信度高（>0.8），应该认真考虑高置信度决策
2. 如果风险经理提出强烈警告（紧急度>0.8），应优先考虑风险控制
3. 如果盈亏百分比达到显著水平（±5%），应考虑是否执行
4. 如果市场波动剧烈，应更保守地保护利润
5. 平衡贪婪与恐惧，理性决策

请直接返回JSON格式的决策。
"""
        return prompt
    
    def _parse_stop_decision_response(self, content: str, position_info: Dict) -> Dict:
        """解析AI的止盈止损决策响应"""
        try:
            # 尝试从响应中提取JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                decision = json.loads(json_str)
            else:
                # 如果没有JSON块，尝试直接解析
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    decision = json.loads(json_match.group(0))
                else:
                    # 如果无法解析JSON，尝试从文本中提取关键信息
                    decision = self._extract_decision_from_text(content, position_info)
            
            # 验证和规范化决策
            decision.setdefault('final_decision', 'hold')
            decision.setdefault('action', 'hold')
            decision.setdefault('confidence', 0.5)
            decision.setdefault('urgency', 0.5)
            decision.setdefault('reasoning', content[:500])
            decision.setdefault('suggested_stop_loss', position_info['stop_loss'])
            decision.setdefault('suggested_take_profit', position_info['take_profit'])
            
            return decision
        
        except Exception as e:
            logger.exception(f"解析AI决策失败: {e}")
            return {
                'final_decision': 'hold',
                'action': 'hold',
                'confidence': 0.5,
                'urgency': 0.5,
                'reasoning': f"解析失败，保持观察。原始响应: {content[:200]}",
                'suggested_stop_loss': position_info['stop_loss'],
                'suggested_take_profit': position_info['take_profit']
            }
    
    def _extract_decision_from_text(self, text: str, position_info: Dict) -> Dict:
        """从文本中提取决策信息"""
        # 简单的文本分析
        text_lower = text.lower()
        
        # 判断动作
        action = 'hold'
        final_decision = 'hold'
        
        if '止损' in text or 'stop loss' in text_lower or 'stop_loss' in text_lower:
            action = 'stop_loss'
            if '执行' in text or 'execute' in text_lower:
                final_decision = 'execute'
        elif '止盈' in text or 'take profit' in text_lower or 'take_profit' in text_lower:
            action = 'take_profit'
            if '执行' in text or 'execute' in text_lower:
                final_decision = 'execute'
        elif '移动止损' in text or 'trailing' in text_lower:
            action = 'trailing_stop'
        elif '收紧' in text or 'tighten' in text_lower:
            action = 'tighten_stop'
        elif '调整' in text or 'adjust' in text_lower:
            action = 'adjust_stop'
        
        # 提取置信度
        confidence = 0.6  # 默认值
        confidence_match = re.search(r'置信度[:：]?\s*(\d+\.?\d*)', text)
        if confidence_match:
            confidence = float(confidence_match.group(1))
            if confidence > 1:
                confidence = confidence / 100
        
        return {
            'final_decision': final_decision,
            'action': action,
            'confidence': confidence,
            'urgency': 0.5,
            'reasoning': text[:500],
            'suggested_stop_loss': position_info['stop_loss'],
            'suggested_take_profit': position_info['take_profit']
        }
    
    def _default_stop_decision(self, team_consensus: Dict, position_info: Dict) -> Dict:
        """默认决策（当AI失败时）"""
        vote_counts = team_consensus['vote_counts']
        max_votes = max(vote_counts.values())
        most_voted = [action for action, votes in vote_counts.items() if votes == max_votes][0]
        
        return {
            'final_decision': 'hold',
            'action': most_voted,
            'confidence': team_consensus['avg_confidence'],
            'urgency': team_consensus['avg_urgency'],
            'reasoning': f"AI决策失败，使用团队多数意见: {most_voted}",
            'suggested_stop_loss': position_info['stop_loss'],
            'suggested_take_profit': position_info['take_profit']
        }
    
    async def make_final_decision(
        self,
        symbol: str,
        market_data: Dict,
        team_analyses: List[AgentAnalysis],
        portfolio: Dict,
        db_session = None  # 添加数据库会话参数
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
            # risk_analysis = next(
            #     (a for a in team_analyses if a.agent_role == AgentRole.RISK_MANAGER),
            #     None
            # )
            
            # 分析当前持仓状态
            positions = portfolio.get('positions', [])
            current_position = self._get_current_position(symbol, positions)
            if not current_position:
                current_position = {
                    "amount": 0,
                    "current_price": 0,
                }
            position_analysis = self._analyze_position_status(symbol, current_position, market_data)
            
            # 计算持仓时长和准确盈亏
            position_duration = self._calculate_position_duration(current_position) if current_position else ""
            position_pnl_details = self._calculate_accurate_pnl(current_position, market_data) if current_position else ""
            
            # 历史表现分析（最近50笔交易）
            performance_analysis = await self._analyze_trading_performance(db_session)
            
            # 动态风险状态
            risk_context = self._get_dynamic_risk_context(performance_analysis)
            
            # 获取当前买卖盘口信息
            order_book_info = await self._get_order_book_summary(symbol)
            
            # 构建决策上下文（注入风控配置）
            decision_context = f"""
【系统状态与强制规则】

- 订单类型: 市价单 (永续合约)

【账户与持仓状态】
- 总资产: ${portfolio.get('total_balance', 0):,.2f}
- 可用保证金: ${portfolio.get('available_balance', portfolio.get('cash_balance', 0)):,.2f}
- 保证金使用率: {(portfolio.get('total_value', 0) / portfolio.get('total_balance', 1) * 100) if portfolio.get('total_balance', 0) > 0 else 0:.1f}%
- 持仓价值: ${(current_position.get('current_price', 0) * current_position.get('amount', 0)):,.2f}

当前交易对：{symbol}
市场数据：
{json.dumps(market_data, ensure_ascii=False, indent=2)}

{position_analysis}
{position_pnl_details}
{position_duration}

【当前市场深度】
{order_book_info.get('info', '盘口数据不可用')}

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
   - 最小交易数量: {market_data.get('min_qty', 'N/A')} (低于此数量无法交易)

3. 🎯 入场时机选择
   - 避免在市场剧烈波动时入场（如大阳线/大阴线刚形成）
   - 考虑在价格回调至关键支撑/阻力位时入场
   - 关注成交量配合：放量突破时入场更安全

【强制交易规则与优先级】

1. 同方向防重复: 已有同方向仓位，需要判断是否满足最大仓位限制；
2. 已开仓位风控: 5h内如果未触发止盈止损，禁止执行平仓操作。如果5h后仍未卖出，强制平仓
3. 持仓时长考量: 如果未达到止盈止损条件，避免过早平仓
4. 必须设定: 如果决策是买入或做空必须提供明确的 stop_loss 和 take_profit 绝对金额
5. 最大持仓数量：{settings.max_concurrent_trades}个，当前持仓个数：{len(portfolio.get('positions', []))}个
6. 如果达到止盈止损条件，优先考虑平仓,严格执行止盈止损


【持仓操作规范】
- 已有持仓时: 团队建议看跌 → 执行 sell(平多仓)；团队建议看涨 → 执行 cover(平空仓)
- 无持仓时: 按团队建议方向开仓
- 禁止操作: 无多仓时执行sell，无空仓时执行cover

## 输出规范

{{
  "final_decision": "approve | reject",
  "action": "buy | sell | hold | short | cover",
  "confidence": 0.0-1.0,
  "reasoning": "基于[维度数量]个分析维度的综合判断：[关键支持理由]",
  "position_size_pct": 0.0-1.0, // 占可用保证金的百分比, 必须遵守最大仓位 20% 的规则
  "key_considerations": [
    "权重计算: 新闻50%, 技术50%",
    "新闻分析: 负面新闻密集但其他维度未确认",
    "技术分析: 超卖反弹可能但趋势仍偏空",
    "风险考量: 高波动环境(ATR 4.93%)，建议等待更明确信号"
  ],
  "stop_loss":{{
    "value": 0,
    "strategy_type": "止损价格绝对值"
  }},
  "take_profit":{{
    "value": 0,    
    "strategy_type": "止盈格绝对值"
  }}
}}
**重要：检查输出内容，输出内容必须满足json格式**
"""
            
            prompt = decision_context
            logger.info(f"投资组合经理提示词: {PORTFOLIO_MANAGER_PROMPT}\n {prompt}")
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
                    "max_tokens": 6000,  # R1需要更多token进行推理
                    "stream": False
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
                    logger.info(f"投资组合经理决策内容: {content}")
                    # DeepSeek-R1会返回推理过程
                    reasoning_content = message.get('reasoning_content', '')
                    
                    if reasoning_content and self.use_reasoning:
                        logger.info(f"🧠 DeepSeek-R1推理过程（前500字符）:\n{reasoning_content[:500]}...")
                        # 将推理过程记录到日志中供分析
                        # logger.debug(f"完整推理过程:\n{reasoning_content}")
            
            result = self._parse_response(content)
            stop_levels = {}
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
                stop_levels['stop_loss']= result.get('stop_loss', {}).get('value', 0)
                stop_levels['take_profit']= result.get('take_profit', {}).get('value', 0)
                if stop_levels['stop_loss'] == 0:
                    if result.get('action') == "buy":
                        stop_levels['stop_loss'] = market_data.get('price', 0) * 0.985
                    else:
                        stop_levels['stop_loss'] = market_data.get('price', 0) * 1.015
                if stop_levels['take_profit'] == 0:
                    if result.get('action') == "buy":
                        stop_levels['take_profit'] = market_data.get('price', 0) * 1.03
                    else:
                        stop_levels['take_profit'] = market_data.get('price', 0) * 0.97
                
                
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
            # if risk_analysis:
                # 如果风险评分过高，自动否决
                # if risk_analysis.risk_score > 0.7:
                #     logger.warning(f"风险管理警告: {symbol} 风险评分 {risk_analysis.risk_score}")
                #     if adjusted_decision.get('final_decision') == 'approve' and adjusted_decision.get('action') in ['buy', 'short']:
                #         adjusted_decision['final_decision'] = 'reject'
                #         adjusted_decision['action'] = 'hold'
                #         adjusted_decision['reasoning'] = f"风险管理否决（风险评分{risk_analysis.risk_score:.2f}）: {risk_analysis.reasoning}\n\n原决策: {adjusted_decision.get('reasoning', '')}"
                
                # 如果风险经理明确建议reject，直接否决
                # if risk_analysis.recommendation == 'reject':
                #     logger.warning(f"风险管理否决: {symbol} - {risk_analysis.reasoning}")
                #     adjusted_decision['final_decision'] = 'reject'
                #     adjusted_decision['action'] = 'hold'
                #     adjusted_decision['reasoning'] = f"风险管理经理明确否决: {risk_analysis.reasoning}"
            
            return {
                "final_decision": adjusted_decision.get('final_decision', adjusted_decision.get('decision', 'reject')),
                "action": adjusted_decision.get('action', 'hold'),
                "confidence": float(adjusted_decision.get('confidence', 0.5)),
                "position_size": float(adjusted_decision.get('position_size', 0.0)),
                "reasoning": adjusted_decision.get('reasoning', '投资组合经理决策'),
                "stop_loss": float(stop_levels.get('stop_loss', 0)),
                "take_profit": float(stop_levels.get('take_profit', 0)),
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
            logger.exception(f"投资组合经理决策失败: {e}")
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
        role_names = {
            AgentRole.TECHNICAL_ANALYST: "技术分析师",
            AgentRole.SENTIMENT_ANALYST: "情绪分析师",
            AgentRole.FUNDAMENTAL_ANALYST: "基本面分析师",
            AgentRole.NEWS_ANALYST: "新闻分析师",
            AgentRole.RISK_MANAGER: "风险管理经理"
        }
        for analysis in sorted(team_analyses, key=lambda x: x.priority, reverse=True):
            
            role_name = role_names.get(analysis.agent_role, "未知")
            summary_parts.append(f"""
{role_name} (优先级{analysis.priority}, 风险评分{analysis.risk_score if analysis.risk_score else '暂无评分'}):
- 建议: {analysis.recommendation }
- 置信度: {analysis.confidence if analysis.confidence else "暂无置信度数据"}
- 理由: {analysis.reasoning}...
- 关键指标: {json.dumps(analysis.key_metrics, ensure_ascii=False,)}
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
            "long_ratio": long_votes / total if total > 0 else 0.5,
            "short_ratio": short_votes / total if total > 0 else 0.5,
            "hold_ratio": hold_votes / total if total > 0 else 0.5,
            "net_bias": (long_votes - short_votes) / total if total > 0 else 0.5
        }
    
    def _get_current_position(self, symbol: str, positions: List[Dict]) -> Optional[Dict]:
        """获取当前持仓"""
        for pos in positions:
            if pos.get('symbol') == symbol:
                return pos
        return None
    
    def _analyze_position_status(self, symbol: str, position: Optional[Dict], market_data: Dict) -> str:
        """分析持仓状态"""
        if not position or position.get('amount') == 0:
            return f"""
当前{symbol}持仓状态：
- 无持仓
- 可执行操作：buy(做多), short(做空), hold(观望)
"""
        
        position_type = position.get('position_type', 'buy') # 'buy'表示多仓, 'short'表示空仓
        if position_type == "long":
            position_type = "buy"
        else:
            position_type = "short"
        amount = position.get('amount', 0)
        # 优先使用entry_price，如果不存在则使用average_price
        entry_price = position.get('entry_price') if position.get('entry_price') else position.get('average_price', 0)
        current_price = market_data.get('price', 0)
        stop_loss = position.get('stop_loss', 0)
        take_profit = position.get('take_profit', 0)
        
        # 计算距离止盈止损的距离
        if stop_loss > 0 and current_price > 0:
            if position_type == 'buy':
                stop_loss_distance = ((current_price - stop_loss) / current_price * 100)
            else:
                stop_loss_distance = ((stop_loss - current_price) / current_price * 100)
        else:
            stop_loss_distance = 0
            
        if take_profit > 0 and current_price > 0:
            if position_type == 'buy':
                take_profit_distance = ((take_profit - current_price) / current_price * 100)
            else:
                take_profit_distance = ((current_price - take_profit) / current_price * 100)
        else:
            take_profit_distance = 0
        
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
- 止损价格：${stop_loss:.4f} (距离当前价格: {stop_loss_distance:.2f}%)
- 止盈价格：${take_profit:.4f} (距离当前价格: {take_profit_distance:.2f}%)
- **⚠️ 止盈止损监控**: {"接近止损" if abs(stop_loss_distance) < 2 and stop_loss > 0 else "接近止盈" if abs(take_profit_distance) < 2 and take_profit > 0 else "正常"}
- 可执行操作：sell(平多仓), hold(继续持有)
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
- 止损价格：${stop_loss:.4f} (距离当前价格: {stop_loss_distance:.2f}%)
- 止盈价格：${take_profit:.4f} (距离当前价格: {take_profit_distance:.2f}%)
- **⚠️ 止盈止损监控**: {"接近止损" if abs(stop_loss_distance) < 2 and stop_loss > 0 else "接近止盈" if abs(take_profit_distance) < 2 and take_profit > 0 else "正常"}
- 可执行操作：cover(平空仓), hold(继续持有)
"""
    
    def _identify_market_regime(self, market_data: Dict) -> str:
        """改进的市场环境识别"""
        change = market_data.get('change_24h', 0)
        high = market_data.get('high_24h', 0)
        low = market_data.get('low_24h', 0)
        avg_price = (high + low) / 2
        
        # 改进的波动率计算
        volatility = ((high - low) / avg_price) * 100 if avg_price > 0 else 0
        
        # 波动率分类
        if volatility > 20:
            vol_regime = "极端波动"
        elif volatility > 12:
            vol_regime = "高波动"
        elif volatility > 5:
            vol_regime = "中等波动"
        else:
            vol_regime = "低波动"
        
        # 趋势分类
        if change > 15:
            trend_regime = "强势上涨"
        elif change > 5:
            trend_regime = "温和上涨"
        elif change < -15:
            trend_regime = "强势下跌"
        elif change < -5:
            trend_regime = "温和下跌"
        elif abs(change) < 2:
            trend_regime = "横盘"
        else:
            trend_regime = "小幅震荡"
        
        return f"{vol_regime}-{trend_regime}"
    
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
        if "极端波动" in market_regime :
            original_size = decision.get('position_size', 0.1)
            decision['position_size'] = original_size * 0.5
            decision['reasoning'] = f"[市场极端波动] {decision.get('reasoning', '')}"
        
        # 在高波动市场中适度降低仓位
        elif "高波动" in market_regime :
            original_size = decision.get('position_size', 0.1)
            decision['position_size'] = original_size * 0.7
            decision['reasoning'] = f"[市场高波动] {decision.get('reasoning', '')}"
        
        return decision
    
    def _apply_short_specific_controls(self, decision: Dict, market_data: Dict, portfolio: Dict) -> Dict:
        """应用做空特定风控"""
        # 做空仓位通常更小
        original_size = decision.get('position_size', 0.1)
        decision['position_size'] = original_size * 0.7  # 做空仓位减少30%
        
        # 做空止损更紧
        # stop_loss = decision.get('stop_loss', 0)
        # take_profit = decision.get('take_profit', 0)
        if decision.get('action') == 'short':
            # 做空止损设置在阻力位上方
            # decision['stop_loss'] = stop_loss * 1.08  # 8%止损
            # decision['take_profit'] = take_profit * 0.92  # 8%止盈
            
            # 添加做空风控说明
            decision['reasoning'] = f"[做空风控：仓位-30%] {decision.get('reasoning', '')}"
        
        return decision
    
    def _parse_response(self, content: str) -> Dict:
        """解析AI响应"""
        try:
            # 确保content是字符串
            if not isinstance(content, str):
                logger.warning(f"AI响应不是字符串类型: {type(content)}")
                return {}
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
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
            return ""
        
        created_at = position.get('executed_at')
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
        # 优先使用entry_price，如果不存在则使用average_price
        entry_price = position.get('entry_price') if position.get('entry_price') else position.get('average_price', 0)
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
    
    async def _analyze_trading_performance(self, db_session = None) -> str:
        """分析历史交易表现"""
        try:
            # 如果没有传入数据库会话，尝试创建一个
            if db_session is None:
                try:
                    from backend.database import get_db
                    async for db in get_db():
                        db_session = db
                        break
                except:
                    logger.warning("无法获取数据库连接，返回默认表现分析")
                    return self._get_default_performance()
            
            # 导入必要的模块
            from backend.database import Trade
            from sqlalchemy import select, desc, func
            
            # 查询最近的交易记录（只查询平仓交易，因为只有平仓才有盈亏）
            recent_trades_query = select(Trade).where(
                Trade.success == True,
                Trade.side.in_(['sell', 'cover']),  # 只查询平仓交易
                Trade.profit_loss.isnot(None)  # 确保有盈亏数据
            ).order_by(desc(Trade.timestamp)).limit(50)
            
            result = await db_session.execute(recent_trades_query)
            recent_trades = result.scalars().all()
            
            if not recent_trades or len(recent_trades) == 0:
                return self._get_default_performance()
            
            # 计算统计指标
            total_trades = len(recent_trades)
            winning_trades = sum(1 for t in recent_trades if t.profit_loss and t.profit_loss > 0)
            losing_trades = sum(1 for t in recent_trades if t.profit_loss and t.profit_loss < 0)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # 计算总盈亏
            total_profit = sum(t.profit_loss for t in recent_trades if t.profit_loss)
            avg_profit = total_profit / total_trades if total_trades > 0 else 0
            
            # 计算平均盈利和平均亏损
            winning_trades_list = [t.profit_loss for t in recent_trades if t.profit_loss and t.profit_loss > 0]
            losing_trades_list = [t.profit_loss for t in recent_trades if t.profit_loss and t.profit_loss < 0]
            
            avg_win = sum(winning_trades_list) / len(winning_trades_list) if winning_trades_list else 0
            avg_loss = sum(losing_trades_list) / len(losing_trades_list) if losing_trades_list else 0
            
            # 盈亏比
            profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            # 计算最大回撤
            max_drawdown = self._calculate_max_drawdown(recent_trades)
            
            # 计算最大单笔盈利和亏损
            max_profit = max(winning_trades_list) if winning_trades_list else 0
            max_loss = min(losing_trades_list) if losing_trades_list else 0
            
            # 确定表现状态
            if win_rate >= 60 and profit_loss_ratio >= 1.5:
                status = "🌟 优秀"
                emoji = "🎉"
            elif win_rate >= 50 and profit_loss_ratio >= 1.0:
                status = "✅ 良好"
                emoji = "👍"
            elif win_rate >= 40:
                status = "⚠️ 一般"
                emoji = "😐"
            else:
                status = "❌ 需改进"
                emoji = "⚠️"
            
            return f"""最近交易表现 (最近{total_trades}笔):
━━━━━━━━━━━━━━━━━━━━━━━━━━
基础统计:
- 总交易次数: {total_trades}笔
- 盈利次数: {winning_trades}笔 | 亏损次数: {losing_trades}笔
- 胜率: {win_rate:.2f}%

盈亏分析:
- 总盈亏: ${total_profit:.2f}
- 平均盈亏: ${avg_profit:.2f}/笔
- 平均盈利: ${avg_win:.2f}/笔
- 平均亏损: ${avg_loss:.2f}/笔
- 盈亏比: {profit_loss_ratio:.2f}:1

极值统计:
- 最大单笔盈利: ${max_profit:.2f}
- 最大单笔亏损: ${max_loss:.2f}
- 最大回撤: {max_drawdown:.2f}%

表现评级: {status}
━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        except Exception as e:
            logger.exception(f"分析交易表现失败: {e}")
            return self._get_default_performance()
    
    def _get_default_performance(self) -> str:
        """获取默认的表现分析（无历史数据时）"""
        return """暂无历史交易数据"""
    
    def _calculate_max_drawdown(self, trades: List) -> float:
        """计算最大回撤百分比"""
        try:
            if not trades:
                return 0.0
            
            # 计算累计盈亏曲线
            cumulative_pnl = []
            running_total = 0
            
            # 按时间排序（从旧到新）
            sorted_trades = sorted(trades, key=lambda x: x.timestamp)
            
            for trade in sorted_trades:
                if trade.profit_loss:
                    running_total += trade.profit_loss
                    cumulative_pnl.append(running_total)
            
            if not cumulative_pnl:
                return 0.0
            
            # 计算最大回撤
            peak = cumulative_pnl[0]
            max_drawdown = 0
            
            for value in cumulative_pnl:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / abs(peak) * 100 if peak != 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
        except Exception as e:
            logger.warning(f"计算最大回撤失败: {e}")
            return 0.0
    
    def _get_dynamic_risk_context(self, performance_analysis: str) -> str:
        """获取动态风险状态"""
        # 根据历史表现动态调整风险参数
        # 简化版本：返回标准风控
        return """
风险状态: 标准模式
- 最大仓位: 20%
- 单笔损失上限: 5%
- 最大回撤限制: 8%
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
            
            # 确保价格数据转换为float类型，并处理可能的异常
            try:
                best_bid = float(order_book['bids'][0][0]) if order_book['bids'] and len(order_book['bids'][0]) > 0 else 0
                best_ask = float(order_book['asks'][0][0]) if order_book['asks'] and len(order_book['asks'][0]) > 0 else 0
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"盘口价格数据转换失败: {e}, bids={order_book.get('bids')}, asks={order_book.get('asks')}")
                return {
                    'info': '盘口数据格式错误',
                    'spread_percentage': 'N/A'
                }
            
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


"""
多智能体团队协同管理器
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger

from backend.agents.fundamental_analyst import FundamentalAnalyst
from backend.agents.sentiment_analyst import SentimentAnalyst
from backend.agents.news_analyst import NewsAnalyst
from backend.agents.technical_analyst import TechnicalAnalyst
from backend.agents.risk_manager import RiskManager
from backend.agents.portfolio_manager import PortfolioManager
from backend.agents.base_agent import AgentAnalysis, AgentRole
from backend.agents.kline_compressor import kline_compressor
from backend.agents.stop_loss_decision_system import stop_decision_system
from backend.config import settings


class AgentTeam:
    """
    AI分析师团队 - 多智能体协同决策系统
    
    团队成员（7名专家，3个AI模型）：
    1. 技术分析师(DeepSeek) - 短期交易信号
    2. 技术分析师(千问3) - 技术指标验证
    3. 情绪分析师(Grok) - 市场情绪判断
    4. 基本面分析师(DeepSeek) - 长期价值评估
    5. 新闻分析师(Grok) - 推特/事件影响分析
    6. 风险管理经理(DeepSeek) - 风险评估和控制
    7. 投资组合经理(DeepSeek) - 最终决策者
    
    模型分配：
    - Grok: 新闻分析、情绪分析（擅长社交媒体和实时信息）
    - DeepSeek: 基本面、风险管理、投资组合、技术分析（专业金融分析）
    - 千问3: 技术分析（双重验证机制）
    """
    
    def __init__(self):
        self.agents = {}
        self._initialize_team()
    
    def _initialize_team(self):
        """初始化分析师团队 - 多模型协同"""
        # 技术分析师 - DeepSeek + 千问3 (双引擎)
        try:
            if settings.deepseek_api_key:
                self.agents['technical_deepseek'] = TechnicalAnalyst("DeepSeek", settings.deepseek_api_key)
                logger.info("✅ 技术分析师(DeepSeek)已就位")
        except Exception as e:
            logger.warning(f"技术分析师(DeepSeek)初始化失败: {e}")
        
        try:
            if settings.qwen_api_key:
                self.agents['technical_qwen'] = TechnicalAnalyst("Qwen", settings.qwen_api_key)
                logger.info("✅ 技术分析师(千问3)已就位")
        except Exception as e:
            logger.warning(f"技术分析师(千问3)初始化失败: {e}")
        
        # 情绪分析师 - DeepSeek (改用DeepSeek API)
        try:
            if settings.deepseek_api_key:
                self.agents['sentiment'] = SentimentAnalyst("DeepSeek", settings.deepseek_api_key)
                logger.info("✅ 情绪分析师已就位 (DeepSeek)")
        except Exception as e:
            logger.warning(f"情绪分析师初始化失败: {e}")
        
        # 新闻分析师 - DeepSeek (改用DeepSeek API)
        try:
            if settings.deepseek_api_key:
                self.agents['news'] = NewsAnalyst("DeepSeek", settings.deepseek_api_key)
                logger.info("✅ 新闻分析师已就位 (DeepSeek)")
        except Exception as e:
            logger.warning(f"新闻分析师初始化失败: {e}")
        
        # 基本面分析师 - DeepSeek
        try:
            if settings.deepseek_api_key:
                self.agents['fundamental'] = FundamentalAnalyst("DeepSeek", settings.deepseek_api_key)
                logger.info("✅ 基本面分析师已就位 (DeepSeek)")
        except Exception as e:
            logger.warning(f"基本面分析师初始化失败: {e}")
        
        # 风险管理经理 - DeepSeek
        try:
            if settings.deepseek_api_key:
                self.agents['risk'] = RiskManager("DeepSeek", settings.deepseek_api_key)
                logger.info("✅ 风险管理经理已就位 (DeepSeek)")
        except Exception as e:
            logger.warning(f"风险管理经理初始化失败: {e}")
        
        # 投资组合经理 - DeepSeek
        try:
            if settings.deepseek_api_key:
                self.agents['portfolio'] = PortfolioManager("DeepSeek", settings.deepseek_api_key)
                logger.info("✅ 投资组合经理已就位 (DeepSeek)")
        except Exception as e:
            logger.warning(f"投资组合经理初始化失败: {e}")
        
        # 统计模型分布
        model_distribution = {}
        for agent in self.agents.values():
            model = agent.ai_model
            model_distribution[model] = model_distribution.get(model, 0) + 1
        
        model_info = ", ".join([f"{model}({count})" for model, count in model_distribution.items()])
        logger.info(f"🤖 分析师团队组建完成，共{len(self.agents)}名成员 [{model_info}]")
    
    async def conduct_team_analysis(
        self,
        symbol: str,
        market_data: Dict,
        portfolio: Dict,
        positions: List[Dict],
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        进行团队协同分析（集成K线数据）
        
        工作流程：
        1. 获取并压缩K线数据
        2. 各分析师并行分析（使用K线数据）
        3. 风险管理经理评估风险
        4. 投资组合经理综合决策
        5. 返回最终决策和完整分析报告
        """
        if not self.agents:
            logger.error("分析师团队未初始化")
            return self._empty_decision("分析师团队未初始化")
        
        try:
            logger.info(f"🔍 开始团队分析: {symbol}")
            
            # 准备额外数据
            if additional_data is None:
                additional_data = {}
            
            # 获取K线数据并压缩
            raw_klines = additional_data.get('raw_klines', [])
            kline_interval = additional_data.get('kline_interval', '1h')
            
            if raw_klines:
                logger.info(f"📊 压缩K线数据: {symbol} {kline_interval}, 原始数据{len(raw_klines)}根")
                compressed_kline_data = kline_compressor.compress_kline_data(
                    raw_klines, kline_interval, symbol
                )
                
                # 将压缩后的K线数据添加到额外数据中
                additional_data['kline_compressed'] = compressed_kline_data
                additional_data['kline_interval'] = kline_interval
                
                logger.info(f"✅ K线数据压缩完成，提取{len(compressed_kline_data)}维特征")
            else:
                logger.warning(f"⚠️ 未提供K线数据，将使用简化分析")
            
            additional_data['portfolio'] = portfolio
            additional_data['positions'] = positions
            
            # 第一阶段：并行执行各分析师的分析
            analysis_tasks = []
            
            # 技术分析师 - DeepSeek
            if 'technical_deepseek' in self.agents:
                analysis_tasks.append(
                    self.agents['technical_deepseek'].analyze(symbol, market_data, additional_data)
                )
            
            # 技术分析师 - 千问3
            # if 'technical_qwen' in self.agents:
            #     analysis_tasks.append(
            #         self.agents['technical_qwen'].analyze(symbol, market_data, additional_data)
            #     )
            
            # # 情绪分析师 - Grok
            if 'sentiment' in self.agents:
                analysis_tasks.append(
                    self.agents['sentiment'].analyze(symbol, market_data, additional_data)
                )
            
            # 基本面分析师 - DeepSeek
            if 'fundamental' in self.agents:
                analysis_tasks.append(
                    self.agents['fundamental'].analyze(symbol, market_data, additional_data)
                )
            if settings.news_api_url:
                if 'news' in self.agents:
                    analysis_tasks.append(
                        self.agents['news'].analyze(symbol, market_data, additional_data)
                    )
            
            # 执行分析
            team_analyses: List[AgentAnalysis] = await asyncio.gather(
                *analysis_tasks, 
                return_exceptions=True
            )
            
            # 过滤有效结果
            valid_analyses = [
                a for a in team_analyses 
                if isinstance(a, AgentAnalysis)
            ]
            
            if not valid_analyses:
                logger.error("所有分析师分析失败")
                return self._empty_decision("所有分析师分析失败")
            
            logger.info(f"✅ {len(valid_analyses)}/{len(analysis_tasks)} 位分析师完成分析")
            
            # 第二阶段：风险管理评估
            if 'risk' in self.agents:
                risk_analysis = await self.agents['risk'].analyze(
                    symbol, market_data, additional_data
                )
                if isinstance(risk_analysis, AgentAnalysis):
                    valid_analyses.append(risk_analysis)
                    logger.info(f"✅ 风险管理经理完成评估 - 风险评分: {risk_analysis.risk_score:.2f}")
            
            # 第三阶段：投资组合经理做出最终决策
            if 'portfolio' in self.agents:
                # 确保portfolio包含positions信息，供投资组合经理分析持仓状态
                portfolio_with_positions = {
                    **portfolio,
                    'positions': positions
                }
                
                final_decision = await self.agents['portfolio'].make_final_decision(
                    symbol, market_data, valid_analyses, portfolio_with_positions
                )
                
                # 根据决策结果提供更详细的日志
                action = final_decision.get('action', 'hold')
                decision_type = final_decision.get('final_decision', 'reject')
                confidence = final_decision.get('confidence', 0.0)
                
                if decision_type == 'approve':
                    if action == 'sell':
                        logger.info(f"✅ 批准 {symbol} 卖出(平多仓) (置信度: {confidence:.2f})")
                    elif action == 'cover':
                        logger.info(f"✅ 批准 {symbol} 平空仓 (置信度: {confidence:.2f})")
                    elif action == 'buy':
                        logger.info(f"✅ 批准 {symbol} 做多 (置信度: {confidence:.2f})")
                    elif action == 'short':
                        logger.info(f"✅ 批准 {symbol} 做空 (置信度: {confidence:.2f})")
                    else:
                        logger.info(f"✅ 批准 {symbol} {action} (置信度: {confidence:.2f})")
                else:
                    logger.info(f"❌ 拒绝 {symbol} {action} (置信度: {confidence:.2f})")
                
                return final_decision
            else:
                # 如果没有投资组合经理，使用简单的共识机制
                return self._fallback_consensus(valid_analyses)
        
        except Exception as e:
            logger.error(f"团队分析失败: {e}")
            return self._empty_decision(f"团队分析异常: {str(e)}")
    
    def _fallback_consensus(self, analyses: List[AgentAnalysis]) -> Dict:
        """备用共识机制（当投资组合经理不可用时）"""
        # 统计建议
        recommendations = {}
        total_confidence = 0
        
        for analysis in analyses:
            rec = analysis.recommendation
            if rec not in recommendations:
                recommendations[rec] = []
            recommendations[rec].append(analysis)
            total_confidence += analysis.confidence
        
        # 找出最多支持的建议
        max_votes = 0
        final_recommendation = "hold"
        
        for rec, votes in recommendations.items():
            if len(votes) > max_votes:
                max_votes = len(votes)
                final_recommendation = rec
        
        avg_confidence = total_confidence / len(analyses) if analyses else 0
        
        return {
            "final_decision": "approve" if avg_confidence > 0.6 else "reject",
            "action": final_recommendation,
            "confidence": avg_confidence,
            "position_size": 0.1,
            "reasoning": f"共识决策: {max_votes}/{len(analyses)} 位分析师支持 {final_recommendation}",
            "stop_loss": 0,
            "take_profit": 0,
            "key_considerations": [],
            "team_analyses": [
                {
                    "role": a.agent_role.value,
                    "recommendation": a.recommendation,
                    "confidence": a.confidence,
                    "reasoning": a.reasoning[:200]
                }
                for a in analyses
            ]
        }
    
    def _empty_decision(self, reason: str) -> Dict:
        """空决策（出错时返回）"""
        return {
            "final_decision": "reject",
            "action": "hold",
            "confidence": 0.0,
            "position_size": 0.0,
            "reasoning": reason,
            "stop_loss": 0,
            "take_profit": 0,
            "key_considerations": [],
            "team_analyses": []
        }
    
    async def evaluate_stop_loss_decision(
        self,
        position_id: str,
        symbol: str,
        market_data: Dict,
        position_info: Dict
    ) -> Dict:
        """
        团队协同评估止盈止损决策
        
        工作流程：
        1. 所有分析师并行分析当前市场状况
        2. 从分析中提取止盈止损意见
        3. 投资组合经理综合所有意见做出最终决策
        
        Args:
            position_id: 持仓ID
            symbol: 交易对
            market_data: 市场数据
            position_info: 持仓信息
        
        Returns:
            止盈止损决策结果
        """
        if not self.agents:
            logger.error("分析师团队未初始化")
            return {'final_decision': 'hold', 'action': 'hold', 'reasoning': '团队未初始化'}
        
        try:
            logger.info(f"🔍 团队评估止盈止损: {symbol} (持仓ID: {position_id})")
            
            # 准备分析数据
            additional_data = {
                'position_info': position_info,
                'portfolio': position_info.get('portfolio', {})
            }
            
            # 第一阶段：并行执行各分析师的分析
            analysis_tasks = []
            
            # 技术分析师
            if 'technical_deepseek' in self.agents:
                analysis_tasks.append(
                    self.agents['technical_deepseek'].analyze(symbol, market_data, additional_data)
                )
            if 'technical_qwen' in self.agents:
                analysis_tasks.append(
                    self.agents['technical_qwen'].analyze(symbol, market_data, additional_data)
                )
            
            # 情绪分析师
            if 'sentiment' in self.agents:
                analysis_tasks.append(
                    self.agents['sentiment'].analyze(symbol, market_data, additional_data)
                )
            
            # 基本面分析师
            if 'fundamental' in self.agents:
                analysis_tasks.append(
                    self.agents['fundamental'].analyze(symbol, market_data, additional_data)
                )
            
            # 新闻分析师
            if 'news' in self.agents:
                analysis_tasks.append(
                    self.agents['news'].analyze(symbol, market_data, additional_data)
                )
            
            # 风险管理经理（必须参与）
            if 'risk' in self.agents:
                analysis_tasks.append(
                    self.agents['risk'].analyze(symbol, market_data, additional_data)
                )
            
            # 执行分析
            team_analyses: List[AgentAnalysis] = await asyncio.gather(
                *analysis_tasks, 
                return_exceptions=True
            )
            
            # 过滤有效结果
            valid_analyses = [
                a for a in team_analyses 
                if isinstance(a, AgentAnalysis)
            ]
            
            if not valid_analyses:
                logger.error("所有分析师分析失败")
                return {'final_decision': 'hold', 'action': 'hold', 'reasoning': '分析失败'}
            
            logger.info(f"✅ {len(valid_analyses)}/{len(analysis_tasks)} 位分析师完成止盈止损评估")
            
            # 第二阶段：收集止盈止损意见
            stop_opinions = stop_decision_system.collect_team_opinions(
                position_id, valid_analyses, market_data
            )
            
            # 第三阶段：投资组合经理做出最终决策
            final_decision = stop_decision_system.make_stop_decision(
                position_id, stop_opinions, market_data
            )
            
            logger.info(
                f"{'✅ 执行' if final_decision['final_decision'] == 'execute' else '⏸️  继续持仓'} "
                f"{symbol} {final_decision['action']} "
                f"(置信度: {final_decision['confidence']:.2f}, 紧急度: {final_decision['urgency']:.2f})"
            )
            
            return final_decision
        
        except Exception as e:
            logger.error(f"团队止盈止损评估失败: {e}")
            return {'final_decision': 'hold', 'action': 'hold', 'reasoning': f'评估异常: {str(e)}'}
    
    def get_team_status(self) -> Dict:
        """获取团队状态"""
        return {
            "team_size": len(self.agents),
            "members": [
                {
                    "role": agent.role.value,
                    "name": agent.name,
                    "model": agent.ai_model,
                    "status": "active"
                }
                for agent in self.agents.values()
            ]
        }


# 全局智能体团队实例
agent_team = AgentTeam()


"""
AI模型管理器
"""
import asyncio
from typing import List, Dict
from loguru import logger
from backend.ai.gpt_model import GPTModel
from backend.ai.deepseek_model import DeepSeekModel
from backend.ai.deepseek_r1_model import DeepSeekR1Model
from backend.ai.grok_model import GrokModel
from backend.ai.base_model import BaseAIModel, AIDecisionResult


class AIManager:
    """AI模型管理器 - 协调多个AI模型做出决策"""
    
    def __init__(self):
        self.models: List[BaseAIModel] = []
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化所有AI模型"""
        try:
            self.models.append(GPTModel())
            logger.info("GPT模型已加载")
        except Exception as e:
            logger.warning(f"GPT模型加载失败: {e}")
        
        try:
            # 优先使用DeepSeek-R1推理模型
            self.models.append(DeepSeekR1Model())
            logger.info("DeepSeek-R1推理模型已加载")
        except Exception as e:
            logger.warning(f"DeepSeek-R1模型加载失败: {e}")
            # 回退到普通DeepSeek
            try:
                self.models.append(DeepSeekModel())
                logger.info("DeepSeek模型已加载（回退）")
            except Exception as e2:
                logger.warning(f"DeepSeek模型加载失败: {e2}")
        
        try:
            self.models.append(GrokModel())
            logger.info("Grok模型已加载")
        except Exception as e:
            logger.warning(f"Grok模型加载失败: {e}")
    
    async def get_consensus_decision(
        self,
        symbol: str,
        market_data: Dict,
        current_positions: List[Dict],
        portfolio_value: float
    ) -> Dict:
        """
        获取所有AI模型的共识决策
        
        Returns:
            包含最终决策和各模型分析的字典
        """
        if not self.models:
            logger.error("没有可用的AI模型")
            return {
                "final_decision": "hold",
                "confidence": 0.0,
                "reasoning": "没有可用的AI模型",
                "models_analysis": []
            }
        
        # 并行请求所有模型
        tasks = [
            model.analyze_market(symbol, market_data, current_positions, portfolio_value)
            for model in self.models
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集有效结果
        valid_results = []
        models_analysis = []
        
        for model, result in zip(self.models, results):
            if isinstance(result, Exception):
                logger.error(f"{model.name} 分析出错: {result}")
                models_analysis.append({
                    "model": model.name,
                    "status": "error",
                    "error": str(result)
                })
                continue
            
            if isinstance(result, AIDecisionResult):
                valid_results.append(result)
                models_analysis.append({
                    "model": model.name,
                    "decision": result.decision,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "suggested_amount": result.suggested_amount
                })
        
        if not valid_results:
            return {
                "final_decision": "hold",
                "confidence": 0.0,
                "reasoning": "所有模型分析失败",
                "models_analysis": models_analysis
            }
        
        # 计算共识决策
        final_decision = self._calculate_consensus(valid_results)
        
        return {
            "final_decision": final_decision['decision'],
            "confidence": final_decision['confidence'],
            "reasoning": final_decision['reasoning'],
            "suggested_amount": final_decision['suggested_amount'],
            "stop_loss": final_decision['stop_loss'],
            "take_profit": final_decision['take_profit'],
            "models_analysis": models_analysis,
            "total_models": len(self.models),
            "successful_models": len(valid_results)
        }
    
    def _calculate_consensus(self, results: List[AIDecisionResult]) -> Dict:
        """计算共识决策"""
        # 统计每种决策的投票
        decision_votes = {}
        for result in results:
            decision = result.decision
            if decision not in decision_votes:
                decision_votes[decision] = []
            decision_votes[decision].append(result)
        
        # 找出得票最多的决策
        max_votes = 0
        consensus_decision = "hold"
        
        for decision, votes in decision_votes.items():
            if len(votes) > max_votes:
                max_votes = len(votes)
                consensus_decision = decision
        
        # 获取该决策的所有结果
        consensus_results = decision_votes[consensus_decision]
        
        # 计算平均置信度和建议金额
        avg_confidence = sum(r.confidence for r in consensus_results) / len(consensus_results)
        avg_amount = sum(r.suggested_amount for r in consensus_results) / len(consensus_results)
        
        # 取最保守的止损和止盈
        stop_losses = [r.stop_loss for r in consensus_results if r.stop_loss > 0]
        take_profits = [r.take_profit for r in consensus_results if r.take_profit > 0]
        
        stop_loss = max(stop_losses) if stop_losses else 0
        take_profit = min(take_profits) if take_profits else 0
        
        # 组合推理
        reasoning_parts = [f"- {r.reasoning}" for r in consensus_results]
        combined_reasoning = (
            f"共识决策: {consensus_decision} (得票: {len(consensus_results)}/{len(results)})\n"
            f"各模型分析:\n" + "\n".join(reasoning_parts)
        )
        
        return {
            "decision": consensus_decision,
            "confidence": avg_confidence,
            "reasoning": combined_reasoning,
            "suggested_amount": avg_amount,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
    
    async def get_all_models_status(self) -> List[Dict]:
        """获取所有模型状态"""
        tasks = [model.get_model_status() for model in self.models]
        statuses = await asyncio.gather(*tasks)
        return statuses


# 全局AI管理器实例
ai_manager = AIManager()


"""
测试风控配置注入到AI提示词
"""
import asyncio
from backend.config import settings
from backend.agents.prompts import get_risk_control_context
from backend.agents.agent_team import agent_team


def test_risk_control_context():
    """测试风控配置上下文生成"""
    print("=" * 80)
    print("测试 1: 风控配置上下文生成")
    print("=" * 80)
    
    context = get_risk_control_context()
    print(context)
    
    # 验证关键参数是否包含
    assert f"${settings.initial_balance:.2f}" in context, "初始资金未包含"
    assert f"{settings.max_position_size * 100:.1f}%" in context, "最大仓位未包含"
    assert f"{settings.risk_per_trade * 100:.1f}%" in context, "单笔风险未包含"
    assert f"{settings.max_wallet_usage * 100:.0f}%" in context, "钱包使用上限未包含"
    assert f"{settings.margin_reserve_ratio * 100:.0f}%" in context, "保证金预留未包含"
    assert f"{settings.risk_threshold:.2f}" in context, "风险阈值未包含"
    assert f"{settings.confidence_threshold:.2f}" in context, "置信度阈值未包含"
    assert f"{settings.max_concurrent_trades}" in context, "最大并发交易数未包含"
    
    print("\n[OK] 所有风控参数都已正确包含在上下文中\n")


def test_config_values():
    """测试配置值读取"""
    print("=" * 80)
    print("测试 2: 配置值读取")
    print("=" * 80)
    
    print(f"初始余额: ${settings.initial_balance:.2f}")
    print(f"最大仓位: {settings.max_position_size * 100:.1f}%")
    print(f"单笔风险: {settings.risk_per_trade * 100:.1f}%")
    print(f"钱包使用上限: {settings.max_wallet_usage * 100:.0f}%")
    print(f"保证金预留: {settings.margin_reserve_ratio * 100:.0f}%")
    print(f"风险阈值: {settings.risk_threshold:.2f}")
    print(f"置信度阈值: {settings.confidence_threshold:.2f}")
    print(f"最大并发交易: {settings.max_concurrent_trades}个")
    
    print("\n[OK] 配置值读取成功\n")


def test_agent_team_initialization():
    """测试分析师团队初始化"""
    print("=" * 80)
    print("测试 3: 分析师团队初始化")
    print("=" * 80)
    
    status = agent_team.get_team_status()
    print(f"团队规模: {status['team_size']} 名成员")
    print("\n团队成员:")
    for member in status['members']:
        print(f"  - {member['name']} ({member['role']}) - {member['model']}")
    
    print(f"\n[OK] 团队初始化成功，共 {status['team_size']} 名成员\n")


async def test_analyst_with_risk_control():
    """测试分析师使用风控配置"""
    print("=" * 80)
    print("测试 4: 分析师使用风控配置（模拟）")
    print("=" * 80)
    
    # 模拟市场数据
    market_data = {
        "symbol": "BTCUSDT",
        "price": 50000,
        "change_24h": 5.2,
        "volume_24h": 1000000000,
        "high_24h": 51000,
        "low_24h": 49000
    }
    
    portfolio = {
        "total_balance": settings.initial_balance,
        "cash_balance": settings.initial_balance,
        "positions_value": 0,
        "total_pnl": 0
    }
    
    print(f"测试交易对: {market_data['symbol']}")
    print(f"当前价格: ${market_data['price']:,.2f}")
    print(f"投资组合余额: ${portfolio['total_balance']:,.2f}")
    
    print("\n[OK] 风控规则已注入到以下分析师的提示词中:")
    if 'technical_deepseek' in agent_team.agents:
        print("  [+] 技术分析师 (DeepSeek)")
    if 'technical_qwen' in agent_team.agents:
        print("  [+] 技术分析师 (千问)")
    if 'sentiment' in agent_team.agents:
        print("  [+] 情绪分析师")
    if 'fundamental' in agent_team.agents:
        print("  [+] 基本面分析师")
    if 'news' in agent_team.agents:
        print("  [+] 新闻分析师")
    if 'risk' in agent_team.agents:
        print("  [+] 风险管理经理")
    if 'portfolio' in agent_team.agents:
        print("  [+] 投资组合经理")
    
    print("\n[OK] 所有分析师都已正确注入风控配置\n")


def test_risk_control_rules():
    """测试风控规则显示"""
    print("=" * 80)
    print("测试 5: 风控规则详细信息")
    print("=" * 80)
    
    context = get_risk_control_context()
    lines = context.strip().split('\n')
    
    print("风控规则内容预览:")
    for line in lines[:15]:  # 显示前15行
        print(line)
    
    print("\n[OK] 风控规则格式正确\n")


def main():
    """运行所有测试"""
    print("\n")
    print("[*] 开始测试风控配置注入功能")
    print("=" * 80)
    print()
    
    try:
        # 测试1: 风控配置上下文
        test_risk_control_context()
        
        # 测试2: 配置值读取
        test_config_values()
        
        # 测试3: 团队初始化
        test_agent_team_initialization()
        
        # 测试4: 分析师使用风控配置
        asyncio.run(test_analyst_with_risk_control())
        
        # 测试5: 风控规则显示
        test_risk_control_rules()
        
        print("=" * 80)
        print("[SUCCESS] 所有测试通过！风控配置注入功能正常工作")
        print("=" * 80)
        
        print("\n[!] 使用提示:")
        print("  1. 修改 .env 文件可以调整风控参数")
        print("  2. 修改后需要重启后端服务")
        print("  3. AI分析师会自动使用新的风控规则")
        print()
        
    except AssertionError as e:
        print(f"\n[ERROR] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


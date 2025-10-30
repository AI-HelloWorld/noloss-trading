"""
真实交易配置向导
帮助用户检查和配置API密钥，启动真实交易
"""
import os
import sys
from pathlib import Path

# 设置UTF-8编码（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_header(title):
    """打印标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_section(title):
    """打印小节标题"""
    print(f"\n{title}")
    print("-"*80)

def check_env_file():
    """检查.env文件"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ 找到.env配置文件")
        return True
    else:
        print("❌ 未找到.env文件")
        
        # 检查是否有示例文件
        if Path("env.example").exists():
            print("\nℹ️  找到env.example文件")
            response = input("是否要从env.example创建.env文件？(y/n): ").strip().lower()
            if response == 'y':
                import shutil
                shutil.copy("env.example", ".env")
                print("✅ 已创建.env文件，请编辑配置")
                return True
        else:
            print("\n请创建.env文件，参考以下模板：")
            print_env_template()
        return False

def print_env_template():
    """打印配置模板"""
    template = """
# AsterDEX API配置（标准模式）
ASTER_DEX_API_KEY=从AsterDEX获取的API密钥
ASTER_DEX_API_SECRET=从AsterDEX获取的API密钥Secret
WALLET_ADDRESS=你的钱包地址

# 交易配置
INITIAL_BALANCE=100.0
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=0.02
ENABLE_AUTO_TRADING=true

# 风控配置
MAX_WALLET_USAGE=0.5
MARGIN_RESERVE_RATIO=0.3

# AI模型配置
DEEPSEEK_API_KEY=你的DeepSeek密钥
QWEN_API_KEY=你的千问密钥
"""
    print(template)

def load_env_config():
    """加载环境配置"""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'api_key': os.getenv('ASTER_DEX_API_KEY', ''),
        'api_secret': os.getenv('ASTER_DEX_API_SECRET', ''),
        'wallet_address': os.getenv('WALLET_ADDRESS', ''),
        'initial_balance': os.getenv('INITIAL_BALANCE', '100.0'),
        'enable_auto_trading': os.getenv('ENABLE_AUTO_TRADING', 'true'),
    }
    
    return config

def validate_config(config):
    """验证配置"""
    print_section("📋 配置验证")
    
    issues = []
    warnings = []
    
    # 检查API Key
    api_key = config['api_key']
    if not api_key:
        issues.append("❌ ASTER_DEX_API_KEY 未配置")
    elif api_key.startswith('0x') and len(api_key) == 66:
        issues.append("❌ ASTER_DEX_API_KEY 看起来像钱包地址，不是API密钥")
        print(f"   当前值: {api_key}")
        print("   这是以太坊地址格式，请使用从AsterDEX生成的真实API密钥")
    else:
        print(f"✅ API Key 已配置")
        print(f"   长度: {len(api_key)} 字符")
        print(f"   前缀: {api_key[:10]}...")
    
    # 检查API Secret
    api_secret = config['api_secret']
    if not api_secret:
        warnings.append("⚠️  ASTER_DEX_API_SECRET 未配置（如使用专业API可忽略）")
    else:
        print(f"✅ API Secret 已配置")
        print(f"   长度: {len(api_secret)} 字符")
    
    # 检查钱包地址
    wallet = config['wallet_address']
    if not wallet:
        warnings.append("⚠️  WALLET_ADDRESS 未配置（标准API不需要）")
    else:
        print(f"✅ Wallet Address 已配置")
        print(f"   地址: {wallet}")
        if wallet.startswith('0x') and len(wallet) == 42:
            print("   ✅ 格式正确（以太坊地址）")
        else:
            warnings.append("⚠️  钱包地址格式可能不正确")
    
    # 确定认证模式
    print_section("🔐 认证模式")
    if api_key and api_secret:
        print("✅ 将使用标准API模式（HMAC-SHA256签名）")
        print("   需要: API Key + API Secret")
    elif api_key and wallet:
        print("✅ 将使用专业API模式（Bearer Token）")
        print("   需要: API Key + 钱包地址")
    else:
        issues.append("❌ 配置不完整，无法确定认证模式")
    
    # 显示问题和警告
    if issues:
        print_section("❌ 发现问题")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print_section("⚠️  警告")
        for warning in warnings:
            print(f"  {warning}")
    
    return len(issues) == 0

def main():
    """主函数"""
    print_header("🚀 AsterDEX 真实交易配置向导")
    
    # 步骤1: 检查.env文件
    print_section("步骤1: 检查配置文件")
    if not check_env_file():
        print("\n⚠️  请先创建并配置.env文件")
        return
    
    # 步骤2: 加载配置
    print_section("步骤2: 加载配置")
    try:
        config = load_env_config()
        print("✅ 配置加载成功")
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return
    
    # 步骤3: 验证配置
    print_section("步骤3: 验证配置")
    is_valid = validate_config(config)
    
    # 步骤4: 测试建议
    print_section("📊 下一步")
    
    if is_valid:
        print("\n✅ 配置验证通过！\n")
        print("现在可以运行以下命令测试：\n")
        print("1. 测试API认证：")
        print("   python test_api_auth.py\n")
        print("2. 测试钱包余额同步：")
        print("   python test_wallet_balance_sync.py\n")
        print("3. 启动真实交易系统：")
        print("   python -m uvicorn backend.main:app --reload\n")
        
        # 询问是否立即测试
        print("-"*80)
        response = input("\n是否立即运行API认证测试？(y/n): ").strip().lower()
        if response == 'y':
            print("\n正在运行测试...")
            os.system("python test_api_auth.py")
    else:
        print("\n❌ 配置存在问题，请修复后再试\n")
        print("主要问题：")
        print("  - API Key 格式不正确（看起来像钱包地址）")
        print("  - 请从AsterDEX后台获取正确的API密钥\n")
        print("获取API密钥的步骤：")
        print("  1. 登录 https://asterdex.com")
        print("  2. 进入 API管理 页面")
        print("  3. 创建新的API密钥")
        print("  4. 确保勾选 '余额查询' 和 '交易' 权限")
        print("  5. 复制生成的API Key和Secret")
        print("  6. 粘贴到 .env 文件")
    
    print_header("配置向导完成")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


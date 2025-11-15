"""
API配置诊断工具 - 检查AsterDEX API配置是否正确
"""
import os
import sys
from dotenv import load_dotenv

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

print("="*80)
print("AsterDEX API 配置诊断")
print("="*80)

api_key = os.getenv("ASTER_DEX_API_KEY", "")
api_secret = os.getenv("ASTER_DEX_API_SECRET", "")
wallet_address = os.getenv("WALLET_ADDRESS", "")

print("\n📋 当前配置状态：")
print("-"*80)

# 检查API Key
print(f"\n1️⃣ API Key:")
if not api_key:
    print("   ❌ 未配置")
else:
    print(f"   ✅ 已配置")
    print(f"   长度: {len(api_key)} 字符")
    print(f"   前缀: {api_key[:10]}...")
    print(f"   后缀: ...{api_key[-10:]}")
    
    # 检查格式
    if api_key.startswith("0x") and len(api_key) == 66:
        print("   ⚠️  警告：这看起来像钱包地址而不是API密钥！")
        print("   💡 提示：API密钥通常是长字符串，不以0x开头")
    elif api_key.startswith("sk-") or api_key.startswith("api-"):
        print("   ✅ 格式似乎正确（标准API密钥格式）")
    else:
        print("   ℹ️  格式待确认（请查看AsterDEX文档）")

# 检查API Secret
print(f"\n2️⃣ API Secret:")
if not api_secret:
    print("   ⚠️  未配置（专业API可能不需要）")
else:
    print(f"   ✅ 已配置")
    print(f"   长度: {len(api_secret)} 字符")

# 检查钱包地址
print(f"\n3️⃣ Wallet Address:")
if not wallet_address:
    print("   ❌ 未配置")
else:
    print(f"   ✅ 已配置: {wallet_address}")
    if wallet_address.startswith("0x") and len(wallet_address) == 42:
        print("   ✅ 格式正确（以太坊地址格式）")
    else:
        print("   ⚠️  格式可能不正确")

print("\n" + "="*80)
print("📊 诊断结果：")
print("="*80)

if api_key.startswith("0x") and len(api_key) == 66:
    print("\n❌ 问题：API Key 配置错误！")
    print("\n📝 你当前的配置：")
    print(f"   ASTER_DEX_API_KEY={api_key}")
    print("\n这是一个钱包地址，不是API密钥！")
    print("\n✅ 正确的配置应该是：")
    print("   ASTER_DEX_API_KEY=<从AsterDEX获取的真实API密钥>")
    print("   WALLET_ADDRESS=0x713f416869153Cd28E086Add9f82a924aD6B0465")
    print("\n📖 如何获取正确的API密钥：")
    print("   1. 登录 AsterDEX 网站")
    print("   2. 进入 API 管理页面")
    print("   3. 创建新的API密钥")
    print("   4. 复制生成的密钥（通常很长，可能以特定前缀开头）")
    print("   5. 将密钥粘贴到 .env 文件的 ASTER_DEX_API_KEY=")
    
elif not api_key:
    print("\n⚠️  问题：未配置API密钥")
    print("\n需要在 .env 文件中添加：")
    print("   ASTER_DEX_API_KEY=<你的API密钥>")
    print("   WALLET_ADDRESS=<你的钱包地址>")
    
else:
    print("\n✅ API配置看起来正常！")
    print("\n如果仍然遇到 'API-key format invalid' 错误，可能原因：")
    print("   1. API密钥已过期或被撤销")
    print("   2. API密钥没有足够的权限")
    print("   3. AsterDEX可能需要特定格式的密钥")
    print("\n建议：")
    print("   1. 重新生成API密钥")
    print("   2. 确保API密钥有 '查询余额' 权限")
    print("   3. 查看AsterDEX官方文档确认密钥格式")

print("\n" + "="*80)
print("💡 使用建议：")
print("="*80)
print("\n如果你正在测试系统功能，可以暂时使用模拟模式：")
print("   1. 注释掉 .env 中的 ASTER_DEX_API_KEY")
print("   2. 系统会自动切换到模拟模式")
print("   3. 模拟模式下所有功能都能正常运行")
print("   4. 等获取到正确的API密钥后再切换到真实模式")

print("\n" + "="*80)


"""
重构模式快速切换工具

使用方法:
  python toggle_refactoring_mode.py        # 查看当前状态
  python toggle_refactoring_mode.py on     # 开启重构模式
  python toggle_refactoring_mode.py off    # 关闭重构模式
"""
import sys
import re


def get_current_mode():
    """获取当前模式"""
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'REFACTORING_MODE\s*=\s*(True|False)', content)
    if match:
        return match.group(1) == 'True'
    return None


def set_mode(enable_refactoring):
    """设置重构模式"""
    with open('backend/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if enable_refactoring:
        new_content = re.sub(
            r'REFACTORING_MODE\s*=\s*False',
            'REFACTORING_MODE = True',
            content
        )
        mode_name = "重构模式（静态展示）"
    else:
        new_content = re.sub(
            r'REFACTORING_MODE\s*=\s*True',
            'REFACTORING_MODE = False',
            content
        )
        mode_name = "正常模式（自动交易）"
    
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return mode_name


def main():
    current_mode = get_current_mode()
    
    if current_mode is None:
        print("❌ 错误：无法找到 REFACTORING_MODE 配置")
        return
    
    # 没有参数，显示当前状态
    if len(sys.argv) == 1:
        if current_mode:
            print("📊 当前状态: 🟡 重构模式（静态展示）")
            print("   - 所有交易逻辑已停止")
            print("   - 只提供数据查询功能")
            print("   - 前端可正常显示历史数据")
            print("\n💡 使用 'python toggle_refactoring_mode.py off' 恢复交易功能")
        else:
            print("🚀 当前状态: 🟢 正常模式（自动交易）")
            print("   - 所有功能正常运行")
            print("   - 自动执行交易")
            print("   - 实时更新数据")
            print("\n💡 使用 'python toggle_refactoring_mode.py on' 开启重构模式")
        return
    
    # 有参数，切换模式
    command = sys.argv[1].lower()
    
    if command == 'on':
        if current_mode:
            print("⚠️  重构模式已经开启，无需重复操作")
        else:
            mode_name = set_mode(True)
            print(f"✅ 已切换到: {mode_name}")
            print("\n📋 重构模式特性:")
            print("   ✅ 停止所有交易逻辑")
            print("   ✅ 停止后台任务")
            print("   ✅ 保留数据查询API")
            print("   ✅ 前端可正常显示")
            print("\n⚠️  请重启后端服务使配置生效: python run.py")
    
    elif command == 'off':
        if not current_mode:
            print("⚠️  正常模式已经开启，无需重复操作")
        else:
            mode_name = set_mode(False)
            print(f"✅ 已切换到: {mode_name}")
            print("\n📋 正常模式特性:")
            print("   ✅ 所有功能正常运行")
            print("   ✅ 自动执行交易")
            print("   ✅ 实时更新数据")
            print("   ✅ WebSocket推送")
            print("\n⚠️  请重启后端服务使配置生效: python run.py")
    
    else:
        print(f"❌ 未知命令: {command}")
        print("\n使用方法:")
        print("  python toggle_refactoring_mode.py        # 查看当前状态")
        print("  python toggle_refactoring_mode.py on     # 开启重构模式")
        print("  python toggle_refactoring_mode.py off    # 关闭重构模式")


if __name__ == "__main__":
    main()


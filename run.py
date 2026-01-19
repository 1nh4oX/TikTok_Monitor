#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抖音热搜监控系统 - 启动脚本

Usage:
    python run.py
"""

import os
import sys
import traceback

def get_base_path():
    """获取基础路径，兼容 PyInstaller 打包"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# 设置工作目录为程序所在目录
os.chdir(get_base_path())

# 添加 backend 到路径
sys.path.insert(0, os.path.join(get_base_path(), 'backend'))


def pause_on_error():
    """在 Windows 下暂停，让用户看到错误信息"""
    if sys.platform == 'win32' and getattr(sys, 'frozen', False):
        print("\n" + "=" * 60)
        print("程序遇到错误，按回车键退出...")
        print("=" * 60)
        try:
            input()
        except:
            pass


def main():
    """主入口"""
    import webbrowser
    import threading
    
    # 延迟导入，确保路径设置正确后再导入
    from backend.app import app, create_app
    from backend.scheduler.jobs import start_scheduler
    from backend.config import FLASK_HOST, FLASK_PORT
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          🔥 抖音热搜监控系统 (Douyin Hot Monitor)         ║
    ╠══════════════════════════════════════════════════════════╣
    ║  启动中...                                                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # 初始化应用
    create_app()
    
    # 启动调度器
    start_scheduler()
    
    def open_browser():
        """延迟打开浏览器"""
        import time
        time.sleep(1.5)
        webbrowser.open(f'http://localhost:{FLASK_PORT}')
    
    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"""
    ✓ 服务已启动
    ✓ 访问地址: http://localhost:{FLASK_PORT}
    ✓ 热榜抓取: 每10分钟自动执行
    
    按 Ctrl+C 停止服务
    """)
    
    # 启动 Flask
    try:
        app.run(
            host=FLASK_HOST, 
            port=FLASK_PORT, 
            debug=False,  # 生产模式
            use_reloader=False  # 禁用重载，避免调度器重复启动
        )
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 程序启动失败！错误信息：")
        print("=" * 60)
        print(f"\n{type(e).__name__}: {e}\n")
        print("详细错误信息：")
        traceback.print_exc()
        pause_on_error()
        sys.exit(1)

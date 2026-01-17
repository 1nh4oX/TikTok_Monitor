#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抖音热搜监控系统 - 启动脚本

Usage:
    python run.py
"""

import os
import sys
import webbrowser
import threading

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from backend.app import app, create_app
from backend.scheduler.jobs import start_scheduler
from backend.config import FLASK_HOST, FLASK_PORT


def open_browser():
    """延迟打开浏览器"""
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{FLASK_PORT}')


def main():
    """主入口"""
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
    main()

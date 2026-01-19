# -*- coding: utf-8 -*-
"""
定时任务调度模块

使用 APScheduler 定时抓取抖音热榜数据。
支持动态调整抓取间隔。
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.unified_scraper import get_unified_scraper
from models.database import save_hot_list, init_database
from settings_manager import load_settings, save_record_snapshot, cleanup_old_records


# 全局调度器实例
scheduler = BackgroundScheduler()
_current_interval = 10


def scrape_job():
    """抓取任务（使用统一抓取器，自动在API和HTML间切换）"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始抓取热榜...")
    
    try:
        unified_scraper = get_unified_scraper()
        result = unified_scraper.fetch_hot_list()
        
        if result['success'] and result['data']:
            # 保存到数据库
            snapshot_id = save_hot_list(result['data'])
            
            # 保存 JSON 快照文件
            save_record_snapshot(result['data'], result['method'])
            
            print(f"[任务完成] 方法: {result['method'].upper()}, "
                  f"保存了 {len(result['data'])} 条热搜，快照ID: {snapshot_id}")
            
            # 打印统计信息
            stats = unified_scraper.get_stats()
            print(f"[统计] API成功率: {stats['api']['success_rate']:.1f}%, "
                  f"HTML成功率: {stats['html']['success_rate']:.1f}%")
            
            # 清理过期记录
            cleanup_old_records()
        else:
            error_msg = result.get('error', '未知错误')
            print(f"[任务警告] 抓取失败: {error_msg}")
            
    except Exception as e:
        print(f"[任务错误] {e}")


def start_scheduler():
    """启动调度器"""
    global _current_interval
    
    # 初始化数据库
    init_database()
    
    # 从配置加载间隔
    settings = load_settings()
    _current_interval = settings.get('scrape_interval_minutes', 10)
    
    # 添加定时任务
    scheduler.add_job(
        scrape_job,
        trigger=IntervalTrigger(minutes=_current_interval),
        id='douyin_scrape',
        name='抖音热榜抓取任务',
        replace_existing=True
    )
    
    # 启动时立即执行一次
    scheduler.add_job(
        scrape_job,
        id='douyin_scrape_initial',
        name='初始抓取任务',
        replace_existing=True
    )
    
    scheduler.start()
    print(f"[调度器] 已启动，抓取间隔: {_current_interval} 分钟")


def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("[调度器] 已停止")


def update_scheduler_interval(minutes: int):
    """动态更新抓取间隔"""
    global _current_interval
    
    if minutes < 1 or minutes > 60:
        print(f"[调度器] 无效间隔: {minutes}，保持当前设置")
        return False
    
    if minutes == _current_interval:
        return True
    
    try:
        scheduler.reschedule_job(
            'douyin_scrape',
            trigger=IntervalTrigger(minutes=minutes)
        )
        _current_interval = minutes
        print(f"[调度器] 间隔已更新为 {minutes} 分钟")
        return True
    except Exception as e:
        print(f"[调度器] 更新间隔失败: {e}")
        return False


def trigger_scrape_now():
    """立即触发一次抓取"""
    scrape_job()


def get_current_interval() -> int:
    """获取当前抓取间隔"""
    return _current_interval


if __name__ == '__main__':
    # 测试调度器
    start_scheduler()
    
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()


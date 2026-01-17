# -*- coding: utf-8 -*-
"""
设置管理模块

提供配置文件的读写和 API 接口。
"""

import os
import json
from typing import Dict, Any

# 配置文件路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
RECORDS_DIR = os.path.join(DATA_DIR, 'records')

# 默认配置
DEFAULT_SETTINGS = {
    "scrape_interval_minutes": 10,
    "max_history_days": 7,
    "auto_refresh_seconds": 60,
    "theme": "dark",
    "show_trending_list": True,
    "max_display_items": 50
}


def ensure_data_dirs():
    """确保数据目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RECORDS_DIR, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    """加载设置"""
    ensure_data_dirs()
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # 合并默认值（确保新字段有值）
                return {**DEFAULT_SETTINGS, **settings}
        except (json.JSONDecodeError, IOError):
            pass
    
    # 如果文件不存在或读取失败，创建默认配置
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """保存设置"""
    ensure_data_dirs()
    
    try:
        # 验证关键字段
        validated = {
            "scrape_interval_minutes": max(1, min(60, int(settings.get("scrape_interval_minutes", 10)))),
            "max_history_days": max(1, min(30, int(settings.get("max_history_days", 7)))),
            "auto_refresh_seconds": max(10, min(300, int(settings.get("auto_refresh_seconds", 60)))),
            "theme": settings.get("theme", "dark"),
            "show_trending_list": bool(settings.get("show_trending_list", True)),
            "max_display_items": max(10, min(100, int(settings.get("max_display_items", 50))))
        }
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(validated, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, ValueError) as e:
        print(f"[设置] 保存失败: {e}")
        return False


def get_scrape_interval() -> int:
    """获取抓取间隔（分钟）"""
    return load_settings().get("scrape_interval_minutes", 10)


def save_record_snapshot(data: list, method: str) -> str:
    """
    保存热榜快照到 JSON 文件
    
    Args:
        data: 热榜数据列表
        method: 抓取方法 (api/html/demo)
        
    Returns:
        保存的文件路径
    """
    from datetime import datetime
    
    ensure_data_dirs()
    
    now = datetime.now()
    date_dir = os.path.join(RECORDS_DIR, now.strftime('%Y-%m-%d'))
    os.makedirs(date_dir, exist_ok=True)
    
    filename = now.strftime('%H-%M') + '.json'
    filepath = os.path.join(date_dir, filename)
    
    record = {
        "timestamp": now.isoformat(),
        "method": method,
        "count": len(data),
        "data": data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        print(f"[记录] 保存快照到 {filepath}")
        return filepath
    except IOError as e:
        print(f"[记录] 保存失败: {e}")
        return ""


def get_record_dates() -> list:
    """获取所有有记录的日期"""
    ensure_data_dirs()
    
    dates = []
    if os.path.exists(RECORDS_DIR):
        for name in sorted(os.listdir(RECORDS_DIR), reverse=True):
            if os.path.isdir(os.path.join(RECORDS_DIR, name)):
                dates.append(name)
    return dates


def get_records_for_date(date: str) -> list:
    """获取某天的所有快照记录"""
    date_dir = os.path.join(RECORDS_DIR, date)
    records = []
    
    if os.path.exists(date_dir):
        for filename in sorted(os.listdir(date_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(date_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        record = json.load(f)
                        record['filename'] = filename
                        records.append(record)
                except (json.JSONDecodeError, IOError):
                    pass
    
    return records


def get_word_history(word: str, days: int = 7) -> list:
    """
    获取某个热搜词的历史数据
    
    Args:
        word: 热搜词
        days: 查询最近几天
        
    Returns:
        历史记录列表 [{timestamp, position, hot_value}, ...]
    """
    from datetime import datetime, timedelta
    
    history = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        records = get_records_for_date(date)
        
        for record in records:
            for item in record.get('data', []):
                if item.get('word') == word:
                    history.append({
                        'timestamp': record.get('timestamp'),
                        'position': item.get('position', 0),
                        'hot_value': item.get('hot_value', 0)
                    })
                    break
    
    return sorted(history, key=lambda x: x['timestamp'])

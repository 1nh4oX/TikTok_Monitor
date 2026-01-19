# -*- coding: utf-8 -*-
"""
数据库模型模块

使用 SQLite 存储热榜历史数据。
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH, DATA_DIR


# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 热搜快照表 - 记录每次抓取
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hot_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_count INTEGER DEFAULT 0
            )
        ''')
        
        # 热搜条目表 - 记录每条热搜
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hot_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                word TEXT NOT NULL,
                hot_value INTEGER DEFAULT 0,
                topic_id TEXT,
                tag TEXT,
                url TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES hot_snapshots(id)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hot_items_word ON hot_items(word)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hot_items_snapshot ON hot_items(snapshot_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_snapshots_time ON hot_snapshots(captured_at)
        ''')
        
        conn.commit()
        print("[数据库] 初始化完成")


def save_hot_list(items: List[Dict]) -> int:
    """
    保存热榜数据到数据库
    
    Args:
        items: 热榜数据列表
        
    Returns:
        快照ID
    """
    if not items:
        return -1
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 创建快照记录
        cursor.execute('''
            INSERT INTO hot_snapshots (captured_at, total_count)
            VALUES (?, ?)
        ''', (datetime.now(), len(items)))
        
        snapshot_id = cursor.lastrowid
        
        # 批量插入热搜条目
        for item in items:
            cursor.execute('''
                INSERT INTO hot_items (snapshot_id, position, word, hot_value, topic_id, tag, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                item.get('position', 0),
                item.get('word', ''),
                item.get('hot_value', 0),
                item.get('topic_id', ''),
                item.get('tag', ''),
                item.get('url', '')
            ))
        
        conn.commit()
        print(f"[数据库] 保存快照 #{snapshot_id}，共 {len(items)} 条记录")
        return snapshot_id


def get_latest_hot_list() -> List[Dict]:
    """获取最新的热榜数据"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 获取最新快照
        cursor.execute('''
            SELECT id, captured_at FROM hot_snapshots
            ORDER BY captured_at DESC
            LIMIT 1
        ''')
        snapshot = cursor.fetchone()
        
        if not snapshot:
            return []
        
        # 获取该快照的所有热搜
        cursor.execute('''
            SELECT position, word, hot_value, topic_id, tag, url
            FROM hot_items
            WHERE snapshot_id = ?
            ORDER BY position
        ''', (snapshot['id'],))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'position': row['position'],
                'word': row['word'],
                'hot_value': row['hot_value'],
                'topic_id': row['topic_id'],
                'tag': row['tag'],
                'url': row['url']
            })
        
        return items


def get_word_trend(word: str, hours: int = 24) -> List[Dict]:
    """
    获取某个热搜词的热度趋势
    
    Args:
        word: 热搜词
        hours: 查询的小时数
        
    Returns:
        趋势数据列表 [{time, position, hot_value}, ...]
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.captured_at, i.position, i.hot_value
            FROM hot_items i
            JOIN hot_snapshots s ON i.snapshot_id = s.id
            WHERE i.word = ?
              AND s.captured_at >= datetime('now', '-' || ? || ' hours')
            ORDER BY s.captured_at
        ''', (word, hours))
        
        trend = []
        for row in cursor.fetchall():
            trend.append({
                'time': row['captured_at'],
                'position': row['position'],
                'hot_value': row['hot_value']
            })
        
        return trend


def get_rising_topics(limit: int = 10) -> List[Dict]:
    """
    获取上升最快的热点话题
    
    优先显示排名上升的词条，如果没有则显示热度值增长最多的词条
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. 获取最新的两个快照
        cursor.execute('''
            SELECT id, captured_at FROM hot_snapshots
            ORDER BY captured_at DESC
            LIMIT 2
        ''')
        snapshots = cursor.fetchall()
        
        if len(snapshots) < 2:
            # 快照不足，显示当前热榜前10
            cursor.execute('''
                SELECT word, position, hot_value, url FROM hot_items
                WHERE snapshot_id = (SELECT id FROM hot_snapshots ORDER BY captured_at DESC LIMIT 1)
                ORDER BY position
                LIMIT ?
            ''', (limit,))
            result = []
            for row in cursor.fetchall():
                result.append({
                    'word': row['word'],
                    'current_position': row['position'],
                    'hot_value': row['hot_value'],
                    'previous_position': None,
                    'rank_change': 'TOP',
                    'url': row['url']
                })
            return result
        
        latest_id = snapshots[0]['id']
        prev_id = snapshots[1]['id']
        
        # 2. 先尝试找排名上升的
        cursor.execute('''
            SELECT 
                curr.word,
                curr.position as curr_pos,
                curr.hot_value as curr_value,
                prev.position as prev_pos,
                prev.hot_value as prev_value,
                (prev.position - curr.position) as rank_change,
                curr.url
            FROM hot_items curr
            LEFT JOIN hot_items prev ON curr.word = prev.word AND prev.snapshot_id = ?
            WHERE curr.snapshot_id = ?
              AND (prev.position IS NULL OR prev.position > curr.position)
            ORDER BY 
                CASE WHEN prev.position IS NULL THEN 1000 ELSE prev.position - curr.position END DESC
            LIMIT ?
        ''', (prev_id, latest_id, limit))
        
        rising = []
        for row in cursor.fetchall():
            rising.append({
                'word': row['word'],
                'current_position': row['curr_pos'],
                'hot_value': row['curr_value'],
                'previous_position': row['prev_pos'],
                'rank_change': row['rank_change'] if row['rank_change'] else 'NEW',
                'url': row['url']
            })
        
        # 3. 如果没有排名上升的，显示热度增长最多的
        if len(rising) == 0:
            cursor.execute('''
                SELECT 
                    curr.word,
                    curr.position as curr_pos,
                    curr.hot_value as curr_value,
                    prev.hot_value as prev_value,
                    (curr.hot_value - COALESCE(prev.hot_value, 0)) as hot_change,
                    curr.url
                FROM hot_items curr
                LEFT JOIN hot_items prev ON curr.word = prev.word AND prev.snapshot_id = ?
                WHERE curr.snapshot_id = ?
                ORDER BY hot_change DESC
                LIMIT ?
            ''', (prev_id, latest_id, limit))
            
            for row in cursor.fetchall():
                hot_change = row['hot_change'] or 0
                # 只显示热度有正增长的
                if hot_change > 0:
                    rising.append({
                        'word': row['word'],
                        'current_position': row['curr_pos'],
                        'hot_value': row['curr_value'],
                        'previous_position': row['curr_pos'],  # 排名相同
                        'rank_change': f'+{hot_change // 10000}w' if hot_change >= 10000 else f'+{hot_change}',
                        'url': row['url']
                    })
        
        return rising


def get_snapshot_history(limit: int = 50) -> List[Dict]:
    """获取快照历史"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, captured_at, total_count
            FROM hot_snapshots
            ORDER BY captured_at DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]


if __name__ == '__main__':
    # 测试数据库
    init_database()
    print("数据库初始化成功")
    
    # 插入测试数据
    test_data = [
        {'position': 1, 'word': '测试热搜1', 'hot_value': 1000000, 'topic_id': '123', 'tag': '热', 'url': ''},
        {'position': 2, 'word': '测试热搜2', 'hot_value': 900000, 'topic_id': '124', 'tag': '新', 'url': ''},
    ]
    save_hot_list(test_data)
    
    # 读取数据
    latest = get_latest_hot_list()
    print(f"最新热榜: {latest}")

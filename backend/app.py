# -*- coding: utf-8 -*-
"""
Flask API 服务

提供热榜数据的 RESTful API 接口。
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, BASE_DIR
from models.database import (
    get_latest_hot_list,
    get_word_trend,
    get_rising_topics,
    get_snapshot_history,
    init_database
)
from scraper.unified_scraper import get_unified_scraper
from scheduler.jobs import start_scheduler, trigger_scrape_now, update_scheduler_interval
from settings_manager import (
    load_settings, save_settings, 
    get_record_dates, get_records_for_date, get_word_history
)


# 创建 Flask 应用
app = Flask(__name__, 
            static_folder=os.path.join(BASE_DIR, 'frontend'),
            static_url_path='')
CORS(app)


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """主页"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """静态文件"""
    return send_from_directory(app.static_folder, path)


# ==================== API 路由 ====================

@app.route('/api/hot')
def api_hot_list():
    """
    获取最新热榜
    
    返回:
        {
            "success": true,
            "data": [
                {"position": 1, "word": "...", "hot_value": 1234567, ...},
                ...
            ],
            "count": 50
        }
    """
    try:
        hot_list = get_latest_hot_list()
        return jsonify({
            'success': True,
            'data': hot_list,
            'count': len(hot_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/trend/<word>')
def api_word_trend(word):
    """
    获取某个热搜词的趋势
    
    参数:
        word: 热搜词
        hours: 查询的小时数 (默认24)
    
    返回:
        {
            "success": true,
            "word": "...",
            "trend": [
                {"time": "2024-01-14 10:00:00", "position": 1, "hot_value": 1234567},
                ...
            ]
        }
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        trend = get_word_trend(word, hours)
        return jsonify({
            'success': True,
            'word': word,
            'trend': trend,
            'count': len(trend)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rising')
def api_rising_topics():
    """
    获取上升热点
    
    参数:
        limit: 返回数量 (默认10)
    
    返回:
        {
            "success": true,
            "data": [
                {"word": "...", "current_position": 1, "rank_change": 5, ...},
                ...
            ]
        }
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        rising = get_rising_topics(limit)
        return jsonify({
            'success': True,
            'data': rising,
            'count': len(rising)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/snapshots')
def api_snapshots():
    """
    获取快照历史
    
    参数:
        limit: 返回数量 (默认50)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        history = get_snapshot_history(limit)
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """
    手动触发抓取
    """
    try:
        trigger_scrape_now()
        return jsonify({
            'success': True,
            'message': '抓取任务已触发'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status')
def api_status():
    """
    获取系统状态（包含抓取器统计）
    """
    try:
        history = get_snapshot_history(1)
        last_update = history[0]['captured_at'] if history else None
        
        # 获取抓取器统计
        unified_scraper = get_unified_scraper()
        scraper_stats = unified_scraper.get_stats()
        
        settings = load_settings()
        return jsonify({
            'success': True,
            'status': 'running',
            'last_update': last_update,
            'total_snapshots': len(get_snapshot_history(1000)),
            'scraper_stats': scraper_stats,
            'settings': settings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """获取当前设置"""
    try:
        settings = load_settings()
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """更新设置"""
    try:
        new_settings = request.get_json()
        if not new_settings:
            return jsonify({'success': False, 'error': '无效的设置数据'}), 400
        
        if save_settings(new_settings):
            # 更新调度器间隔
            interval = new_settings.get('scrape_interval_minutes', 10)
            update_scheduler_interval(interval)
            
            return jsonify({
                'success': True,
                'message': '设置已更新',
                'settings': load_settings()
            })
        return jsonify({'success': False, 'error': '保存失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/records')
def api_get_records():
    """获取历史记录日期列表"""
    try:
        dates = get_record_dates()
        return jsonify({
            'success': True,
            'dates': dates
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/records/<date>')
def api_get_records_for_date(date):
    """获取某天的所有快照"""
    try:
        records = get_records_for_date(date)
        return jsonify({
            'success': True,
            'date': date,
            'records': records,
            'count': len(records)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/history/<word>')
def api_word_history(word):
    """获取热搜词的历史趋势"""
    try:
        days = request.args.get('days', 7, type=int)
        history = get_word_history(word, days)
        return jsonify({
            'success': True,
            'word': word,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def create_app():
    """创建并配置应用"""
    init_database()
    return app


if __name__ == '__main__':
    init_database()
    start_scheduler()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

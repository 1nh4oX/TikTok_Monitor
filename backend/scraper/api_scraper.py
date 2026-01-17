# -*- coding: utf-8 -*-
"""
抖音热榜 API 抓取模块

直接调用抖音内部 API 获取热搜数据（主方案）。
"""

import time
import random
import requests
from typing import List, Dict, Optional
from urllib.parse import urlencode

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import HEADERS, COOKIE, MSTOKEN, WEBID


class DouyinAPIScraperError(Exception):
    """API抓取异常"""
    pass


class DouyinAPIScraper:
    """抖音热榜 API 抓取器（主方案）"""
    
    # API 端点
    HOT_SEARCH_API = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
    CHANNEL_HOTSPOT_API = "https://www.douyin.com/aweme/v1/web/channel/hotspot"
    
    # 基础请求参数
    BASE_PARAMS = {
        'device_platform': 'webapp',
        'aid': '6383',
        'channel': 'channel_pc_web',
        'version_code': '170400',
        'version_name': '17.4.0',
        'cookie_enabled': 'true',
        'screen_width': '1920',
        'screen_height': '1080',
        'browser_language': 'zh-CN',
        'browser_platform': 'MacIntel',
        'browser_name': 'Chrome',
        'browser_version': '120.0.0.0',
        'browser_online': 'true',
        'engine_name': 'Blink',
        'engine_version': '120.0.0.0',
        'os_name': 'Mac OS',
        'os_version': '10.15.7',
        'cpu_core_num': '8',
        'device_memory': '8',
        'platform': 'PC',
        'downlink': '10',
        'effective_type': '4g',
        'round_trip_time': '50',
    }
    
    def __init__(self, cookie: str = "", ms_token: str = "", webid: str = ""):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cookie = cookie
        self.ms_token = ms_token
        self.webid = webid
        
        if cookie:
            self.session.headers['Cookie'] = cookie
    
    def _build_params(self, extra_params: dict = None) -> dict:
        """构建请求参数"""
        params = self.BASE_PARAMS.copy()
        
        if self.webid:
            params['webid'] = self.webid
        if self.ms_token:
            params['msToken'] = self.ms_token
            
        if extra_params:
            params.update(extra_params)
            
        return params
    
    def fetch_hot_search_list(self) -> List[Dict]:
        """
        获取热搜榜列表
        
        Returns:
            热搜数据列表，包含:
            - position: 排名
            - word: 热搜词
            - hot_value: 热度值
            - view_count: 浏览量
            - video_count: 视频数
            - sentence_id: 话题ID
            - tag: 标签 (热/新等)
            - cover_url: 封面图URL
        """
        try:
            time.sleep(random.uniform(0.3, 1.0))
            
            params = self._build_params({
                'detail_list': '1',
                'source': '6',
                'pc_client_type': '1',
            })
            
            response = self.session.get(
                self.HOT_SEARCH_API,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status_code') != 0:
                raise DouyinAPIScraperError(f"API返回错误: status_code={data.get('status_code')}")
            
            return self._parse_hot_search_response(data)
            
        except requests.RequestException as e:
            raise DouyinAPIScraperError(f"请求失败: {e}")
        except Exception as e:
            raise DouyinAPIScraperError(f"解析失败: {e}")
    
    def _parse_hot_search_response(self, data: dict) -> List[Dict]:
        """解析热搜API响应"""
        hot_list = []
        
        word_list = data.get('data', {}).get('word_list', [])
        
        for idx, item in enumerate(word_list):
            position = item.get('position', idx + 1)
            
            # 解析标签
            label = item.get('label', 0)
            tag = self._parse_label(label)
            
            # 获取封面图
            cover_url = ""
            word_cover = item.get('word_cover', {})
            if word_cover and word_cover.get('url_list'):
                cover_url = word_cover['url_list'][0]
            
            hot_list.append({
                'position': position,
                'word': item.get('word', ''),
                'hot_value': item.get('hot_value', 0),
                'view_count': item.get('view_count', 0),
                'video_count': item.get('video_count', 0),
                'sentence_id': item.get('sentence_id', ''),
                'tag': tag,
                'cover_url': cover_url,
                'url': f"https://www.douyin.com/hot/{item.get('sentence_id', '')}"
            })
        
        # 同时添加 trending_list（实时上升热点）
        trending_list = data.get('data', {}).get('trending_list', [])
        for item in trending_list:
            cover_url = ""
            word_cover = item.get('word_cover', {})
            if word_cover and word_cover.get('url_list'):
                cover_url = word_cover['url_list'][0]
                
            hot_list.append({
                'position': 0,  # 实时上升无固定排名
                'word': item.get('word', ''),
                'hot_value': item.get('hot_value', 0),
                'view_count': 0,
                'video_count': item.get('video_count', 0),
                'sentence_id': item.get('sentence_id', ''),
                'tag': '上升',
                'cover_url': cover_url,
                'url': f"https://www.douyin.com/hot/{item.get('sentence_id', '')}"
            })
        
        print(f"[API] 成功获取 {len(hot_list)} 条热搜")
        return hot_list
    
    def _parse_label(self, label: int) -> str:
        """解析标签类型"""
        label_map = {
            0: '',
            1: '新',
            3: '热',
            8: '独家',
            16: '辟谣',
            17: '热舞',
        }
        return label_map.get(label, '')
    
    def fetch_channel_hotspot(self, channel_id: int = 99, count: int = 10) -> List[Dict]:
        """
        获取频道热点视频
        
        Args:
            channel_id: 频道ID (99为推荐)
            count: 获取数量
            
        Returns:
            视频列表，包含作者、统计数据等
        """
        try:
            time.sleep(random.uniform(0.3, 1.0))
            
            params = self._build_params({
                'tag_id': '',
                'count': str(count),
                'Seo-Flag': '0',
                'channel_id': str(channel_id),
                'pc_client_type': '1',
                'support_h265': '1',
                'support_dash': '0',
            })
            
            response = self.session.get(
                self.CHANNEL_HOTSPOT_API,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_channel_response(data)
            
        except requests.RequestException as e:
            raise DouyinAPIScraperError(f"请求失败: {e}")
        except Exception as e:
            raise DouyinAPIScraperError(f"解析失败: {e}")
    
    def _parse_channel_response(self, data: dict) -> List[Dict]:
        """解析频道热点响应"""
        videos = []
        
        aweme_list = data.get('aweme_list', [])
        
        for item in aweme_list:
            author = item.get('author', {})
            statistics = item.get('statistics', {})
            video = item.get('video', {})
            
            # 获取封面
            cover_url = ""
            cover = video.get('cover', {})
            if cover and cover.get('url_list'):
                cover_url = cover['url_list'][0]
            
            videos.append({
                'aweme_id': item.get('aweme_id', ''),
                'desc': item.get('desc', ''),
                'create_time': item.get('create_time', 0),
                'duration': item.get('duration', 0),
                'author': {
                    'uid': author.get('uid', ''),
                    'nickname': author.get('nickname', ''),
                    'sec_uid': author.get('sec_uid', ''),
                },
                'statistics': {
                    'digg_count': statistics.get('digg_count', 0),
                    'comment_count': statistics.get('comment_count', 0),
                    'share_count': statistics.get('share_count', 0),
                    'collect_count': statistics.get('collect_count', 0),
                },
                'cover_url': cover_url,
                'url': f"https://www.douyin.com/video/{item.get('aweme_id', '')}"
            })
        
        print(f"[API] 成功获取 {len(videos)} 个热点视频")
        return videos
    
    def update_credentials(self, cookie: str = None, ms_token: str = None, webid: str = None):
        """更新凭证"""
        if cookie:
            self.cookie = cookie
            self.session.headers['Cookie'] = cookie
        if ms_token:
            self.ms_token = ms_token
        if webid:
            self.webid = webid


# 单例
_api_scraper_instance = None

def get_api_scraper() -> DouyinAPIScraper:
    """获取API抓取器单例（自动从配置文件加载凭证）"""
    global _api_scraper_instance
    if _api_scraper_instance is None:
        _api_scraper_instance = DouyinAPIScraper(
            cookie=COOKIE,
            ms_token=MSTOKEN,
            webid=WEBID
        )
    return _api_scraper_instance


if __name__ == '__main__':
    # 测试
    scraper = DouyinAPIScraper()
    try:
        data = scraper.fetch_hot_search_list()
        for item in data[:10]:
            print(f"#{item['position']} [{item['tag']}] {item['word']} - {item['hot_value']:,}")
    except DouyinAPIScraperError as e:
        print(f"API抓取失败: {e}")

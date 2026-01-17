# -*- coding: utf-8 -*-
"""
演示数据加载模块

从 mono_finding 目录加载已抓取的 JSON 样本数据用于演示。
"""

import json
import os
from typing import List, Dict


class DemoDataLoader:
    """演示数据加载器"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # 自动定位 mono_finding 目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            data_dir = os.path.join(project_root, 'mono_finding')
        
        self.data_dir = data_dir
        self._hot_search_data = None
        self._channel_data = None
    
    def load_hot_search_list(self) -> List[Dict]:
        """
        加载热搜榜样本数据
        
        从 b.json 或 d.json 加载（热搜榜API响应）
        """
        if self._hot_search_data:
            return self._hot_search_data
        
        # 优先加载 b.json
        for filename in ['b.json', 'd.json']:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    self._hot_search_data = self._parse_hot_search(data)
                    print(f"[Demo] 从 {filename} 加载了 {len(self._hot_search_data)} 条热搜")
                    return self._hot_search_data
                    
                except Exception as e:
                    print(f"[Demo] 加载 {filename} 失败: {e}")
                    continue
        
        return []
    
    def _parse_hot_search(self, data: dict) -> List[Dict]:
        """解析热搜API响应"""
        hot_list = []
        
        # 解析 word_list
        word_list = data.get('data', {}).get('word_list', [])
        for item in word_list:
            position = item.get('position', 0)
            
            label = item.get('label', 0)
            tag = self._parse_label(label)
            
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
        
        # 解析 trending_list（实时上升）
        trending_list = data.get('data', {}).get('trending_list', [])
        for item in trending_list:
            cover_url = ""
            word_cover = item.get('word_cover', {})
            if word_cover and word_cover.get('url_list'):
                cover_url = word_cover['url_list'][0]
            
            hot_list.append({
                'position': 0,
                'word': item.get('word', ''),
                'hot_value': item.get('hot_value', 0),
                'view_count': 0,
                'video_count': item.get('video_count', 0),
                'sentence_id': item.get('sentence_id', ''),
                'tag': '上升',
                'cover_url': cover_url,
                'url': f"https://www.douyin.com/hot/{item.get('sentence_id', '')}"
            })
        
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
    
    def load_channel_hotspot(self) -> List[Dict]:
        """
        加载频道热点样本数据
        
        从 a.json, c.json 或 e.json 加载
        """
        if self._channel_data:
            return self._channel_data
        
        for filename in ['a.json', 'c.json', 'e.json']:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    self._channel_data = self._parse_channel(data)
                    print(f"[Demo] 从 {filename} 加载了 {len(self._channel_data)} 个热点视频")
                    return self._channel_data
                    
                except Exception as e:
                    print(f"[Demo] 加载 {filename} 失败: {e}")
                    continue
        
        return []
    
    def _parse_channel(self, data: dict) -> List[Dict]:
        """解析频道热点响应"""
        videos = []
        
        aweme_list = data.get('aweme_list', [])
        for item in aweme_list:
            author = item.get('author', {})
            statistics = item.get('statistics', {})
            video = item.get('video', {})
            
            cover_url = ""
            cover = video.get('cover', {})
            if cover and cover.get('url_list'):
                cover_url = cover['url_list'][0]
            
            avatar_url = ""
            avatar = author.get('avatar_thumb', {})
            if avatar and avatar.get('url_list'):
                avatar_url = avatar['url_list'][0]
            
            videos.append({
                'aweme_id': item.get('aweme_id', ''),
                'desc': item.get('desc', ''),
                'caption': item.get('caption', ''),
                'create_time': item.get('create_time', 0),
                'duration': item.get('duration', 0),
                'author': {
                    'uid': author.get('uid', ''),
                    'nickname': author.get('nickname', ''),
                    'sec_uid': author.get('sec_uid', ''),
                    'avatar_url': avatar_url,
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
        
        return videos


# 单例
_demo_loader_instance = None

def get_demo_loader() -> DemoDataLoader:
    """获取演示数据加载器单例"""
    global _demo_loader_instance
    if _demo_loader_instance is None:
        _demo_loader_instance = DemoDataLoader()
    return _demo_loader_instance


if __name__ == '__main__':
    loader = DemoDataLoader()
    
    print("=== 加载热搜榜数据 ===")
    hot_list = loader.load_hot_search_list()
    for item in hot_list[:10]:
        print(f"#{item['position']} [{item['tag']}] {item['word']} - {item['hot_value']:,}")
    
    print("\n=== 加载频道热点数据 ===")
    videos = loader.load_channel_hotspot()
    for v in videos[:5]:
        print(f"@{v['author']['nickname']}: {v['desc'][:30]}...")
        print(f"  👍{v['statistics']['digg_count']:,} 💬{v['statistics']['comment_count']:,}")

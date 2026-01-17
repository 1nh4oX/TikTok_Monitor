# -*- coding: utf-8 -*-
"""
抖音热榜 HTML 解析模块

基于 BeautifulSoup 解析抖音热搜页面，提取热榜数据。
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from typing import List, Dict, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DOUYIN_HOT_URL, HEADERS


class DouyinScraper:
    """抖音热榜抓取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def _parse_hot_value(self, value_str: str) -> int:
        """
        解析热度值字符串为整数
        
        例如:
        - "1206.9万" -> 12069000
        - "925.1万" -> 9251000
        - "1.2亿" -> 120000000
        """
        if not value_str:
            return 0
        
        value_str = value_str.strip()
        
        try:
            if '亿' in value_str:
                num = float(value_str.replace('亿', ''))
                return int(num * 100000000)
            elif '万' in value_str:
                num = float(value_str.replace('万', ''))
                return int(num * 10000)
            else:
                return int(float(value_str))
        except ValueError:
            return 0
    
    def _extract_topic_id(self, href: str) -> str:
        """从链接中提取话题ID"""
        # /hot/2366771/韩国检方要求判处尹锡悦死刑
        match = re.search(r'/hot/(\d+)/', href)
        return match.group(1) if match else ""
    
    def _extract_title_from_href(self, href: str) -> str:
        """从 URL 中提取标题（备用方案）"""
        # /hot/2366771/%E9%9F%A9%E5%9B%BD... -> 韩国检方要求判处尹锡悦死刑
        parts = href.split('/')
        if len(parts) >= 4:
            return unquote(parts[3])
        return ""
    
    def fetch_hot_list(self) -> List[Dict]:
        """
        抓取抖音热榜数据
        
        Returns:
            热榜数据列表，每个元素包含:
            - position: 排名
            - word: 热搜词
            - hot_value: 热度值
            - topic_id: 话题ID
            - tag: 标签(热/新/独家等)
        """
        try:
            # 添加随机延迟，模拟人工访问
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(DOUYIN_HOT_URL, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 查找热榜列表容器
            hot_list_container = soup.find('ul', class_='WxZ6fnC5')
            if not hot_list_container:
                print("[警告] 未找到热榜容器，页面结构可能已变化")
                return []
            
            # 查找所有热榜条目
            items = hot_list_container.find_all('li', class_='NINGm7vw')
            
            hot_list = []
            for idx, item in enumerate(items):
                try:
                    data = self._parse_item(item, idx + 1)
                    if data:
                        hot_list.append(data)
                except Exception as e:
                    print(f"[警告] 解析第 {idx + 1} 条失败: {e}")
                    continue
            
            print(f"[成功] 抓取到 {len(hot_list)} 条热搜")
            return hot_list
            
        except requests.RequestException as e:
            print(f"[错误] 请求失败: {e}")
            return []
        except Exception as e:
            print(f"[错误] 解析失败: {e}")
            return []
    
    def _parse_item(self, item, default_position: int) -> Optional[Dict]:
        """解析单个热榜条目"""
        
        # 提取标题和链接
        link = item.find('a', class_='uz1VJwFY')
        if not link:
            return None
        
        href = link.get('href', '')
        title_tag = link.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else self._extract_title_from_href(href)
        
        if not title:
            return None
        
        # 提取话题ID
        topic_id = self._extract_topic_id(href)
        
        # 提取热度值
        hot_value = 0
        hot_span = item.find('span', class_='WreZoKD3')
        if hot_span:
            hot_value = self._parse_hot_value(hot_span.get_text(strip=True))
        
        # 提取标签（热/新/独家等）
        tag = ""
        tag_imgs = item.find_all('img', alt='')
        for img in tag_imgs:
            src = img.get('src', '')
            if 'hot_hot' in src:
                tag = "热"
            elif 'hot_new' in src:
                tag = "新"
            elif 'hot_exclusive' in src:
                tag = "独家"
            elif 'hot_first' in src:
                tag = "首发"
            elif 'piyao' in src:
                tag = "辟谣"
            elif 'up.svg' in src:
                tag = "上升"
        
        # 提取排名（从图标或数字）
        position = default_position
        rank_div = item.find('div', class_='CjXX0j55')
        if rank_div:
            rank_text = rank_div.get_text(strip=True)
            if rank_text.isdigit():
                position = int(rank_text)
        
        return {
            'position': position,
            'word': title,
            'hot_value': hot_value,
            'topic_id': topic_id,
            'tag': tag,
            'url': f"https://www.douyin.com{href}" if href.startswith('/') else href
        }
    
    def update_cookie(self, cookie: str):
        """更新 Cookie"""
        self.session.headers['Cookie'] = cookie


# 单例模式
_scraper_instance = None

def get_scraper() -> DouyinScraper:
    """获取抓取器单例"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = DouyinScraper()
    return _scraper_instance


if __name__ == '__main__':
    # 测试抓取
    scraper = DouyinScraper()
    data = scraper.fetch_hot_list()
    
    for item in data[:10]:
        print(f"#{item['position']} [{item['tag']}] {item['word']} - {item['hot_value']:,}")

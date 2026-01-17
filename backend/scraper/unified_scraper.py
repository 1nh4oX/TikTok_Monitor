# -*- coding: utf-8 -*-
"""
统一热榜抓取器

结合 API 抓取、HTML 解析和演示数据的三重策略：
- 主方案：直接调用抖音 API（更稳定、数据更丰富）
- 备用方案：HTML 页面解析（API 受限时自动切换）
- 演示模式：加载本地样本数据（用于开发/演示）
"""

import time
from typing import List, Dict, Optional
from enum import Enum

from .api_scraper import DouyinAPIScraper, DouyinAPIScraperError, get_api_scraper
from .douyin_api import DouyinScraper, get_scraper as get_html_scraper
from .demo_loader import DemoDataLoader, get_demo_loader


class ScraperMethod(Enum):
    """抓取方式"""
    API = "api"
    HTML = "html"
    DEMO = "demo"  # 演示数据
    AUTO = "auto"  # 自动选择（API → HTML → Demo）


class UnifiedScraper:
    """
    统一热榜抓取器
    
    自动在 API、HTML 解析和演示数据之间切换，确保数据获取的稳定性。
    """
    
    def __init__(self, preferred_method: ScraperMethod = ScraperMethod.AUTO, 
                 enable_demo_fallback: bool = True):
        self.api_scraper = get_api_scraper()
        self.html_scraper = get_html_scraper()
        self.demo_loader = get_demo_loader()
        self.preferred_method = preferred_method
        self.enable_demo_fallback = enable_demo_fallback
        
        # 统计信息
        self.api_success_count = 0
        self.api_fail_count = 0
        self.html_success_count = 0
        self.html_fail_count = 0
        self.demo_success_count = 0
        
        # 连续失败计数
        self._consecutive_api_fails = 0
        self._consecutive_html_fails = 0
        self._max_consecutive_fails = 3
        
        self._last_method_used: Optional[ScraperMethod] = None
    
    def fetch_hot_list(self, method: ScraperMethod = None) -> Dict:
        """
        获取热榜数据
        
        Args:
            method: 指定抓取方式，None则使用默认策略
            
        Returns:
            {
                'success': bool,
                'data': List[Dict],
                'method': str,  # 'api', 'html', 或 'demo'
                'error': str (可选)
            }
        """
        method = method or self.preferred_method
        
        if method == ScraperMethod.AUTO:
            return self._fetch_with_auto_fallback()
        elif method == ScraperMethod.API:
            return self._fetch_via_api()
        elif method == ScraperMethod.HTML:
            return self._fetch_via_html()
        else:  # DEMO
            return self._fetch_via_demo()
    
    def _fetch_with_auto_fallback(self) -> Dict:
        """自动模式：API → HTML → Demo"""
        
        # 如果 API 连续失败太多次，先尝试 HTML
        if self._consecutive_api_fails >= self._max_consecutive_fails:
            print(f"[Unified] API 连续失败 {self._consecutive_api_fails} 次，优先尝试 HTML")
            result = self._fetch_via_html()
            if result['success']:
                self._consecutive_api_fails = 0
                return result
        else:
            # 正常流程：先试 API
            result = self._fetch_via_api()
            if result['success']:
                return result
        
            # API 失败，切换 HTML
            print("[Unified] API 失败，切换到 HTML 解析...")
            result = self._fetch_via_html()
            if result['success']:
                return result
        
        # API 和 HTML 都失败，尝试演示数据
        if self.enable_demo_fallback:
            print("[Unified] HTML 也失败，切换到演示数据...")
            return self._fetch_via_demo()
        
        return result  # 返回最后一次失败结果
    
    def _fetch_via_api(self) -> Dict:
        """通过 API 获取"""
        try:
            data = self.api_scraper.fetch_hot_search_list()
            
            self.api_success_count += 1
            self._consecutive_api_fails = 0
            self._last_method_used = ScraperMethod.API
            
            return {
                'success': True,
                'data': data,
                'method': 'api',
                'count': len(data)
            }
            
        except DouyinAPIScraperError as e:
            self.api_fail_count += 1
            self._consecutive_api_fails += 1
            
            return {
                'success': False,
                'data': [],
                'method': 'api',
                'error': str(e)
            }
        except Exception as e:
            self.api_fail_count += 1
            self._consecutive_api_fails += 1
            
            return {
                'success': False,
                'data': [],
                'method': 'api',
                'error': f"未知错误: {e}"
            }
    
    def _fetch_via_html(self) -> Dict:
        """通过 HTML 解析获取"""
        try:
            data = self.html_scraper.fetch_hot_list()
            
            if not data:
                raise Exception("HTML解析返回空数据")
            
            self.html_success_count += 1
            self._consecutive_html_fails = 0
            self._last_method_used = ScraperMethod.HTML
            
            return {
                'success': True,
                'data': data,
                'method': 'html',
                'count': len(data)
            }
            
        except Exception as e:
            self.html_fail_count += 1
            self._consecutive_html_fails += 1
            
            return {
                'success': False,
                'data': [],
                'method': 'html',
                'error': str(e)
            }
    
    def _fetch_via_demo(self) -> Dict:
        """加载演示数据"""
        try:
            data = self.demo_loader.load_hot_search_list()
            
            if not data:
                raise Exception("演示数据为空")
            
            self.demo_success_count += 1
            self._last_method_used = ScraperMethod.DEMO
            
            return {
                'success': True,
                'data': data,
                'method': 'demo',
                'count': len(data),
                'note': '使用本地样本数据（非实时）'
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'method': 'demo',
                'error': str(e)
            }
    
    def fetch_channel_videos(self) -> Dict:
        """获取频道热点视频（仅支持演示模式）"""
        try:
            data = self.demo_loader.load_channel_hotspot()
            
            if not data:
                raise Exception("无频道视频数据")
            
            return {
                'success': True,
                'data': data,
                'method': 'demo',
                'count': len(data)
            }
        except Exception as e:
            return {
                'success': False,
                'data': [],
                'method': 'demo',
                'error': str(e)
            }
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_api = self.api_success_count + self.api_fail_count
        total_html = self.html_success_count + self.html_fail_count
        
        return {
            'api': {
                'success': self.api_success_count,
                'fail': self.api_fail_count,
                'total': total_api,
                'success_rate': (self.api_success_count / total_api * 100) if total_api > 0 else 0
            },
            'html': {
                'success': self.html_success_count,
                'fail': self.html_fail_count,
                'total': total_html,
                'success_rate': (self.html_success_count / total_html * 100) if total_html > 0 else 0
            },
            'demo': {
                'success': self.demo_success_count,
            },
            'last_method': self._last_method_used.value if self._last_method_used else None,
            'demo_fallback_enabled': self.enable_demo_fallback
        }
    
    def update_api_credentials(self, cookie: str = None, ms_token: str = None, webid: str = None):
        """更新 API 凭证"""
        self.api_scraper.update_credentials(cookie, ms_token, webid)
        if cookie:
            self.html_scraper.update_cookie(cookie)


# 单例
_unified_scraper_instance = None

def get_unified_scraper() -> UnifiedScraper:
    """获取统一抓取器单例"""
    global _unified_scraper_instance
    if _unified_scraper_instance is None:
        _unified_scraper_instance = UnifiedScraper()
    return _unified_scraper_instance


if __name__ == '__main__':
    # 测试
    scraper = UnifiedScraper()
    
    print("=== 测试自动模式（含演示数据回退）===")
    result = scraper.fetch_hot_list()
    
    if result['success']:
        print(f"成功！使用方法: {result['method'].upper()}, 获取 {result['count']} 条")
        if result.get('note'):
            print(f"  注意: {result['note']}")
        for item in result['data'][:5]:
            print(f"  #{item.get('position', '-')} {item['word']}")
    else:
        print(f"失败: {result.get('error')}")
    
    print("\n=== 统计信息 ===")
    stats = scraper.get_stats()
    print(f"API: 成功{stats['api']['success']}次, 失败{stats['api']['fail']}次")
    print(f"HTML: 成功{stats['html']['success']}次, 失败{stats['html']['fail']}次")
    print(f"Demo: 成功{stats['demo']['success']}次")
    print(f"最后使用: {stats['last_method']}")

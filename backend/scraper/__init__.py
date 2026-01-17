# -*- coding: utf-8 -*-
"""
抓取模块

提供统一的热榜抓取接口，支持 API、HTML 和演示数据三重抓取策略。
"""

from .unified_scraper import UnifiedScraper, get_unified_scraper, ScraperMethod
from .api_scraper import DouyinAPIScraper, get_api_scraper
from .douyin_api import DouyinScraper, get_scraper as get_html_scraper
from .demo_loader import DemoDataLoader, get_demo_loader

__all__ = [
    'UnifiedScraper',
    'get_unified_scraper',
    'ScraperMethod',
    'DouyinAPIScraper',
    'get_api_scraper',
    'DouyinScraper',
    'get_html_scraper',
    'DemoDataLoader',
    'get_demo_loader',
]

# refactored_mihomo/src/core/network.py
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from src.utils.constants import BASE_URL, TIMEOUT, RETRY
from src.utils.logger import MihomoLogger
from src.utils.validators import validate_yaml_url


class MihomoNetwork:
    def __init__(self, base_url, timeout, retry, logger, is_running_func):
        self.base_url = base_url
        self.timeout = timeout
        self.retry = retry
        self.logger = logger
        self.is_running = is_running_func

    def make_request(self, url, retries=None):
        """
        封装的HTTP GET请求方法，包含重试和超时逻辑。
        """
        if retries is None:
            retries = self.retry
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        for attempt in range(retries):
            if not self.is_running():
                return None
            try:
                resp = requests.get(url, timeout=self.timeout, headers=headers)
                resp.raise_for_status()
                # Try multiple encodings to handle potential encoding issues
                encodings = ['utf-8', 'gbk', 'gb2312']
                for encoding in encodings:
                    try:
                        resp.encoding = encoding
                        content = resp.text
                        if 'qzdy-title' in content:  # Check if content seems valid
                            return resp
                    except UnicodeDecodeError:
                        continue
                # Fallback to utf-8 with replacement
                resp.encoding = 'utf-8'
                return resp
            except requests.RequestException as e:
                self.logger.log(f"请求失败 (尝试 {attempt + 1}/{retries}): {e}", "WARN")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None

    @staticmethod
    def get_date_formats(target_date):
        """返回可能的日期格式列表，用于匹配文章标题."""
        return [
            f"{target_date.year}年{target_date.month}月{target_date.day}日",
            f"{target_date.year}/{target_date.month}/{target_date.day}",
            f"{target_date.year}-{target_date.month:02d}-{target_date.day:02d}",
            target_date.strftime("%Y年%m月%d日"),
            f"{target_date.year}.{target_date.month}.{target_date.day}",
            f"{target_date.year}.{target_date.month:02d}.{target_date.day:02d}",
        ]

    def find_post_by_date(self, target_date):
        """
        在首页查找指定日期的文章链接。
        """
        try:
            resp = self.make_request(self.base_url)
            if not resp:
                self.logger.log("无法获取首页内容", "ERROR")
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            date_formats = self.get_date_formats(target_date)
            for article in soup.find_all(["h2", "h3", "article"], class_=["qzdy-title", "post-title"]):
                title_text = article.get_text(strip=True)
                for fmt in date_formats:
                    if fmt in title_text and any(keyword in title_text.lower() for keyword in ["免费节点", "free node", "订阅"]):
                        link = article.find("a") or (article if article.name == "a" else None)
                        if link and link.get("href"):
                            full_url = link["href"]
                            if not full_url.startswith("http"):
                                full_url = self.base_url.rstrip("/") + "/" + full_url.lstrip("/")
                            self.logger.log(f"找到匹配文章: {full_url}", "INFO")
                            return full_url
            self.logger.log(f"未找到 {target_date.strftime('%Y年%m月%d日')} 的匹配文章", "WARN")
            return None
        except Exception as e:
            self.logger.log(f"查找文章失败: {e}", "ERROR")
            return None

    def extract_mihomo_urls(self, post_url):
        """
        从文章页面提取 Mihomo 订阅链接。
        使用多个正则表达式和上下文过滤来确保准确性。
        """
        try:
            resp = self.make_request(post_url)
            if not resp:
                return []
            content = resp.text
            patterns = [
                r'https://[^\s<>"\' )]*mihomo[^\s<>"\' )]*\.ya?ml',
                r'(?i)(?:clash\.?mihomo|mihomo).*?订阅.*?(?:地址|链接).*?(https://[^\s<>"\' )]+\.ya?ml)',
                r'https://www\.85la\.com/wp-content/uploads/[^\s<>"\' )]+\.ya?ml',
            ]
            found_urls = set()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    url = match[0] if isinstance(match, tuple) else match
                    found_urls.add(url)
            
            filtered_urls = []
            for url in found_urls:
                url_index = content.find(url)
                if url_index != -1:
                    start = max(0, url_index - 300)
                    end = min(len(content), url_index + len(url) + 300)
                    context = content[start:end].lower()
                    # 确保上下文中包含 'mihomo' 或 'yaml' 且不包含 'clash.meta'
                    if ('mihomo' in context or 'yaml' in context) and 'clash.meta' not in context:
                        filtered_urls.append(url)
                    else:
                        self.logger.log(f"排除非 Mihomo 链接: {url}", "INFO")
            return filtered_urls
        except Exception as e:
            self.logger.log(f"提取 Mihomo 链接失败: {e}", "ERROR")
            return []

    def validate_yaml_url(self, url):
        """
        通过HEAD请求验证URL是否可访问。
        """
        try:
            # 使用 HEAD 请求，更快且不下载整个文件
            resp = requests.head(url, timeout=10, allow_redirects=True)
            return resp.status_code == 200
        except requests.RequestException:
            return False
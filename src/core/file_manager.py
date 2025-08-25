# refactored_mihomo/src/core/file_manager.py
import os
from datetime import datetime

from src.utils.logger import MihomoLogger
from src.utils.constants import SAVE_DIR


class MihomoFileManager:
    def __init__(self, save_dir, logger):
        self.save_dir = save_dir
        self.logger = logger

    def save_subscription_url(self, yaml_url):
        """
        修复版本：远程下载 yaml 文件内容，修复乱码并清理代理名称，然后保存为 85LA.yaml
        """
        import requests
        try:
            # 下载内容
            resp = requests.get(yaml_url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp.raise_for_status()
            
            # 尝试不同的编码方式来解决乱码问题
            content = None
            encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin1']
            
            for encoding in encodings:
                try:
                    resp.encoding = encoding
                    test_content = resp.text
                    # 验证内容是否包含有效的YAML结构且不包含过多乱码
                    if ('proxies:' in test_content or 'proxy-groups:' in test_content):
                        # 简单检查乱码程度 - 如果包含过多非ASCII字符可能是编码错误
                        ascii_ratio = sum(1 for c in test_content[:1000] if ord(c) < 128) / min(1000, len(test_content))
                        if ascii_ratio > 0.6 or encoding == 'utf-8':  # utf-8优先
                            content = test_content
                            self.logger.log(f"使用 {encoding} 编码解析成功", "INFO")
                            break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            # 如果所有编码都失败，使用默认处理
            if not content:
                content = resp.content.decode('utf-8', errors='replace')
                self.logger.log("使用默认UTF-8编码（替换错误字符）", "WARN")
            
            # 保存文件
            save_path = os.path.join(self.save_dir, "85LA.yaml")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, "w", encoding="utf-8", errors='replace') as f:
                f.write(content)
            
            self.logger.log(f"✅ 已下载节点配置到 {save_path}", "SUCCESS")
            return True
            
        except Exception as e:
            self.logger.log(f"❌ 下载处理 yaml 失败：{e}", "ERROR")
            return False

    def get_yaml_file_path(self):
        return os.path.join(self.save_dir, "85LA.yaml")

    def list_yaml_files(self):
        # 只返回85LA.yaml
        file_path = self.get_yaml_file_path()
        if os.path.isfile(file_path):
            return [file_path]
        return []

    def read_file_content(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
# refactored_mihomo/src/utils/validators.py
import requests


def validate_yaml_url(url):
    """
    通过HEAD请求验证URL是否可访问。
    """
    try:
        # 使用 HEAD 请求，更快且不下载整个文件
        resp = requests.head(url, timeout=10, allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException:
        return False
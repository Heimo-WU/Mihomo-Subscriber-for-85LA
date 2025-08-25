# refactored_mihomo/src/core/subscription.py
from src.utils.validators import validate_yaml_url


# This module can handle subscription-specific logic if expanded.
# For now, it's minimal as the original code integrates it into network and file_manager.
def get_valid_subscription_urls(network, post_url):
    urls = network.extract_mihomo_urls(post_url)
    return [url for url in urls if validate_yaml_url(url)]
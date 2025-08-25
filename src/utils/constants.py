# refactored_mihomo/src/utils/constants.py
import os
import logging

from config import SAVE_DIR, BASE_URL, TIMEOUT, RETRY

os.makedirs(SAVE_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
# refactored_mihomo/src/utils/logger.py
import os
import logging


class MihomoLogger:
    def __init__(self, save_dir):
        log_file = os.path.join(save_dir, "mihomo_auto.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file, encoding='utf-8'),
                      logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

    def log(self, message, level='INFO'):
        getattr(self.logger, level.lower(), self.logger.info)(message)
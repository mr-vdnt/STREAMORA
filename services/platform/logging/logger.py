import logging
import json
from services.platform.config.settings import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        # Use simple text format for dev, JSON structure could be used for prod
        if settings.ENV == "production":
            formatter = logging.Formatter('{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "msg": "%(message)s"}')
        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

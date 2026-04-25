import logging
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import LOG_FILE

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("terroir_local")

def log_info(message):
    logger.info(message)

def log_erreur(message):
    logger.error(message)

def log_warning(message):
    logger.warning(message)

if __name__ == "__main__":
    log_info("Test logger OK !")
    log_warning("Test warning OK !")
    log_erreur("Test erreur OK !")
    print("Logs ecrits dans : " + LOG_FILE)

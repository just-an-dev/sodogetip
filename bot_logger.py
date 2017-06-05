import logging
import os
from logging.handlers import RotatingFileHandler

from config import DATA_PATH, bot_config

if not os.path.exists(DATA_PATH + bot_config['logs_path']):
    os.makedirs(DATA_PATH + bot_config['logs_path'])

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('prawcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

formatter_file = logging.Formatter('%(asctime)s :: (%(threadName)-11s) :: (%(levelname)-10s) :: %(name)s :: %(pathname)s:%(lineno)s :: %(message)s')
formatter_output = logging.Formatter('%(asctime)s - (%(threadName)-11s) - (%(levelname)-10s) - %(message)s')

file_handler = RotatingFileHandler(DATA_PATH + bot_config['logs_path'] + 'activity.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter_file)
logger.addHandler(file_handler)

steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
steam_handler.setFormatter(formatter_output)
logger.addHandler(steam_handler)

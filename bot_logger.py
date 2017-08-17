import logging
import os
import threading
from datetime import date
from logging.handlers import RotatingFileHandler

import config

if not os.path.exists(config.logs_path):
    os.makedirs(config.logs_path)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('prawcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

formatter_file = logging.Formatter(
    '%(asctime)s :: (%(threadName)-11s) :: (%(levelname)-10s) :: %(name)s :: %(pathname)s:%(lineno)s :: %(message)s')
formatter_output = logging.Formatter('%(asctime)s - (%(threadName)-11s) - (%(levelname)-10s) - %(message)s')

path_log_file = config.logs_path + 'activity_' + date.today().strftime('%Y%m%d') + '.log'

# move logs to an other file for anti-spam
if threading.current_thread().name is "anti_spam":
    path_log_file = config.logs_path + 'anti_spam_' + date.today().strftime('%Y%m%d') + '.log'

file_handler = RotatingFileHandler(path_log_file, 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter_file)
logger.addHandler(file_handler)

if threading.current_thread().name is not "anti_spam":
    # add log to std out for other thread
    steam_handler = logging.StreamHandler()
    steam_handler.setLevel(logging.DEBUG)
    steam_handler.setFormatter(formatter_output)
    logger.addHandler(steam_handler)

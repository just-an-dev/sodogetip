import logging
import os
from logging.handlers import RotatingFileHandler

from config import DATA_PATH

if not os.path.exists(DATA_PATH+'/logs/'):
    os.makedirs(DATA_PATH+'/logs/')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter_file = logging.Formatter('%(asctime)s :: %(levelname)s :: %(name)s :: %(pathname)s:%(lineno)s :: %(message)s')
formatter_output = logging.Formatter('%(asctime)s -  - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler(DATA_PATH+'/logs/activity.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter_file)
logger.addHandler(file_handler)

steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
steam_handler.setFormatter(formatter_output)
logger.addHandler(steam_handler)

# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# logger = logging.getLogger('prawcore')
# logger.addHandler(handler)

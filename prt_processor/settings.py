import logging
import logging.handlers
import configparser
from os import path
import traceback
import sys


# Defaults
LOG_FILENAME = '/media/card/prt_processor/log/prt_processor.log'
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"

# Opening config
config= configparser.ConfigParser()
config_file_path = path.join(path.dirname(path.abspath(__file__)), 'params.ini')
if not path.exists(config_file_path):
    config_file_path= '/home/debian/prt_processor/params.ini'
config.read(config_file_path)

LOG_FILENAME= config['LOGGING']['filename']
LOG_LEVEL= int(config['LOGGING']['level'])

MQTT_BROKER_ADDRESS= config['MQTT_BROKER']['address']
MQTT_BROKER_PORT= int(config['MQTT_BROKER']['port'])
MQTT_BROKER_USER= config['MQTT_BROKER']['user']
MQTT_BROKER_PASSWORD= config['MQTT_BROKER']['password']

COMMON_PANEL_PASSWORD= config['COMMON']['panel_password']

COM_TTY_PORT= config['COM_TTY']['port']
COM_TTY_BAUD_RATE= int(config['COM_TTY']['baud_rate'])

# Configure logging to log to a file, making a new file at midnight and keeping the last 7 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger("prt_processor_logger")
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, mode='a', maxBytes=1*1024*1024,
                                 backupCount=10, encoding=None, delay=0)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(module)s - %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Console logger
consoleHandler = logging.StreamHandler()
logger.addHandler(consoleHandler)

# Exception logger into one log line
def log_app_error(e: BaseException, level=logging.ERROR) -> None:
    e_traceback = traceback.format_exception(e.__class__, e, e.__traceback__)
    traceback_lines = []
    for line in [line.rstrip('\n') for line in e_traceback]:
        traceback_lines.extend(line.splitlines())
    logger.log(level, traceback_lines.__str__())

def uncaughtHandler(type, value, tb):
    f_tb= traceback.format_tb(tb)
    traceback_lines = []
    for line in [line.rstrip('\n') for line in f_tb]:
        traceback_lines.extend(line.splitlines())
    logger.critical("Uncaught exception: {0}; Traceback: {1}".format(value, traceback_lines.__str__()))

sys.excepthook = uncaughtHandler

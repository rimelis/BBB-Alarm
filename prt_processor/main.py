import logging
import logging.handlers
import configparser
import paho.mqtt.client as MQTTClient
from os import path

# Defaults
LOG_FILENAME = '/media/card/prt_processor/log/prt_processor.log'
LOG_LEVEL = logging.DEBUG  # Could be e.g. "DEBUG" or "WARNING"

# Opening config
config= configparser.ConfigParser()
config_file_path = path.join(path.dirname(path.abspath(__file__)), 'params.ini')
if not path.exists(config_file_path):
    logger.debug("Config reader: /home/debian/prt_processor/params.ini")
    config_file_path= '/home/debian/prt_processor/params.ini'
config.read(config_file_path)

LOG_FILENAME= config['LOGGING']['filename']
LOG_LEVEL= int(config['LOGGING']['level'])

MQTT_BROKER_ADDRESS= config['MQTT_BROKER']['address']
MQTT_BROKER_PORT= int(config['MQTT_BROKER']['port'])
MQTT_BROKER_USER= config['MQTT_BROKER']['user']
MQTT_BROKER_PASSWORD= config['MQTT_BROKER']['password']

# Configure logging to log to a file, making a new file at midnight and keeping the last 7 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, mode='a', maxBytes=1*1024*1024,
                                 backupCount=10, encoding=None, delay=0)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)


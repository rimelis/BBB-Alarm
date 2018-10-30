# -*- coding: utf-8 -*-

import paho.mqtt.client as MQTT
import queue
import sqlite3 as sqlite
import time
import settings
from classes import SLists

logger= settings.logger
log_app_error = settings.log_app_error

class MQTTClient(object):
  def OnConnect(self, p_client, p_userdata, p_flags, p_rc):
    if p_rc == 0:
        logger.debug("MQTT CONN")
        try:
            self.__db_connection = sqlite.connect('db.sqlite')
            self.__db_connection.row_factory = sqlite.Row
            self.__db_cursor = self.__db_connection.cursor()

            # Keyswitch IN subscribes
            for self.__db_row in \
                    self.__db_cursor.execute("SELECT DISTINCT mqtt_topic FROM keyswitches WHERE direction = 'IN'"):
                self.__topic = self.__db_row['mqtt_topic'] + "/komanda"
                self.subscribe(self.__topic)

            # Areas subscribes
            for self.__db_row in \
                    self.__db_cursor.execute("SELECT mqtt_topic FROM areas"):
                self.__topic = self.__db_row['mqtt_topic'] + "/komanda"
                self.subscribe(self.__topic)

            logger.debug("-----------------------------")
        except sqlite.Error as e:
            raise TypeError("SQL error: %s:" % e.args[0])
        finally:
            if self.__db_connection:
                self.__db_connection.close()
    else:
        logger.error("Connection to MQTT failed!")

  def OnMessage(self, p_client, p_userdata, p_message):
    self.__topic= p_message.topic
    self.__payload= p_message.payload.decode('utf-8')
    logger.info("MQTT RECV: > " + self.__topic + " : " + self.__payload)
    # searching for keyswitch
    self.__keyswitch_obj = None
    self.__keyswitch_obj = SLists.getKeySwitchByMQTT(self.__topic.replace('/komanda', ''), 'IN', self.__payload)
    if self.__keyswitch_obj :
        self.__keyswitch_obj.trigger(self.__serial_queue)
    else : # searching for area
        self.__area_obj = None
        self.__area_obj = SLists.getAreaByMQTT(self.__topic.replace('/komanda', ''))
        if self.__area_obj :
#            self.__area_obj.processCommand(self.__serial_queue, self.__payload)
            self.__area_obj.processCommand(self.__payload)


  def OnDisconnect(self, p_client, p_userdata, p_rc):
      if p_rc != 0:
          logger.critical("MQTT UNEXPECTED DISCONNECT !!!")
      else:
          logger.info("MQTT DISCONN")
          self.__client.loop_stop()

  def publish(self, p_topic, p_payload, p_retain=True):
      self.__published_msg_info= self.__client.publish(p_topic, p_payload, retain=p_retain)
#      self.__published_msg_info.wait_for_publish()
      wait_200_ms= 50 # wait 10 sec.
      while wait_200_ms > 0 and not self.__published_msg_info.is_published() :
          time.sleep(0.2)
          wait_200_ms -= 1
      if self.__published_msg_info.is_published():
          logger.debug("MQTT PUB: > " + p_topic + " : " + p_payload)
      elif wait_200_ms == 0 and not self.__published_msg_info.is_published():
          logger.critical("MQTT RECONNECTING !!!")
          try:
              self.__client.reconnect()
          except TimeoutError:
              logger.critical("MQTT CONN Timeout!")

  def subscribe(self, p_topic):
      self.__client.subscribe(p_topic)
      logger.info("MQTT SUB: > " + p_topic)

  def __init__(self, p_broker_address, p_broker_port, p_username, p_password):
    logger.debug("MQTT INIT")
    self.__client= MQTT.Client(client_id="PRT_processor_client", clean_session=True)
    self.__client.username_pw_set(p_username, password=p_password)
    self.__client.on_connect = self.OnConnect
    self.__client.on_message = self.OnMessage
    self.__client.on_disconnect = self.OnDisconnect
    self.isConnected= False
    try:
        self.__client.connect(p_broker_address, port=p_broker_port, keepalive=10)
        self.__client.loop_start()
        self.isConnected= True
    except TimeoutError:
        logger.critical("MQTT CONN Timeout!")
    except Exception as e:
        log_app_error(e)
    # self.__serial_queue= SerialOutQueue

  def __del__(self):
      if self.isConnected:
          self.__client.disconnect()
      logger.debug('MQTT STOP')


# Global MQTT and Serial output queue
SerialOutQueue = queue.Queue()

mqtt = MQTTClient(settings.MQTT_BROKER_ADDRESS,
                  settings.MQTT_BROKER_PORT,
                  settings.MQTT_BROKER_USER,
                  settings.MQTT_BROKER_PASSWORD)

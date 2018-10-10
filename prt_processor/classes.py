# -*- coding: utf-8 -*-

import sqlite3 as sqlite
from builtins import TypeError, isinstance
from datetime import datetime
import logging
import json
import comm
import settings


"""
G004N009A000
G064N000A001
G064N001A001
G065N000A015
G064N000A003
G064N003A003
G001N020A002
G000N020A002
G015N002A003  - nerealizuota
G001N017A002
G000N017A002
G048N001A000
G001N019A001
"""


logger = logging.getLogger("prt_processor_logger")




CommDict= {'VO':'Virtual input open',\
           'VC':'Virtual input closed',\
           'RA':'Request Area Status',\
           'RZ':'Request Zone Status',\
           'AA':'Area Arm',\
           'AD':'Area Disarm',\
           'UK':'Utility Key'}




class Area(object):
  def __init__(self, id):
    self.id= id
    self.name= None
    self.mode= None
    self.status= None
    self.last_refresh= None
    self.mqtt_topic= None
    self.mqtt_payload= None
    self.zones_list= []
    self.load_from_db()

  def load_from_db(self):
     try:
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_connection.row_factory = sqlite.Row
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("SELECT name, mode, status, last_refresh, mqtt_topic FROM areas WHERE id = :id", {"id":self.id})
       self.__db_row = self.__db_cursor.fetchone()
       if self.__db_row:
           self.name= self.__db_row['name']
           self.mode= self.__db_row['mode']
           self.status= self.__db_row['status']
           self.last_refresh= self.__db_row['last_refresh']
           self.mqtt_topic= self.__db_row['mqtt_topic']
       del self.zones_list[:]
       for self.__db_row in self.__db_cursor.execute("SELECT id FROM zones WHERE area_id = :id", {"id":self.id}):
           self.zones_list.append(self.__db_row['id'])
     except sqlite.Error as e:
       raise TypeError("Area load SQL error: %s:" % e.args[0])
     finally:
        if self.__db_connection:
          self.__db_connection.close()

  def update(self, mode, status='OOOOOO'):
    self.mode = mode
    self.status = status
    self.last_refresh = datetime.now()
    try:
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("UPDATE areas SET status= :new_status, mode= :new_mode, last_refresh= :new_date WHERE id = :id",
                                {"id":self.id, "new_status":self.status, "new_mode":self.mode, "new_date":self.last_refresh})
       self.__db_connection.commit()
       logger.info("Area '{0:s}' updated: mode:{1:s} status:{2:s} last_refresh:{3:%Y-%m-%d %H:%M:%S}".format(self.name,
                                                                                                                self.mode,
                                                                                                                self.status,
                                                                                                                self.last_refresh)
              )
       if self.__db_cursor.rowcount == 0:
         raise TypeError("Area '{0:s}' update: no DB record found".format(self.name))
    except sqlite.Error as e:
       if self.__db_connection:
         self.__db_connection.rollback()
       raise TypeError("Area {0:s}' update SQL error: %s:" % e.args[0].format(self.name))
    finally:
       if self.__db_connection:
         self.__db_connection.close()
    # Getting mode string
    if self.mode == 'D' :
        l_mode_str = 'Disarmed'
    elif self.mode == 'A' :
        l_mode_str = 'Armed'
    elif self.mode == 'F' :
        l_mode_str = 'Force armed'
    elif self.mode == 'S' :
        l_mode_str = 'Stay armed'
    elif self.mode == 'I' :
        l_mode_str = 'Instant armed'
    # Getting status string
    if self.status == 'OOOOOO' :
        l_status_list = ['Ready']
    else :
        l_status_list = []
        if self.status[0:1] == 'M' :
            l_status_list.append('Zone in memory')
        if self.status[1:2] == 'T' :
            l_status_list.append('Trouble')
        if self.status[2:3] == 'N' :
            l_status_list.append('Not ready')
        if self.status[3:4] == 'P':
            l_status_list.append('In programming')
        if self.status[4:5] == 'A':
            l_status_list.append('In alarm')
        if self.status[5:6] == 'S':
            l_status_list.append('Strobe')
    self.mqtt_payload = json.dumps(dict
                              ([
                                ("datetime", self.last_refresh.strftime("%Y-%m-%d %H:%M:%S")),
                                ("mode_str", l_mode_str),
                                ("status_str", '; '.join(l_status_list)),
                                ("mode", self.mode),
                                ("status", self.status),
                               ])
                              )
    comm.mqtt.publish(self.mqtt_topic, self.mqtt_payload)

  def processCommand(self, p_serial_queue, p_mqtt_command):
      self.__serialCommand = None
      self.mqtt_payload = p_mqtt_command
      if self.mqtt_payload == 'STATUS' :
          self.__serialCommand = "RA{0:03d}".format(self.id)
      elif self.mqtt_payload == 'DISARM' :
          self.__serialCommand = "AD{0:03d}{1:s}".format(self.id, settings.COMMON_PANEL_PASSWORD)
      elif self.mqtt_payload == 'ARM_INSTANT' :
          self.__serialCommand = "AA{0:03d}I{1:s}".format(self.id, settings.COMMON_PANEL_PASSWORD)
      elif self.mqtt_payload == 'ARM_FORCE' :
          self.__serialCommand = "AA{0:03d}F{1:s}".format(self.id, settings.COMMON_PANEL_PASSWORD)
      if self.__serialCommand :
        logger.debug("Process {0:s} area command : {1:s}".format(self.name, self.mqtt_payload))
        p_serial_queue.put(self.__serialCommand)
      else :
        logger.error("Unknown {0:s} area command : {1:s}".format(self.name, self.mqtt_payload))
      if self.mqtt_payload == 'FULL_STATUS' :
          for index in range(len(self.zones_list)) :
              p_serial_queue.put("RZ{0:03d}".format(self.zones_list[index]))


class Zone(object):
  def __init__(self, id):
    self.id= id
    self.name= None
    self.mode= None
    self.status= None
    self.area_id= None
    self.last_refresh= None
    self.load_from_db()

  def load_from_db(self):
     try:
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_connection.row_factory = sqlite.Row
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("SELECT name, mode, status, area_id, last_refresh FROM zones WHERE id = :id", {"id":self.id})
       self.__db_row = self.__db_cursor.fetchone()
       if self.__db_row:
           self.name= self.__db_row['name']
           self.mode= self.__db_row['mode']
           self.status= self.__db_row['status']
           self.area_id= self.__db_row['area_id']
           self.last_refresh= self.__db_row['last_refresh']
     except sqlite.Error as e:
         raise TypeError("Zone load SQL error: %s:" % e.args[0])
     finally:
        if self.__db_connection:
          self.__db_connection.close()

  def update(self, mode, status='0000'):
    self.mode = mode
    self.status = status
    self.last_refresh = datetime.now()
    try:
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_connection.row_factory = sqlite.Row
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("UPDATE zones SET status= :new_status, mode= :new_mode, last_refresh= :new_date WHERE id = :id",
                                {"id":self.id, "new_status":self.status, "new_mode":self.mode, "new_date":self.last_refresh})
       self.__db_connection.commit()
       logger.info("Zone '{0:s}' updated: mode:{1:s} status:{2:s} last_refresh:{3:%Y-%m-%d %H:%M:%S}".format(self.name,
                                                                                                                self.mode,
                                                                                                                self.status,
                                                                                                                self.last_refresh)
              )
       if self.__db_cursor.rowcount == 0:
         raise TypeError("Zone '{0:s}' update: no DB record found".format(self.name))
    except sqlite.Error as e:
       if self.__db_connection:
         self.__db_connection.rollback()
       raise TypeError("Zone {0:s}' update SQL error: %s:" % e.args[0].format(self.name))
    finally:
        if self.__db_connection:
          self.__db_connection.close()



class KeySwitch(object):
    def __init__(self, id):
        self.id= id
        self.name= None
        self.mqtt_topic= None
        self.mqtt_payload= None
        self.mqtt_direction= None
        try:
            self.__db_connection = sqlite.connect('db.sqlite')
            self.__db_connection.row_factory = sqlite.Row
            self.__db_cursor = self.__db_connection.cursor()
            self.__db_cursor.execute("SELECT desc, mqtt_topic, payload, direction FROM keyswitches WHERE id = :id",
                                     {"id": self.id})
            self.__db_row = self.__db_cursor.fetchone()
            if self.__db_row:
                self.name = self.__db_row['desc']
                self.mqtt_topic = self.__db_row['mqtt_topic']
                self.mqtt_payload = self.__db_row['payload']
                self.mqtt_direction = self.__db_row['direction']
        except sqlite.Error as e:
            raise TypeError("Key switch load SQL error: %s:" % e.args[0])
        finally:
            if self.__db_connection:
                self.__db_connection.close()

    def trigger(self, p_serial_queue):
        logger.debug("Triggering keyswitch: {0:s} ({1:03d})".format(self.name, self.id))
        p_serial_queue.put("UK{0:03d}".format(self.id))

    def __str__(self):
        return "Keyswitch: {0:s} ({1:03d})".format(self.name, self.id)



class SystemLists(object):
    def __init__(self):
        self.Zones = [Zone(x) for x in range(49)]
        self.Areas = [Area(x) for x in range(5)]
        self.KeySwitches = [KeySwitch(x) for x in range(8)]

    def getArea(self, id):
        return next((x for x in self.Areas if x.id == id), None)

    def getAreaByMQTT(self, p_topic):
        return next((x for x in self.Areas if x.mqtt_topic == p_topic), None)

    def getZone(self, id):
        return next((x for x in self.Zones if x.id == id), None)

    def getKeySwitch(self, id):
        return next((x for x in self.KeySwitches if x.id == id), None)

    def getKeySwitchByMQTT(self, p_topic, p_direction, p_payload):
        return next((x for x in self.KeySwitches if (x.mqtt_topic == p_topic and x.mqtt_direction == p_direction and x.mqtt_payload == p_payload) ), None)


SLists = SystemLists()



class SystemEvent(object):
  def __init__(self, EventStr):
    self.area_desc = 'None'
    self.__area_obj = None
    self.__zone_obj = None
    self.__keyswitch_obj = None
    if isinstance(EventStr, str):
      if (len(EventStr) == 12) \
          and (EventStr[0:1] == 'G') \
          and (EventStr[4:5] == 'N') \
          and (EventStr[8:9] == 'A') :
             """ Isskaidom ivykio eilute """
             try:
               self.group= EventStr[1:4]
             except ValueError:
               raise TypeError("System event conversion error - wrong group")
             try:
               self.event= int(EventStr[5:8])
             except ValueError:
               raise TypeError("System event conversion error - wrong event")
             try:
               self.area= int(EventStr[9:12])
             except ValueError:
               raise TypeError("System event conversion error - wrong area")

             try:
               self.__db_connection = sqlite.connect('db.sqlite')
               self.__db_connection.row_factory = sqlite.Row
               self.__db_cursor = self.__db_connection.cursor()

               """ Ivykio duomenis """
               self.eventdesc= 'Unknown event'
               self.eventtype= None
               self.action= None
               self.__db_cursor.execute("SELECT eg_desc, en_desc, en_type, action FROM system_events" +
                                        " WHERE eg = :eg AND :en BETWEEN en_from AND en_until",
                           {"eg":self.group, "en":self.event})
               self.__db_row = self.__db_cursor.fetchone()
               if self.__db_row:
                    self.eventdesc= self.__db_row['eg_desc']+": "+self.__db_row['en_desc']
                    self.eventtype= self.__db_row['en_type']
                    self.action= self.__db_row['action']

               """ Srities duomenys """
               if self.area > 0:
                 self.__area_obj = SLists.getArea(self.area)
                 if self.__area_obj:
                     self.area_desc= self.__area_obj.name

               """ Zonos duomenys """
               if self.eventtype == 'Z':
                 self.__zone_obj = SLists.getZone(self.event)

               """ Keyswitch duomenys """
               if self.eventtype == 'K':
                   self.__keyswitch_obj = SLists.getKeySwitch(self.event)

               if self.action:
                   if self.action == 'Process_Utility_Key':
                       if self.__keyswitch_obj.mqtt_direction == 'OUT':
                            comm.mqtt.publish(self.__keyswitch_obj.mqtt_topic + "/komanda",
                                              self.__keyswitch_obj.mqtt_payload,
                                              p_retain=False)

             except sqlite.Error as e:
               raise TypeError("System event SQL error: %s:" % e.args[0])
             finally:
                if self.__db_connection:
                  self.__db_connection.close()
      else :
        raise TypeError("System event should be formatted GxxxNyyyAzzz")
    else :
      raise TypeError("System event should be string")

  def __str__(self):
    if not self.eventtype:
      return "Event: {0:s}; Area: {1:2d}({2:s})".format(self.eventdesc,
                                                        self.area,
                                                        self.area_desc)
    elif self.eventtype == 'Z':
      return "Event: {0:s}{1:02d}({2:s}); Area: {3:1d}({4:s})".format(self.eventdesc,
                                                                        self.event,
                                                                        self.__zone_obj.name,
                                                                        self.area,
                                                                        self.area_desc)
    elif (self.eventtype == 'U'):
      return "Event: {0:s}{1:03d}; Area: {2:1d}({3:s})".format(self.eventdesc,
                                                                        self.event,
                                                                        self.area,
                                                                        self.area_desc)
    elif (self.eventtype == 'K'):
      return "Event: {0:s}{1:03d}({2:s}); Area: {3:1d}({4:s})".format(self.eventdesc,
                                                                        self.event,
                                                                        self.__keyswitch_obj.name,
                                                                        self.area,
                                                                        self.area_desc)



class AreaEvent(object):
  def __init__(self, EventStr):
    self.call_str= None
    self.created= None
    self.desc= None
    self.mode= None
    if EventStr[0:2] == 'RA' :
        self.desc= 'Area request'
    elif EventStr[0:2] == 'AD' :
        self.desc= 'Area disarm'
        self.mode = 'D'
    elif EventStr[0:2] == 'AA':
        if len(EventStr) >= 6:
          if (EventStr[5:6] != 'F') \
            and (EventStr[5:6] != 'I') \
            and (EventStr[5:6] != 'S') \
            and (EventStr[5:6] != 'A'):
            raise TypeError("Area arm mode must be F,I,S,A")
          else:
            self.mode = EventStr[5:6]
    else :
        raise TypeError("Area event should start with RA, AA, AD")
    try:
       self.__area_id= int(EventStr[3:5])
    except ValueError:
       raise TypeError("Area Event conversion error - wrong area")
    if self.__area_id < 1 or self.__area_id > 4 :
       raise TypeError("Area Event error: area must be between 1..4")
    self.call_str= EventStr[0:5]
    self.created= datetime.now()
    self.area= SLists.getArea(self.__area_id)
    """
    # Setting Instant arming in case unset
    if (EventStr[0:2] == 'AA') and (len(EventStr) == 5) :
        self.call_str = self.call_str + 'I'
    # Add password
    if (EventStr[0:2] == 'AA') or (EventStr[0:2] == 'AD') :
        self.call_str = self.call_str + COMMON_PANEL_PASSWORD
    """
  def answer(self, EventStr):
    if isinstance(EventStr, str):
      if (EventStr[0:2] == 'RA') or (EventStr[0:2] == 'AA') or (EventStr[0:2] == 'AD') :
          try:
              self.__area_id = int(EventStr[3:5])
          except ValueError:
              raise TypeError("Area conversion error - wrong area")
          if self.__area_id < 1 or self.__area_id > 4:
              raise TypeError("Area must be between 1..4")
          if EventStr[0:2] == 'RA' :
              if len(EventStr) == 12 :
                 self.__mode= EventStr[5:6]
                 self.__status= EventStr[6:12]
                 self.area.update(self.__mode, self.__status)
              else :
                  raise TypeError("Request event answer length must be 12 bytes")
          elif (EventStr[0:2] == 'AA') or (EventStr[0:2] == 'AD') :
              if EventStr[5:8] == '&ok' :
                  self.area.update(self.mode)
              elif EventStr[5:10] != '&fail' :
                  raise TypeError("Area event answer AA or AD should end with &ok or &fail")

      else :
          raise TypeError("Area event answer should start with RA, AA, AD")
    else :
      raise TypeError("Area event should be string")

  def __str__(self):
    return "Area event: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.area.name)
  def __del__(self):
    if self.call_str and self.created :
        logger.debug("Area event initiator destroyed: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.area.name))


class ZoneEvent(object):
  def __init__(self, EventStr):
    self.call_str= None
    self.created= None
    self.desc= None
    try:
       self.__zone_id= int(EventStr[3:5])
    except ValueError:
       raise TypeError("Zone Event conversion error - wrong identificator")
    if self.__zone_id < 1 or self.__zone_id > 48 :
       raise TypeError("Zone Event error: area must be between 1..48")
    self.call_str= EventStr[0:5]
    self.created= datetime.now()
    self.zone= SLists.getZone(self.__zone_id)
  def answer(self, EventStr):
    if isinstance(EventStr, str):
      if EventStr[0:2] == 'RZ':
          try:
              self.__zone_id = int(EventStr[3:5])
          except ValueError:
              raise TypeError("Zone conversion error - wrong identificator")
          if self.__zone_id < 1 or self.__zone_id > 48:
              raise TypeError("Zone must be between 1..48")
          if len(EventStr) == 10:
             self.__mode= EventStr[5:6]
             self.__status= EventStr[6:10]
             self.zone.update(self.__mode, self.__status)
          else :
              raise TypeError("Zone event answer length must be 10 bytes")
      else :
          raise TypeError("Zone event answer should start with RZ")
    else :
      raise TypeError("Zone event should be string")
  def __str__(self):
    return "Zone event: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.zone.name)
  def __del__(self):
    if self.call_str and self.created :
        logger.debug("Zone event initiator destroyed: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.zone.name))


class KeySwitchEvent(object):
    def __init__(self, EventStr):
        self.call_str = None
        self.created = None
        if EventStr[0:2] == 'UK' :
            if len(EventStr) == 5 :
                self.call_str = EventStr
                self.created = datetime.now()
                try:
                    self.__id = int(EventStr[3:5])
                except ValueError:
                    raise TypeError("Utility key event conversion error - wrong id")
                self.__keyswitch_obj= SLists.getKeySwitch(self.__id)
            else :
                raise TypeError("Utility key event length should be 5 bytes")
        else :
            raise TypeError("Utility key event should start with UK")
        try:
           self.__db_connection = sqlite.connect('db.sqlite')
           self.__db_connection.row_factory = sqlite.Row
           self.__db_cursor = self.__db_connection.cursor()
           self.__db_cursor.execute("SELECT name FROM zones WHERE id = :id", {"id":self.__id})
           self.__db_row = self.__db_cursor.fetchone()
           if self.__db_row:
               self.name= self.__db_row['name']
        except sqlite.Error as e:
             raise TypeError("Keyswitch load SQL error: %s:" % e.args[0])
        finally:
            if self.__db_connection:
              self.__db_connection.close()

    def answer(self, EventStr):
        if isinstance(EventStr, str):
            if EventStr[0:2] == 'UK' :
                try :
                    self.__id = int(EventStr[3:5])
                except ValueError:
                    raise TypeError("Utility key event conversion error - wrong id")
                if EventStr[5:8] == '&ok' :
                    self.__keyswitch_obj = SLists.getKeySwitch(self.__id)
                elif EventStr[5:10] != '&fail':
                    raise TypeError("Utility key event answer should end with &ok or &fail")
            else:
                raise TypeError("Utility key event answer should start with UK")
        else:
            raise TypeError("Utility key event answer should be string")

    def __str__(self):
        return "Utility key event: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.__keyswitch_obj.name)

    def __del__(self):
        if self.call_str and self.created:
            logger.debug("Utility key event initiator destroyed: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.__keyswitch_obj.name))


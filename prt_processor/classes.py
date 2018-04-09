# -*- coding: utf-8 -*-

import sqlite3 as sqlite
import sys
from builtins import TypeError, isinstance
from datetime import datetime
import time

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
"""

#ZoneList= []
#AreaList= []

Cpassw= '4521'

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

    self.load_from_db()
  def load_from_db(self):
     try:
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_connection.row_factory = sqlite.Row
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("SELECT name, mode, status, last_refresh FROM areas WHERE id = :id", {"id":self.id})
       self.__db_row = self.__db_cursor.fetchone()
       if self.__db_row:
           self.name= self.__db_row['name']
           self.mode= self.__db_row['mode']
           self.status= self.__db_row['status']
           self.last_refresh= self.__db_row['last_refresh']
     except sqlite.Error as e:
       raise TypeError("Area load SQL error: %s:" % e.args[0])
     finally:
        if self.__db_connection:
          self.__db_connection.close()

  def update(self, mode, status='OOOOOO'):
     try:
       self.mode= mode
       self.status= status
       self.last_refresh= datetime.now()
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("UPDATE areas SET status= :new_status, mode= :new_mode, last_refresh= :new_date WHERE id = :id",
                                {"id":self.id, "new_status":self.status, "new_mode":self.mode, "new_date":self.last_refresh})
       self.__db_connection.commit()
       print ("Area '{0:s}' updated: mode:{1:s} status:{2:s} last_refresh:{3:%Y-%m-%d %H:%M:%S}".format(self.name,
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

  def update(self):
     try:
       self.__db_connection = sqlite.connect('db.sqlite')
       self.__db_connection.row_factory = sqlite.Row
       self.__db_cursor = self.__db_connection.cursor()
       self.__db_cursor.execute("UPDATE zones SET status= :new_status, mode= :new_mode, last_refresh= :new_date WHERE id = :id",
                                {"id":self.id, "new_status":self.status, "new_mode":self.mode, "new_date":self.last_refresh})
       self.__db_connection.commit()
       print ("Zone '{0:s}' updated: mode:{1:s} status:{2:s} last_refresh:{3:%Y-%m-%d %H:%M:%S}".format(self.name,
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
        try:
            self.__db_connection = sqlite.connect('db.sqlite')
            self.__db_connection.row_factory = sqlite.Row
            self.__db_cursor = self.__db_connection.cursor()
            self.__db_cursor.execute("SELECT desc FROM keyswitches WHERE id = :id",
                                     {"id": self.id})
            self.__db_row = self.__db_cursor.fetchone()
            if self.__db_row:
                self.name = self.__db_row['desc']
        except sqlite.Error as e:
            raise TypeError("Key switch load SQL error: %s:" % e.args[0])
        finally:
            if self.__db_connection:
                self.__db_connection.close()


class SystemLists(object):
    def __init__(self):
        self.Zones = [Zone(x) for x in range(48)]
        self.Areas = [Area(x) for x in range(5)]
        self.KeySwitches = [KeySwitch(x) for x in range(8)]
    def getArea(self, id):
        return next((x for x in self.Areas if x.id == id), None)
    def getZone(self, id):
        return next((x for x in self.Zones if x.id == id), None)
    def getKeySwitch(self, id):
        return next((x for x in self.KeySwitches if x.id == id), None)

SLists = SystemLists()

class SystemEvent(object):
  def __init__(self, EventStr):
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
               self.__area_obj= None
               self.area_desc= 'None'
               if self.area > 0:
                 self.__area_obj = SLists.getArea(self.area)
                 if self.__area_obj:
                     self.area_desc= self.__area_obj.name

               """ Zonos duomenys """
               if self.eventtype == 'Z':
                 self.__zone_obj = SLists.getZone(self.event)
               else:
                 self.__zone_obj= None

               """ Keyswitch duomenys """
               if self.eventtype == 'K':
                   self.__keyswitch_obj = SLists.getKeySwitch(self.event)
               else:
                   self.__keyswitch_obj = None

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
    if EventStr[0:2] == 'RA' :
        if len(EventStr) == 5 :
            self.desc= 'Area request'
        else :
            raise TypeError("Area request event length must be 5 bytes")
    elif EventStr[0:2] == 'AD' :
        if len(EventStr) == 5 :
            self.desc= 'Area disarm'
        else :
            raise TypeError("Area disarm event length must be 5 bytes")
    elif EventStr[0:2] == 'AA' :
        if (len(EventStr) < 5) or (len(EventStr) > 6) :
           raise TypeError("Area arm event length must be 5..6 bytes")
        if len(EventStr) == 6 :
          if (EventStr[5:6] != 'F') \
            and (EventStr[5:6] != 'I') \
            and (EventStr[5:6] != 'S') \
            and (EventStr[5:6] != 'A') :
            raise TypeError("Area arm event must be F,I,S,A")
    else :
        raise TypeError("Area event should start with RA, AA, AD")
    try:
       self.__area= int(EventStr[3:5])
    except ValueError:
       raise TypeError("Area Event conversion error - wrong area")
    if self.__area < 1 or self.__area > 4 :
       raise TypeError("Area Event error: area must be between 1..4")
    self.call_str= EventStr
    self.created= datetime.now()
    self.__area_obj = SLists.getArea(self.__area)
    if (EventStr[0:2] == 'AA') and (len(EventStr) == 5) :
        self.call_str = self.call_str + 'I'
    if (EventStr[0:2] == 'AA') or (EventStr[0:2] == 'AD') :
        self.call_str = self.call_str + '<passw>'
        self.__mode= self.call_str[5:6]

  def answer(self, EventStr):
    if isinstance(EventStr, str):
      if (EventStr[0:2] == 'RA') or (EventStr[0:2] == 'AA') or (EventStr[0:2] == 'AD') :
          try:
              self.__area = int(EventStr[3:5])
          except ValueError:
              raise TypeError("Area conversion error - wrong area")
          if self.__area < 1 or self.__area > 4:
              raise TypeError("Area must be between 1..4")
          if EventStr[0:2] == 'RA' :
              if len(EventStr) == 12 :
                 self.__area_obj= SLists.getArea(self.__area)
                 self.__mode= EventStr[5:6]
                 self.__status= EventStr[6:12]
                 self.__area_obj.update(self.__mode, self.__status)
              else :
                  raise TypeError("Request event answer length must be 12 bytes")
          elif (EventStr[0:2] == 'AA') or (EventStr[0:2] == 'AD') :
              if EventStr[5:8] == '&ok' :
                  self.__area_obj = SLists.getArea(self.__area)
                  self.__area_obj.update(self.__mode)
              elif EventStr[5:10] != '&fail' :
                  raise TypeError("Area event answer AA or AD should end with &ok or &fail")

      else :
          raise TypeError("Area event answer should start with RA, AA, AD")
    else :
      raise TypeError("Area event should be string")

  def __str__(self):
    return "Area event: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.__area_obj.name)
  def __del__(self):
    if self.call_str and self.created :
      print ("Area event initiator destroyed: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.__area_obj.name))


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
        self.__keyswitch_obj = SLists.getKeySwitch(self.__id)

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
        self.__keyswitch_obj = SLists.getKeySwitch(self.__id)

    def __str__(self):
        return "Utility key event: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.__keyswitch_obj.name)

    def __del__(self):
        if self.call_str and self.created:
            print("Utility key event initiator destroyed: {0:s} {1:%Y-%m-%d %H:%M:%S} - {2:s}".format(self.call_str, self.created, self.__keyswitch_obj.name))



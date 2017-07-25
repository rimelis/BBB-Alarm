# -*- coding: utf-8 -*-

import sqlite3 as sqlite
import sys
from builtins import TypeError, isinstance
from datetime import datetime

"""
G004N009A000
G064N000A001
G064N001A001
G065N000A015
G064N000A003
G064N003A003
G001N020A002
G000N020A002
G015N002A003
G001N017A002
G000N017A002
"""

ZoneList= []
AreaList= []

class Area(object):
  def __init__(self, id):
    self._id= id  
    self._name= None
    self._mode= None 
    self._status= None
    self._last_refresh= None

    self.load_from_db()
  def load_from_db(self):      
     try:
       self._db_connection = sqlite.connect('alarm.sqlite')
       self._db_connection.row_factory = sqlite.Row
       self._db_cursor = self._db_connection.cursor()
             
       self._db_cursor.execute("SELECT name, mode, status, last_refresh FROM areas WHERE id = :id", {"id":self._id})
       self._db_row = self._db_cursor.fetchone()
       if self._db_row: 
           self._name= self._db_row['name']
           self._mode= self._db_row['mode'] 
           self._status= self._db_row['status']
           self._last_refresh= self._db_row['last_refresh']

     except sqlite.Error as e:
       raise TypeError("Area load SQL error: %s:" % e.args[0])
     finally:
        if self._db_connection:
          self._db_connection.close()
          
  def update_status(self, status):
     try:
       self._status= status
       self._last_refresh= datetime.now()  
         
       self._db_connection = sqlite.connect('alarm.sqlite')
       self._db_cursor = self._db_connection.cursor()
       self._db_cursor.execute("UPDATE zones SET status= :new_status, last_refresh= :new_date WHERE id = :id",
                                {"id":self._id, "status":self._status, "last_refresh":self._last_refresh})
       self._db_connection.commit()
       if self._db_cursor.rewcount == 0: 
         raise TypeError("Area update: no DB record found")
     except sqlite.Error as e:
       raise TypeError("Area update SQL error: %s:" % e.args[0])
     finally:
        if self._db_connection:
          self._db_connection.close()



class Zone(object):
  def __init__(self, id):
    self._id= id  
    self._name= None
    self._mode= None 
    self._status= None
    self._area_id= None
    self._last_refresh= None
    
    self.load_from_db()
  def load_from_db(self):      
     try:
       self._db_connection = sqlite.connect('alarm.sqlite')
       self._db_connection.row_factory = sqlite.Row
       self._db_cursor = self._db_connection.cursor()
             
       self._db_cursor.execute("SELECT name, mode, status, area_id, last_refresh FROM zones WHERE id = :id", {"id":self._id})
       self._db_row = self._db_cursor.fetchone()
       if self._db_row: 
           self._name= self._db_row['name']
           self._mode= self._db_row['mode'] 
           self._status= self._db_row['status']
           self._area_id= self._db_row['area_id']
           self._last_refresh= self._db_row['last_refresh']

     except sqlite.Error as e:
       raise TypeError("Zone load SQL error: %s:" % e.args[0])
     finally:
        if self._db_connection:
          self._db_connection.close()

class SystemEvent(object):
  def __init__(self, EventStr):
    if isinstance(EventStr, str):
      if (len(EventStr) == 12) \
          and (EventStr[0:1] == 'G') \
          and (EventStr[4:5] == 'N') \
          and (EventStr[8:9] == 'A') :
             """ Isskaidom ivykio eilute """
             try: 
               self._group= EventStr[1:4]
             except ValueError:
               raise TypeError("System event conversion error - wrong group")
             try:     
               self._event= int(EventStr[5:8])
             except ValueError:
               raise TypeError("System event conversion error - wrong event")      
             try:
               self._area= int(EventStr[9:12])
             except ValueError:
               raise TypeError("System event conversion error - wrong area")
           
             try:
               self._db_connection = sqlite.connect('alarm.sqlite')
               self._db_connection.row_factory = sqlite.Row
               self._db_cursor = self._db_connection.cursor()      

               """ Ivykio duomenis """  
               self._eventdesc= 'Unknown event'
               self._eventtype= None
               self._action= None 
               self._db_cursor.execute("SELECT eg_desc, en_desc, en_type, action FROM system_events" +  
                                        " WHERE eg = :eg AND :en BETWEEN en_from AND en_until",
                           {"eg":self._group, "en":self._event})
               self._db_row = self._db_cursor.fetchone()
               if self._db_row: 
                 self._eventdesc= self._db_row['eg_desc']+": "+self._db_row['en_desc']
                 self._eventtype= self._db_row['en_type']
                 self._action= self._db_row['action']
                 
               """ Srities duomenys """
               if self._area > 0:  
                 self._area_obj= next((x for x in AreaList if x._id == self._area), None)
                 self._area_desc= self._area_obj._name
               else:
                 self._area_obj= None
                 self._area_desc= 'None'       
               
               """ Zonos duomenys """
               if self._eventtype == 'Z':
                 self._zone_obj= next((x for x in ZoneList if x._id == self._event), None)
               else:
                 self._zone_obj= None
                       
             except sqlite.Error as e:
               raise TypeError("System event SQL error: %s:" % e.args[0])
             finally:
                if self._db_connection:
                  self._db_connection.close()
      else :
        raise TypeError("System event should be formatted GxxxNyyyAzzz")  
    else :     
      raise TypeError("System event should be string")

  def __str__(self):
    if self._eventtype == None:  
      return "Event: {0:s}; Area: {1:1d}({2:s})".format(self._eventdesc,
                                                        self._area,
                                                        self._area_desc)
    elif self._eventtype == 'Z':      
      return "Event: {0:s}{1:02d}({2:s}); Area: {3:1d}({4:s})".format(self._eventdesc,
                                                                        self._event,
                                                                        self._zone_obj._name,
                                                                        self._area,
                                                                        self._area_desc) 
    elif (self._eventtype == 'U') or (self._eventtype == 'K'):      
      return "Event: {0:s}{1:02d}; Area: {2:1d}({3:s})".format(self._eventdesc,
                                                                        self._event,
                                                                        self._area,
                                                                        self._area_desc) 


"""
try:
    
    con = sqlite.connect('alarm.sqlite')

    print(type(con))
    
    cur = con.cursor()    
    cur.execute('SELECT SQLITE_VERSION()')    
    data = cur.fetchone()
    print ("SQLite version: %s" % data)
    
    cur.execute("SELECT * FROM zones")
    rows = cur.fetchall()
    for row in rows:
        print (row)
            
except (sqlite.Error, e):
    print ("Error %s:" % e.args[0])
    sys.exit(1)
finally:
    if con:
        con.close()
"""

ZoneList= [Zone(x) for x in range(48)]
AreaList= [Area(x) for x in range(4)]

test= SystemEvent("G001N005A003")
print(test)

        
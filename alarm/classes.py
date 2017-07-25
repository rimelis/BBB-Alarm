# -*- coding: utf-8 -*-

import sqlite3 as sqlite
import sys
from builtins import TypeError, isinstance
from datetime import datetime
import traceback
import threading
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
G015N002A003
G001N017A002
G000N017A002
"""

#ZoneList= []
#AreaList= []

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
       self.__db_connection = sqlite.connect('alarm.sqlite')
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
          
  def update(self, mode, status):
     try:
       self.mode= mode  
       self.status= status
       self.last_refresh= datetime.now()  
         
       self.__db_connection = sqlite.connect('alarm.sqlite')
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
       self.__db_connection = sqlite.connect('alarm.sqlite')
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
               self.__db_connection = sqlite.connect('alarm.sqlite')
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
                 self.__area_obj= next((x for x in AreaList if x.id == self.area), None)
                 if self.__area_obj:
                     self.area_desc= self.__area_obj.name
               
               """ Zonos duomenys """
               if self.eventtype == 'Z':
                 self.__zone_obj= next((x for x in ZoneList if x.id == self.event), None)
               else:
                 self.__zone_obj= None

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
    elif (self.eventtype == 'U') or (self.eventtype == 'K'):      
      return "Event: {0:s}{1:02d}; Area: {2:1d}({3:s})".format(self.eventdesc,
                                                                        self.event,
                                                                        self.area,
                                                                        self.area_desc) 


class AreaEvent(object):
  def __init__(self, EventStr):
    self.call_str= None
    self.created= None 
    if (EventStr[0:2] == 'RA') or (EventStr[0:2] == 'AD') :
      if len(EventStr) != 5 :  
        raise TypeError("Area request event length must be 5 bytes")    
    else :   
      if EventStr[0:2] == 'AA' : 
        if (len(EventStr) < 5) or (len(EventStr) > 6) :   
           raise TypeError("Area arm event length must be 5..6 bytes")
        if len(EventStr) == 6 :
          if (EventStr[5:6] != 'F') \
            and (EventStr[5:6] != 'I') \
            and (EventStr[5:6] != 'S') \
            and (EventStr[5:6] != 'A') :    
            raise TypeError("Area arm event must be F,I,S,A")
      else :
        raise TypeError("Area event should be start with RA, AA, AD")  
    try:     
       self.__area= int(EventStr[3:5])
    except ValueError:
       raise TypeError("Area Event conversion error - wrong area")
    if self.__area < 1 or self.__area > 4 :    
       raise TypeError("Area Event error: area must be between 1..4")
    self.call_str= EventStr
    self.created= datetime.now()
    if (EventStr[0:2] == 'AA') and (len(EventStr) == 5) :
      self.call_str.join('F')
       
  def answer(self, EventStr):    
    if isinstance(EventStr, str):
      if EventStr[0:2] == 'RA' :
        if len(EventStr) == 12 :  
             try:     
               self.__area= int(EventStr[3:5])
             except ValueError:
               raise TypeError("Request Area conversion error - wrong area")
             if self.__area < 1 or self.__area > 4 :    
               raise TypeError("Request Area must be between 1..4")
           
             self.__area_obj= next((x for x in AreaList if x.id == self.__area), None)
             self.__mode= EventStr[5:6]
             self.__status= EventStr[6:12]
             self.__area_obj.update(self.__mode, self.__status)
           
        else :
          raise TypeError("Request event answer length must be 12 bytes")  
      else :
        raise TypeError("Request event should start with RA")  
    else :     
      raise TypeError("Request event should be string")
  def __str__(self):
    return "Area event: {0:s} {1:%Y-%m-%d %H:%M:%S}".format(self.call_str, self.created)
  def __del__(self):
    if self.call_str and self.created : 
      print ("Request Area destroyed: {0:s} {1:%Y-%m-%d %H:%M:%S}".format(self.call_str, self.created))       

   

#####################################################################################

if __name__ == '__main__':

    ZoneList= [Zone(x) for x in range(48)]
    AreaList= [Area(x) for x in range(4)]
    
#    RAQueueLock = threading.Lock()
    RAList= []
    
    try:
      while True:
        instr= input(">")
        if len(instr) > 0 :
          if instr == "exit" :
              break
          elif instr[0:1] == 'G' : 
              try:
                  se= SystemEvent(instr)
                  print(se)
                  del se
              except:
                  formatted_lines = traceback.format_exc().splitlines()
#                  print (formatted_lines[-1])
                  print (formatted_lines)
          elif instr[0:2] == 'RA' :
              try:
                  if len(instr) == 5 :
                    ra= next((x for x in RAList if x.call_str == instr), None)
                    if not ra:  
                        ra= RequestArea(instr)
                        RAList.append(ra)
                        print (ra)
                  if len(instr) == 12 :
                    ra= next((x for x in RAList if x.call_str == instr[0:5]), None)
                    if ra:  
                        ra.put_answer(instr)
                        RAList.remove(ra)
                        del ra
                    else :
                        print ("Request Area answer {0:s} has not found the request!".format(instr))      
              except:
                  formatted_lines = traceback.format_exc().splitlines()
#                  print (formatted_lines[-1])
                  print (formatted_lines)
          else:
              print ("Unknown input.")                   
    except KeyboardInterrupt :
      print("Stopped.")
   
    while len(RAList) > 0 :
        ra= RAList.pop()
        del ra
    
#    for t in threads:
#        t.join()
    
    """
    test= SystemEvent("G001N005A003")
    print(test)
    """
        
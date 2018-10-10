import serial
import sys
import time
import settings

# Custom serial redaline to carry CR instead of LN
def serial_read_line(ser):
    str = ""
    while True:
        ch = ser.read()
        if(ch == b'\r' or ch == b'' and len(str) == 0):
            break
        str += ch.decode('ascii')
    return str

#####################################################################################################

if __name__ == '__main__':

    logger = settings.logger
    log_app_error= settings.log_app_error

    logger.debug("vvvvv---------v---------vvvvv")
    logger.info("Initializing...")

    import comm
    from classes import SystemEvent, AreaEvent, KeySwitchEvent, ZoneEvent

    serOutCommand= ''

    RZList= []
    RAList= []
    AAList= []
    ADList= []
    KSList= []

    if comm.mqtt.isConnected:
        ser= None
        try:
            ser= serial.Serial(
                            port=settings.COM_TTY_PORT,
                            baudrate=settings.COM_TTY_BAUD_RATE,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS,
                            timeout=0
                            )
            if ser.isOpen():
                logger.info("SERIAL {0:s} is OPENED.".format(settings.COM_TTY_PORT))
                try:
                  while True:
                    if len(serOutCommand) > 0:
                        # command send to serial on previous iteration is not processed so let's do it
                        instr= serOutCommand
                        serOutCommand= ''
                    else:
                        # reading serial
                        instr = serial_read_line(ser)
                    if len(instr) > 0:
                      logger.debug(">"+instr)
                      if instr == "exit" :
                          break
                      elif instr[0:1] == 'G' :
                          try:
                              se= SystemEvent(instr)
                              logger.debug(se)
                              del se
                          except Exception as e:
                              log_app_error(e)
                      elif instr[0:2] == 'RA' :
                          try:
                              if len(instr) == 5 :
                                ra= next((x for x in RAList if x.call_str[0:5] == instr[0:5]), None)
                                if not ra:
                                    ra= AreaEvent(instr)
                                    RAList.append(ra)
                                    logger.debug(ra)
                              else :
                                  if len(instr) == 12 :
                                    ra= next((x for x in RAList if x.call_str[0:5] == instr[0:5]), None)
                                    if ra:
                                        logger.debug("Request Area answer received.")
                                        ra.answer(instr)
                                        RAList.remove(ra)
                                        del ra
                                    else :
                                        logger.debug("Request Area answer {0:s} has not found the initiator!".format(instr))
                                  else :
                                      logger.debug("Wrong Request Area answer")
                          except Exception as e:
                              log_app_error(e)
                      elif instr[0:2] == 'RZ' :
                          try:
                              if len(instr) == 5 :
                                rz= next((x for x in RZList if x.call_str[0:5] == instr[0:5]), None)
                                if not rz:
                                    rz= ZoneEvent(instr)
                                    RZList.append(rz)
                                    logger.debug(rz)
                              else :
                                  if len(instr) == 10 :
                                    rz= next((x for x in RZList if x.call_str[0:5] == instr[0:5]), None)
                                    if rz:
                                        logger.debug("Request zone answer received.")
                                        rz.answer(instr)
                                        RZList.remove(rz)
                                        del rz
                                    else :
                                        logger.debug("Request zone answer {0:s} has not found the initiator!".format(instr))
                                  else :
                                      logger.debug("Wrong request zone answer")
                          except Exception as e:
                              log_app_error(e)
                      elif instr[0:2] == 'AA':
                          try:
                              if ('&' not in instr) :
                                  aa = next((x for x in AAList if x.call_str[0:5] == instr[0:5]), None)
                                  if not aa:
                                      aa = AreaEvent(instr)
                                      AAList.append(aa)
                                      logger.debug(aa)
                              else:
                                  aa = next((x for x in AAList if x.call_str[0:5] == instr[0:5]), None)
                                  if aa:
                                      logger.debug("Area arm answer received.")
                                      aa.answer(instr)
                                      AAList.remove(aa)
                                      del aa
                                  else:
                                      logger.debug("Area arm answer {0:s} has not found the initiator!".format(instr))
                          except Exception as e:
                              log_app_error(e)
                      elif instr[0:2] == 'AD':
                          try:
                              if ('&' not in instr) :
                                  ad = next((x for x in ADList if x.call_str[0:5] == instr[0:5]), None)
                                  if not ad:
                                      ad = AreaEvent(instr)
                                      ADList.append(ad)
                                      logger.debug(ad)
                              else:
                                  ad = next((x for x in ADList if x.call_str[0:5] == instr[0:5]), None)
                                  if ad:
                                      logger.debug("Area disarm answer received.")
                                      ad.answer(instr)
                                      ADList.remove(ad)
                                      del ad
                                  else:
                                      logger.debug("Area disarm answer {0:s} has not found the initiator!".format(instr))
                          except Exception as e:
                              log_app_error(e)
                      elif instr[0:2] == 'UK':
                          try:
                              if len(instr) == 5 :
                                  ks = next((x for x in KSList if x.call_str[0:5] == instr[0:5]), None)
                                  if not ks:
                                      ks = KeySwitchEvent(instr)
                                      KSList.append(ks)
                                      logger.debug(ks)
                              else:
                                  ks = next((x for x in KSList if x.call_str[0:5] == instr[0:5]), None)
                                  if ks:
                                      logger.debug("Utility key event answer received.")
                                      ks.answer(instr)
                                      KSList.remove(ks)
                                      del ks
                                  else:
                                      logger.debug("Utility key event answer {0:s} has not found the initiator!".format(instr))
                          except Exception as e:
                              log_app_error(e)
                      else:
                          logger.debug("Unknown input.")

                    # sending to serial
                    if not comm.SerialOutQueue.empty():
                        serOutCommand = comm.SerialOutQueue.get()
                        if serOutCommand:
                            try:
                                ser.write('{0:s}\r'.format(serOutCommand).encode('ascii'))
                                ser.flush()
                            except serial.SerialTimeoutException:
                                logger.error("Serial write timeout occurred!")

                    time.sleep(0.1)
                except KeyboardInterrupt :
                    print("Stopped.")
                except Exception as e:
                    log_app_error(e)

            while len(RAList) > 0 :
                ra= RAList.pop()
                del ra
            while len(AAList) > 0 :
                aa= AAList.pop()
                del aa
            while len(ADList) > 0 :
                ad= ADList.pop()
                del ad
            while len(KSList) > 0 :
                ks= KSList.pop()
                del ks
        except serial.SerialException as e:
            logger.critical("Could not open serial! {0}".format(sys.exc_info()[1]))
        except Exception as e:
            log_app_error(e)
        finally:
            if ser:
                ser.close()

    del comm.mqtt

    logger.info("Stopped.")
    logger.debug("^^^^^---------^---------^^^^^")

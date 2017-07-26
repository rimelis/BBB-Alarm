from mmap import mmap
import time, struct

GPIO2_offset = 0x481ac000
GPIO2_size = 0x481acfff-GPIO2_offset
GPIO_OE = 0x134
GPIO_SETDATAOUT = 0x194
GPIO_CLEARDATAOUT = 0x190
GPIO_DATAOUT = 0x13C
GPIO_DATAIN = 0x138
GPIO2_4 = 1<<4
GPIO2_5 = 1<<5

with open("/dev/mem", "r+b" ) as f:
  mem = mmap(f.fileno(), GPIO2_size, offset=GPIO2_offset)

reg = struct.unpack("<L", mem[GPIO_DATAOUT:GPIO_DATAOUT+4])[0]
print (reg & GPIO2_4)
print (reg)

mem.close()

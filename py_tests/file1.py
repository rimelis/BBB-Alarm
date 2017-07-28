import mmap

with open("/sys/class/gpio/gpio69/value", "r") as f:
    map = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    print(map.read_byte())
    map.flush()
    map.seek(0)
    print(map.read_byte())
    map.close()

    

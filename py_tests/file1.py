import mmap, os

mfd = os.open('/sys/class/gpio/gpio69/value', os.O_RDONLY)
mm = mmap.mmap(mfd, 0, access=mmap.ACCESS_READ)

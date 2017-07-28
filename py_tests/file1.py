f = file("'/sys/class/gpio/gpio69/value'", "r")
f.seek(0, 2)  # Seek relative to end of file
size = fh.tell()
fh = f.fileno()

print(size)
print(fh)

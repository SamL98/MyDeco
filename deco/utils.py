import math

def addr_to_str(addr):
    addr_int = int(math.floor(addr))
    return '%s.%02d' % (hex(addr_int), (addr - addr_int) * 100)

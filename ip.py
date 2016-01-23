import struct

class addr:
    def __eq__(self, other):
        return isinstance(other, addr) and other._addr == self._addr

    def _op(self, other, op,instance= True):
        if isinstance(other, addr):
            r = op(self._addr, other._addr)
        elif isinstance(other, int):
            r = op(self._addr, other)
        else:
            raise TypeError('Expected instance of the same class or int')
        if instance:
            return self.__class__(r)
        else:
            return r

    def __and__(self, other):
        return self._op(other, lambda x,y: x & y)

    def __or__(self, other):
        return self._op(other, lambda x,y: x | y)

    def __add__(self, other):
        return self._op(other, lambda x,y: x + y)

    def __sub__(self, other):
        return self._op(other, lambda x,y: x - y)

    def __xor__(self, other):
        return self._op(other, lambda x,y: x ^ y)

    def __lshift__(self, other):
        return self._op(other, lambda x,y: x << y)

    def __rshift__(self, other):
        return self._op(other, lambda x,y: x >> y)

    def __eq__(self, other):
        return self._op(other, lambda x,y: x == y, instance=False)

    def __ne__(self, other):
        return self._op(other, lambda x,y: x != y, instance=False)

    def __lt__(self, other):
        return self._op(other, lambda x,y: x < y, instance=False)

    def __le__(self, other):
        return self._op(other, lambda x,y: x <= y, instance=False)

    def __gt__(self, other):
        return self._op(other, lambda x,y: x > y, instance=False)

    def __ge__(self, other):
        return self._op(other, lambda x,y: x >= y, instance=False)

    def __bytes__(self):
        return str(self).encode('ascii')

    def __repr__(self):
        return '%s(%d)' % (self.__class__.__name__, self._addr)

    def __int__(self):
        return self._addr

    def __invert__(self):
        return ~self._addr

class IpAddr(addr):
    def __init__(self, address):
        if isinstance(address, str):
            address = bytes(address, 'ascii')

        if isinstance(address, bytes):
            octets = list(map(int, address.split(b'.')))

            if len(octets) == 2:
                octets = [octets[0],0,0,octets[1]]
            elif len(octets) == 3:
                octets = [octets[0],octets[1],0,octets[2]]
            elif len(octets) > 4:
                raise TypeError('Invalid IP address')

            self._addr = 0
            for val in octets:
                if val < 0 or val > 255:
                    raise TypeError('Invalid IP address')

                self._addr <<= 8
                self._addr |= val
        elif isinstance(address, int):
            if address < 0 or address > 4294967295:
                raise TypeError('Invalid IP address')
            self._addr = address
        elif isinstance(address, IpAddr):
            self._addr = address._addr
        else:
            raise TypeError('IP address can only be created from bytes. str or int')

    def __str__(self):
        octets = []
        addr = self._addr
        for i in range(4):
            val = addr & 255
            addr >>= 8
            octets.insert(0, str(val))
        return '.'.join(octets)
    def __bytes__(self):
        return struct.pack('!I', self._addr)

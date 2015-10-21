import struct


class nstruct(object):

    '''
    Provides a named struct. An object is created providing
    the fmt string in the same way as for the struct module
    and then providing a (ordered) iterable of field names.

    Then the unpack function returns a dictionary rather than
    a tuple, and the pack function accepts a dictionary or
    named parameters.
    '''

    def __init__(self, fmt, fields):
        self._s = struct.Struct(fmt)
        self._fields = tuple(fields)
        self.size = self._s.size

    def unpack(self, buffer):
        return {k: v for k, v in zip(self._fields, self._s.unpack(buffer))}

    def pack(self, *args, **kwargs):
        '''
        Valid ways to call this function are:

        pack(0,0,0)
        pack(arg0=0, arg1=1)
        pack({'arg0': 0, 'arg1': 1})
        '''

        if len(args) and isinstance(args[0], dict):
            d = args[0]
        elif len(kwargs) > 0:
            d = kwargs
        else:
            d = {k: v for k, v in zip(self._fields, args)}

        r = [d[i] for i in self._fields]
        return self._s.pack(*r)

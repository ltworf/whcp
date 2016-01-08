import struct
from itertools import repeat

from nstruct import nstruct

bootp_message = nstruct(
    '!BBBBIHHIIII16s64s128sI',
    (
        'OP', # Message type
        'HTYPE', # Hardware type
        'HLEN', # Hardware address length
        'HOPS',
        'XID', # Transaction id
        'SECS', # Seconds elapsed
        'FAGS', #
        'CIADDR', # (Client IP address)
        'YIADDR', # (Your Client IP address)
        'SIADDR', # (Next Server IP address)
        'GIADDR', # (Gateway IP address)
        'CHADDR', # (Client hardware address)
        'SHOST', # Server host name
        'BOOTP', # Bootp file
        'COOKIE', # Magic cookie
    )
)

class DHCPOption:
    END = 255
    GATEWAY = 3
    DNS = 6
    MESSAGE_TYPE = 53
    SERVER_IDENTIFIER = 54
    REQUESTED_IP = 50
    LEASE_TIME = 51
    MAXIMUM_SIZE = 57
    VENDOR_CLASS_ID = 60
    HOST_NAME = 12
    PARAMETER_REQUEST = 55

    def __init__(self, raw_data):
        if raw_data is not None:
            _,length = struct.unpack('!BB', raw_data[:2])
            type,length,data = struct.unpack('!BB%ds' % length, raw_data)
            self.data = data
            self.type = type
            self.length = length
        else:
            self.data = b''
            self.type = 0
            self.length = 0

    def pack(self):
        if self.type == END:
            return b'\xff'
        return struct.pack('!BB', self.type, len(self.data)) + self.data

class DHCPPacket:
    BOOTP_REQUEST = 1


    def __init__(self, raw_packet):
        if len(raw_packet) < bootp_message.size:
            raise TypeError('Message too short for a DHCP packet')
        self.bootp = bootp_message.unpack(raw_packet[:bootp_message.size])

        self.hwaddr = self.bootp['CHADDR'][:self.bootp['HLEN']]

        self.options = []

        raw_options = raw_packet[bootp_message.size:]

        while len(raw_options)>=2:
            type,length = struct.unpack('!BB', raw_options[:2])

            if type == DHCPOption.END:
                break

            self.options.append(DHCPOption(raw_options[:length+2]))
            raw_options = raw_options[length+2:]

    def _find_option(self, type):
        return tuple(
            filter(
                lambda i: i.type == type,
                self.options
            )
        )

    def is_discovery(self):
        m = self._find_option(DHCPOption.MESSAGE_TYPE)
        if len(m) == 0:
            return False
        return m[0].data == b'\x03'

    def get_hostname(self):
        '''
        Returns the hostname or
        None
        '''
        m = self._find_option(DHCPOption.HOST_NAME)
        if not len(m):
            return None
        return m[0].data

    def get_requested_addr(self):
        '''
        Returns the requested IP (as int)
        or 0
        '''
        m = self._find_option(DHCPOption.REQUESTED_IP)
        if not len(m):
            return 0
        return struct.unpack('!I', m[0].data)[0]

    def is_request(self):
        # TODO
        pass

    def pack(self):
        bootp = self.bootp.pack()
        options = (i.pack() for i in self.options)
        padding_size = 548 - len(bootp + options)

        if padding_size < 0:
            #TODO Log an error
            pass

        padding = b''.join(repeat(b'\0', padding_size))

        return bootp + options + padding


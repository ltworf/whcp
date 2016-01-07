import struct

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
    MESSAGE_TYPE = 53
    REQUESTED_IP = 50
    MAXIMUM_SIZE = 57
    VENDOR_CLASS_ID = 60
    HOST_NAME = 12
    PARAMETER_REQUEST = 55

    def __init__(self, raw_data):
        _,length = struct.unpack('!BB', raw_data[:2])
        type,length,data = struct.unpack('!BB%ds' % length, raw_data)
        self.data = data

class DHCPPacket:
    def __init__(self, raw_packet):
        if len(raw_packet) < bootp_message.size:
            raise TypeError('Message too short for a DHCP packet')
        self.bootp = bootp_message.unpack(raw_packet[:bootp_message.size])

        self.options = []

        raw_options = raw_packet[bootp_message.size:]

        while len(raw_options)>=2:
            type,length = struct.unpack('!BB', raw_options[:2])

            if type == DHCPOption.END:
                break

            self.options.append(DHCPOption(raw_options[:length+2]))
            raw_options = raw_options[length+2:]




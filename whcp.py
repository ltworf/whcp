#!/usr/bin/env python3

import socket
import IN
import sys
import getopt

from dhcp import DHCPPacket, DHCPOption
from leases import Leases
import ip

def make_reply(message, client_addr, message_type):
    offer = DHCPPacket(message)
    offer.bootp['OP'] = 2
    offer.bootp['SECS'] = 0
    offer.bootp['YIADDR'] = client_addr
    offer.options = []

    # Type offer
    option = DHCPOption(None)
    option.type = DHCPOption.MESSAGE_TYPE
    option.data = message_type
    offer.options.append(option)

    # Server ADDRESS
    option = DHCPOption(None)
    option.type = DHCPOption.SERVER_IDENTIFIER
    option.data = b'0000' # FIXME Int IP address of server
    offer.options.append(option)

    # Lease time
    option = DHCPOption(None)
    option.type = DHCPOption.LEASE_TIME
    option.data = b'\xff\xff\xff\x00' # 1 day
    offer.options.append(option)

    # Gateway
    option = DHCPOption(None)
    option.type = DHCPOption.GATEWAY
    option.data = b'0000' # FIXME Int IP addr of server
    offer.options.append(option)

    # Mask
    option = DHCPOption(None)
    option.type = DHCPOption.MASK
    option.data = b'\xff\xff\xff\x00' # FIXME
    offer.options.append(option)

    # DNS
    option = DHCPOption(None)
    option.type = DHCPOption.DNS
    option.data = b'0000' # FIXME Int IP addr of DNS
    offer.options.append(option)

    # End
    option = DHCPOption(None)
    option.type = DHCPOption.END
    offer.options.append(option)

    return offer

def create_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET,IN.SO_BINDTODEVICE,b'eth0' + b'\0') #experimental
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(('',67))
    return s

s = create_socket()
# FIXME custom IP range
leases = Leases(b'10.0.1.50', b'10.0.1.100')

while 1: #main loop
    try:
        message, addressf = s.recvfrom(8192)

        print(message, addressf)

        if addressf[0] != '0.0.0.0':
            print ('Not to 0.0.0.0')
            # Broken message
            continue

        try:
            dhcp_message = DHCPPacket(message)
        except:
            # Ignore all sort of malformed messages
            print ('Not dhcp parsable')
            continue

        if dhcp_message.bootp['OP'] != DHCPPacket.BOOTP_REQUEST:
            print ('Not REQUEST')
            continue

        if dhcp_message.is_discovery():
            client_addr = None

            # Check if requested address can be given
            if dhcp_message.get_requested_addr():
                if leases.request_lease(
                    dhcp_message.hwaddr,
                    dhcp_message.get_requested_addr(),
                    dhcp_message.get_hostname(),
                ):
                    client_addr = dhcp_message.get_requested_addr()

            if client_addr is None:
                client_addr = leases.request_address(
                    dhcp_message.hwaddr,
                    dhcp_message.get_hostname(),
                )

            print('Giving out address: %s' %ip.IpAddr(client_addr))

            offer = make_reply(message, client_addr, b'\x02')
            data = offer.pack()
            s.sendto(data,('<broadcast>',68))

        elif dhcp_message.is_request():

            if not leases.request_lease(
                dhcp_message.hwaddr,
                dhcp_message.get_requested_addr(),
                dhcp_message.get_hostname(),
            ):
                # IP can't be granted, ignoring
                continue

            client_addr = dhcp_message.get_requested_addr()

            offer = make_reply(message, client_addr, b'\x05')
            data = offer.pack()
            s.sendto(data,(str(ip.IpAddr(client_addr)),68))

        else:
            print ('Else :(')

    except KeyboardInterrupt:
        exit()

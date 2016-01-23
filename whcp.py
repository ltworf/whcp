#!/usr/bin/env python3

import socket
import IN
import sys
import getopt

from dhcp import DHCPPacket, DHCPOption
from leases import Leases
import ip


def make_reply(message, client_addr, message_type, params):
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
    # option = DHCPOption(None)
    # option.type = DHCPOption.SERVER_IDENTIFIER
    # option.data = b'0000' # FIXME Int IP address of server
    # offer.options.append(option)

    # Lease time
    option = DHCPOption(None)
    option.type = DHCPOption.LEASE_TIME
    option.data = b'\xff\xff\xff\x00'  # 1 day
    offer.options.append(option)

    # Gateway
    option = DHCPOption(None)
    option.type = DHCPOption.GATEWAY
    option.data = bytes(params.gateway)
    offer.options.append(option)

    # Mask
    option = DHCPOption(None)
    option.type = DHCPOption.MASK
    option.data = bytes(params.netmask)
    offer.options.append(option)

    # DNS
    option = DHCPOption(None)
    option.type = DHCPOption.DNS
    option.data = bytes(params.dns)
    offer.options.append(option)

    # End
    option = DHCPOption(None)
    option.type = DHCPOption.END
    offer.options.append(option)

    return offer


def create_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, b'eth0' + b'\0')
                 #experimental
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(('', 67))
    return s


def set_params():
    h = ip.IpAddr('10.0.0.100')
    bytes(h)
    str(h)
    int(h)

    class Params:
        pass

    p = Params()

    p.gateway = ip.IpAddr('0.0.0.0')
    p.dns = ip.IpAddr('8.8.8.8')
    p.netmask = ip.IpAddr('255.0.0.0')
    p.rangel = ip.IpAddr('10.0.0.50')
    p.rangeh = ip.IpAddr('10.0.0.100')

    switches, _ = getopt.getopt(sys.argv[1:], 'g:d:n:r:R:')

    for i in switches:
        if i[0] == '-g':
            p.gateway = ip.IpAddr(i[1])
        if i[0] == '-d':
            p.dns = ip.IpAddr(i[1])
        if i[0] == '-n':
            p.netmask = ip.IpAddr(i[1])
        if i[0] == '-r':
            p.rangel = ip.IpAddr(i[1])
        if i[0] == '-R':
            p.rangeh = ip.IpAddr(i[1])
    return p


def main():
    params = set_params()
    s = create_socket()
    print('Leasing addresses in range %s - %s' %
          (params.rangel, params.rangeh))
    leases = Leases(params.rangel, params.rangeh)

    while 1:  # main loop
        try:
            message, addressf = s.recvfrom(8192)

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

                offer = make_reply(message, client_addr, b'\x02', params)
                data = offer.pack()
                s.sendto(data, ('<broadcast>', 68))

            elif dhcp_message.is_request():

                if not leases.request_lease(
                    dhcp_message.hwaddr,
                    dhcp_message.get_requested_addr(),
                    dhcp_message.get_hostname(),
                ):
                    # IP can't be granted, ignoring
                    continue

                client_addr = dhcp_message.get_requested_addr()
                print('Giving out address: %s to %s ' %
                      (ip.IpAddr(client_addr), dhcp_message.get_hostname()))

                offer = make_reply(message, client_addr, b'\x05', params)
                data = offer.pack()
                s.sendto(data, (str(ip.IpAddr(client_addr)), 68))
                # s.sendto(data,('<broadcast>',68))
            else:
                print ('Unsupported DHCP message')

        except KeyboardInterrupt:
            exit()

if __name__ == '__main__':
    main()

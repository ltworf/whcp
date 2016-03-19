#!/usr/bin/env python3

import socket
import IN
import sys
import getopt

from dhcp import DHCPPacket, DHCPOption
from leases import Leases
import ip


class Params:

    '''
    Holds the parameters for this program
    '''

    def __init__(self):
        self.gateway = ip.IpAddr('0.0.0.0')
        self.dns = ip.IpAddr('8.8.8.8')
        self.netmask = ip.IpAddr('255.0.0.0')
        self.rangel = ip.IpAddr('10.0.0.50')
        self.rangeh = ip.IpAddr('10.0.0.100')
        self.iface = b'eth0' + b'\0'

    def __str__(self):
        r = 'gateway: %s\n' \
            'DNS: %s\n' \
            'netmask: %s\n' \
            'lease range: %s - %s\n' \
            'network interface: %s\n' % (
                self.gateway,
                self.dns,
                self.netmask,
                self.rangel,
                self.rangeh,
                self.iface.decode('ascii')
            )
        return r


def make_reply(message, client_addr, message_type, params):
    '''
    Creates a reply message.

    The incoming message must be passed so that
    the response will have the same session id.

    client_addr is the address to give.
    message_type can be b'\x05' or b'\x02'
        use x02 to reply to discovery
        and x05 to reply to request
    params is an object that has fields
        with the settings.

    returns a binary string
    '''
    offer = DHCPPacket(message)
    offer.bootp['OP'] = 2
    offer.bootp['SECS'] = 0
    offer.bootp['YIADDR'] = client_addr
    offer.options = []

    # Type offer
    option = DHCPOption()
    option.type = DHCPOption.MESSAGE_TYPE
    option.data = message_type
    offer.options.append(option)

    # Server ADDRESS
    # option = DHCPOption()
    # option.type = DHCPOption.SERVER_IDENTIFIER
    # option.data = b'0000' # FIXME Int IP address of server
    # offer.options.append(option)

    # Lease time
    option = DHCPOption()
    option.type = DHCPOption.LEASE_TIME
    option.data = b'\xff\xff\xff\x00'  # 1 day
    offer.options.append(option)

    # Gateway
    option = DHCPOption()
    option.type = DHCPOption.GATEWAY
    option.data = bytes(params.gateway)
    offer.options.append(option)

    # Mask
    option = DHCPOption()
    option.type = DHCPOption.MASK
    option.data = bytes(params.netmask)
    offer.options.append(option)

    # DNS
    option = DHCPOption()
    option.type = DHCPOption.DNS
    option.data = bytes(params.dns)
    offer.options.append(option)

    # End
    option = DHCPOption()
    option.type = DHCPOption.END
    offer.options.append(option)

    return offer


def create_socket(params):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # experimental
        s.setsockopt(socket.SOL_SOCKET, IN.SO_BINDTODEVICE, params.iface)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', 67))
        return s
    except PermissionError:
        print("Permission error", file=sys.stderr)
        sys.exit(10)
    except:
        print("Unable to create and bind the socket", file=sys.stderr)
        sys.exit(11)



def print_help(e=0):
    p = Params()
    print('Usage: %s [OPTIONS]' % sys.argv[0])
    print()
    print('  -h     Print help and exit')
    print('  -v     Print version and exit')
    print('  -i     Set network interface')
    print('         whcp only binds one interface at a time')
    print('         default value: %s' % p.iface.decode('ascii'))
    print('  -g     Set gateway')
    print('         default value: %s' % p.gateway)
    print('  -d     Set DNS')
    print('         default value: %s' % p.dns)
    print('  -n     Set netmask')
    print('         default value: %s' % p.netmask)
    print('  -r     Set lower end of lease range')
    print('         default value: %s' % p.rangel)
    print('  -R     Set higher end of lease range')
    print('         default value: %s' % p.rangeh)
    sys.exit(e)


def set_params():
    p = Params()
    switches, f = getopt.getopt(sys.argv[1:], 'hvi:g:d:n:r:R:')

    if f:
        print_help(1)

    for i in switches:
        if i[0] == '-g':
            p.gateway = ip.IpAddr(i[1])
        elif i[0] == '-d':
            p.dns = ip.IpAddr(i[1])
        elif i[0] == '-n':
            p.netmask = ip.IpAddr(i[1])
        elif i[0] == '-r':
            p.rangel = ip.IpAddr(i[1])
        elif i[0] == '-R':
            p.rangeh = ip.IpAddr(i[1])
        elif i[0] == '-i':
            p.iface = i[1].encode('ascii') + b'\0'
        elif i[0] == '-h':
            print_help(0)
        else:
            print_help(1)
    return p


def main():
    params = set_params()
    s = create_socket(params)
    print(params)
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
                s.sendto(data, ('<broadcast>', 68))
            else:
                print ('Unsupported DHCP message')

        except KeyboardInterrupt:
            exit()

if __name__ == '__main__':
    main()

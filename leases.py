import random
import time

import ip

class Leases:
    def __init__(self, lower, higher):
        '''
        Keeps track of the assigned leases

        Leases(b'10.1.1.3',b'10.1.1.100')
        '''

        self.lower = ip.IpAddr(lower)
        self.higher = ip.IpAddr(higher)

        # Keep track of the leases.
        # Indexes as ints
        self._leases = {}

    def request_address(self, hwaddr, domain_name=b''):
        while True:
            random_addr = random.randint(
                int(self.lower),
                int(self.higher)
            )
            if random_addr not in self._leases:
                self._leases[random_addr] = (
                    hwaddr,
                    time.time(),
                    domain_name,
                )
                return random_addr

    def request_lease(self, hwaddr, preferred, domain_name=b''):
        '''
        All parameters as bytes.
        Preferred can be an int or a b'0.0.0.0'

        Returns True if the requested IP can be given out
        False if not
        '''
        preferred = ip.IpAddr(preferred)

        current = self._leases.get(
            int(preferred),
            (hwaddr, time.time(), domain_name)
        )

        if current[0] == hwaddr:
            return True
        return False



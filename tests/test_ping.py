from unittest import TestCase, main
from scapy.all import *
from json import dumps


from srv6_ping.ping import ping1


class TestSRv6Ping(TestCase):

    def test_ping_destination_srh(self):
        results = []
        for _ in range(3):
            result = ping1(dst="2001:db8:10::2", including_srh=True)
            if result:
                results.append(result)
        
        self.assertTrue(len(results) > 0)
        if len(results) > 0:
            self.assertEqual("EchoReply", results[0]["msg"])
    
    def test_srv6_ping(self):
        results = []
        for _ in range(3):
            result = ping1(dst="2001:db8:30::2", segs=["2001:db8:10::2", "2001:db8:20::2"])
            if result:
                results.append(result)
        
        self.assertTrue(len(results) > 0)
        if len(results) > 0:
            self.assertEqual("EchoReply", results[0]["msg"])
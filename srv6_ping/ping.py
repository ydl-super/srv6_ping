import time
import json
from typing import List, Optional

from scapy.all import Packet, IPv6, ICMPv6EchoRequest, IPv6ExtHdrSegmentRouting, IPv6ExtHdrSegmentRoutingTLV, ICMPv6EchoReply, sr1, RandString, debug
from scapy.layers.inet6 import ICMPv6EchoReply, ICMPv6DestUnreach, ICMPv6PacketTooBig, ICMPv6TimeExceeded, ICMPv6ParamProblem


def ping_and_show(dst: str, segs: List[str] = None, hlim=64, timeout=3, max_count=-1, srh_tlvs: List[IPv6ExtHdrSegmentRoutingTLV] = None, json_format=False):
    try:
        count=0
        while (max_count < 0) or (count < max_count):
            result = ping1(dst, segs, hlim=hlim, timeout=timeout, srh_tlvs=srh_tlvs)
            result.pop("sent_pkt", None)
            result.pop("recv_pkt", None)
            if result:
                if json_format:
                    result_format = {"result": result}
                    print(json.dumps(result_format))
                else:
                    print("%s: code=%d from=%s hlim=%d rtt=%f" % \
                          (result["msg"], result["code"], result["recv_from"], result["hlim"], result["rtt"]))
            else:
                if json_format:
                    result_format = {"result": "timeout"}
                    print(json.dumps(result_format))
                else:
                    print("timeout.")
            count += 1
            time.sleep(1)
    except KeyboardInterrupt:
        if not json_format:
            print("end.")


def _ping1(packet: Packet, timeout: int, verbose: int, return_pkt: bool) -> Optional[dict]:
    start = time.time()
    rep = sr1(packet, timeout=timeout, verbose=verbose, chainCC=True)
    if rep:
        end = time.time()
        result = {}
        result["hlim"] = rep[IPv6].hlim
        result["recv_from"] = rep[IPv6].src
        result["rtt"] = (end - start)*1000
        
        if return_pkt:
            result["sent_pkt"] = packet
            result["recv_pkt"] = rep

        code = -1
        msg = "UNKOWN"
        if ICMPv6EchoReply in rep:
            code = rep[ICMPv6EchoReply].code
            msg = "EchoReply"
        elif ICMPv6DestUnreach in rep:
            code = rep[ICMPv6DestUnreach].code
            msg = "DestUnreach"
        elif ICMPv6PacketTooBig in rep:
            code = rep[ICMPv6PacketTooBig].code
            msg = "PacketTooBig"
        elif ICMPv6TimeExceeded in rep:
            code = rep[ICMPv6TimeExceeded].code
            msg = "TimeExceeded"
        elif ICMPv6ParamProblem in rep:
            code = rep[ICMPv6ParamProblem].code
            msg = "ParamProblem"
        result["code"] = code
        result["msg"] = msg

        return result
    else:
        return None


def ping1(dst: str, segs: List[str] = None, hlim=64, timeout=3, verbose=0, including_srh=True, srh_tlvs: List[IPv6ExtHdrSegmentRoutingTLV] = None, return_pkt=False) -> Optional[dict]:
    packet = new_icmp_packet(dst, segs, hlim=hlim, including_srh=including_srh)
    if srh_tlvs and IPv6ExtHdrSegmentRouting in packet:
        for tlv in srh_tlvs:
            packet[IPv6ExtHdrSegmentRouting].tlv_objects.append(tlv)
    return _ping1(packet, timeout, verbose, return_pkt=return_pkt)


def new_icmp_packet(dst: str, segs: List[str] = None, hlim=64, including_srh=True) -> Packet:
    echo_req = ICMPv6EchoRequest(data=RandString(32))
    
    if segs and len(segs) > 0 and segs[0] != "":
        s = segs[::-1]
        s.insert(0, dst)
        return IPv6(dst=s[-1], hlim=hlim)/IPv6ExtHdrSegmentRouting(addresses=s)/echo_req
    else:
        if including_srh:
            return IPv6(dst=dst, hlim=hlim)/IPv6ExtHdrSegmentRouting(addresses=[dst])/echo_req
        else:
            return IPv6(dst=dst, hlim=hlim)/echo_req


def new_srh_tlv(type, value) -> IPv6ExtHdrSegmentRoutingTLV:
    length = len(value)
    return IPv6ExtHdrSegmentRoutingTLV(type=type, len=length, value=value)

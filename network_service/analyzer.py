from collections import defaultdict
from pathlib import Path
from typing import BinaryIO

import dpkt


def _open_reader(stream: BinaryIO):
    try:
        return dpkt.pcap.Reader(stream)
    except (ValueError, dpkt.dpkt.NeedData):
        stream.seek(0)
        return dpkt.pcapng.Reader(stream)


def _ip_packet(frame: bytes, data_link: int):
    if data_link == dpkt.pcap.DLT_EN10MB:
        payload = dpkt.ethernet.Ethernet(frame).data
    elif data_link == dpkt.pcap.DLT_LINUX_SLL:
        payload = dpkt.sll.SLL(frame).data
    elif data_link == dpkt.pcap.DLT_RAW:
        payload = frame
    else:
        return None

    if isinstance(payload, (dpkt.ip.IP, dpkt.ip6.IP6)):
        return payload

    if isinstance(payload, bytes) and payload:
        version = payload[0] >> 4

        if version == 4:
            return dpkt.ip.IP(payload)

        if version == 6:
            return dpkt.ip6.IP6(payload)

    return None


def analyze_pcap(
    path: str | Path,
) -> dict[str, int | float | None]:
    total_bytes = 0
    payload_bytes = 0
    retransmissions = 0
    zero_windows = 0
    resets = 0

    seen_sequences: dict[
        tuple[str, int, str, int],
        set[tuple[int, int]],
    ] = defaultdict(set)

    syn_times: dict[tuple[str, int, str, int], float] = {}
    handshake_rtts: list[float] = []

    with open(path, "rb") as stream:
        packets = _open_reader(stream)
        data_link = packets.datalink()

        for timestamp, frame in packets:
            total_bytes += len(frame)

            try:
                ip = _ip_packet(frame, data_link)
            except (dpkt.dpkt.UnpackError, ValueError):
                continue

            if ip is None:
                continue

            if isinstance(ip.data, dpkt.udp.UDP):
                payload_bytes += len(ip.data.data)
                continue

            if not isinstance(ip.data, dpkt.tcp.TCP):
                continue

            tcp = ip.data
            flags = tcp.flags
            payload_length = len(tcp.data)

            payload_bytes += payload_length

            if int(tcp.win) == 0:
                zero_windows += 1

            if flags & 0x04:
                resets += 1

            forward = (
                bytes(ip.src),
                int(tcp.sport),
                bytes(ip.dst),
                int(tcp.dport),
            )
            reverse = (
                forward[2],
                forward[3],
                forward[0],
                forward[1],
            )

            is_syn = bool(flags & dpkt.tcp.TH_SYN)
            is_ack = bool(flags & dpkt.tcp.TH_ACK)

            if is_syn and not is_ack:
                syn_times.setdefault(
                    forward,
                    float(timestamp),
                )
            elif is_syn and is_ack and reverse in syn_times:
                handshake_rtts.append(
                    (
                        float(timestamp)
                        - syn_times.pop(reverse)
                    )
                    * 1000
                )

            sequence_size = (
                payload_length
                + int(is_syn)
                + int(bool(flags & dpkt.tcp.TH_FIN))
            )

            if sequence_size > 0:
                marker = (int(tcp.seq), sequence_size)

                if marker in seen_sequences[forward]:
                    retransmissions += 1
                else:
                    seen_sequences[forward].add(marker)

    overhead_bytes = max(total_bytes - payload_bytes, 0)

    return {
        "handshake_rtt_ms": (
            round(
                sum(handshake_rtts) / len(handshake_rtts),
                3,
            )
            if handshake_rtts
            else None
        ),
        "retransmission_count": retransmissions,
        "zero_window_count": zero_windows,
        "tcp_reset_count": resets,
        "total_bytes": total_bytes,
        "payload_bytes": payload_bytes,
        "overhead_ratio": (
            round(overhead_bytes / total_bytes, 6)
            if total_bytes
            else 0.0
        ),
    }
